#!/usr/bin/env python3
"""One-shot surgical edits to desktop/plugin.js. Every replacement asserts.

Run from the repo root. Fails loudly if an anchor is missing, so a rename or a
reformat upstream cannot silently skip an edit.
"""

import pathlib
import sys

P = pathlib.Path("desktop/plugin.js")
src = P.read_text(encoding="utf-8")
out = src
applied = []


def sub(label, old, new, count=1):
    global out
    found = out.count(old)
    if found == 0:
        print(f"FAIL  {label}: anchor not found")
        sys.exit(1)
    if count and found != count:
        print(f"WARN  {label}: expected {count} occurrence(s), found {found}")
    out = out.replace(old, new)
    applied.append(label)


# 1 ── imports: the kit primitives this pane should have been using
sub(
    "imports",
    """import {
  Badge,
  Button,
  Codicon,
  Input,
  PALETTE_AREA,""",
    """import {
  Badge,
  Button,
  Codicon,
  EmptyState,
  ErrorState,
  Input,
  Loader,
  PALETTE_AREA,""",
)

# 2 ── own stylesheet for the values the app's build never emits
sub(
    "stylesheet + directive name",
    """const ROUTE = '/academy'
const QUERY_KEY = ['field-academy', 'passport']
const PATHS = ['operator', 'integrator', 'architect', 'ambassador']""",
    """const ROUTE = '/academy'
const QUERY_KEY = ['field-academy', 'passport']
const PATHS = ['operator', 'integrator', 'architect', 'ambassador']

/** The transcript directive this half renders. The agent half names the same
 *  string in DIRECTIVE; a test asserts the two agree, because a rename on one
 *  side alone is a silent no-op. */
const DIRECTIVE = 'field-academy-practice'

/** Classes the app's build never emits. The desktop stylesheet is compiled
 *  from app sources at build time and a runtime plugin file is never scanned,
 *  so an arbitrary-value utility invented here renders unstyled with no error
 *  anywhere. These are prefixed and shipped with the plugin instead of relying
 *  on the app to have compiled them. */
const CSS = `
.fa-fact { display: grid; grid-template-columns: 7.5rem 1fr; gap: 0.75rem; }
.fa-eyebrow { letter-spacing: 0.1em; }
.fa-display { letter-spacing: -0.02em; }
`

/** Directive attributes are untrusted model output. Bound them before use: a
 *  hallucinated value should render nothing, never a wall of text. */
const MISSION_ID_RE = /^[a-z0-9][a-z0-9._-]{0,63}$/i

function Styles() {
  return jsx('style', { dangerouslySetInnerHTML: { __html: CSS } })
}""",
)

# 3 ── the three uncompiled utilities, as whole class strings so the order stays clean
sub("fact row grid", "className: 'grid grid-cols-[7.5rem_1fr] gap-3 text-sm',", "className: 'fa-fact text-sm',")
sub(
    "eyebrow tracking (tertiary)",
    "'text-xs font-semibold tracking-[0.1em] text-(--ui-text-tertiary)'",
    "'fa-eyebrow text-xs font-semibold text-(--ui-text-tertiary)'",
    count=0,
)
sub(
    "eyebrow tracking (accent)",
    "'text-xs font-semibold tracking-[0.1em] text-(--ui-accent)'",
    "'fa-eyebrow text-xs font-semibold text-(--ui-accent)'",
    count=0,
)
sub(
    "display tracking",
    "'mt-4 text-3xl font-semibold leading-tight tracking-[-0.02em] text-(--ui-text-primary)'",
    "'fa-display mt-4 text-3xl font-semibold leading-tight text-(--ui-text-primary)'",
)

# 4 ── opt-in: this plugin adds chrome AND touches message flow
sub("defaultEnabled", "  defaultEnabled: true,", "  defaultEnabled: false,")

# 5 ── 'primary' is not a Button variant; the real one is 'default'
sub(
    "button variant",
    "jsx(Button, { variant: done ? 'secondary' : 'primary', onClick: markRead, children: done ? 'Mark unread' : 'Got it' })",
    "jsx(Button, { variant: done ? 'secondary' : 'default', onClick: markRead, children: done ? 'Mark unread' : 'Got it' })",
)

