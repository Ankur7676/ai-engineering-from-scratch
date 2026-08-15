"""MLOps CI/CD pipeline gate simulator — stdlib Python.

Models the stage gates that ci.yml, docker.yml, deploy-staging.yml, and
deploy-prod.yml enforce as separate GitHub Actions workflows: lint, test,
build/push, staging smoke test, production approval.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Commit:
    sha: str
    branch: str
    lint_ok: bool
    tests_ok: bool
    staging_smoke_ok: bool
    approved_for_prod: bool


@dataclass
class PipelineResult:
    sha: str
    stages_run: list[str] = field(default_factory=list)
    stages_blocked: list[str] = field(default_factory=list)
    image_tags: list[str] = field(default_factory=list)
    deployed_to: list[str] = field(default_factory=list)


def run_ci(commit: Commit) -> PipelineResult:
    result = PipelineResult(sha=commit.sha)

    if not commit.lint_ok:
        result.stages_blocked.append(
            "lint failed — ci.yml exits 1, docker.yml and both deploy workflows never trigger"
        )
        return result
    result.stages_run.append("lint")

    if not commit.tests_ok:
        result.stages_blocked.append("tests failed — ci.yml exits 1, docker.yml never triggers")
        return result
    result.stages_run.append("test")

    if commit.branch != "main":
        result.stages_blocked.append(
            f"branch {commit.branch!r} is not main — docker.yml's push trigger never fires on PR branches"
        )
        return result

    result.stages_run.append("build")
    result.stages_run.append("push")
    result.image_tags = [
        f"ghcr.io/org/aiefs-mlops-lesson:{commit.sha}",
        "ghcr.io/org/aiefs-mlops-lesson:staging",
    ]

    if not commit.staging_smoke_ok:
        result.stages_blocked.append(
            "staging smoke test failed — deploy-prod.yml is never manually dispatched against this SHA"
        )
        return result
    result.stages_run.append("deploy_staging")
    result.deployed_to.append("staging")

    if not commit.approved_for_prod:
        result.stages_blocked.append(
            "no production environment approval — deploy-prod.yml's workflow_dispatch job "
            "waits on required reviewers"
        )
        return result
    result.stages_run.append("deploy_prod")
    result.deployed_to.append("production")
    result.image_tags.append("ghcr.io/org/aiefs-mlops-lesson:prod")
    return result


SCENARIOS = [
    Commit("a1b2c3d", "feature/x", lint_ok=False, tests_ok=True, staging_smoke_ok=True, approved_for_prod=True),
    Commit("b2c3d4e", "feature/y", lint_ok=True, tests_ok=False, staging_smoke_ok=True, approved_for_prod=True),
    Commit("c3d4e5f", "feature/z", lint_ok=True, tests_ok=True, staging_smoke_ok=True, approved_for_prod=True),
    Commit("d4e5f6a", "main", lint_ok=True, tests_ok=True, staging_smoke_ok=False, approved_for_prod=True),
    Commit("e5f6a7b", "main", lint_ok=True, tests_ok=True, staging_smoke_ok=True, approved_for_prod=False),
    Commit("f6a7b8c", "main", lint_ok=True, tests_ok=True, staging_smoke_ok=True, approved_for_prod=True),
]


def main() -> None:
    print("=" * 80)
    print("MLOPS CI/CD PIPELINE GATE SIMULATOR — ci -> docker -> deploy-staging -> deploy-prod")
    print("=" * 80)
    for commit in SCENARIOS:
        result = run_ci(commit)
        print(f"\n[{commit.sha}] branch={commit.branch}")
        print(f"  ran: {result.stages_run}")
        if result.stages_blocked:
            print(f"  blocked: {result.stages_blocked[0]}")
        if result.deployed_to:
            print(f"  deployed to: {result.deployed_to}")
        if result.image_tags:
            print(f"  image tags: {result.image_tags}")


if __name__ == "__main__":
    main()
