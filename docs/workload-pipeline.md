# Workload planning policies

Workload selection now follows a local run through FETCH, DECOMPOSE, REVIEW,
REVISE and REPORT. Both shipped descriptors use the existing RHAI decisions:
`rhaistrat-strategy` accepts legacy strategies and `rhai-initiative` accepts
approved RHOAIENG Initiative attachments. The architecture is still
[Proposed](ADRs/0001-descriptor-driven-planning-workloads.md).

## Where strategies and policies live

An Initiative's strategy is its newest exact `{key}-strategy.md` Jira attachment.
Fetching stores the validated local strategy in `artifacts/strat-tasks/{key}.md`.
Planning rules live separately in the repository:

```text
workloads/
  rhai-initiative.yaml
  rhaistrat-strategy.yaml
  _schema/{workload,scoring}.schema.json
  policies/rhai/v1/
    artifacts.md
    decompose.md
    review.md
    revise.md
    scoring.yaml
```

The descriptor's `planning` block references those files, a component project
and local cache, and the ordered review criteria and gate. References must stay
inside `workloads/policies/`; missing files, escaping paths and invalid scoring
thresholds fail validation. Policies are reviewed data and Markdown instructions.
The registry does not load executable plugins.

Shared prompts retain stage procedure, artifact locations and validation steps.
The dispatcher supplies `POLICY_FILE`, `ARTIFACT_TEMPLATE`, `COMPONENT_FILE`,
`PASS_SCORE` and `MAX_SCORE` from the bound descriptor. RHAI scoring retains its
existing investigation guards; versioned scoring data supplies the thresholds.

Workers can inspect the selected frontmatter contract before writing:

```bash
python3 scripts/frontmatter.py schema epic-task --workload rhai-initiative
python3 scripts/frontmatter.py schema decomp-review --workload rhai-initiative
```

The Epic contract lists canonical Jira component names from the selected cache.
Typed Epic writes reject unknown names before changing frontmatter. The review
contract gives ordered criterion scores and each issue's exact criterion-name
enum. Rejected writes must be corrected before the worker marks its phase done.

## Run and resume

In an agent environment that exposes the existing skill:

```text
/epic-decompose RHOAIENG-9001 --workload rhai-initiative --headless
```

The key above is illustrative. Use a real approved Initiative with both
Strategy Creator approval labels and the strategy attachment. This skill performs
Jira reads and creates local artifacts and reports. It does not invoke submission.
Bootstrap also reads the selected component project and architecture context.

Without `--workload`, invocation preserves the legacy RHAISTRAT path unless its
registered workload enables repository planning (see below). Explicit
selection is passed to fetching and component bootstrap. An intake-only descriptor
cannot initialize a planning run.

Pipeline state records workload ID/version, descriptor digest, planning content
digest and source bindings. On an unfinished run, resume its dispatch loop rather
than initializing a new state. Changed descriptor data or policy bytes reject
resume. Generic state edits cannot switch the workload binding. A changed source
revision also fails once the FETCH boundary has bound it.

Adding `planning` or `submission` changes the shipped descriptor digests. Typed artifacts from
earlier implementations need a fresh fetch and planning run. Old legacy
artifacts without workload metadata remain supported by default invocation.

## Artifact and review checks

Agent frontmatter commands use `--source artifacts/strat-tasks/{ID}.md` to copy
validated source provenance. Completed stage boundaries require the same metadata
on summaries, main and conditional branch epics, and reviews. Missing epics,
conflicting identity or omitted provenance stop the pipeline before advancing.

Reviews include ordered `criterion_scores`. Validation checks their count, integer
range, total, pass status and recommendation against the selected gate. Critical
or major issues require zero points for the affected criterion. The RHAI gate
continues to require at least 10/14 and no zero-scoring criterion. Shared wave
scheduling and the existing two revision cycles are retained.

Reports record the workload/version, both digests, gate and each source revision.
[Submission and Jira recovery](workload-submission.md) are available through the
explicit submission CLI. The planning skill still stops at REPORT; production
runner configuration and real model quality evaluation remain subsequent work.

## Repository-oriented planning

An optional `planning.repository_policy` inserts `PLAN_REPOSITORIES` between
FETCH and DECOMPOSE. The shared planner extracts required work and acceptance
conditions, resolves their contribution repositories using configured evidence,
then groups work into one Implementation epic per repository in each effective
conditional scenario. Components, teams and documentation work stay within those
scopes. Investigations and repository dependencies remain explicit.

```yaml
planning:
  # Existing planning fields are still required.
  repository_policy:
    mode: one-implementation-epic-per-repository
    inventory: {source_id: mapping, path: inventory.yaml}
    guidance: {source_id: mapping, path: repository-planning.md} # Optional
    sources:
      - id: mapping
        url: https://github.com/example/repository-ownership
        ref: main
        paths: [inventory.yaml, mapping.md, repository-planning.md]
        role: authoritative
        owner: example-maintainers
        max_age_seconds: 86400
      - id: architecture
        url: https://gitlab.example.org/example/architecture/-/tree/main/release-context
        ref: main
        role: supporting
        owner: example-architecture
```

