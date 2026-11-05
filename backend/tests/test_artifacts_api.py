"""API tests for submission deliverable artifacts, limits, security, and gated downloads."""

from __future__ import annotations

import concurrent.futures
import io
import shutil
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.infrastructure.rate_limiter import limiter
from app.infrastructure.storage.factory import get_storage_service, reset_storage_service
from app.modules.auth.models import User
from app.modules.projects.artifact_service import ArtifactService
from app.modules.projects.models import (
    Portfolio,
    PortfolioItem,
    PortfolioItemVisibility,
    ProjectArtifact,
    ProjectSubmission,
    SubmissionStatus,
)
from app.modules.skills.models import Discipline, Skill, SkillDifficulty


@pytest.fixture(autouse=True)
def isolated_storage():
    """Ensure tests run against a clean isolated local storage directory."""
    temp_dir = tempfile.mkdtemp(prefix="test_skillverse_storage_")
    old_root = settings.storage_local_root
    old_provider = settings.storage_provider
    settings.storage_local_root = temp_dir
    settings.storage_provider = "local"
    reset_storage_service()

    yield temp_dir

    reset_storage_service()
    settings.storage_local_root = old_root
    settings.storage_provider = old_provider
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def active_draft_submission(
    client: TestClient,
    creator_headers: dict[str, str],
    auth_headers: dict[str, str],
    db: Session,
) -> tuple[str, str]:
    """Fixture returning (project_id, submission_id) in DRAFT status."""
    discipline = Discipline(
        slug="data-eng-disc",
        name="Data Engineering",
        description="Pipelines and ETL engineering",
    )
    db.add(discipline)
    db.commit()

    skill = Skill(
        slug="pipeline-etl",
        name="ETL Pipeline Architecture",
        discipline_id=discipline.id,
        difficulty_level=SkillDifficulty.INTERMEDIATE,
    )
    db.add(skill)
    db.commit()

    project_payload = {
        "title": "ETL Pipeline Capstone",
        "short_description": "Build a robust pipeline ingesting time-series telemetry data.",
        "full_description": "Comprehensive capstone requiring stream buffering, validation, and analytics storage.",
        "discipline_id": discipline.id,
        "difficulty_level": "INTERMEDIATE",
        "requirements": {
            "milestones": [{"id": "m1", "title": "Pipeline Architecture"}],
            "deliverables": ["Pipeline archive"],
        },
        "evaluation_criteria": {
            "passing_score": 70.0,
            "rubric": [{"id": "c1", "title": "Correctness", "max_score": 100.0, "weight": 1.0}],
        },
        "skills": [{"skill_id": skill.id, "is_primary": True}],
    }
    proj_res = client.post("/api/v1/projects", json=project_payload, headers=creator_headers)
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    pub_res = client.post(f"/api/v1/projects/{proj_id}/publish", headers=creator_headers)
    assert pub_res.status_code == 200

    sub_res = client.post(f"/api/v1/projects/{proj_id}/submissions", headers=auth_headers)
    assert sub_res.status_code == 201
    sub_id = sub_res.json()["id"]

    return proj_id, sub_id


