import json
from pathlib import Path
import sys
import shutil

import pytest
import yaml

from repository_fixtures import ROOT, configured, git_source, proposal, strategy
import artifact_utils as artifacts
import check_decompose_progress as progress
import pipeline_state as pipeline
import pipeline_workload
import repository_plan
import workload


def setup_pipeline(monkeypatch, tmp_path, capsys):
    repo = git_source(tmp_path)
    selected = configured(repo)
    shutil.copytree(ROOT / "workloads", tmp_path / "workloads")
    monkeypatch.setattr(workload, "WORKLOADS_DIR", tmp_path / "workloads")
    components = tmp_path / selected.planning.component_file
    components.parent.mkdir(parents=True, exist_ok=True)
    components.write_text("Operator\nCloudmanager\n")
    monkeypatch.setattr(workload, "get_workload", lambda *a, **k: selected)
    monkeypatch.setattr(pipeline_workload, "get_workload", lambda *a, **k: selected)
    source = strategy(tmp_path)
    body = source.read_text()
    metadata = dict(strat_id=source.stem, title="Operator logging", labels=list(selected.ready_labels),
                    workload_id=selected.id, workload_version=selected.version,
                    workload_digest=selected.digest, planning_digest=selected.planning.digest,
                    source_key=source.stem, source_project=selected.project,
                    source_issue_type=selected.issue_type, source_revision="fixture-v1")
    artifacts.write_frontmatter(source, metadata, "strat-task", body=body)
    monkeypatch.chdir(tmp_path)
    pipeline.cmd_init(["--workload", selected.id])
    pipeline._write_ids("tmp/pipeline-active-ids.txt", [source.stem])
    pipeline.cmd_set_phase(["FETCH"])
    capsys.readouterr()
    return selected, source


def test_repository_stage_before_drafts_and_polling_is_atomic(monkeypatch, tmp_path, capsys):
    selected, source = setup_pipeline(monkeypatch, tmp_path, capsys)
    pipeline.cmd_next_action([])
    action = yaml.safe_load(capsys.readouterr().out)
    assert action["phase"] == "PLAN_REPOSITORIES"
    locations = repository_plan.paths("artifacts", source.stem)
    assert locations["context"].exists()
    assert progress.check_id("plan_repositories", source.stem) == "pending"
    context = json.loads(locations["context"].read_text())
    plan = repository_plan.finalize_repository_plan(context, proposal(context))
    repository_plan.atomic_json(locations["plan"], plan)
    assert progress.check_id("plan_repositories", source.stem) == "completed"
    assert not Path("artifacts/epic-tasks").exists()
    pipeline.cmd_next_action([])
    action = yaml.safe_load(capsys.readouterr().out)
    assert action["phase"] == "DECOMPOSE"
    assert f'MAPPING_SNAPSHOT_DIGEST={context["digest"]}' in action["agents"][0]["vars"]


def test_draft_not_launched_without_ready_repository_plan(monkeypatch, tmp_path, capsys):
    _, source = setup_pipeline(monkeypatch, tmp_path, capsys)
    pipeline.cmd_set_phase(["DECOMPOSE"])
    with pytest.raises(workload.WorkloadError, match="[Rr]epository"):
        pipeline_workload.validate_inputs(pipeline._load_state(), "DECOMPOSE", [source.stem])


def test_changed_mapping_snapshot_cannot_resume(monkeypatch, tmp_path, capsys):
    _, source = setup_pipeline(monkeypatch, tmp_path, capsys)
    pipeline.cmd_next_action([])
    capsys.readouterr()
    source.write_text(source.read_text() + "\nNew acceptance condition\n")
    with pytest.raises(workload.WorkloadError, match="changed"):
        pipeline_workload.validate_inputs(pipeline._load_state(), "PLAN_REPOSITORIES", [source.stem])


def test_one_blocked_repository_plan_does_not_stop_other_strategy(monkeypatch, tmp_path, capsys):
    _, source = setup_pipeline(monkeypatch, tmp_path, capsys)
    second = source.with_name("RHAISTRAT-9002.md")
    data, body = artifacts.read_frontmatter(source)
    data.update(strat_id=second.stem, source_key=second.stem)
    artifacts.write_frontmatter(second, data, "strat-task", body=body)
    pipeline._write_ids("tmp/pipeline-active-ids.txt", [source.stem, second.stem])
    pipeline.cmd_next_action([])
    capsys.readouterr()
    source.write_text(source.read_text() + "\nChanged input\n")
    valid = pipeline._validate_ids_individually(pipeline._load_state(), "PLAN_REPOSITORIES",
              "tmp/pipeline-active-ids.txt", pipeline._validate_inputs_one)
    assert valid == [second.stem]


def test_default_repository_workload_fetches_typed_sources(monkeypatch, tmp_path, capsys):
    setup_pipeline(monkeypatch, tmp_path, capsys)
    pipeline.cmd_init([])
    state = pipeline._load_state()
    state["phase"] = "FETCH"
    config = pipeline_workload.phase_config(state, pipeline.PHASE_CONFIG["FETCH"])
    assert config["vars"]["FETCH_OPTIONS"] == "--workload rhaistrat-strategy"


def test_finalizer_rejects_noncanonical_planned_component(monkeypatch, tmp_path, capsys):
    selected, source = setup_pipeline(monkeypatch, tmp_path, capsys)
    pipeline.cmd_next_action([])
    locations = repository_plan.paths("artifacts", source.stem)
    context = json.loads(locations["context"].read_text())
    invalid = proposal(context)
    invalid["work_items"][0]["component"] = "unregistered"
    repository_plan.atomic_json(locations["proposal"], invalid)
    monkeypatch.setattr(repository_plan, "get_workload", lambda _: selected)
    monkeypatch.setattr(sys, "argv", ["repository_plan.py", "finalize", "--workload", selected.id, "--source", source.stem])
    assert repository_plan.main() == 1
    assert not locations["plan"].exists()
