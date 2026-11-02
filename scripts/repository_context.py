"""Canonical contribution inventory and content-bound repository evidence."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import yaml

from repository_sources import fetch_git_sources, normalize_git_source
from workload import WorkloadError

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "workloads/_schema"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_inventory(data):
    schema = json.loads((SCHEMA_DIR / "repository-inventory.schema.json").read_text())
    errors = list(Draft202012Validator(schema).iter_errors(data))
    if errors:
        raise WorkloadError(f"Invalid contribution inventory: {errors[0].message}")
    inventory, labels, identities, aliases = {}, set(), set(), {}
    for entry in data["repositories"]:
        key = entry["inventory_key"]
        identity = f"{entry['host'].lower()}/{entry['namespace']}/{entry['repository']}"
        if key in inventory or entry["label"] in labels or identity in identities:
            raise WorkloadError("Duplicate repository inventory key, label or canonical identity")
        if entry["label"] != f"target-repo-{key}":
            raise WorkloadError("Repository label must match its inventory key")
        inventory[key] = entry
        labels.add(entry["label"])
        identities.add(identity)
        for alias in [identity, *entry.get("aliases", [])]:
            if alias in aliases and aliases[alias] != key:
                raise WorkloadError("Conflicting repository aliases")
            aliases[alias] = key
    return inventory


def source_binding(manifests):
    return [{**{k: v for k, v in source.items() if k not in ("files", "fetched_at")},
             "files": {name: {"sha256": content["sha256"]} for name, content in source["files"].items()}}
            for source in manifests]


def load_repository_context(selected, source_path: Path, artifacts_dir: Path) -> dict:
    policy = selected.planning.repository_policy
    if not policy:
        raise WorkloadError("Selected workload has no repository policy")
    # Validate references before recording diagnostics or copying configuration.
    for source in policy["sources"]:
        normalize_git_source(source)
    context = {"schema_version": 1, "source_key": Path(source_path).stem,
               "workload_id": selected.id, "workload_version": selected.version,
               "workload_digest": selected.digest, "planning_digest": selected.planning.digest,
               "strategy_sha256": hashlib.sha256(Path(source_path).read_bytes()).hexdigest(),
               "policy": policy, "cache_root": str((Path(artifacts_dir) / "repository-sources").resolve())}
    try:
        sources = fetch_git_sources(policy, Path(context["cache_root"]))
        inventory_ref = policy["inventory"]
        source = next(s for s in sources if s["id"] == inventory_ref["source_id"])
        inventory_path = source["files"][inventory_ref["path"]]["local_path"]
        inventory_data = yaml.safe_load(Path(inventory_path).read_text())
        inventory = validate_inventory(inventory_data)
    except (WorkloadError, OSError, KeyError, StopIteration, yaml.YAMLError) as exc:
        return {**context, "status": "blocked", "reason": "source_unavailable",
                "inventory": {}, "sources": [], "digest": digest({**context, "cache_root": None})}
    binding = {k: v for k, v in context.items() if k != "cache_root"}
    binding.update(sources=source_binding(sources), inventory=inventory_data)
    return {**context, "status": "ready", "sources": sources, "inventory": inventory,
            "inventory_revision": inventory_data["revision"], "digest": digest(binding)}


def assert_context_current(context: dict, selected, source_path: Path) -> None:
    if context.get("status") != "ready":
        raise WorkloadError("Repository context is unresolved")
    for source in context["sources"]:
        if source.get("max_age_seconds") is not None:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(source["fetched_at"])).total_seconds()
            if age > source["max_age_seconds"]:
                raise WorkloadError("Repository evidence freshness expired; plan again")
    current = load_repository_context(selected, source_path, Path(context["cache_root"]).parent)
    if current.get("status") != "ready" or current["digest"] != context["digest"]:
        raise WorkloadError("Repository mapping inputs changed or became unavailable; plan and review again")
