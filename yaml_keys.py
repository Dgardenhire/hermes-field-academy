"""Read named keys from a Hermes ``config.yaml``, and set a few plain values, with no YAML package.

Decision (0.9): Field Academy reads and plants a handful of keys in a practice profile's config. PyYAML ships inside
Hermes, but this plugin takes no outside packages, and a load-then-dump round trip would rewrite the learner's whole
config file: comments, key order and quoting. The editor here changes only the lines it names, so the profile's
fingerprint afterwards differs by exactly the planted keys, which is what the disclosure promises.

The reader is tolerant on purpose. It understands block mappings, block lists (of plain values or of small mappings),
inline ``[a, b]`` lists and plain scalars. Anything else (a ``|`` or ``>`` block of text, an inline ``{...}``
mapping) comes back as ``Text`` and is never looked inside, so a key written inside a block of text can't be
mistaken for a real one. A line it can't place is skipped, never fatal. ``labs.parse_yaml`` stays as it is for the
Guide labs, which want a strict reader that names the broken line.

The writer only sets bool, int, float or one-line string values at a dotted path, or a short list of one-line strings
written as an inline ``["a", "b"]`` list. It refuses to replace a block, a block list or a non-empty inline mapping; an
inline list (``[]`` or ``[a, b]``) may be replaced by another list. After every edit it reads the result back and checks that the named values took
and every other value read the same as before.
"""

from __future__ import annotations

import copy
import json
import re


class Text(str):
    """A value this reader does not look inside: a block of text or an inline mapping."""


_BLOCK = re.compile(r"^[|>][-+0-9]*\s*(?:#.*)?$")
_PLAIN = re.compile(r"^[A-Za-z0-9_./@-]+$")
_RESERVED = {"true", "false", "yes", "no", "on", "off", "null", "~", "none", ""}


def _split_key(text: str):
    """(key, raw key, rest) for a ``key: value`` line, or None."""
    if text[:1] in "\"'":
        quote = text[0]
        end = text.find(quote, 1)
        while quote == "'" and end != -1 and text[end + 1:end + 2] == "'":
            end = text.find(quote, end + 2)
        if end == -1 or text[end + 1:end + 2] != ":":
            return None
        raw = text[:end + 1]
        rest = text[end + 2:]
        if rest and not rest[0].isspace():
            return None
        return _unquote(raw), raw, rest.strip()
    match = re.search(r":(?:\s|$)", text)
    if not match or text.startswith(("#", "- ", "[", "{")) or text == "-":
        return None
    raw = text[:match.start()].rstrip()
    if not raw:
        return None
    return raw, raw, text[match.end():].strip()


def _unquote(raw: str) -> str:
    if raw[:1] == '"':
        try:
            return json.loads(raw)
        except ValueError:
            return raw[1:-1]
    if raw[:1] == "'":
        return raw[1:-1].replace("''", "'")
    return raw


def _strip_comment(text: str) -> str:
    if text[:1] in "\"'":
        return text
    cut = re.search(r"\s#", text)
    return text[:cut.start()].rstrip() if cut else text


def _closing_quote(text: str) -> int:
    """Index of the quote that closes the one at text[0], or -1."""
    quote = text[0]
    i = 1
    while i < len(text):
        ch = text[i]
        if quote == '"' and ch == "\\":
            i += 2
            continue
        if ch == quote:
            if quote == "'" and text[i + 1:i + 2] == "'":
                i += 2
                continue
            return i
        i += 1
    return -1


def _split_flow(inner: str):
    parts, depth, quote, start = [], 0, "", 0
    for i, ch in enumerate(inner):
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(inner[start:i])
            start = i + 1
    parts.append(inner[start:])
    return [p.strip() for p in parts]


def scalar(raw: str):
    text = raw.strip()
    if text[:1] in "\"'":
        end = _closing_quote(text)
        if end > 0 and (text[end + 1:].strip() == "" or text[end + 1:].lstrip().startswith("#")):
            return _unquote(text[:end + 1])
        return Text(text)
    text = _strip_comment(text)
    if text == "":
        return None
    if _BLOCK.match(text):
        return Text("")
    if text == "{}":
        return {}
    if text.startswith("{"):
        return Text(text)
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        items = _split_flow(inner)
        if any(item[:1] in "[{" for item in items):
            return Text(text)
        return [scalar(item) for item in items]
    low = text.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"[-+]?\d+", text):
        return int(text)
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\.\d+)(?:[eE][-+]?\d+)?", text):
        return float(text)
    return text