def test_upload_valid_artifacts(
    client: TestClient,
    auth_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
) -> None:
    """Learner can upload valid deliverable files (e.g. PDF and text notes)."""
    _, sub_id = active_draft_submission

    # Upload valid text notes
    txt_content = b"Database schema and benchmark analysis report.\nAll tests passing."
    res = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("report.txt", io.BytesIO(txt_content), "text/plain")},
        data={"is_public": "true"},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["original_filename"] == "report.txt"
    assert data["file_size_bytes"] == len(txt_content)
    assert data["is_public"] is True
    assert f"/api/v1/artifacts/{data['id']}/download" in data["download_url"]

    # Upload valid PDF
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
    res2 = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("architecture.pdf", io.BytesIO(pdf_content), "application/pdf")},
        data={"is_public": "false"},
        headers=auth_headers,
    )
    assert res2.status_code == 201
    assert res2.json()["original_filename"] == "architecture.pdf"

    # List submission artifacts
    list_res = client.get(f"/api/v1/submissions/{sub_id}/artifacts", headers=auth_headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total_count"] == 2
    assert list_data["total_size_bytes"] == len(txt_content) + len(pdf_content)


def test_upload_blocked_and_spoofed_files_rejected(
    client: TestClient,
    auth_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
) -> None:
    """Executable extensions and text files containing binary null bytes or MZ headers are strictly rejected."""
    _, sub_id = active_draft_submission

    # 1. Blocked extension .exe
    exe_res = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("payload.exe", io.BytesIO(b"binarycontent"), "application/octet-stream")},
        headers=auth_headers,
    )
    assert exe_res.status_code in (400, 422)
    assert "blocked" in exe_res.json()["error"]["message"]

    # 2. Blocked script .py
    py_res = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("script.py", io.BytesIO(b"import os; os.system('echo')"), "text/x-python")},
        headers=auth_headers,
    )
    assert py_res.status_code in (400, 422)

    # 3. Spoofed text with executable MZ header
    mz_res = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("spoof.txt", io.BytesIO(b"MZ\x90\x00thisisbinaryexecutable"), "text/plain")},
        headers=auth_headers,
    )
    assert mz_res.status_code in (400, 422)
    assert "executable binary signature" in mz_res.json()["error"]["message"]

    # 4. Text file containing null bytes
    null_res = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("null.txt", io.BytesIO(b"Some text\x00corrupted with null byte"), "text/plain")},
        headers=auth_headers,
    )
    assert null_res.status_code in (400, 422)
    assert "null bytes" in null_res.json()["error"]["message"]


def test_upload_to_submitted_project_prohibited(
    client: TestClient,
    auth_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
) -> None:
    """Artifacts cannot be uploaded after submission is SUBMITTED."""
    _, sub_id = active_draft_submission

    # Submit
    client.patch(
        f"/api/v1/submissions/{sub_id}",
        json={"summary": "Finalizing solution deliverables."},
        headers=auth_headers,
    )
    sub_res = client.post(f"/api/v1/submissions/{sub_id}/submit", headers=auth_headers)
    assert sub_res.status_code == 200

    # Attempt to upload artifact to submitted submission
    res = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("notes.txt", io.BytesIO(b"late notes"), "text/plain")},
        headers=auth_headers,
    )
    assert res.status_code in (400, 422)
    assert "draft" in res.json()["error"]["message"]


def test_upload_rate_limiting(
    client: TestClient,
    auth_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
) -> None:
    """Uploading more than 10 artifacts in an hour is throttled with HTTP 429."""
    _, sub_id = active_draft_submission
    limiter.reset()

    # Upload 10 artifacts
    for i in range(10):
        res = client.post(
            f"/api/v1/submissions/{sub_id}/artifacts",
            files={"file": (f"note_{i}.txt", io.BytesIO(f"Notes {i}".encode()), "text/plain")},
            headers=auth_headers,
        )
        assert res.status_code == 201

    # 11th upload should trigger rate limiting (HTTP 429)
    res_11 = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("note_11.txt", io.BytesIO(b"Throttled notes"), "text/plain")},
        headers=auth_headers,
    )
    assert res_11.status_code == 429
    assert res_11.json()["error"]["code"] == "RATE_LIMITED"


