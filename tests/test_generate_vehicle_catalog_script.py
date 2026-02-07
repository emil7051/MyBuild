"""Regression tests for the TypeScript catalog generator script."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.enable_redis_cache
def test_generator_writes_to_repo_root_from_non_repo_cwd(tmp_path: Path) -> None:
    """Generator output paths should be anchored to repo root, not current CWD."""

    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts/generate_vehicle_catalog_ts.py"
    external_cwd = tmp_path / "external-cwd"
    external_cwd.mkdir()

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=external_cwd,
        capture_output=True,
        text=True,
        check=True,
    )

    # The script should report repo-relative paths and avoid writing into caller CWD.
    assert "shared/data/vehicleCatalog.ts" in result.stdout
    assert "shared/data/constants.generated.ts" in result.stdout
    assert "shared/data/scenarios.ts" in result.stdout
    assert "shared/data/policies.ts" in result.stdout

    assert not (external_cwd / "shared/data/vehicleCatalog.ts").exists()
    assert not (external_cwd / "shared/data/constants.generated.ts").exists()
    assert not (external_cwd / "shared/data/scenarios.ts").exists()
    assert not (external_cwd / "shared/data/policies.ts").exists()

    assert (repo_root / "shared/data/vehicleCatalog.ts").exists()
    assert (repo_root / "shared/data/constants.generated.ts").exists()
    assert (repo_root / "shared/data/scenarios.ts").exists()
    assert (repo_root / "shared/data/policies.ts").exists()