def lex(text: str):
    """[(line number, indent, text)] for every line that carries YAML, skipping the insides of blocks of text."""
    rows = []
    skip_deeper = None
    for number, raw in enumerate(str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")):
        body = raw.rstrip()
        stripped = body.lstrip(" ")
        indent = len(body) - len(stripped)
        if skip_deeper is not None:
            if not stripped or indent > skip_deeper:
                continue
            skip_deeper = None
        if not stripped or stripped.startswith("#") or stripped in ("---", "...") or stripped.startswith("\t"):
            continue
        rows.append((number, indent, stripped))
        content, column = stripped, indent
        while content.startswith("- ") or content == "-":
            rest = content[1:].lstrip()
            column += len(content) - len(rest)
            content = rest
        parts = _split_key(content)
        value = parts[2] if parts else content
        if value and _BLOCK.match(value):
            skip_deeper = column if parts else indent
    return rows


def _mapping(rows, i, indent):
    out = {}
    while i < len(rows) and rows[i][1] >= indent:
        _, level, text = rows[i]
        if level > indent or text.startswith("-"):
            if level == indent:
                break
            i += 1
            continue
        parts = _split_key(text)
        i += 1
        if not parts:
            continue
        key, _, rest = parts
        if rest == "" or rest.startswith("#"):
            if i < len(rows) and rows[i][1] > indent:
                value, i = _block(rows, i, rows[i][1])
            elif i < len(rows) and rows[i][1] == indent and rows[i][2].startswith("-"):
                value, i = _list(rows, i, indent)
            else:
                value = None
        else:
            value = scalar(rest)
        out[key] = value
    return out, i


def _list(rows, i, indent):
    items = []
    while i < len(rows) and rows[i][1] == indent and (rows[i][2].startswith("- ") or rows[i][2] == "-"):
        text = rows[i][2]
        rest = text[1:].lstrip()
        column = indent + len(text) - len(rest)
        i += 1
        if not rest:
            if i < len(rows) and rows[i][1] > indent:
                value, i = _block(rows, i, rows[i][1])
            else:
                value = None
            items.append(value)
            continue
        parts = _split_key(rest)
        if parts is None:
            items.append(scalar(rest))
            continue
        key, _, value_text = parts
        item = {}
        if value_text == "":
            if i < len(rows) and rows[i][1] > column:
                item[key], i = _block(rows, i, rows[i][1])
            else:
                item[key] = None
        else:
            item[key] = scalar(value_text)
        more, i = _mapping(rows, i, column)
        item.update(more)
        items.append(item)
    while i < len(rows) and rows[i][1] > indent:
        i += 1
    return items, i


def _block(rows, i, indent):
    if rows[i][2].startswith("- ") or rows[i][2] == "-":
        return _list(rows, i, indent)
    return _mapping(rows, i, indent)


def parse(text: str) -> dict:
    """The document as dicts, lists and plain values. Never raises on a strange line."""
    rows = lex(text)
    out = {}
    i = 0
    while i < len(rows):
        indent = rows[i][1]
        if rows[i][2].startswith("-"):
            _, i = _list(rows, i, indent)
            continue
        part, i = _mapping(rows, i, indent)
        for key, value in part.items():
            out.setdefault(key, value)
    return out


def get(tree, path: str, default=None):
    node = tree
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


# ------------------------------------------------------------------ writing --


def _format(value) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(json.dumps(item, ensure_ascii=False) for item in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if value == "":
        return "''"
    if _PLAIN.match(value) and value.lower() not in _RESERVED and scalar(value) == value:
        return value
    return json.dumps(value, ensure_ascii=False)


def _check_value(path, value):
    if isinstance(value, bool) or isinstance(value, (int, float)):
        return
    if isinstance(value, str) and "\n" not in value and "\r" not in value and len(value) <= 500:
        return
    if isinstance(value, list) and len(value) <= 50 and all(
            isinstance(item, str) and "\n" not in item and "\r" not in item and len(item) <= 500 for item in value):
        return
    raise ValueError(f"{path}: only true/false, a number, one line of text or a short list of lines can be written")


def _kids(rows, start, parent_indent):
    """Rows directly in the block that starts after ``start`` (an index into rows) at deeper indent."""
    out = []
    for row in rows[start:]:
        if row[1] <= parent_indent:
            break
        out.append(row)
    return out


def _set_one(lines, path, value):
    rows = lex("\n".join(lines))
    parts = path.split(".")
    span = rows
    parent = None  # (row index, row)
    parent_indent = -1
    for depth, part in enumerate(parts):
        last = depth == len(parts) - 1
        child_indent = min((r[1] for r in span), default=None)
        if span and span[0][2].startswith("-"):
            raise ValueError(f"{'.'.join(parts[:depth]) or 'the file'} holds a list, so {path} can't be set in it")
        found = None
        for row in span:
            if row[1] != child_indent:
                continue
            split = _split_key(row[2])
            if split and split[0] == part:
                found = (row, split)
                break
        if found is None:
            indent = child_indent if child_indent is not None else (parent_indent + 2 if parent else 0)
            new = []
            for extra, name in enumerate(parts[depth:]):
                pad = " " * (indent + 2 * extra)
                key = name if _PLAIN.match(name) else json.dumps(name)
                new.append(f"{pad}{key}: {_format(value)}" if extra == len(parts) - depth - 1 else f"{pad}{key}:")
            if parent is None:
                at = len(lines)
                while at > 0 and lines[at - 1].strip() == "":
                    at -= 1
                lines[at:at] = new
            else:
                lines[parent[1][0] + 1:parent[1][0] + 1] = new
            return
        (number, indent, text), (_, raw_key, rest) = found
        index = rows.index(found[0])
        comment = ""
        bare = _strip_comment(rest)
        if bare != rest:
            comment = "  " + rest[len(bare):].strip()
        kids = _kids(rows, index + 1, indent)
        if not kids and index + 1 < len(rows) and rows[index + 1][1] == indent and rows[index + 1][2].startswith("-"):
            raise ValueError(f"{'.'.join(parts[:depth + 1])} holds a list, so Field Academy won't replace it")
        if last:
            current = scalar(bare) if bare else None
            inline_list = isinstance(current, list) and isinstance(value, list) and not kids
            if not inline_list and (kids or isinstance(current, (Text, list, dict))):
                raise ValueError(f"{path} holds more than one value, so Field Academy won't replace it")
            lines[number] = f"{' ' * indent}{raw_key}: {_format(value)}{comment}"
            return
        if bare and bare not in ("{}", "~", "null"):
            raise ValueError(f"{'.'.join(parts[:depth + 1])} is written on one line, so Field Academy won't rewrite it")
        if bare:
            lines[number] = f"{' ' * indent}{raw_key}:{comment}"
        parent = (index, found[0])
        parent_indent = indent
        span = kids


def _without(tree, paths):
    out = copy.deepcopy(tree)
    for path in paths:
        parts = path.split(".")
        node = out
        for part in parts[:-1]:
            node = node.get(part) if isinstance(node, dict) else None
            if node is None:
                break
        if isinstance(node, dict):
            node.pop(parts[-1], None)
    return out


def _prune_empty(tree):
    if isinstance(tree, dict):
        pruned = {k: _prune_empty(v) for k, v in tree.items()}
        return {k: v for k, v in pruned.items() if not (v is None or v == {})}
    return tree


def set_values(text: str, values: dict) -> str:
    """The text with each dotted path set to its plain value, every other line as it was. Raises ValueError."""
    for path, value in values.items():
        if not re.fullmatch(r"[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*", str(path)):
            raise ValueError(f"{path!r} is not a key path")
        _check_value(path, value)
    source = str(text or "")
    newline = "\r\n" if "\r\n" in source else "\n"
    lines = source.replace("\r\n", "\n").split("\n")
    for path, value in values.items():
        _set_one(lines, path, value)
    out = newline.join(lines)
    if out and not out.endswith(newline):
        out += newline
    before, after = parse(source), parse(out)
    for path, value in values.items():
        got = get(after, path)
        if got != value or type(got) is not type(value):
            raise ValueError(f"{path} did not read back as {value!r} after the edit")
    if _prune_empty(_without(before, values)) != _prune_empty(_without(after, values)):
        raise ValueError("The edit would have changed other settings, so it was not made")
    return out