def test_delete_artifact(
    client: TestClient,
    auth_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
) -> None:
    """Learner can delete an uploaded artifact while in DRAFT status."""
    _, sub_id = active_draft_submission

    upload_res = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("to_delete.txt", io.BytesIO(b"Temporary artifact content"), "text/plain")},
        headers=auth_headers,
    )
    assert upload_res.status_code == 201
    art_id = upload_res.json()["id"]

    del_res = client.delete(f"/api/v1/artifacts/{art_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # Verify deleted from list
    list_res = client.get(f"/api/v1/submissions/{sub_id}/artifacts", headers=auth_headers)
    assert list_res.status_code == 200
    assert list_res.json()["total_count"] == 0


def test_download_authorization_and_headers(
    client: TestClient,
    auth_headers: dict[str, str],
    creator_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
) -> None:
    """Owner and project creator can download with safe headers; unauthenticated is blocked."""
    _, sub_id = active_draft_submission

    upload_res = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("safe_doc.txt", io.BytesIO(b"Verified safe content"), "text/plain")},
        headers=auth_headers,
    )
    assert upload_res.status_code == 201
    art_id = upload_res.json()["id"]

    # 1. Owner downloads -> 200 with attachment header
    owner_dl = client.get(f"/api/v1/artifacts/{art_id}/download", headers=auth_headers)
    assert owner_dl.status_code == 200
    assert owner_dl.content == b"Verified safe content"
    assert 'attachment; filename="safe_doc.txt"' in owner_dl.headers["content-disposition"]
    assert owner_dl.headers["x-content-type-options"] == "nosniff"

    # 2. Project creator downloads -> 200
    creator_dl = client.get(f"/api/v1/artifacts/{art_id}/download", headers=creator_headers)
    assert creator_dl.status_code == 200
    assert creator_dl.content == b"Verified safe content"

    # 3. Anonymous user blocked without 5-gate portfolio setup -> 403
    anon_dl = client.get(f"/api/v1/artifacts/{art_id}/download")
    assert anon_dl.status_code == 403


def test_public_portfolio_5_gate_download(
    client: TestClient,
    auth_headers: dict[str, str],
    creator_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
    db: Session,
) -> None:
    """Anonymous download succeeds ONLY when all 5 public portfolio gates are satisfied."""
    _, sub_id = active_draft_submission

    # Upload public artifact
    upload_res = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("portfolio_doc.txt", io.BytesIO(b"Showcase content"), "text/plain")},
        data={"is_public": "true"},
        headers=auth_headers,
    )
    art_id = upload_res.json()["id"]

    # Learner submits
    client.patch(
        f"/api/v1/submissions/{sub_id}",
        json={"summary": "Deliverable for portfolio."},
        headers=auth_headers,
    )
    client.post(f"/api/v1/submissions/{sub_id}/submit", headers=auth_headers)

    # Evaluator approves (COMPLETED status)
    client.post(
        f"/api/v1/submissions/{sub_id}/evaluation",
        json={"feedback": "Approved for portfolio showcase", "action": "APPROVE"},
        headers=creator_headers,
    )

    # Get learner user id from submission
    sub = db.query(ProjectSubmission).filter(ProjectSubmission.id == sub_id).first()
    learner_id = sub.user_id

    # Create learner's Portfolio (is_public=True)
    portfolio = Portfolio(
        user_id=learner_id,
        is_public=True,
        title="Learner Engineering Portfolio",
    )
    db.add(portfolio)
    db.commit()

    # Create PortfolioItem referencing the submission (visibility=PUBLIC)
    p_item = PortfolioItem(
        portfolio_user_id=learner_id,
        title="ETL Pipeline Project Showcase",
        reference_id=sub_id,
        visibility=PortfolioItemVisibility.PUBLIC.value,
    )
    db.add(p_item)
    db.commit()

    # Anonymous user attempts download: All 5 gates pass -> 200 OK!
    anon_res = client.get(f"/api/v1/artifacts/{art_id}/download")
    assert anon_res.status_code == 200
    assert anon_res.content == b"Showcase content"

    # Now make portfolio private (gate 1 fails): anonymous download must be blocked
    portfolio.is_public = False
    db.commit()

    anon_blocked = client.get(f"/api/v1/artifacts/{art_id}/download")
    assert anon_blocked.status_code == 403


