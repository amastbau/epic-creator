"""Synthetic Git-backed workload fixtures, never production approval data."""
from dataclasses import replace
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from workload import get_workload


def module(name):
    assert importlib.util.find_spec(name) is not None, f"Missing {name} implementation"
    return importlib.import_module(name)


def git(path, *args):
    return subprocess.run(["git", "-C", str(path), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def inventory():
    return {"version": 1, "revision": "fixture-v1", "repositories": [
        {"inventory_key": key, "provider": "github", "host": "github.com",
         "namespace": "example", "repository": key,
         "label": f"target-repo-{key}", "approval_reference": "synthetic-fixture-only",
         "aliases": []}
        for key in ("operator", "dashboard", "guidelines")]}


def git_source(tmp_path):
    repo = tmp_path / "sources"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", "fixture@example.org")
    (repo / "inventory.yaml").write_text(yaml.safe_dump(inventory()))
    (repo / "mapping.md").write_text("Manager and cloudmanager changes belong in operator.\n")
    (repo / "architecture.json").write_text(json.dumps({"operator": ["manager", "cloudmanager"]}))
    git(repo, "add", ".")
    git(repo, "commit", "--signoff", "-m", "Fixture input")
    return repo


def policy(repo):
    return {"mode": "one-implementation-epic-per-repository",
            "inventory": {"source_id": "mapping", "path": "inventory.yaml"},
            "sources": [{"id": "mapping", "url": repo.as_uri(), "ref": "main",
                         "paths": ["inventory.yaml", "mapping.md", "architecture.json"],
                         "role": "authoritative", "owner": "fixture-maintainers"}]}


def configured(repo):
    base = get_workload("rhaistrat-strategy")
    return replace(base, planning=replace(base.planning, repository_policy=policy(repo)))


def strategy(tmp_path):
    path = tmp_path / "artifacts/strat-tasks/RHAISTRAT-9001.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Synthetic operator strategy\n\nHLR-1: Manager logs.\nHLR-2: Cloudmanager logs.\nAC-1: Manager log tests pass.\nAC-2: Cloudmanager log tests pass.\n")
    return path
