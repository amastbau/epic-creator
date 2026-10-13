"""Validated, repository-owned workload descriptors for strategy intake.

The first schema covers intake and artifact identity. Stage policies and
submission routing are subsequent AISDLC-61 review units, not plugins.
"""
from dataclasses import dataclass
import json
import hashlib
from pathlib import Path
import re

from jsonschema import Draft202012Validator
import yaml

WORKLOADS_DIR = Path(__file__).resolve().parents[1] / "workloads"


class WorkloadError(ValueError):
    """Invalid descriptor, tracker identity or workload provenance."""


def _tracker_binding(issue):
    fields = issue.get("fields") if isinstance(issue, dict) else None
    if not isinstance(fields, dict):
        raise WorkloadError("Missing Jira source fields")
    project, issue_type = fields.get("project"), fields.get("issuetype")
    if not isinstance(project, dict) or not isinstance(issue_type, dict):
        raise WorkloadError("Missing Jira source project or issue type")
    return fields, (project.get("key"), issue_type.get("name"))


@dataclass(frozen=True)
class Workload:
    id: str
    version: int
    project: str
    issue_type: str
    id_pattern: str
    attachment_template: str
    description_fallback: bool
    ready_labels: tuple
    skip_policy: str
    processed_label: str
    handoff_type: str
    identity_fields: tuple
    digest: str

    def validate_identity(self, key, project, issue_type):
        if (project, issue_type) != (self.project, self.issue_type):
            raise WorkloadError(f"{self.id}: source project/issue type does not match")
        if (not isinstance(key, str)
                or not re.fullmatch(r"[A-Z][A-Z0-9_]*-\d+", key)
                or not re.fullmatch(self.id_pattern, key)):
            raise WorkloadError(f"{self.id}: invalid source key {key!r}")

    def validate_ready(self, issue):
        fields, binding = _tracker_binding(issue)
        self.validate_identity(issue.get("key"), *binding)
        labels = fields.get("labels") or []
        if not all(label in labels for label in self.ready_labels):
            raise WorkloadError(f"{issue.get('key')}: missing strategy approval labels")

    def validate_handoff(self, data, key):
        for name in self.identity_fields:
            if name in data and data[name] != key:
                raise WorkloadError(f"{key}: attachment {name} conflicts with source identity")
        if "type" in data and data["type"] != self.handoff_type:
            raise WorkloadError(f"{key}: attachment type conflicts with tracker binding")
        for name, expected in (("workload_id", self.id), ("workload_version", self.version),
                               ("workload_digest", self.digest)):
            if name in data and data[name] != expected:
                raise WorkloadError(f"{key}: attachment {name} conflicts with selected descriptor")


def load_registry(directory=None):
    """Load and validate every descriptor; reject duplicate IDs/bindings."""
    directory = Path(directory) if directory is not None else WORKLOADS_DIR
    schema = json.loads((WORKLOADS_DIR / "_schema/workload.schema.json").read_text())
    validator = Draft202012Validator(schema)
    registry, bindings = {}, set()
    try:
        paths = sorted(directory.glob("*.yaml"))
        if not paths:
            raise WorkloadError(f"No workload descriptors in {directory}")
        for path in paths:
            data = yaml.safe_load(path.read_text())
            errors = list(validator.iter_errors(data))
            if errors:
                raise WorkloadError(f"{path.name}: {errors[0].message}")
            source = data["source"]
            pattern = source["id_pattern"]
            if not pattern.startswith("^") or not pattern.endswith("$"):
                raise WorkloadError(f"{path.name}: id_pattern must be anchored")
            re.compile(pattern)
            digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            selected = Workload(data["id"], data["version"], digest=digest,
                                **{**source, "ready_labels": tuple(source["ready_labels"]),
                                   "identity_fields": tuple(source["identity_fields"])})
            binding = (selected.project, selected.issue_type)
            if selected.id in registry or binding in bindings:
                raise WorkloadError(f"{path.name}: duplicate workload ID or tracker binding")
            registry[selected.id] = selected
            bindings.add(binding)
    except (OSError, yaml.YAMLError, re.error) as exc:
        raise WorkloadError(f"Unable to load workload descriptors: {exc}") from exc
    return registry


def get_workload(workload_id, registry=None):
    registry = load_registry() if registry is None else registry
    try:
        return registry[workload_id]
    except (KeyError, TypeError) as exc:
        raise WorkloadError(f"Unknown workload {workload_id!r}") from exc


def resolve_issue(issue, workload_id=None, registry=None):
    """Resolve by Jira project + issue type, then verify the source key.

    An explicit selection constrains the binding; it cannot override it.
    Key prefixes alone never select a workload.
    """
    registry = load_registry() if registry is None else registry
    _, binding = _tracker_binding(issue)
    candidates = [w for w in registry.values()
                  if (w.project, w.issue_type) == binding]
    if len(candidates) != 1:
        raise WorkloadError(f"Unknown or ambiguous tracker binding {binding!r}")
    selected = candidates[0]
    if workload_id is not None and selected.id != workload_id:
        raise WorkloadError(f"Selected workload {workload_id!r} conflicts with {binding!r}")
    selected.validate_identity(issue.get("key"), *binding)
    return selected
