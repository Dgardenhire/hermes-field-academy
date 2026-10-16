"""Tool schemas for the agent half of Field Academy."""

FIELD_ACADEMY_SNAPSHOT = {
    "name": "field_academy_snapshot",
    "description": (
        "Compact Field Academy status: the learner's path, their own goal, how many reviews are due, the active mission with its steps, "
        "and per-track progress. Start here. Call field_academy_mission for the full mission text before teaching."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

FIELD_ACADEMY_MISSION = {
    "name": "field_academy_mission",
    "description": (
        "Full text of one Field Academy mission: the lesson, the worked examples, the lab, the question, the check, and the linked sources. "
        "Pass no id to get the learner's active mission."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "mission_id": {
                "type": "string",
                "description": "Mission id such as operator.runtime. Omit for the active mission.",
            }
        },
        "required": [],
    },
}

FIELD_ACADEMY_GRADE_EXPLANATION = {
    "name": "field_academy_grade_explanation",
    "description": (
        "Record your grade for a Field Academy explanation step. Call this after the learner submits an "
        "explanation for review, using the score and feedback you decided. This is what closes the step; the "
        "learner cannot close it themselves. Passing threshold is 70 unless the mission says otherwise."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "mission_id": {"type": "string", "description": "Mission id, e.g. operator.runtime."},
            "step_id": {"type": "string", "description": "Explanation step id, normally 'explain'."},
            "score": {"type": "integer", "description": "0-100, on substance only."},
            "missed": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "The numbers of the points the answer left out, from the list in the grading instruction. Empty when it covered them all.",
            },
            "feedback": {
                "type": "string",
                "description": "Two or three sentences: what they got right, the specific point they missed, what to add.",
            },
        },
        "required": ["mission_id", "step_id", "score", "feedback"],
    },
}

FIELD_ACADEMY_GRADE_REVIEW = {
    "name": "field_academy_grade_review",
    "description": (
        "Record your grades for a Field Academy review session: three short answers, one per mission, from the learner's "
        "spaced review. Call this once after the learner submits a review for scoring, with one grade per question. "
        "This is what moves each mission's review schedule; the learner cannot do it themselves. Passing is 70."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "session_id": {"type": "string", "description": "The review session id from the grading instruction."},
            "grades": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "mission_id": {"type": "string"},
                        "score": {"type": "integer", "description": "0-100, on substance only."},
                        "missed": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Numbers of the points the answer left out. Empty when it covered them all.",
                        },
                        "feedback": {"type": "string", "description": "Two sentences: what they got right, then the specific point they missed."},
                    },
                    "required": ["mission_id", "score", "feedback"],
                },
            },
        },
        "required": ["session_id", "grades"],
    },
}

FIELD_ACADEMY_RECORD_EVIDENCE = {
    "name": "field_academy_record_evidence",
    "description": (
        "Save a short, non-sensitive note against a mission. Use only after the learner did the work or "
        "asked you to save it. Gates record their own evidence; do not duplicate a gate result here."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "competency_id": {"type": "string", "description": "Mission id."},
            "summary": {"type": "string", "description": "What was done, in one or two sentences."},
            "artifact": {"type": "string", "description": "Safe artifact name or location. Optional."},
        },
        "required": ["competency_id", "summary"],
    },
}


FIELD_ACADEMY_GRADE_DEPLOYER = {
    "name": "field_academy_grade_deployer",
    "description": (
        "Record your grade for a written answer on the Deployer path: a judgment scenario or the prose of the client proposal. "
        "Call this once after the learner submits an answer for scoring, using the item id from the grading instruction "
        "(for example scenario.shared-login, or brief). This is what closes the item; the learner cannot close it themselves. "
        "Score the reasoning, not the verdict. Passing is 70. An answer that already has a score cannot be graded again."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "item_id": {"type": "string", "description": "The item id from the grading instruction, such as brief or scenario.email-customers."},
            "score": {"type": "integer", "description": "0-100, on substance only."},
            "missed": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "The numbers of the points the answer left out, from the list in the grading instruction. Empty when it covered them all.",
            },
            "feedback": {"type": "string", "description": "Two or three sentences: what they did well, the specific point they missed, what to add."},
        },
        "required": ["item_id", "score", "feedback"],
    },
}