These URLs are examples. Repository URLs use optional `paths` (default `.`).
GitHub/GitLab file and directory links accept an explicit matching `ref`,
including branch names containing slashes. Files must live in an accessible Git
repository; credentials come from the existing Git credential helper and must
never be embedded in URLs. Local `file://` Git sources support isolated tests.
Supported content is Markdown, YAML, JSON and text. This feature does not import
Google Docs or invent their Git location.

Optional `guidance` selects a UTF-8 Markdown prompt from one of these sources.
Its `source_id` must match a configured source and its repository-relative `path`
must be included in that source's selected files. It can also live in a separate
configured Git repository. For example, `repository-planning.md` might contain:

```markdown
Read mapping.md's Contribution repository column for ownership; its Product
repository column lists downstream distributions. Use architecture documents to
identify component boundaries and mapping.md to resolve contribution targets.
If these sources disagree about ownership, leave the target unresolved.
```

The planner and reviewer use this prompt to interpret the supplied documents.
It cannot override shared workflow rules, declared source roles, approved targets,
strategy requirements or repository boundaries, and cannot establish ownership
by itself. All other retrieved documents remain evidence rather than instructions.
The context includes the guidance text and hash, bound to its Git commit and the
planning snapshot. Missing, empty or unreadable guidance blocks drafting. Changing
it invalidates the existing snapshot and review. Publication evidence records its
source, path and hash. Omitting `guidance` preserves the existing behavior.

The inventory follows `_schema/repository-inventory.schema.json`:

```yaml
version: 1
revision: example-v1
repositories:
  - inventory_key: operator
    provider: github
    host: github.com
    namespace: example
    repository: operator
    label: target-repo-operator
    aliases: [example/operator]
    approval_reference: approved-contribution-policy-reference
```

Inventory ownership must approve contribution destinations, including upstream
versus downstream. Architecture evidence helps resolve scope; an approved repo
being available does not make it the right destination for every change.
Optional explicit repository names in strategy text are validated against this
inventory and the resolved work. No new Jira input field is required.

The context manifest pins Git commits, file hashes, workload and strategy input.
The planner writes a proposal; `repository_plan.py finalize --workload ID
--source ISSUE-KEY` atomically validates/finalizes it. Missing evidence, conflicts,
unknown targets and grouping cycles block drafting with a persisted reason.
Independent conditional gates that would create simultaneous scopes for one
repository also block with `conditional_repository_collision`; the planner must
resolve that conflict rather than silently merging gate semantics.
Submission re-fetches refs, checks freshness when configured, and requires the
review to match the current plan and full decomposition content. Replanning
requires a new run and a fresh review. A policy/source change cannot silently
resume an old run.

Each Implementation epic carries its canonical `target_repository`,
`repository_scope`, `work_item_ids`, `components` and `mapping_snapshot_digest`.
Publication derives exactly one `target-repo-*` label from the inventory in the
initial Jira create request and attaches pinned evidence. Recovery rejects a
missing or conflicting live target rather than implicitly relabeling an issue.
For enabled default workloads, default invocation uses these same checks and
cannot publish historical artifacts without targets. Unconfigured workloads
retain their existing behavior.

Both shipped RHAI workloads remain unconfigured for this feature until the
maintained Git mapping source, contribution inventory and owner expectations
are verified. Synthetic tests do not establish production source readiness.
See [repository evaluation](../eval/repository-planning/README.md).

The architecture proposal is [ADR 0002 in PR #45](https://github.com/fullsend-ai/epic-creator/pull/45).
See the [implementation plan](repository-planning-plan.md) for this producer change.

## Testing without Jira writes

Run the deterministic local contract tests:

```bash
python3 -m pytest -q tests/test_workload_pipeline.py
python3 -m pytest -q tests/test_workload_intake.py tests/test_fetch_strategy.py \
  tests/test_artifact_utils.py tests/test_frontmatter_cli.py \
  tests/test_check_decompose_progress.py tests/test_compute_ai_scores.py \
  tests/test_fetch_components.py tests/test_workload_pipeline.py
```

The flow tests use synthetic cached strategies and deterministic agent outputs
with socket and URL access blocked. They exercise the actual registry, dispatcher,
artifact checks, revision/re-review, scoring and report for RHOAI and a second
synthetic workload. They prove local orchestration and contracts; they do not
measure model-generated plan quality. Separate legacy artifact tests cover
compatibility. Eval staging now copies the registry and policies into its isolated
workspace so existing model evaluations can load them.

The full suite has a known upstream failure in
`tests/test_submit.py::TestDryRun::test_dry_run_shows_component_warning` when local
component context is absent. Report it separately from workload failures.
