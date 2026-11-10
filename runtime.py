"""The bridge to Hermes for Field Academy's model calls. Everything the AI features take from the host comes through here.

Why this file exists. Hermes imports the plugin once to run ``register(ctx)``. The desktop page imports
``dashboard/plugin_api.py`` on its own, and that file loads a second copy of the package under the name
``field_academy_dashboard_package``. The two copies don't share module globals, so a context saved in one copy's
module is invisible to the other. Imprint solves this by loading the page's copy from ``register`` and handing it the
context (``hermes-imprint/__init__.py``). Field Academy keeps the same idea with less loading: the context lives on
one small holder module under a fixed name in ``sys.modules``, which every copy of this file reads and writes. No
second copy of the package is imported just to pass the context along.

- ``set_context`` / ``context``: the ``PluginContext`` that ``register(ctx)`` received, when this process ran it.
- ``llm()``: ``ctx.llm`` when there is a context; otherwise a ``PluginLlm`` bound to this plugin when Hermes's own
  module can be imported; otherwise ``None`` (the harness and the tests, which set a stand-in with ``set_llm``).
- ``data_dir()``: ``plugin-data/field-academy`` inside Hermes, or ``FIELD_ACADEMY_DATA_DIR`` in tests and the
  harness, so they never touch a real profile. AI caches and the token ledger live here.

Nothing in this file calls a model, reads a profile or writes outside the data folder.
"""

from __future__ import annotations

import os
import sys
import threading
import types
from pathlib import Path

PLUGIN_ID = "field-academy"
TASK_GUIDE = "field_academy_guide"
TASK_GRADER = "field_academy_grader"
# The built-in task the guide inherits its model settings from. ``approval`` is Hermes's own short classifier call:
# its defaults say "a fast/cheap model is recommended" and give it a 30 second budget (hermes_cli/config_defaults.py,
# ``auxiliary.approval``). The guide's calls are the same shape: short context in, a sentence or two of JSON out. The
# other candidate, ``title_generation``, is the only task that can opt into a provider's fast tier, but its block also
# carries ``enabled`` and ``model_upgrade_enabled`` switches that mean "make session titles", which a learner who
# turned off titles would inherit by surprise. The grader inherits nothing: it uses the main model (``provider: auto``)
# with the 60 second default, because a level is a judgement and the learner can pin a stronger model in Settings.
GUIDE_INHERITS = "approval"

_HOLDER = "field_academy_runtime_holder"
_lock = threading.Lock()


def _holder() -> types.ModuleType:
    with _lock:
        holder = sys.modules.get(_HOLDER)
        if holder is None:
            holder = types.ModuleType(_HOLDER)
            holder.ctx = None
            holder.llm = None
            sys.modules[_HOLDER] = holder
        return holder


def set_context(ctx) -> None:
    _holder().ctx = ctx


def context():
    return _holder().ctx


def set_llm(llm) -> None:
    """A stand-in model for tests and the harness bench. ``None`` clears it."""
    _holder().llm = llm


def clear() -> None:
    """Forget the context and any stand-in. Tests call this between cases."""
    holder = _holder()
    holder.ctx = None
    holder.llm = None


def llm():
    """The model facade to call, or ``None`` when this process has no way to reach the learner's model."""
    holder = _holder()
    if holder.llm is not None:
        return holder.llm
    ctx = holder.ctx
    found = getattr(ctx, "llm", None) if ctx is not None else None
    if found is not None:
        return found
    try:
        from agent.plugin_llm import PluginLlm  # inside Hermes only
    except Exception:
        return None
    return PluginLlm(plugin_id=PLUGIN_ID)


def data_dir() -> Path:
    override = os.environ.get("FIELD_ACADEMY_DATA_DIR")
    if override:
        path = Path(override)
    else:
        from plugins.plugin_storage import plugin_data_dir  # inside Hermes

        path = Path(plugin_data_dir(PLUGIN_ID))
    path.mkdir(parents=True, exist_ok=True)
    return path