def test_upload_text_formats_and_disguised_binaries(
    client: TestClient,
    auth_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
) -> None:
    """All valid text formats (.txt, .md, .json, .csv) are accepted, but executable/null-byte disguised files are rejected."""
    _, sub_id = active_draft_submission

    # 1. Valid TXT
    r_txt = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("readme.txt", io.BytesIO(b"Sample plain text deliverable documentation"), "text/plain")},
        headers=auth_headers,
    )
    assert r_txt.status_code == 201

    # 2. Valid MD
    r_md = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("notes.md", io.BytesIO(b"# Project Notes\nEverything is working as expected."), "text/markdown")},
        headers=auth_headers,
    )
    assert r_md.status_code == 201

    # 3. Valid JSON
    r_json = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("config.json", io.BytesIO(b'{"version": 1, "status": "ok"}'), "application/json")},
        headers=auth_headers,
    )
    assert r_json.status_code == 201

    # 4. Valid CSV
    r_csv = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("data.csv", io.BytesIO(b"id,name,score\n1,alice,95\n2,bob,88"), "text/csv")},
        headers=auth_headers,
    )
    assert r_csv.status_code == 201

    # 5. MZ executable header disguised as .txt
    r_mz = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("disguised.txt", io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00windowsbinarycontent"), "text/plain")},
        headers=auth_headers,
    )
    assert r_mz.status_code in (400, 422)
    assert "executable binary signature" in r_mz.json()["error"]["message"]

    # 6. ELF binary header disguised as .txt
    r_elf = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("linux_elf.txt", io.BytesIO(b"\x7fELF\x02\x01\x01\x00linuxexecutablecontent"), "text/plain")},
        headers=auth_headers,
    )
    assert r_elf.status_code in (400, 422)
    assert "executable binary signature" in r_elf.json()["error"]["message"]

    # 7. Null byte embedded in text file
    r_null = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("corrupted.txt", io.BytesIO(b"Ordinary text with embedded \x00 null byte"), "text/plain")},
        headers=auth_headers,
    )
    assert r_null.status_code in (400, 422)
    assert "null bytes" in r_null.json()["error"]["message"]


def test_upload_aggregate_limit_exceeded(
    client: TestClient,
    auth_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
) -> None:
    """Uploading files that push total submission size over 50MB is rejected."""
    _, sub_id = active_draft_submission
    limiter.reset()

    # Upload two 18MB files (18 + 18 = 36MB <= 50MB)
    chunk_18mb = b"A" * (18 * 1024 * 1024)
    res1 = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("chunk1.txt", io.BytesIO(chunk_18mb), "text/plain")},
        headers=auth_headers,
    )
    assert res1.status_code == 201

    limiter.reset()
    res2 = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("chunk2.txt", io.BytesIO(chunk_18mb), "text/plain")},
        headers=auth_headers,
    )
    assert res2.status_code == 201

    # Upload third 16MB file (36 + 16 = 52MB > 50MB aggregate limit) -> rejected
    limiter.reset()
    chunk_16mb = b"B" * (16 * 1024 * 1024)
    res3 = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("chunk3.txt", io.BytesIO(chunk_16mb), "text/plain")},
        headers=auth_headers,
    )
    assert res3.status_code in (400, 422)
    assert "aggregate limit" in res3.json()["error"]["message"]


def test_upload_eleventh_artifact_rejected(
    client: TestClient,
    auth_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
) -> None:
    """A submission cannot exceed 10 artifacts, even when rate limits are reset."""
    _, sub_id = active_draft_submission
    limiter.reset()

    for i in range(10):
        limiter.reset()
        res = client.post(
            f"/api/v1/submissions/{sub_id}/artifacts",
            files={"file": (f"artifact_{i}.txt", io.BytesIO(f"Doc {i}".encode()), "text/plain")},
            headers=auth_headers,
        )
        assert res.status_code == 201

    limiter.reset()
    # 11th upload must be rejected by submission-level count limit
    res_11 = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("artifact_11.txt", io.BytesIO(b"Eleventh artifact"), "text/plain")},
        headers=auth_headers,
    )
    assert res_11.status_code in (400, 422)
    assert "maximum limit of 10 artifacts" in res_11.json()["error"]["message"]


