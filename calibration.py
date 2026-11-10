"""How well a learner judges their own work, computed from what they predicted, how they scored themselves, and what
the checks found. Pure functions: nothing is stored, so the numbers can always be recomputed from f_entries and
f_checks.

Per mission:
* hit rate: the share of checks where the prediction (pass or fail) matched the result;
* Brier score: the mean of (p - outcome)^2, where p is the stated chance of passing (confidence when the learner
  expected a pass, 1 - confidence when they expected a fail) and outcome is 1 for a pass. 0 is perfect, 1 is worst;
* signed gap: self-scored passes minus checked passes. Positive means the learner rated themselves higher.

Across missions, in the order they were done: the mean Brier score and the slope of the signed gap (negative means
the gap is closing). Checks with no result yet are left out, never counted as a fail.
"""

from __future__ import annotations


def _confidence(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return max(50, min(100, number))


def mission(standard_ids, prediction, self_scores, results) -> dict:
    prediction = prediction if isinstance(prediction, dict) else {}
    self_scores = self_scores if isinstance(self_scores, dict) else {}
    results = results if isinstance(results, dict) else {}
    per_check = []
    squares = []
    hits = 0
    checked = 0
    for check_id in standard_ids:
        guess = prediction.get(check_id) if isinstance(prediction.get(check_id), dict) else {}
        expect = guess.get("expect_pass") if isinstance(guess.get("expect_pass"), bool) else None
        confidence = _confidence(guess.get("confidence")) if expect is not None else None
        mine = self_scores.get(check_id) if isinstance(self_scores.get(check_id), bool) else None
        passed = results.get(check_id) if isinstance(results.get(check_id), bool) else None
        row = {"id": check_id, "expect_pass": expect, "confidence": confidence, "self_pass": mine, "passed": passed,
               "hit": None, "self_gap": None}
        if passed is not None:
            checked += 1
            if expect is not None:
                row["hit"] = expect == passed
                hits += 1 if row["hit"] else 0
                p = confidence / 100 if expect else 1 - confidence / 100
                squares.append((p - (1 if passed else 0)) ** 2)
            if mine is not None:
                row["self_gap"] = int(mine) - int(passed)
        per_check.append(row)
    judged = [r for r in per_check if r["hit"] is not None]
    return {
        "per_check": per_check,
        "checked": checked,
        "hit_rate": (hits / len(judged)) if judged else None,
        "brier": (sum(squares) / len(squares)) if squares else None,
        "predicted_passes": sum(1 for r in per_check if r["expect_pass"] is True),
        "self_passes": sum(1 for r in per_check if r["self_pass"] is True),
        "actual_passes": sum(1 for r in per_check if r["passed"] is True),
        "signed_gap": sum(r["self_gap"] for r in per_check if r["self_gap"] is not None),
    }


def _slope(values):
    n = len(values)
    if n < 2:
        return None
    mean_x = (n - 1) / 2
    mean_y = sum(values) / n
    top = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(values))
    bottom = sum((i - mean_x) ** 2 for i in range(n))
    return top / bottom if bottom else None


def across(missions) -> dict:
    """Missions in the order they were done, each the output of mission()."""
    rows = [m for m in (missions or []) if isinstance(m, dict) and m.get("checked")]
    briers = [m["brier"] for m in rows if m.get("brier") is not None]
    hits = [m["hit_rate"] for m in rows if m.get("hit_rate") is not None]
    gaps = [m.get("signed_gap", 0) for m in rows]
    return {
        "missions": len(rows),
        "brier": (sum(briers) / len(briers)) if briers else None,
        "hit_rate": (sum(hits) / len(hits)) if hits else None,
        "gaps": gaps,
        "trend": _slope(gaps),
    }
