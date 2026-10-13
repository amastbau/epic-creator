# Descriptor-driven strategy intake

AISDLC-61 adds a validated intake registry, opt-in strategy fetching, workload
provenance, and descriptor-bound local planning stages. The
architecture remains [Proposed](ADRs/0001-descriptor-driven-planning-workloads.md).
See [workload planning](workload-pipeline.md) for policy storage, stage validation
and tests. Submission routing, recovery and production Fullsend configuration
remain later review units.

## Existing invocation

Existing commands without `--workload` retain the legacy RHAISTRAT path,
including description fallback and artifacts without workload metadata.
Legacy discovery JQL, including its Target Version filter, remains supplied
by the caller/CI job.

## Opt-in Initiative intake

Install `requirements.txt` using your normal Python environment. The existing
Jira environment variables (`JIRA_SERVER`, `JIRA_USER`, `JIRA_TOKEN`) are used
for read operations. Do not put their values in files or command history.

```bash
python3 scripts/fetch_strategy.py fetch \
  'project = RHOAIENG AND issuetype = Initiative AND labels = strat-creator-rubric-pass AND labels = strat-creator-human-sign-off' \
  --workload rhai-initiative --skip-if-processed --ids-file tmp/initiative-ids.txt

python3 scripts/fetch_strategy.py fetch-one RHOAIENG-9001 \
  --workload rhai-initiative
```

The query deliberately has no Target Version condition. This slice continues
to accept caller-supplied JQL; moving production discovery queries into the
descriptor is a later configuration change.

Both commands resolve the fetched issue's project and issue type, then check
that they agree with `--workload` and its key grammar. A key prefix alone never
selects a workload. Both approval labels are required. When attachment
frontmatter provides `type`, `strat_id`, `jira_key` or `source_initiative`, those
fields must agree with the selected source contract.

Intake reads the newest exact `{key}-strategy.md` attachment, comparing upload
timestamps with timezone offsets. A missing Initiative attachment skips the
source; a failed download, invalid body or conflicting identity fails without
using the Initiative description. Batch IDs include only written strategies.
`--skip-if-processed` uses the descriptor's policy: for Initiatives, only
`epic-creator-auto-decomposed` marks the source processed. Hand-made child
Epics and Incorporates links do not cause an Initiative skip. Fetching and
re-fetching create local artifacts only; they perform no Jira writes.

## Artifact provenance

Opt-in artifacts retain `strat_id`/`parent_strat` for existing consumers and add
`workload_id`, `workload_version`, `workload_digest`, `source_key`,
`source_project`, `source_issue_type` and `source_revision`. Descriptors with
planning policies also stamp `planning_digest`. Downloaded
attachments also record `attachment_source`, `attachment_id` and
`attachment_created`. Source keys preserve the original Initiative identity.

All four artifact schemas validate workload/source identity together. Old
RHAISTRAT artifacts remain valid without these fields. Unidentified Initiative
artifacts, mixed source identities, unknown descriptors and stale versions or
digests are rejected. The digest hashes canonical descriptor data, so a
semantic descriptor change invalidates previously stamped artifacts even when
someone forgot to increment its version. Formatting changes do not affect it.

## Adding an intake workload

Add a YAML descriptor under `workloads/`, following
`workloads/_schema/workload.schema.json`. The registry loads from the repository
location, independently of the current working directory. It rejects missing
fields, unsupported versions/policies, unsafe attachment templates, invalid
key patterns, duplicate IDs and duplicate project/type bindings. Descriptors
are data; they do not name executable plugins.

The schema covers source identity, strategy body, ready labels, processed policy,
handoff identity and optional planning policies. Intake-only descriptors remain
valid; starting a pipeline requires `planning`. Submission requirements will
extend the contract in a later AISDLC-61 review unit.

## Local contract tests

```bash
python3 -m pytest -q tests/test_workload_intake.py tests/test_fetch_strategy.py \
  tests/test_artifact_utils.py tests/test_frontmatter_cli.py
python3 -m pytest -q
```

The tests use synthetic issues and mock Jira reads/downloads while exercising
the real registry, schema validators, CLI handlers and filesystem. On upstream
`1544ef1`, the complete baseline suite has one known failure:
`tests/test_submit.py::TestDryRun::test_dry_run_shows_component_warning`.
Report that separately from new intake failures.

Assisted-by: Codex