def test_concurrent_uploads_quota_enforcement(
    client: TestClient,
    auth_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
) -> None:
    """Concurrent artifact uploads are serialized by mutex locking and quotas enforced."""
    _, sub_id = active_draft_submission
    limiter.reset()

    def do_upload(idx: int) -> int:
        data = f"Concurrent deliverable content #{idx}".encode()
        r = client.post(
            f"/api/v1/submissions/{sub_id}/artifacts",
            files={"file": (f"concurrent_{idx}.txt", io.BytesIO(data), "text/plain")},
            headers=auth_headers,
        )
        return r.status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(do_upload, i) for i in range(4)]
        status_codes = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert all(code == 201 for code in status_codes)

    list_res = client.get(f"/api/v1/submissions/{sub_id}/artifacts", headers=auth_headers)
    assert list_res.status_code == 200
    assert list_res.json()["total_count"] == 4


def test_concurrent_upload_quota_boundary(
    client: TestClient,
    auth_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
) -> None:
    """Under concurrent load at quota boundary (8 existing + 4 simultaneous), exactly 2 succeed and 2 fail."""
    _, sub_id = active_draft_submission
    storage = get_storage_service()
    storage_root = Path(storage.base_dir)

    # 1. Create a draft submission with 8 existing artifacts
    for i in range(8):
        limiter.reset()
        res = client.post(
            f"/api/v1/submissions/{sub_id}/artifacts",
            files={"file": (f"initial_{i}.txt", io.BytesIO(f"Initial artifact {i}".encode()), "text/plain")},
            headers=auth_headers,
        )
        assert res.status_code == 201

    data_files_at_8 = [f for f in storage_root.rglob("*.*") if not f.name.endswith(".meta.json")]
    assert len(data_files_at_8) == 8

    # 2. Launch 4 simultaneous upload requests against that same submission
    # Using threading.Barrier(4) ensures all 4 worker threads synchronize and dispatch simultaneously
    barrier = threading.Barrier(4)
    limiter.reset()

    def do_boundary_upload(idx: int) -> tuple[int, dict]:
        data = f"Boundary concurrent upload content #{idx}".encode()
        filename = f"boundary_{idx}.txt"
        barrier.wait()  # Release all 4 threads simultaneously to hit the server at once
        r = client.post(
            f"/api/v1/submissions/{sub_id}/artifacts",
            files={"file": (filename, io.BytesIO(data), "text/plain")},
            headers=auth_headers,
        )
        return r.status_code, r.json()

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(do_boundary_upload, i) for i in range(4)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # 3. Verify exactly 2 uploads succeed and 2 are rejected by the artifact-count limit
    successes = [r for r in results if r[0] == 201]
    rejections = [r for r in results if r[0] in (400, 422)]

    assert len(successes) == 2, f"Expected 2 successes, got {len(successes)}: {[r[0] for r in results]}"
    assert len(rejections) == 2, f"Expected 2 rejections, got {len(rejections)}: {[r[0] for r in results]}"

    for rej in rejections:
        assert "maximum limit of 10 artifacts" in rej[1]["error"]["message"]

    # 4. Verify the final artifact count is exactly 10
    list_res = client.get(f"/api/v1/submissions/{sub_id}/artifacts", headers=auth_headers)
    assert list_res.status_code == 200
    assert list_res.json()["total_count"] == 10

    # 5. Verify rejected uploads leave no orphaned files
    data_files_final = [f for f in storage_root.rglob("*.*") if not f.name.endswith(".meta.json")]
    assert len(data_files_final) == 10, f"Expected exactly 10 data files in storage, got {len(data_files_final)}"
    all_files_final = list(storage_root.rglob("*.*"))
    assert len(all_files_final) == 20, f"Expected 20 total files (10 data + 10 meta.json), got {len(all_files_final)}"


