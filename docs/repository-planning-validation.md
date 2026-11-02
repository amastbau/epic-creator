# Repository-oriented epic validation

Implementation branch: `jira/AISDLC-547-repository-oriented-epics`.
Base: PR #40 head `424bffd790afa96a91244654a59f4c3d11800307`.
Initial implementation commit: `bba8726d82e8edd3e3cf6f0c005c4f46aa339abd`.

## Deterministic checks

After the scope cleanup, local full suites on Python 3.11.15 and 3.12.13 each
reported **689 passed, 5 skipped, 4 failed**. The four failures exactly match
the inherited package-fixture failures reproduced on PR #40 below; no other
tests failed. Earlier additional report/evaluator checks passed 38 tests, with
three model tests skipped. `git diff --check` and the existing evaluation PII
scanner passed.

The full PR scope review removed two unrelated changes: a sign-off addition in
`eval/scripts/stage-case.sh` and dependency-copy repairs in
`tests/test_fullsend_package.py`. Both files now match PR #40 exactly. Remaining
changes implement repository planning/guidance, artifact and review binding,
publication/recovery, reports, or their tests and documentation.

On an isolated checkout of exact PR #40 base `424bffd790afa96a91244654a59f4c3d11800307`,
the package suite has **4 failed, 46 passed**. These inherited failures are:

- `test_sandbox_bootstrap_reuses_prepared_inputs`: fixture omits `workload`.
- `test_project_compact_hook_activation[epic-creator-False-True]`: fixture omits `pipeline_workload`.
- `test_project_compact_hook_activation[epic-creator-True-True]`: same missing module.
- `test_project_hook_does_not_duplicate_plugin_hook`: same missing module.

Their repairs belong to the base change rather than this repository-planning PR.
Earlier 693-pass full-suite results included those unrelated repairs and are
superseded by the post-cleanup results above.

The tests exercise Git document links, commit/content binding, changed refs,
unavailable evidence, source coverage, repository grouping, dependencies,
conditional scenarios, review content binding, initial Jira labels/components,
evidence attachments and recovery after a lost create response. The integrated
tests use the real dispatcher and CLI commands with a loopback HTTPS Jira
substitute. They verify an alternate workload reading JSON ownership evidence.

The fresh review found one conditional grouping defect: independent Investigation
gates could create simultaneous scopes for one repository. A regression first
reproduced it; the planner now blocks with `conditional_repository_collision`
rather than inventing combined gate semantics. The planner/pipeline/artifact
checks passed 37 tests after this fix.

## Fresh synthetic model checks

These runs start from synthetic strategy input and configured Git evidence,
without expected targets or old drafts supplied to generation. They use the
actual selected prompts, policies and artifact validators, followed by local
submission. Expectations use source requirement/AC IDs independently of
model-chosen work IDs. Exact staged code/policy/input hashes, source commits,
model responses, runtime and Jira requests are retained under ignored
`eval/runs/2026-11-02-repository-planning/`.

| Case | Expected behavior | Result |
| --- | --- | --- |
| Manager and cloudmanager | One operator epic, both logging requirements and source ACs | Passed full loop, local Jira create and independent evaluator |
| Operator and Dashboard | Two repository epics, Dashboard depends on operator | Passed full loop, local Jira create and independent evaluator |
| Alternate workload with JSON ownership | Same shared behavior with another project/destination policy | Passed full loop, local Jira create and independent evaluator |
| Correct operator target plus Dashboard modification AC | Review must reject cross-repository scope | Rejected: 10/14, `pass: false`, zero for Epic Boundaries and Acceptance Criteria Quality |

Runtime: Claude Code 2.1.250. Actual response metadata reports `claude-opus-5`
and `claude-sonnet-4-5@20250929`; per-call usage and duration are preserved rather
than inferred from an alias. Each model phase has a fresh context and no tools.
Jira credentials are removed from the model CLI environment.

Initial attempts failed safely before publication: the tool-free adapter omitted
canonical component input, and the planner validator rejected acceptance checks
that also traced assigned HLRs. The adapter now includes the component file; the
CLI finalizer rejects noncanonical planned components. Criteria may trace assigned
requirements while still covering every assigned source AC. Both fixes have
observed failing/passing regressions. Initial attempts are not counted as passes.

The alternate workload's first draft also attempted to emit a review file during
drafting. The adapter rejected it before publication. Output paths are now
restricted by phase, drafting instructions prohibit review artifacts, and the
repository-mode dispatcher clears any pre-created review before launching its
independent review phase. The regression first failed and then passed; 71
artifact/pipeline checks passed after the protection was added. One additional
adapter attempt exposed incompatible Python escaping in the CLI's Unicode JSON
Schema regex; the corrected path schema was accepted on the subsequent run.

## Optional document interpretation guidance

`repository_policy.guidance` can select a Git-hosted Markdown prompt by source ID
and path. The planner and reviewer receive its text in the bound context.
Configured source roles, approved targets and shared repository rules still apply;
guidance cannot establish repository ownership by itself. Publication evidence
identifies the guidance source, path and content hash.

New regressions first reproduced missing context content, accepted inline
tampering, ignored missing/empty/unreadable guidance, guidance-only ownership
citations, rejected valid configuration and missing publication provenance.
These now pass. Additional checks cover unsafe/unknown references, configuration
digest binding and changed guidance blocking publication after review.
The focused repository context/plan checks passed 39 tests, and the guidance,
submission, pipeline and artifact checks passed 58 tests before the full suites.

A fresh tool-free model planning check used an alternate workload and mapping
rows with two otherwise unexplained repository columns. The selected guidance
identified `lane-2` as the contribution column and `lane-1` as the downstream
runtime column. The planner resolved manager/cloudmanager work to one operator
scope, preserved both requirements and ACs, and cited the actual mapping rows.
The CLI finalizer accepted it; no epics or Jira writes were made in this planning
check. This is a focused guidance check, not a repeat of the earlier full model
loops. Raw response, input/context, pinned sources and staged code hashes are
retained under the ignored run directory's `guidance-model/` subdirectory.

## Activation boundary

Neither shipped RHAI workload enables `planning.repository_policy` yet. A verified
maintained Git mapping document, approved contribution inventory/ownership,
operator namespace and guideline publication destination remain required.
Owner-verified real RHAI and non-RHAI expected answers are also pending. Synthetic
model runs establish behavior on their supplied evidence; they do not verify
production ownership or replace those real-case acceptance checks.

No live Jira issues, Fullsend deployment, PR #40 branch or main branch were
changed. The feature is available for prepared workloads through the optional
configuration documented in [workload planning](workload-pipeline.md).
