import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import Commit, run_ci


def test_lint_failure_blocks_everything():
    result = run_ci(Commit("x", "main", lint_ok=False, tests_ok=True, staging_smoke_ok=True, approved_for_prod=True))
    assert result.stages_run == []
    assert "lint" in result.stages_blocked[0]


def test_non_main_branch_never_ships_an_image():
    result = run_ci(
        Commit("x", "feature/y", lint_ok=True, tests_ok=True, staging_smoke_ok=True, approved_for_prod=True)
    )
    assert result.image_tags == []


def test_failed_staging_smoke_blocks_both_deploys():
    result = run_ci(Commit("x", "main", lint_ok=True, tests_ok=True, staging_smoke_ok=False, approved_for_prod=True))
    assert result.deployed_to == []


def test_missing_prod_approval_stops_after_staging():
    result = run_ci(Commit("x", "main", lint_ok=True, tests_ok=True, staging_smoke_ok=True, approved_for_prod=False))
    assert result.deployed_to == ["staging"]


def test_full_green_path_deploys_to_prod_and_tags_prod_image():
    result = run_ci(Commit("x", "main", lint_ok=True, tests_ok=True, staging_smoke_ok=True, approved_for_prod=True))
    assert result.deployed_to == ["staging", "production"]
    assert any(tag.endswith(":prod") for tag in result.image_tags)