# 6 ── Button owns its own working state; swapping the label reflows the row
sub(
    "gate busy button",
    """      jsx(Button, {
        disabled: busy || step.status === 'done',
        onClick: run,
        children: step.status === 'done' ? 'Gate passed' : busy ? 'Checking…' : isArtifact ? 'Verify the file' : 'Run the check',
      }),""",
    """      jsx(Button, {
        disabled: step.status === 'done',
        loading: busy,
        onClick: run,
        children: step.status === 'done' ? 'Gate passed' : isArtifact ? 'Verify the file' : 'Run the check',
      }),""",
)
sub(
    "explain busy button",
    "jsx(Button, { disabled: busy, onClick: submit, children: busy ? 'Sending…' : graded ? 'Resubmit for review' : 'Submit for review' }),",
    "jsx(Button, { loading: busy, onClick: submit, children: graded ? 'Resubmit for review' : 'Submit for review' }),",
)

# 7 ── Progress: announce it, do not just draw it
sub(
    "progress aria",
    """  const safe = Number.isFinite(Number(value)) ? Math.max(0, Math.min(100, Number(value))) : 0
  return jsx('div', {
    className: 'h-1 w-full overflow-hidden rounded-full bg-(--ui-bg-tertiary)',""",
    """  const safe = Number.isFinite(Number(value)) ? Math.max(0, Math.min(100, Number(value))) : 0
  return jsx('div', {
    'aria-label': 'Progress',
    'aria-valuemax': 100,
    'aria-valuemin': 0,
    'aria-valuenow': safe,
    className: 'h-1 w-full overflow-hidden rounded-full bg-(--ui-bg-tertiary)',
    role: 'progressbar',""",
)

# 8 ── loading: a Loader, never the literal words
sub(
    "loading state",
    """  if (query.isLoading) {
    return jsx('div', { className: 'px-6 py-16 text-base text-(--ui-text-secondary)', children: 'Loading Field Academy…' })
  }""",
    """  if (query.isLoading) {
    return jsxs('div', { className: 'grid min-h-48 place-items-center gap-3', children: [
      jsx(Loader, { type: 'lemniscate-bloom' }),
      jsx('p', { className: 'text-sm text-(--ui-text-tertiary)', children: 'Loading Field Academy' }),
    ] })
  }""",
)

# 9 ── error and empty: the app's own primitives
sub(
    "offline state",
    """function Offline({ error, onRetry }) {
  return jsxs('div', { className: 'mx-auto max-w-2xl px-6 py-16', children: [
    jsx('h1', { className: 'text-2xl font-semibold text-(--ui-text-primary)', children: 'Field Academy is not connected yet' }),
    jsx('p', { className: 'mt-3 text-base leading-7 text-(--ui-text-secondary)', children: 'The window half is running. The half that saves your progress is not, so nothing you do here would be remembered.' }),
    jsx('pre', { className: 'mt-4 overflow-x-auto rounded-lg bg-(--ui-bg-tertiary) p-3 text-xs text-(--ui-text-tertiary)', children: 'hermes plugins enable field-academy' }),
    jsx('p', { className: 'mt-4 text-sm leading-6 text-(--ui-text-tertiary)', children: 'Run that once in a terminal, restart Hermes, and reopen this page.' }),
    error ? jsx('p', { className: 'mt-4 text-sm leading-6 text-(--ui-text-quaternary)', children: `Reported: ${String(error)}` }) : null,
    jsx(Button, { className: 'mt-6', onClick: onRetry, children: 'Try again' }),
  ] })
}""",
    """function Offline({ error, onRetry }) {
  return jsx('div', { className: 'mx-auto max-w-2xl px-6 py-16', children: jsx(ErrorState, {
    title: 'Field Academy is not connected yet',
    description: 'The window half is running. The half that saves your progress is not, so nothing you do here would be remembered.',
    children: jsxs('div', { className: 'grid gap-3', children: [
      jsx('pre', { className: 'overflow-x-auto rounded-lg bg-(--ui-bg-tertiary) p-3 text-xs text-(--ui-text-tertiary)', children: 'hermes plugins enable field-academy' }),
      jsx('p', { className: 'text-sm leading-6 text-(--ui-text-tertiary)', children: 'Run that once in a terminal, restart Hermes, and reopen this page.' }),
      error ? jsx('p', { className: 'text-sm leading-6 text-(--ui-text-quaternary)', children: `Reported: ${String(error)}` }) : null,
      jsx(Button, { variant: 'secondary', onClick: onRetry, children: 'Try again' }),
    ] }),
  }) })
}""",
)
sub(
    "empty state",
    ": jsx('div', { className: 'px-6 py-16 text-base text-(--ui-text-secondary)', children: 'Nothing here yet.' })",
    """: jsx('div', { className: 'px-6 py-16', children: jsx(EmptyState, {
          title: 'Nothing here yet',
          description: 'Pick a level on the left to see its missions.',
        }) })""",
)