def test_concurrent_aggregate_size_boundary(
    client: TestClient,
    auth_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
) -> None:
    """Under concurrent load near 50MB aggregate limit, simultaneous requests are serialized and only permitted within headroom."""
    _, sub_id = active_draft_submission
    storage = get_storage_service()
    storage_root = Path(storage.base_dir)
    limiter.reset()

    # Initial files: two 18 MB files = 36 MB (headroom left is 14 MB out of 50 MB, each file <= 20 MB limit)
    chunk_18mb = b"X" * (18 * 1024 * 1024)
    res_init1 = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("large_base_1.txt", io.BytesIO(chunk_18mb), "text/plain")},
        headers=auth_headers,
    )
    assert res_init1.status_code == 201

    limiter.reset()
    res_init2 = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("large_base_2.txt", io.BytesIO(chunk_18mb), "text/plain")},
        headers=auth_headers,
    )
    assert res_init2.status_code == 201
    assert len([f for f in storage_root.rglob("*.*") if not f.name.endswith(".meta.json")]) == 2

    # Two concurrent 8 MB uploads (8 + 8 = 16 MB > 14 MB headroom)
    barrier = threading.Barrier(2)
    limiter.reset()

    def do_large_upload(idx: int) -> tuple[int, dict]:
        data = b"Y" * (8 * 1024 * 1024)
        filename = f"large_chunk_{idx}.txt"
        barrier.wait()
        r = client.post(
            f"/api/v1/submissions/{sub_id}/artifacts",
            files={"file": (filename, io.BytesIO(data), "text/plain")},
            headers=auth_headers,
        )
        return r.status_code, r.json()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(do_large_upload, i) for i in range(2)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Exactly 1 succeeds, bringing total to 44 MB; 1 fails (exceeds 50 MB)
    successes = [r for r in results if r[0] == 201]
    rejections = [r for r in results if r[0] in (400, 422)]

    assert len(successes) == 1, f"Expected 1 success, got {len(successes)}: {[r[0] for r in results]}"
    assert len(rejections) == 1, f"Expected 1 rejection, got {len(rejections)}: {[r[0] for r in results]}"
    assert "aggregate limit" in rejections[0][1]["error"]["message"]

    # Final aggregate size is 44 MB (18 + 18 + 8), exactly 3 data files in storage, 0 orphaned files
    list_res = client.get(f"/api/v1/submissions/{sub_id}/artifacts", headers=auth_headers)
    assert list_res.status_code == 200
    assert list_res.json()["total_count"] == 3
    assert list_res.json()["total_size_bytes"] == (18 + 18 + 8) * 1024 * 1024
    data_files_agg = [f for f in storage_root.rglob("*.*") if not f.name.endswith(".meta.json")]
    assert len(data_files_agg) == 3



def test_failed_db_insertion_removes_stored_file(
    active_draft_submission: tuple[str, str],
    db: Session,
) -> None:
    """If database persistence fails during upload, the stored artifact file is purged from disk."""
    _, sub_id = active_draft_submission
    sub = db.query(ProjectSubmission).filter(ProjectSubmission.id == sub_id).first()
    learner = sub.user

    storage = get_storage_service()
    service = ArtifactService(db)

    storage_root = Path(storage.base_dir)
    files_before = list(storage_root.rglob("*.*"))

    with (
        patch.object(db, "commit", side_effect=RuntimeError("Simulated DB failure")),
        pytest.raises(RuntimeError, match="Simulated DB failure"),
    ):
        service.upload_artifact(
            submission_id=sub_id,
            user=learner,
            file_data=b"Test artifact content that should be rolled back",
            filename="rollback_test.txt",
        )

    files_after = list(storage_root.rglob("*.*"))
    assert len(files_after) == len(files_before)


