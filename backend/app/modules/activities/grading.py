"""Deterministic server-side grading engine and type-dispatched strategies."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

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
    """Grades sequence arrangement activities, supporting single or multiple acceptable orders."""

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

        acceptable_orders = answer_key.get("acceptable_orders")
        correct_order = answer_key.get("correct_order")

        if not acceptable_orders and not correct_order:
            raise GradingError("Ordering answer key is misconfigured.", code="INVALID_CONFIG", status_code=500)

        candidate_orders: list[list[str]] = (
            [order for order in acceptable_orders if isinstance(order, list)]
            if acceptable_orders
            else ([correct_order] if isinstance(correct_order, list) else [])
        )

        if not candidate_orders:
            raise GradingError("Ordering answer key has no valid target sequence.", code="INVALID_CONFIG", status_code=500)

        total_positions = len(expected_ids)
        best_matches = 0
        is_exact_match = False

        for candidate in candidate_orders:
            if len(candidate) == total_positions:
                matches = sum(
                    1 for idx, item_id in enumerate(ordered_ids) if item_id == candidate[idx]
                )
                if matches > best_matches:
                    best_matches = matches
                if matches == total_positions:
                    is_exact_match = True
                    break

        points_per_pos = 100.0 / total_positions if total_positions > 0 else 0.0
        score = 100.0 if is_exact_match else round(best_matches * points_per_pos, 2)
        passed = score >= passing_score

        return GradingResult(
            score=score,
            max_score=100.0,
            passed=passed,
            status=AttemptStatus.GRADED,
            result={
                "matching_positions": best_matches,
                "total_positions": total_positions,
                "is_exact_match": is_exact_match,
            },
            feedback={
                "message": (
                    "Perfect order!"
                    if is_exact_match
                    else f"{best_matches} of {total_positions} items in correct relative position."
                ),
                "explanation": (feedback_config or {}).get("explanation"),
            },
        )


# ── 7. Matching Grader ───────────────────────────────────────────────────────


class MatchingGrader(BaseGrader):
    """Grades bipartite matching activities between left and right item groups, supporting multi-target acceptable pairs."""

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
        acceptable_pairs = answer_key.get("acceptable_pairs", {})
        if not key_pairs and not acceptable_pairs:
            raise GradingError("Matching answer key is misconfigured.", code="INVALID_CONFIG", status_code=500)

        all_target_keys = set(key_pairs.keys()).union(acceptable_pairs.keys())
        total_pairs = len(all_target_keys)
        correct_count = 0
        pair_breakdown: dict[str, bool] = {}

        for left_id in all_target_keys:
            actual_right = pairs.get(left_id)
            matched = False
            if actual_right:
                if left_id in key_pairs and actual_right == key_pairs[left_id]:
                    matched = True
                elif left_id in acceptable_pairs:
                    acc = acceptable_pairs[left_id]
                    if (isinstance(acc, list) and actual_right in acc) or (isinstance(acc, str) and actual_right == acc):
                        matched = True
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


# ── 10. Web Development Practice Grader ─────────────────────────────────────


SAFE_URL_REGEX = re.compile(r"^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+$")


def _validate_safe_url(url: str, field_name: str) -> None:
    if not url or not isinstance(url, str):
        raise GradingError(f"{field_name} must be a valid string.", code="INVALID_URL")
    url_trimmed = url.strip()
    if len(url_trimmed) > 500:
        raise GradingError(f"{field_name} exceeds maximum length of 500 characters.", code="URL_TOO_LONG")
    if not SAFE_URL_REGEX.match(url_trimmed):
        raise GradingError(
            f"{field_name} contains invalid characters or unsafe scheme.",
            code="UNSAFE_URL_SCHEME",
        )
    parsed = urlparse(url_trimmed)
    if parsed.scheme.lower() not in ("http", "https"):
        raise GradingError(
            f"{field_name} must use http or https protocol.",
            code="UNSAFE_URL_SCHEME",
        )
    if not parsed.netloc or "." not in parsed.netloc:
        raise GradingError(
            f"{field_name} must include a valid domain name.",
            code="INVALID_DOMAIN",
        )


class WebPracticeGrader(BaseGrader):
    """Deterministic validation and scoring for web development practice deliverables.

    SECURITY INVARIANT: External URLs are strictly validated for safe protocols (HTTP/HTTPS)
    and domain syntax. The platform NEVER fetches, executes, or sandboxes external repositories
    or live demonstration URLs automatically during practice grading.
    """

    def grade(
        self,
        configuration: dict[str, Any],
        answer_key: dict[str, Any],
        submission: dict[str, Any],
        passing_score: float,
        feedback_config: dict[str, Any] | None = None,
    ) -> GradingResult:
        require_repo = configuration.get("require_repo_url", True)
        require_live = configuration.get("require_live_url", False)
        require_reflection = configuration.get("require_reflection", True)

        repo_url = submission.get("repo_url")
        live_url = submission.get("live_url")
        notes = submission.get("implementation_notes", "")
        completed_milestones = set(submission.get("completed_milestone_ids", []))
        reflection_answers = submission.get("reflection_answers", {})
        reflection_text = submission.get("reflection", "")

        url_validation: dict[str, Any] = {}

        # 1. URL format and protocol validation
        if require_repo or repo_url:
            if not repo_url:
                raise GradingError("Repository URL is required for this exercise.", code="MISSING_REPO_URL")
            _validate_safe_url(str(repo_url), "Repository URL")
            url_validation["repo_url"] = "valid"

        if require_live or live_url:
            if not live_url and require_live:
                raise GradingError("Live demonstration URL is required for this exercise.", code="MISSING_LIVE_URL")
            if live_url:
                _validate_safe_url(str(live_url), "Live demonstration URL")
                url_validation["live_url"] = "valid"

        # 2. Milestones validation
        milestones = configuration.get("milestones", [])
        required_milestone_ids = {
            m["id"] for m in milestones if isinstance(m, dict) and m.get("required", True)
        }
        all_milestone_ids = {
            m["id"] for m in milestones if isinstance(m, dict) and "id" in m
        }

        # Check for invalid milestone IDs
        invalid_ids = completed_milestones.difference(all_milestone_ids)
        if invalid_ids:
            raise GradingError(
                f"Unknown milestone ID(s): {', '.join(sorted(invalid_ids))}",
                code="UNKNOWN_MILESTONE_ID",
            )

        # 3. Reflection validation
        reflection_length = len(str(reflection_text).split())
        for ans in reflection_answers.values() if isinstance(reflection_answers, dict) else []:
            reflection_length += len(str(ans).split())

        if require_reflection and reflection_length < 10:
            raise GradingError(
                "Technical reflection must be provided (at least 10 words).",
                code="INSUFFICIENT_REFLECTION",
            )

        # 4. Deterministic Rubric Scoring:
        # Deliverables (URLs & notes): 35 pts
        # Required Milestones: 45 pts
        # Reflection: 20 pts
        deliverable_score = 0.0
        if repo_url:
            deliverable_score += 25.0
        if live_url or not require_live:
            deliverable_score += 10.0

        milestone_score = 0.0
        if required_milestone_ids:
            completed_req = completed_milestones.intersection(required_milestone_ids)
            milestone_score = (len(completed_req) / len(required_milestone_ids)) * 45.0
        else:
            milestone_score = 45.0

        reflection_score = 0.0
        if require_reflection:
            reflection_score = 20.0 if reflection_length >= 10 else 10.0
        else:
            reflection_score = 20.0

        total_score = round(min(100.0, deliverable_score + milestone_score + reflection_score), 2)
        passed = total_score >= passing_score

        return GradingResult(
            score=total_score,
            max_score=100.0,
            passed=passed,
            status=AttemptStatus.GRADED,
            result={
                "url_validation": url_validation,
                "completed_milestones_count": len(completed_milestones),
                "required_milestones_total": len(required_milestone_ids),
                "reflection_words": reflection_length,
            },
            feedback={
                "message": (
                    "Web development deliverables verified and milestones satisfied!"
                    if passed
                    else "Deliverables submitted, but passing criteria threshold was not reached."
                ),
                "url_validation": url_validation,
                "milestones_completed": f"{len(completed_milestones)} of {len(all_milestone_ids)} milestones completed",
                "notes_provided": bool(notes and len(str(notes).strip()) > 0),
                "security_notice": "URLs were validated for safe schemes and domain format. External repositories/demonstrations are not executed or fetched automatically.",
                "explanation": (feedback_config or {}).get("explanation"),
            },
        )


# ── 11. Communication Practice Grader (BLUF & STAR) ─────────────────────────


class CommunicationGrader(BaseGrader):
    """Deterministic structural verification and scoring for professional communication practice (BLUF and STAR)."""

    def grade(
        self,
        configuration: dict[str, Any],
        answer_key: dict[str, Any],
        submission: dict[str, Any],
        passing_score: float,
        feedback_config: dict[str, Any] | None = None,
    ) -> GradingResult:
        comm_format = str(submission.get("format") or configuration.get("format", "bluf")).lower()
        if comm_format not in ("bluf", "star"):
            raise GradingError(f"Unsupported communication format: '{comm_format}'", code="UNKNOWN_FORMAT")

        sections = submission.get("sections")
        if not isinstance(sections, dict):
            raise GradingError("sections must be a dictionary of section names to written responses.", code="INVALID_SUBMISSION")

        reflection = str(submission.get("reflection") or "").strip()
        section_breakdown: dict[str, Any] = {}
        total_words = 0

        if reflection:
            refl_words = len(reflection.split())
            section_breakdown["reflection"] = {
                "word_count": refl_words,
                "meets_requirements": refl_words >= 5,
                "status": "complete" if refl_words >= 5 else "brief",
            }
            total_words += refl_words

        if comm_format == "bluf":
            # BLUF: Bottom Line Up Front
            # Expected sections: bottom_line, context_details, next_steps
            expected_keys = ["bottom_line", "context_details", "next_steps"]
            bl_text = str(sections.get("bottom_line", "")).strip()
            if not bl_text:
                raise GradingError("Bottom Line (BLUF) is required and cannot be empty.", code="MISSING_BLUF")

            bl_words = len(bl_text.split())
            if bl_words < 5:
                raise GradingError("Bottom line must be a concise, substantive statement (at least 5 words).", code="BLUF_TOO_SHORT")

            section_breakdown["bottom_line"] = {
                "word_count": bl_words,
                "meets_requirements": bl_words >= 5,
                "status": "complete",
            }
            total_words += bl_words

            details_text = str(sections.get("context_details", "")).strip()
            details_words = len(details_text.split())
            section_breakdown["context_details"] = {
                "word_count": details_words,
                "meets_requirements": details_words >= 10,
                "status": "complete" if details_words >= 10 else "needs_substance",
            }
            total_words += details_words

            steps_text = str(sections.get("next_steps", "")).strip()
            steps_words = len(steps_text.split())
            section_breakdown["next_steps"] = {
                "word_count": steps_words,
                "meets_requirements": steps_words >= 5,
                "status": "complete" if steps_words >= 5 else "needs_substance",
            }
            total_words += steps_words

            # Scoring:
            # bottom_line: 40 pts
            # context_details: 35 pts
            # next_steps: 25 pts
            score = 0.0
            if bl_words >= 5:
                score += 40.0
            if details_words >= 10:
                score += 35.0
            elif details_words > 0:
                score += 20.0
            if steps_words >= 5:
                score += 25.0
            elif steps_words > 0:
                score += 15.0

        else:
            # STAR: Situation, Task, Action, Result
            expected_keys = ["situation", "task", "action", "result"]
            score = 0.0
            for key in expected_keys:
                sec_text = str(sections.get(key, "")).strip()
                sec_words = len(sec_text.split()) if sec_text else 0
                total_words += sec_words

                meets_req = sec_words >= 10
                section_breakdown[key] = {
                    "word_count": sec_words,
                    "meets_requirements": meets_req,
                    "status": "complete" if meets_req else ("incomplete" if sec_words > 0 else "missing"),
                }
                if meets_req:
                    score += 25.0
                elif sec_words >= 5:
                    score += 15.0

        # Word count range enforcement if configured
        min_total = configuration.get("min_total_words")
        max_total = configuration.get("max_total_words")
        if min_total and total_words < min_total:
            score = max(0.0, score - 15.0)
        if max_total and total_words > max_total:
            score = max(0.0, score - 10.0)

        passed = score >= passing_score

        return GradingResult(
            score=round(score, 2),
            max_score=100.0,
            passed=passed,
            status=AttemptStatus.GRADED,
            result={
                "format": comm_format,
                "total_words": total_words,
                "section_breakdown": section_breakdown,
            },
            feedback={
                "message": (
                    f"Professional {comm_format.upper()} structure verified successfully!"
                    if passed
                    else f"Response submitted, but some {comm_format.upper()} sections were incomplete or too brief."
                ),
                "format": comm_format,
                "total_words": total_words,
                "section_breakdown": section_breakdown,
                "qualitative_notice": "This score is based on structural completeness and length requirements. Use the AI Writing Review button for qualitative feedback on tone, clarity, and impact.",
                "explanation": (feedback_config or {}).get("explanation"),
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
            ActivityType.WEB_PRACTICE: WebPracticeGrader(),
            ActivityType.COMMUNICATION: CommunicationGrader(),
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
