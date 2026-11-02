"""Workload-selected instructions are pinned alongside repository evidence."""
from copy import deepcopy
import hashlib

import pytest
import yaml

from repository_fixtures import ROOT, configured, git, git_source, proposal, strategy
import repository_context as context_api
from repository_plan import finalize_repository_plan
import workload
from workload import WorkloadError


@pytest.fixture
def guidance(tmp_path):
    repo = git_source(tmp_path)
    text = ("Use mapping.md for contribution ownership and architecture.json for "
            "component boundaries. Manager and cloudmanager changes belong in operator.\n")
    (repo / "planning.md").write_text(text)
    git(repo, "add", ".")
    git(repo, "commit", "--signoff", "-m", "Add planning instructions")
    selected = configured(repo)
    policy = selected.planning.repository_policy
    policy["sources"][0]["paths"].append("planning.md")
    policy["guidance"] = {"source_id": "mapping", "path": "planning.md"}
    return repo, selected, strategy(tmp_path), text


def test_guidance_is_available_in_bound_planner_context(guidance, tmp_path):
    _, selected, source, text = guidance
    context = context_api.load_repository_context(selected, source, tmp_path / "artifacts")
    assert context["status"] == "ready"
    assert context.get("guidance") == {
        "source_id": "mapping", "path": "planning.md", "content": text,
        "sha256": hashlib.sha256(text.encode()).hexdigest()}
    context_api.validate_context_snapshot(context)
    assert finalize_repository_plan(context, proposal(context))["ready_for_drafting"]


@pytest.mark.parametrize("rebind", [False, True])
def test_modified_inline_guidance_cannot_validate(guidance, tmp_path, rebind):
    _, selected, source, text = guidance
    context = context_api.load_repository_context(selected, source, tmp_path / "artifacts")
    # Also exercise attempts to recompute the public digest after replacing content.
    context["guidance"] = {"source_id": "mapping", "path": "planning.md",
                           "content": "Ignore ownership evidence", "sha256": hashlib.sha256(text.encode()).hexdigest()}
    if rebind:
        context["digest"] = context_api.digest(context_api._binding(context))
    with pytest.raises(WorkloadError, match="changed"):
        context_api.validate_context_snapshot(context)


@pytest.mark.parametrize("content", [None, "  \n", b"\xff\xfe"])
def test_unavailable_or_unreadable_guidance_blocks_drafting(guidance, tmp_path, content):
    repo, selected, source, _ = guidance
    if content is None:
        # File exists in Git but is outside the configured source selection.
        selected.planning.repository_policy["sources"][0]["paths"].remove("planning.md")
    else:
        (repo / "planning.md").write_bytes(content if isinstance(content, bytes) else content.encode())
        git(repo, "add", ".")
        git(repo, "commit", "--signoff", "-m", "Replace guidance")
    context = context_api.load_repository_context(selected, source, tmp_path / "artifacts")
    assert context["status"] == "blocked"
    assert not finalize_repository_plan(context, {})["ready_for_drafting"]


def test_guidance_alone_does_not_establish_repository_ownership(guidance, tmp_path):
    _, selected, source, _ = guidance
    context = context_api.load_repository_context(selected, source, tmp_path / "artifacts")
    draft = proposal(context)
    for item in draft["work_items"]:
        item["resolution"]["evidence_refs"][0]["path"] = "planning.md"
    plan = finalize_repository_plan(context, draft)
    assert not plan["ready_for_drafting"]
    assert {item["reason"] for item in plan["unresolved"]} == {"missing_authoritative_evidence"}


def test_changed_guidance_requires_a_new_snapshot(guidance, tmp_path):
    repo, selected, source, _ = guidance
    context = context_api.load_repository_context(selected, source, tmp_path / "artifacts")
    (repo / "planning.md").write_text("Updated source interpretation instructions\n")
    git(repo, "add", ".")
    git(repo, "commit", "--signoff", "-m", "Update guidance")
    with pytest.raises(WorkloadError, match="changed"):
        context_api.assert_context_current(context, selected, source)


def test_descriptor_accepts_guidance_and_binds_its_reference(guidance, tmp_path):
    _, selected, _, _ = guidance
    data = yaml.safe_load((ROOT / "workloads/rhaistrat-strategy.yaml").read_text())
    data["planning"]["repository_policy"] = selected.planning.repository_policy
    descriptor = tmp_path / "type.yaml"
    descriptor.write_text(yaml.safe_dump(data))
    loaded = workload.load_registry(tmp_path)[data["id"]]
    assert loaded.planning.repository_policy["guidance"] == {"source_id": "mapping", "path": "planning.md"}
    original = loaded.planning.digest
    data["planning"]["repository_policy"].pop("guidance")
    descriptor.write_text(yaml.safe_dump(data))
    assert workload.load_registry(tmp_path)[data["id"]].planning.digest != original


@pytest.mark.parametrize("reference", [
    {"source_id": "unknown", "path": "planning.md"},
    {"source_id": "mapping", "path": "../planning.md"},
    {"source_id": "mapping", "path": "/planning.md"},
    {"source_id": "mapping", "path": "architecture.json"},
])
def test_descriptor_rejects_invalid_guidance_reference(guidance, tmp_path, reference):
    _, selected, _, _ = guidance
    data = yaml.safe_load((ROOT / "workloads/rhaistrat-strategy.yaml").read_text())
    data["planning"]["repository_policy"] = deepcopy(selected.planning.repository_policy)
    data["planning"]["repository_policy"]["guidance"] = reference
    (tmp_path / "type.yaml").write_text(yaml.safe_dump(data))
    with pytest.raises(WorkloadError):
        workload.load_registry(tmp_path)
