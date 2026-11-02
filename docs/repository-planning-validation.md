# Repository-oriented epic validation

Implementation branch: `jira/AISDLC-547-repository-oriented-epics`.
Base: PR #40 head `424bffd790afa96a91244654a59f4c3d11800307`.
Implementation commit: `bba8726d82e8edd3e3cf6f0c005c4f46aa339abd`.

## Deterministic checks

Local full suites on Python 3.11.15 and 3.12.13 each passed **678 tests**, with
four opt-in model tests skipped. Both include the unchanged legacy workload
path. Additional report/evaluator checks passed 38 tests, with three model tests
skipped. `git diff --check` and the existing evaluation PII scanner passed.

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
