"""The page routes for Field Academy's AI features, under the plugin's prefix (/api/plugins/field-academy).

``dashboard/plugin_api.py`` calls ``mount(router)`` once. Each route runs its model call on a worker thread, so the
page's other requests keep moving while a model thinks. Shapes are fixed by the contract fixtures in
``tests/data/ai_contract/``; change a shape only with a note to the product owner.

* ``POST /ai/grade/{mission_id}/{step_id}``  body ``{answer}``: Score my answer (``grading.grade_inline``).
* ``GET|POST /settings/ai``  body ``{ai_help?, practice_offer?}``: the two switches.
* ``POST /data/delete``  body ``{keep_records: bool}``: Delete my progress (true) or Delete everything (false), from
  ``forget.delete_data``. A 400 names any practice profile still set up.
* ``GET /guide/{attempt_id}?step=&active=``: the Field guide column (``guide.guide_view``). ``active=practice`` while
  the practice profile is the active one: nothing is fetched then.
* ``POST /guide/{attempt_id}/help``  body ``{rung: 1|2|3, step}`` or ``{action: "explain"|"do_it_with_me", step}``.
* ``POST /guide/{attempt_id}/ask``  body ``{question, step}``.
* ``POST /guide/{attempt_id}/pins``  body ``{make: true, step}`` to ask for pins, or ``{keep, dismiss, add}``.
* ``GET /replay/{attempt_id}?step=``: Replay your run (``recorder.replay``); ``state: "not_ready"`` before Compare.
* ``GET /replay/sample``: the committed sample run (``content/sample_run.json``), labelled as a sample.
* ``POST /first-flight/start``: start mission 3 as a First Flight (``foundations.first_flight_start``).

A refusal the learner can act on (no answer yet, already graded) comes back as a 400 with plain words, the same as the
rest of the page's API. A model failure is not an HTTP error: it is a 200 with ``state`` set to the failure kind, so
the page can show the right words and next step.
"""

from __future__ import annotations

import asyncio

from . import grading, state


def mount(router) -> None:
    from fastapi import HTTPException

    def guard(call, *args, **kwargs):
        try:
            return call(*args, **kwargs)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/ai/grade/{mission_id}/{step_id}")
    async def ai_grade(mission_id: str, step_id: str, body: dict):
        answer = str((body or {}).get("answer", ""))
        return await asyncio.to_thread(guard, grading.grade_inline, mission_id, step_id, answer)

    @router.post("/first-flight/start")
    async def first_flight_start(body: dict = None):
        from . import foundations

        return guard(foundations.first_flight_start)

    @router.get("/first-flight")
    async def first_flight_info():
        from . import foundations

        return {"mission_id": foundations.FIRST_FLIGHT_MISSION, "guess": foundations.FIRST_FLIGHT_GUESS,
                "words": foundations.FIRST_FLIGHT_WORDS, "guide": "The Field guide opens after you answer Did it work?"}

    @router.get("/settings/ai")
    async def ai_settings_get():
        return state.ai_settings()

    @router.post("/settings/ai")
    async def ai_settings_set(body: dict):
        body = body or {}
        return guard(state.set_ai_settings, body.get("ai_help"), body.get("practice_offer"))

    @router.get("/data/delete")
    async def data_delete_check():
        from . import forget

        return {"practice_left": forget.live_practice()}

    @router.post("/data/delete")
    async def data_delete(body: dict):
        from . import forget

        return guard(forget.delete_data, (body or {}).get("keep_records"))

    try:
        from . import recorder
    except ImportError:
        recorder = None
    if recorder is not None:
        recorder.mount(router, guard)  # GET /replay/sample, GET /replay/{attempt_id}?step=
    try:
        from . import guide
    except ImportError:
        return
    guide.mount(router, guard)