# 10 ── a11y: landmarks and current-item state
sub("nav landmark", "jsx('nav', { className: 'grid gap-1 px-3 pb-6',", "jsx('nav', { 'aria-label': 'Missions', className: 'grid gap-1 px-3 pb-6',")
sub(
    "path pressed",
    """            return jsxs('button', {
              type: 'button',
              onClick: () => choosePath(id),""",
    """            return jsxs('button', {
              type: 'button',
              'aria-pressed': active,
              onClick: () => choosePath(id),""",
)
sub(
    "mission current",
    """              jsxs('button', {
                type: 'button',
                onClick: () => chooseMission(item.id),""",
    """              jsxs('button', {
                type: 'button',
                'aria-current': mission?.id === item.id ? 'true' : undefined,
                onClick: () => chooseMission(item.id),""",
)

# 11 ── the directive: validate the model's input, then render
sub(
    "directive validation",
    """function GrowthDirective({ attrs }) {
  const missionId = attrs?.mission
  if (!missionId) return null""",
    """function GrowthDirective({ attrs }) {
  const raw = typeof attrs?.mission === 'string' ? attrs.mission.trim() : ''
  if (!MISSION_ID_RE.test(raw)) return null
  const missionId = raw""",
)
sub("directive human label", "  const human = missionId.replace('.', ' · ')", "  const human = missionId.replace(/\\./g, ' · ')")
sub(
    "directive style tag",
    """  return jsxs('div', { className: 'my-3 rounded-xl border border-(--ui-stroke-secondary) bg-(--ui-bg-secondary) p-4', children: [
    jsx('div', { className: 'fa-eyebrow text-xs font-semibold text-(--ui-accent)', children: 'ONE OPTIONAL PRACTICE' }),""",
    """  return jsxs('div', { className: 'my-3 rounded-xl border border-(--ui-stroke-secondary) bg-(--ui-bg-secondary) p-4', children: [
    jsx(Styles, {}),
    jsx('div', { className: 'fa-eyebrow text-xs font-semibold text-(--ui-accent)', children: 'ONE OPTIONAL PRACTICE' }),""",
)

# 12 ── the page carries its own stylesheet, and the registration uses DIRECTIVE
sub(
    "page style tag",
    """  return jsxs('div', { className: 'flex h-full min-h-0', children: [
    jsxs('aside', {""",
    """  return jsxs('div', { className: 'flex h-full min-h-0', children: [
    jsx(Styles, {}),
    jsxs('aside', {""",
)
sub(
    "directive registration",
    "data: { name: 'field-academy-practice', render: ({ attrs }) => jsx(GrowthDirective, { attrs }) }",
    "data: { name: DIRECTIVE, render: ({ attrs }) => jsx(GrowthDirective, { attrs }) }",
)

P.write_text(out, encoding="utf-8")
print(f"applied {len(applied)} edits:")
for name in applied:
    print(f"  - {name}")
print(f"\n{len(src.splitlines())} -> {len(out.splitlines())} lines")
