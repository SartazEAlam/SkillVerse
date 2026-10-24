"""Deterministic server-side grading engine and type-dispatched strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.infrastructure.sandbox.runner import (
    CodeExecutionRequest,
    ExecutionStatus,
    sandbox_runner,
)
from app.modules.activities.models import ActivityType, AttemptStatus


class GradingError(Exception):
    """Raised when activity configuration or learner submission is invalid for grading."""

    def __init__(self, message: str, code: str = "GRADING_ERROR", status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


@dataclass
class GradingResult:
    """Structured evaluation outcome computed on the server."""

    score: float | None
    max_score: float
    passed: bool | None
    status: AttemptStatus
    result: dict[str, Any] = field(default_factory=dict)
    feedback: dict[str, Any] = field(default_factory=dict)


class BaseGrader:
    """Base class for activity-specific grading strategies."""

    def grade(
        self,
        configuration: dict[str, Any],
        answer_key: dict[str, Any],
        submission: dict[str, Any],
        passing_score: float,
        feedback_config: dict[str, Any] | None = None,
    ) -> GradingResult:
        raise NotImplementedError


# ── 1. Single Choice Grader ──────────────────────────────────────────────────


class SingleChoiceGrader(BaseGrader):
    """Grades single-choice / multiple-choice single-answer activities."""

    def grade(
        self,
        configuration: dict[str, Any],
        answer_key: dict[str, Any],
        submission: dict[str, Any],
        passing_score: float,
        feedback_config: dict[str, Any] | None = None,
    ) -> GradingResult:
        selected_id = submission.get("selected_option_id")
        if not selected_id or not isinstance(selected_id, str):
            raise GradingError("A single option must be selected.", code="INVALID_SUBMISSION")

        options = configuration.get("options", [])
        valid_ids = {opt["id"] for opt in options if isinstance(opt, dict) and "id" in opt}
        if selected_id not in valid_ids:
            raise GradingError(
                f"Selected option '{selected_id}' is not a valid choice for this activity.",
                code="UNKNOWN_OPTION_ID",
            )

        correct_id = answer_key.get("correct_option_id")
        if not correct_id:
            raise GradingError("Activity answer key is misconfigured.", code="INVALID_CONFIG", status_code=500)

        is_correct = selected_id == correct_id
        score = 100.0 if is_correct else 0.0
        passed = score >= passing_score

        explanations = (feedback_config or {}).get("explanations", {})
        selected_explanation = explanations.get(selected_id, "")
        overall_feedback = (feedback_config or {}).get("summary", "")

        return GradingResult(
            score=score,
            max_score=100.0,
            passed=passed,
            status=AttemptStatus.GRADED,
            result={
                "selected_option_id": selected_id,
                "is_correct": is_correct,
            },
            feedback={
                "is_correct": is_correct,
                "message": "Correct! Well done." if is_correct else "Incorrect answer. Review the concept and try again.",
                "explanation": selected_explanation or overall_feedback or None,
            },
        )


# ── 2. Multiple Select Grader ────────────────────────────────────────────────


class MultipleSelectGrader(BaseGrader):
    """Grades multiple-select activities with partial credit and negative penalization."""

    def grade(
        self,
        configuration: dict[str, Any],
        answer_key: dict[str, Any],
        submission: dict[str, Any],
        passing_score: float,
        feedback_config: dict[str, Any] | None = None,
    ) -> GradingResult:
        selected_ids = submission.get("selected_option_ids")
        if not isinstance(selected_ids, list):
            raise GradingError("selected_option_ids must be a list of strings.", code="INVALID_SUBMISSION")

        # Check for duplicates
        if len(selected_ids) != len(set(selected_ids)):
            raise GradingError("Duplicate option selections are not allowed.", code="DUPLICATE_OPTIONS")

        options = configuration.get("options", [])
        valid_ids = {opt["id"] for opt in options if isinstance(opt, dict) and "id" in opt}

        for sid in selected_ids:
            if sid not in valid_ids:
                raise GradingError(f"Option '{sid}' does not belong to this activity.", code="UNKNOWN_OPTION_ID")

        correct_ids = set(answer_key.get("correct_option_ids", []))
        if not correct_ids:
            raise GradingError("Activity answer key is misconfigured.", code="INVALID_CONFIG", status_code=500)

        submitted_set = set(selected_ids)
        correct_selected = submitted_set.intersection(correct_ids)
        incorrect_selected = submitted_set.difference(correct_ids)

        # Deterministic Partial Credit Policy:
        # Each correct selection awards (100 / total_correct).
        # Each incorrect selection (false positive) penalizes (100 / total_correct).
        # Total score is strictly bounded between [0.0, 100.0].
        points_per_item = 100.0 / len(correct_ids)
        raw_score = (len(correct_selected) * points_per_item) - (len(incorrect_selected) * points_per_item)
        score = max(0.0, min(100.0, round(raw_score, 2)))
        passed = score >= passing_score

        return GradingResult(
            score=score,
            max_score=100.0,
            passed=passed,
            status=AttemptStatus.GRADED,
            result={
                "correct_selections_count": len(correct_selected),
                "incorrect_selections_count": len(incorrect_selected),
                "total_correct_required": len(correct_ids),
                "selected_option_ids": list(selected_ids),
            },
            feedback={
                "score_percentage": score,
                "message": (
                    "All correct options selected!"
                    if score == 100.0
                    else (
                        "Partially correct." if score > 0.0 else "Incorrect selections. Review the question."
                    )
                ),
                "breakdown": {
                    "correct_count": len(correct_selected),
                    "incorrect_count": len(incorrect_selected),
                    "missed_count": len(correct_ids - correct_selected),
                },
                "general_explanation": (feedback_config or {}).get("summary"),
            },
        )


# ── 3. True / False Grader ───────────────────────────────────────────────────


class TrueFalseGrader(BaseGrader):
    """Grades boolean true/false statements."""

    def grade(
        self,
        configuration: dict[str, Any],
        answer_key: dict[str, Any],
        submission: dict[str, Any],
        passing_score: float,
        feedback_config: dict[str, Any] | None = None,
    ) -> GradingResult:
        selected_bool = submission.get("selected_boolean")
        if not isinstance(selected_bool, bool):
            raise GradingError("A boolean answer (True or False) is required.", code="INVALID_SUBMISSION")

        correct_bool = answer_key.get("correct_boolean")
        if correct_bool is None or not isinstance(correct_bool, bool):
            raise GradingError("Answer key missing correct boolean setting.", code="INVALID_CONFIG", status_code=500)

        is_correct = selected_bool == correct_bool
        score = 100.0 if is_correct else 0.0
        passed = score >= passing_score

        explanation = (feedback_config or {}).get("explanation")

        return GradingResult(
            score=score,
            max_score=100.0,
            passed=passed,
            status=AttemptStatus.GRADED,
            result={"selected_boolean": selected_bool, "is_correct": is_correct},
            feedback={
                "is_correct": is_correct,
                "message": "Correct!" if is_correct else "Incorrect.",
                "explanation": explanation,
            },
        )


# ── 4. Short Answer Grader ───────────────────────────────────────────────────


class ShortAnswerGrader(BaseGrader):
    """Grades short answers via normalized exact match or manual rubric queuing."""

    def grade(
        self,
        configuration: dict[str, Any],
        answer_key: dict[str, Any],
        submission: dict[str, Any],
        passing_score: float,
        feedback_config: dict[str, Any] | None = None,
    ) -> GradingResult:
        text = submission.get("text")
        if text is None or not isinstance(text, str):
            raise GradingError("Short answer submission must contain 'text'.", code="INVALID_SUBMISSION")

        cleaned = text.strip()
        max_len = configuration.get("max_length", 2000)
        if len(cleaned) == 0:
            raise GradingError("Short answer cannot be blank.", code="EMPTY_SUBMISSION")
        if len(cleaned) > max_len:
            raise GradingError(f"Submission exceeds maximum length of {max_len} characters.", code="SUBMISSION_TOO_LONG")

        # Check if subjective / review required
        review_required = answer_key.get("review_required", False)
        if review_required:
            return GradingResult(
                score=None,
                max_score=100.0,
                passed=None,
                status=AttemptStatus.REVIEW_REQUIRED,
                result={"submitted_length": len(cleaned)},
                feedback={
                    "message": "Your response has been received and queued for instructor/rubric evaluation.",
                    "status": "awaiting_review",
                },
            )

        # Objective normalized matching
        accepted = answer_key.get("accepted_answers", [])
        if not accepted:
            raise GradingError("No accepted answers configured for objective short answer.", code="INVALID_CONFIG", status_code=500)

        case_sensitive = answer_key.get("case_sensitive", False)
        norm_submission = cleaned if case_sensitive else cleaned.lower()
        norm_accepted = [a.strip() if case_sensitive else a.strip().lower() for a in accepted]

        is_match = norm_submission in norm_accepted
        score = 100.0 if is_match else 0.0
        passed = score >= passing_score

        return GradingResult(
            score=score,
            max_score=100.0,
            passed=passed,
            status=AttemptStatus.GRADED,
            result={"matched": is_match},
            feedback={
                "is_correct": is_match,
                "message": "Correct response!" if is_match else "Your response did not match the expected answer.",
                "explanation": (feedback_config or {}).get("explanation"),
            },
        )


# ── 5. Fill-in-the-Blank Grader ──────────────────────────────────────────────


class FillBlankGrader(BaseGrader):
    """Grades multi-blank fill-in-the-blank questions with independent field weights."""

    def grade(
        self,
        configuration: dict[str, Any],
        answer_key: dict[str, Any],
        submission: dict[str, Any],
        passing_score: float,
        feedback_config: dict[str, Any] | None = None,
    ) -> GradingResult:
        answers = submission.get("answers")
        if not isinstance(answers, dict):
            raise GradingError("Answers must be a dictionary of blank ID to text.", code="INVALID_SUBMISSION")

        configured_blanks = configuration.get("blanks", [])
        if not configured_blanks:
            raise GradingError("Activity blanks are not configured.", code="INVALID_CONFIG", status_code=500)

        blank_keys = answer_key.get("blanks", {})
        correct_count = 0
        total_blanks = len(configured_blanks)
        breakdown: dict[str, bool] = {}

        for blank in configured_blanks:
            b_id = blank.get("id")
            if not b_id:
                continue

            submitted_val = str(answers.get(b_id, "")).strip()
            key_data = blank_keys.get(b_id, {})
            accepted = key_data.get("accepted_answers", [])
            case_sens = key_data.get("case_sensitive", False)

            norm_sub = submitted_val if case_sens else submitted_val.lower()
            norm_accepted = [a.strip() if case_sens else a.strip().lower() for a in accepted]

            matched = bool(norm_sub and norm_sub in norm_accepted)
            breakdown[b_id] = matched
            if matched:
                correct_count += 1

        points_per_blank = 100.0 / total_blanks if total_blanks > 0 else 0.0
        score = round(correct_count * points_per_blank, 2)
        passed = score >= passing_score

        return GradingResult(
            score=score,
            max_score=100.0,
            passed=passed,
            status=AttemptStatus.GRADED,
            result={
                "correct_blanks": correct_count,
                "total_blanks": total_blanks,
                "breakdown": breakdown,
            },
            feedback={
                "message": (
                    "All blanks filled correctly!"
                    if correct_count == total_blanks
                    else f"{correct_count} of {total_blanks} blanks correct."
                ),
                "breakdown": breakdown,
                "explanation": (feedback_config or {}).get("explanation"),
            },
        )


# ── 6. Ordering Grader ───────────────────────────────────────────────────────


class OrderingGrader(BaseGrader):
    """Grades sequence arrangement activities."""

    def grade(
        self,
        configuration: dict[str, Any],
        answer_key: dict[str, Any],
        submission: dict[str, Any],
        passing_score: float,
        feedback_config: dict[str, Any] | None = None,
    ) -> GradingResult:
        ordered_ids = submission.get("ordered_item_ids")
        if not isinstance(ordered_ids, list):
            raise GradingError("ordered_item_ids must be a list of item IDs.", code="INVALID_SUBMISSION")

        items = configuration.get("items", [])
        expected_ids = [item["id"] for item in items if isinstance(item, dict) and "id" in item]

        if set(ordered_ids) != set(expected_ids) or len(ordered_ids) != len(expected_ids):
            raise GradingError(
                "Submission must include all configured items exactly once with no duplicates.",
                code="INVALID_ITEM_SET",
            )

        correct_order = answer_key.get("correct_order", [])
        if not correct_order or len(correct_order) != len(expected_ids):
            raise GradingError("Ordering answer key is misconfigured.", code="INVALID_CONFIG", status_code=500)

        total_positions = len(correct_order)
        matching_positions = sum(
            1 for idx, item_id in enumerate(ordered_ids) if item_id == correct_order[idx]
        )

        points_per_pos = 100.0 / total_positions if total_positions > 0 else 0.0
        score = round(matching_positions * points_per_pos, 2)
        passed = score >= passing_score

        return GradingResult(
            score=score,
            max_score=100.0,
            passed=passed,
            status=AttemptStatus.GRADED,
            result={
                "matching_positions": matching_positions,
                "total_positions": total_positions,
            },
            feedback={
                "message": (
                    "Perfect order!"
                    if matching_positions == total_positions
                    else f"{matching_positions} of {total_positions} items in correct relative position."
                ),
                "explanation": (feedback_config or {}).get("explanation"),
            },
        )


# ── 7. Matching Grader ───────────────────────────────────────────────────────


class MatchingGrader(BaseGrader):
    """Grades bipartite matching activities between left and right item groups."""

    def grade(
        self,
        configuration: dict[str, Any],
        answer_key: dict[str, Any],
        submission: dict[str, Any],
        passing_score: float,
        feedback_config: dict[str, Any] | None = None,
    ) -> GradingResult:
        pairs = submission.get("pairs")
        if not isinstance(pairs, dict):
            raise GradingError("pairs must be a dictionary of left_id -> right_id.", code="INVALID_SUBMISSION")

        left_items = configuration.get("left_items", [])
        right_items = configuration.get("right_items", [])
        valid_left = {item["id"] for item in left_items if isinstance(item, dict) and "id" in item}
        valid_right = {item["id"] for item in right_items if isinstance(item, dict) and "id" in item}

        for left_id, right_id in pairs.items():
            if left_id not in valid_left:
                raise GradingError(f"Left item '{left_id}' is invalid.", code="UNKNOWN_LEFT_ID")
            if right_id not in valid_right:
                raise GradingError(f"Right item '{right_id}' is invalid.", code="UNKNOWN_RIGHT_ID")

        key_pairs = answer_key.get("pairs", {})
        if not key_pairs:
            raise GradingError("Matching answer key is misconfigured.", code="INVALID_CONFIG", status_code=500)

        total_pairs = len(key_pairs)
        correct_count = 0
        pair_breakdown: dict[str, bool] = {}

        for left_id, expected_right in key_pairs.items():
            actual_right = pairs.get(left_id)
            matched = actual_right == expected_right
            pair_breakdown[left_id] = matched
            if matched:
                correct_count += 1

        points_per_pair = 100.0 / total_pairs if total_pairs > 0 else 0.0
        score = round(correct_count * points_per_pair, 2)
        passed = score >= passing_score

        return GradingResult(
            score=score,
            max_score=100.0,
            passed=passed,
            status=AttemptStatus.GRADED,
            result={
                "correct_pairs": correct_count,
                "total_pairs": total_pairs,
                "breakdown": pair_breakdown,
            },
            feedback={
                "message": (
                    "All pairs matched correctly!"
                    if correct_count == total_pairs
                    else f"{correct_count} of {total_pairs} pairs matched correctly."
                ),
                "breakdown": pair_breakdown,
                "explanation": (feedback_config or {}).get("explanation"),
            },
        )


# ── 8. Scenario Decision Grader ──────────────────────────────────────────────


class ScenarioGrader(BaseGrader):
    """Grades realistic professional decision-making scenarios."""

    def grade(
        self,
        configuration: dict[str, Any],
        answer_key: dict[str, Any],
        submission: dict[str, Any],
        passing_score: float,
        feedback_config: dict[str, Any] | None = None,
    ) -> GradingResult:
        decision_id = submission.get("selected_decision_id")
        if not decision_id or not isinstance(decision_id, str):
            raise GradingError("A decision must be selected.", code="INVALID_SUBMISSION")

        decisions = configuration.get("decisions", [])
        valid_ids = {d["id"] for d in decisions if isinstance(d, dict) and "id" in d}
        if decision_id not in valid_ids:
            raise GradingError(f"Decision '{decision_id}' is not in the scenario options.", code="UNKNOWN_DECISION_ID")

        best_id = answer_key.get("best_decision_id")
        acceptable_ids = set(answer_key.get("acceptable_decision_ids", []))
        explanations = (feedback_config or {}).get("explanations", {})
        decision_feedback = explanations.get(decision_id, "")

        if decision_id == best_id:
            score = 100.0
            passed = True
            msg = "Optimal decision selected! This approach demonstrates high-leverage judgment."
        elif decision_id in acceptable_ids:
            score = max(passing_score, 75.0)
            passed = True
            msg = "Acceptable decision, though an even higher-leverage strategy was available."
        else:
            score = 0.0
            passed = False
            msg = "Suboptimal decision with unintended negative friction."

        return GradingResult(
            score=score,
            max_score=100.0,
            passed=passed,
            status=AttemptStatus.GRADED,
            result={"selected_decision_id": decision_id, "is_best": decision_id == best_id},
            feedback={
                "is_correct": passed,
                "message": msg,
                "explanation": decision_feedback or (feedback_config or {}).get("summary"),
            },
        )


# ── 9. Coding Exercise Grader (Sandbox Boundary) ────────────────────────────


class CodingGrader(BaseGrader):
    """Evaluates code submissions via isolated sandbox runner boundary."""

    def grade(
        self,
        configuration: dict[str, Any],
        answer_key: dict[str, Any],
        submission: dict[str, Any],
        passing_score: float,
        feedback_config: dict[str, Any] | None = None,
    ) -> GradingResult:
        code = submission.get("code")
        if not code or not isinstance(code, str) or not code.strip():
            raise GradingError("Code submission cannot be empty.", code="EMPTY_CODE")

        if len(code) > 50000:
            raise GradingError("Code submission exceeds 50,000 character limit.", code="CODE_TOO_LONG")

        language = submission.get("language") or configuration.get("language", "text")
        test_cases = answer_key.get("test_cases", [])

        # INVARIANT: Untrusted code is dispatched to the isolated sandbox boundary
        exec_request = CodeExecutionRequest(
            code=code,
            language=str(language),
            test_cases=test_cases,
            timeout_seconds=5,
        )
        exec_result = sandbox_runner.execute(exec_request)

        if exec_result.status == ExecutionStatus.SERVICE_UNAVAILABLE:
            return GradingResult(
                score=None,
                max_score=100.0,
                passed=None,
                status=AttemptStatus.SUBMITTED,
                result={"execution_status": "service_unavailable"},
                feedback={
                    "status": "service_unavailable",
                    "message": exec_result.message,
                    "error": exec_result.error,
                },
            )

        # When isolated sandbox reports results:
        tests_total = exec_result.tests_total or len(test_cases)
        tests_passed = exec_result.tests_passed
        score = round((tests_passed / tests_total) * 100.0, 2) if tests_total > 0 else 0.0
        passed = score >= passing_score

        return GradingResult(
            score=score,
            max_score=100.0,
            passed=passed,
            status=AttemptStatus.GRADED,
            result={
                "tests_passed": tests_passed,
                "tests_total": tests_total,
                "output": exec_result.output,
            },
            feedback={
                "message": f"{tests_passed} of {tests_total} tests passed.",
                "details": [d.model_dump() for d in exec_result.details],
            },
        )


# ── Unified Grading Engine Dispatcher ────────────────────────────────────────


class GradingEngine:
    """Dispatches submissions to the appropriate type-specific grader strategy."""

    def __init__(self) -> None:
        self._graders: dict[ActivityType, BaseGrader] = {
            ActivityType.SINGLE_CHOICE: SingleChoiceGrader(),
            ActivityType.MULTIPLE_SELECT: MultipleSelectGrader(),
            ActivityType.TRUE_FALSE: TrueFalseGrader(),
            ActivityType.SHORT_ANSWER: ShortAnswerGrader(),
            ActivityType.FILL_IN_THE_BLANK: FillBlankGrader(),
            ActivityType.ORDERING: OrderingGrader(),
            ActivityType.MATCHING: MatchingGrader(),
            ActivityType.SCENARIO: ScenarioGrader(),
            ActivityType.CODE_EXERCISE: CodingGrader(),
        }

    def grade(
        self,
        activity_type: ActivityType | str,
        configuration: dict[str, Any],
        answer_key: dict[str, Any],
        submission: dict[str, Any],
        passing_score: float = 70.0,
        feedback_config: dict[str, Any] | None = None,
    ) -> GradingResult:
        try:
            typed_type = ActivityType(activity_type)
        except ValueError as err:
            raise GradingError(f"Unsupported activity type: '{activity_type}'", code="UNKNOWN_TYPE") from err

        grader = self._graders.get(typed_type)
        if not grader:
            raise GradingError(f"No grader strategy registered for '{typed_type}'", code="NO_GRADER")

        return grader.grade(
            configuration=configuration,
            answer_key=answer_key,
            submission=submission,
            passing_score=passing_score,
            feedback_config=feedback_config,
        )


# Global grading engine instance
grading_engine = GradingEngine()