def test_public_portfolio_5_gates_independently(
    client: TestClient,
    auth_headers: dict[str, str],
    creator_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
    db: Session,
) -> None:
    """Each of the 5 public portfolio gates is verified independently for anonymous access."""
    _, sub_id = active_draft_submission

    # Upload public artifact
    up_res = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("gated_demo.txt", io.BytesIO(b"Gated showcase notes"), "text/plain")},
        data={"is_public": "true"},
        headers=auth_headers,
    )
    assert up_res.status_code == 201
    art_id = up_res.json()["id"]

    # Submit and approve
    client.patch(f"/api/v1/submissions/{sub_id}", json={"summary": "Gated submission."}, headers=auth_headers)
    client.post(f"/api/v1/submissions/{sub_id}/submit", headers=auth_headers)
    client.post(
        f"/api/v1/submissions/{sub_id}/evaluation",
        json={"feedback": "Approved for testing gates.", "action": "APPROVE"},
        headers=creator_headers,
    )

    sub = db.query(ProjectSubmission).filter(ProjectSubmission.id == sub_id).first()
    learner_id = sub.user_id

    # Create public portfolio
    portfolio = Portfolio(user_id=learner_id, is_public=True, title="Learner Showcase")
    db.add(portfolio)
    db.commit()

    # Create public portfolio item referencing submission
    p_item = PortfolioItem(
        portfolio_user_id=learner_id,
        title="Gated Project Showcase",
        reference_id=sub_id,
        visibility=PortfolioItemVisibility.PUBLIC.value,
    )
    db.add(p_item)
    db.commit()

    artifact = db.query(ProjectArtifact).filter(ProjectArtifact.id == art_id).first()

    # Baseline: all 5 pass -> 200
    res_base = client.get(f"/api/v1/artifacts/{art_id}/download")
    assert res_base.status_code == 200

    # Gate 1: Portfolio is private -> 403
    portfolio.is_public = False
    db.commit()
    assert client.get(f"/api/v1/artifacts/{art_id}/download").status_code == 403
    portfolio.is_public = True
    db.commit()

    # Gate 2: Portfolio item is unlisted/private -> 403
    p_item.visibility = PortfolioItemVisibility.PRIVATE.value
    db.commit()
    assert client.get(f"/api/v1/artifacts/{art_id}/download").status_code == 403
    p_item.visibility = PortfolioItemVisibility.PUBLIC.value
    db.commit()

    # Gate 3: Artifact is private -> 403
    artifact.is_public = False
    db.commit()
    assert client.get(f"/api/v1/artifacts/{art_id}/download").status_code == 403
    artifact.is_public = True
    db.commit()

    # Gate 4: Submission is not COMPLETED (e.g. UNDER_REVIEW) -> 403
    sub.status = SubmissionStatus.UNDER_REVIEW.value
    db.commit()
    assert client.get(f"/api/v1/artifacts/{art_id}/download").status_code == 403
    sub.status = SubmissionStatus.COMPLETED.value
    db.commit()

    # Gate 5: Portfolio item references a different submission -> 403
    p_item.reference_id = "00000000-0000-0000-0000-000000000000"
    db.commit()
    assert client.get(f"/api/v1/artifacts/{art_id}/download").status_code == 403
    p_item.reference_id = sub_id
    db.commit()

    # Re-verify baseline passes again
    assert client.get(f"/api/v1/artifacts/{art_id}/download").status_code == 200


def test_cross_user_portfolio_owner_mismatch(
    client: TestClient,
    auth_headers: dict[str, str],
    creator_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
    db: Session,
) -> None:
    """An attacker (User C) cannot grant public access to User A's deliverables via their own portfolio."""
    _, sub_a_id = active_draft_submission

    # 1. Create User A's completed submission and public artifact
    up_res = client.post(
        f"/api/v1/submissions/{sub_a_id}/artifacts",
        files={"file": ("user_a_deliverable.txt", io.BytesIO(b"User A confidential deliverable"), "text/plain")},
        data={"is_public": "true"},
        headers=auth_headers,
    )
    assert up_res.status_code == 201
    art_a_id = up_res.json()["id"]

    client.patch(f"/api/v1/submissions/{sub_a_id}", json={"summary": "User A deliverable notes."}, headers=auth_headers)
    client.post(f"/api/v1/submissions/{sub_a_id}/submit", headers=auth_headers)
    client.post(
        f"/api/v1/submissions/{sub_a_id}/evaluation",
        json={"feedback": "Approved User A work.", "action": "APPROVE"},
        headers=creator_headers,
    )

    sub_a = db.query(ProjectSubmission).filter(ProjectSubmission.id == sub_a_id).first()
    user_a_id = sub_a.user_id

    # 2. Register User C (different user)
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_c_attacker@example.com",
            "password": "SecureP@ss1",
            "display_name": "User C Attacker",
        },
    )
    user_c = db.query(User).filter(User.email == "user_c_attacker@example.com").first()
    user_c_id = user_c.id
    assert user_c_id != user_a_id

    # User C creates a public portfolio
    portfolio_c = Portfolio(user_id=user_c_id, is_public=True, title="User C Public Portfolio")
    db.add(portfolio_c)
    db.commit()

    # Case A: User C's public portfolio item references User A's submission ID
    item_c_sub = PortfolioItem(
        portfolio_user_id=user_c_id,
        title="Unauthorized Item Referencing User A Submission",
        reference_id=sub_a_id,
        visibility=PortfolioItemVisibility.PUBLIC.value,
    )
    db.add(item_c_sub)
    db.commit()

    # 3. Attempt anonymous artifact download
    anon_res1 = client.get(f"/api/v1/artifacts/{art_a_id}/download")

    # 4. Verify HTTP 403 and confirm no file contents or private metadata are returned
    assert anon_res1.status_code == 403
    err1 = anon_res1.json()
    assert err1["error"]["code"] == "FORBIDDEN"
    assert "not authorized" in err1["error"]["message"].lower()
    assert b"User A confidential deliverable" not in anon_res1.content
    assert "storage_key" not in err1
    assert "path" not in err1

    # Case B: User C's public portfolio item references User A's artifact ID directly
    item_c_sub.reference_id = art_a_id
    db.commit()

    anon_res2 = client.get(f"/api/v1/artifacts/{art_a_id}/download")
    assert anon_res2.status_code == 403
    assert b"User A confidential deliverable" not in anon_res2.content

    # 5. Legitimate owner-matched public portfolio configuration permits access
    portfolio_a = Portfolio(user_id=user_a_id, is_public=True, title="User A Legitimate Portfolio")
    db.add(portfolio_a)
    db.commit()

    item_a = PortfolioItem(
        portfolio_user_id=user_a_id,
        title="User A Genuine Showcase",
        reference_id=sub_a_id,
        visibility=PortfolioItemVisibility.PUBLIC.value,
    )
    db.add(item_a)
    db.commit()

    anon_res_valid = client.get(f"/api/v1/artifacts/{art_a_id}/download")
    assert anon_res_valid.status_code == 200
    assert anon_res_valid.content == b"User A confidential deliverable"
    assert 'attachment; filename="user_a_deliverable.txt"' in anon_res_valid.headers["content-disposition"]



def test_download_security_checks(
    client: TestClient,
    auth_headers: dict[str, str],
    active_draft_submission: tuple[str, str],
) -> None:
    """Security checks: guessed UUID (404), CRLF filename sanitization, and unauthorized deletion (403)."""
    _, sub_id = active_draft_submission

    # 1. Guessed UUID returns 404
    non_existent = client.get("/api/v1/artifacts/00000000-0000-0000-0000-000000000000/download")
    assert non_existent.status_code == 404

    # 2. CRLF filename injection in Content-Disposition
    crlf_res = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("report\r\nSet-Cookie: evil=1\r\n.txt", io.BytesIO(b"CRLF injection test"), "text/plain")},
        headers=auth_headers,
    )
    assert crlf_res.status_code == 201
    crlf_id = crlf_res.json()["id"]

    dl_res = client.get(f"/api/v1/artifacts/{crlf_id}/download", headers=auth_headers)
    assert dl_res.status_code == 200
    disp = dl_res.headers["content-disposition"]
    assert "\r" not in disp
    assert "\n" not in disp
    assert "Set-Cookie" not in dl_res.headers

    # 3. Unauthorized deletion by another user (403)
    client.post(
        "/api/v1/auth/register",
        json={"email": "attacker@example.com", "password": "SecureP@ss1", "display_name": "Attacker"},
    )
    att_login = client.post(
        "/api/v1/auth/login",
        json={"email": "attacker@example.com", "password": "SecureP@ss1"},
    )
    attacker_headers = {"Authorization": f"Bearer {att_login.json()['access_token']}"}

    del_unauth = client.delete(f"/api/v1/artifacts/{crlf_id}", headers=attacker_headers)
    assert del_unauth.status_code == 403
    assert "only delete your own artifacts" in del_unauth.json()["error"]["message"]

