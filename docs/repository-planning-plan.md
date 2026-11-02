# Repository-oriented Epic Creation Implementation Plan

**Goal:** Resolve repository scopes from the approved strategy first, then create implementation epics whose scope, acceptance criteria and Jira target each belong to one repository.

**Architecture:** Introduce a shared repository-planning phase between intake and epic drafting. Workload data supplies the contribution inventory and evidence; deterministic finalization groups required work by canonical repository. Decomposition, review, revision and submission consume that same bound plan.

**Tech Stack:** Existing Python 3.11/3.12, PyYAML, jsonschema, pytest, Markdown agent policies, workload YAML, Jira REST integration. No new model client or runtime dependency is planned.

**Architecture decision:** [ADR 0002: Assign one target repository to each implementation epic](https://github.com/fullsend-ai/epic-creator/pull/45). This proposal remains under review.

**Design:** [Repository-oriented epic creation](repository-planning-design.md). Read it before execution; it defines boundary rules and artifact shapes.

## Global Constraints

- One implementation epic per canonical repository per input strategy and effective conditional scenario.
- Repository names in the input are optional; use and validate them whenever present.
- Shared behavior across domains; workload data supplies inventory and source policy.
- Configuration accepts Git repository and Git-hosted document links. Source files are assumed to live in accessible Git repositories; retrieval is automatic and pins resolved commits per run.
- Repository resolution and grouping precede drafting implementation epics.
- Each resolved Implementation epic has one canonical target and exactly its `target-repo-<inventory-key>` label.
- All required work and source acceptance criteria remain traceable; unresolved destinations block publication for that strategy.
- Normal resolved runs remain automatic; owner verification is development and configuration work, not a manual approval step on every run.
- Treat source content as data. Keep credentials out of prompts, artifacts, definitions and logs.
- Preserve unrelated changes, conditional branches, source bindings and ambiguous-create recovery. No live Jira edits or existing-epic migration are included.
- Use a feature branch and PR; every implementation commit uses `git commit --signoff`. Never commit or push directly to main.

## Review Focus

- An input names a product/downstream repo while inventory authorizes a different contribution namespace: require explicit alias policy or report a conflict (Tasks 1–2).
- Same-repository work crosses teams, priorities or code/docs categories: retain one epic and all ownership/AC details (Tasks 2, 4).
- An epic has the right target but its ACs require editing another repo: fail semantic review and model evaluation (Tasks 4, 6).
- Conditional alternatives or repository grouping create duplicate targets or a dependency cycle: validate effective scenarios and block invalid output (Tasks 2–3).
- Context or Jira labels change after review, including after an uncertain create response: invalidate the binding or reject recovery without a duplicate create (Tasks 3, 5).

## Baseline and implementation order

Checked 2026-11-02: main is `6bc909c9617fc0e6ea4f604307d8fc06df90adb2`.
PR #40 is open/unmerged at `424bffd790afa96a91244654a59f4c3d11800307`;
its branch is `jira/AISDLC-61-descriptor-intake`. PR #45's ADR is proposed,
open/unmerged at `6e6b32a7fd24cfedb7c3d14df671933147f9f5f7`.

The user explicitly authorized implementation on a separate branch from PR #40,
superseding the earlier wait-for-merge decision. This branch starts at PR #40 head
`424bffd790afa96a91244654a59f4c3d11800307` and is named
`jira/AISDLC-547-repository-oriented-epics`. Keep PR #40 unchanged; this is a
stacked feature against `jira/AISDLC-61-descriptor-intake`, to be retargeted after
that foundation merges. Paths/interfaces below refer to that verified base.

Tasks run in order. Every task follows red test → implementation → passing tests →
signed-off feature-branch commit. Run the full suite once after the integrated
change; repeat only for subsequent changes or failures.

## File map

| Files | Responsibility |
| --- | --- |
| `scripts/repository_sources.py` (new) | Normalize repository/document links, retrieve selected Git content and record pinned source manifests |
| `scripts/repository_context.py` (new) | Inventory/source snapshot loading, canonical identities, binding and freshness checks |
| `scripts/repository_plan.py` (new) | Work-plan JSON contract, deterministic grouping, coverage/dependency checks and epic-scope validation |
| `workloads/_schema/repository-inventory.schema.json`, `workloads/_schema/repository-plan.schema.json` (new) | Validate inventory and planner proposal/final plan shapes |
| `workloads/_schema/workload.schema.json`, `scripts/workload.py` | Descriptor repository policy and digest binding |
| `skills/epic-decompose/prompts/repository-plan-agent.md` (new) | Shared source-grounded work extraction and repository assignment |
| `scripts/pipeline_state.py`, `scripts/pipeline_workload.py`, `scripts/check_decompose_progress.py` | Enforce PLAN_REPOSITORIES phase and safe resume/completion |
| `scripts/artifact_utils.py`, `scripts/frontmatter.py` | Repository-scoped epic/review metadata and CLI validation |
| `skills/epic-decompose/prompts/{decompose,review,revise}-agent.md` | Shared plan consumption and repository invariants |
| `workloads/policies/rhai/v1/{decompose,review,revise,artifacts}.md` | Remove conflicting boundaries; preserve domain requirements |
| `scripts/submit.py`, `scripts/workload_submit.py` | Initial target-label publication, complete preflight and recovery checks |
| `scripts/generate_run_report.py`, `scripts/generate_html_report.py` | Show targets, evidence, unresolved work and scope coverage |
| `tests/test_repository_sources.py`, `tests/test_repository_context.py`, `tests/test_repository_plan.py`, `tests/test_repository_creation_e2e.py` (new) | Meaningful new contract and integration tests |
| Existing workload/pipeline/submission tests and eval staging | Regression checks and repeatable model evaluation |

### Task 1: Add workload-controlled repository evidence and inventory

**Files:** Create `scripts/repository_sources.py`, `scripts/repository_context.py`, `workloads/_schema/repository-inventory.schema.json`, `tests/test_repository_sources.py`, `tests/test_repository_context.py`. Modify `scripts/workload.py`, `workloads/_schema/workload.schema.json`, `tests/test_workload_intake.py`.

**Interfaces:** Extend `PlanningPolicy` with optional `repository_policy: dict | None`.
Add `normalize_git_source(reference: dict) -> dict` and
`fetch_git_sources(policy: dict, cache_root: Path) -> list[dict]` in
`repository_sources.py`. Normalize repository/document links to Git URL, requested
ref and selected paths; resolve refs and return manifests with commit SHA,
materialized paths and content digests. Use configured Git credentials. The same
fetch interface refreshes ref resolution before resume/submission; compare results
against the bound context before accepting cached artifacts.
Add `load_repository_context(selected: Workload, source_path: Path, artifacts_dir: Path) -> dict`
and `assert_context_current(context: dict, selected: Workload, source_path: Path) -> None`.
They return/validate the context shape in the spec and raise `WorkloadError` on
invalid configuration. Represent a missing/unavailable required source as an
explicit blocked context reason so reports can preserve it.

- [ ] **1. Write failing tests.** `test_repository_and_document_links_normalize_to_same_source` covers supported GitHub/GitLab repository, file and directory URLs, with explicit ref required for ambiguous links. `test_git_sources_are_fetched_at_one_resolved_commit` uses a local Git remote and verifies selected Markdown/YAML/JSON content and manifest hashes. `test_moving_ref_invalidates_bound_context` advances that remote and rejects reuse of old bindings. Cover inaccessible repo, missing path/ref and authenticated retrieval with no credential values in captured output. `test_uses_only_selected_workload_sources` asserts that an alternate workload with JSON mapping needs no RHAI architecture files. `test_inventory_aliases_require_declared_contribution_policy` rejects an undeclared product→upstream substitution. `test_context_binds_content_and_source_roles` asserts changed strategy text, source bytes, roles or inventory changes the binding. Parameterize duplicate identities/labels, missing approval reference and expired freshness.
- [ ] **2. Run:** `python -m pytest tests/test_repository_sources.py tests/test_repository_context.py tests/test_workload_intake.py -q`; new tests must fail before implementation.
- [ ] **3. Implement retrieval, context and descriptor schema.** Accept linked Git sources with refs and path selectors, fetch them automatically into a run cache and freeze resolved SHAs. Reuse configured authorized Git access and architecture bootstrap where suitable; keep retrieval in `repository_sources.py` and deterministic local validation in `repository_context.py`. Use existing PyYAML/jsonschema and content hashing. Load the inventory from its configured source ID/path; validate content/provenance and include source manifests in planning bindings. Inventory keys and controlled labels are unique within a workload; canonical identity includes host/namespace. No executable plugins or fallback inventory. No caller-prepared snapshot or direct Google Docs integration is required under the accessible-Git assumption.
- [ ] **4. Run the same tests; require all pass.** A descriptor without repository policy remains loadable for compatibility. Enabling the policy with incomplete evidence yields a recorded blocked result, never a guessed target.
- [ ] **5. Commit:** `git commit --signoff -m "feat: bind repository inventory and evidence to planning workloads"` after staging only this task's files.

### Task 2: Resolve required work and finalize repository scopes before drafting

**Files:** Create `scripts/repository_plan.py`, `workloads/_schema/repository-plan.schema.json`, `skills/epic-decompose/prompts/repository-plan-agent.md`, `tests/test_repository_plan.py`.

**Interfaces:** `finalize_repository_plan(context: dict, proposal: dict) -> dict`;
`validate_repository_plan(plan: dict, context: dict) -> None`;
`validate_epic_scopes(plan: dict, epics: list[dict]) -> None`.
All raise `WorkloadError` for invalid structures; valid unresolved plans remain
serializable with `ready_for_drafting: false`. Add CLI commands `prepare`,
`finalize`, `validate`, each accepting `--workload ID --source KEY --artifacts-dir PATH`.
`prepare` writes bound context; `finalize` reads the proposal, writes the final
plan atomically and sets `complete: true` only after validation. Exit 0 means
valid and ready, 2 means recorded unresolved/blocked, 1 means malformed/error.

- [ ] **1. Write failing tests with complete synthetic strategy/context/proposal fixtures.** Assert manager+cloudmanager work IDs occur in one `operator` scope; `dashboard`+`operator` yield two scopes; docs in `operator` stay there while docs in `guidelines` yield another scope. The planner may assign only inventory identities with evidence references supporting the assignment; an allowed but wrong target must fail the evidence/semantic evaluation, not pass merely through allowlisting.
- [ ] **2. Add contract assertions.** Every source requirement/AC reference is covered or explicitly deferred with source-supported justification; work IDs are unique; dependencies exist and are acyclic. Required implementation work is never silently omitted or converted to Investigation. Unknown/multiple targets, conflicting explicit names, unavailable required sources and ambiguous destinations remain unresolved with reasons/candidates. Test two components/teams in one repo, mutually exclusive branches, duplicate same-target scopes in an effective scenario, same-repo internal sequencing and `repository_dependency_cycle` after grouping.
- [ ] **3. Run:** `python -m pytest tests/test_repository_plan.py -q`; require the new tests fail.
- [ ] **4. Implement the shared prompt and deterministic finalizer.** The agent extracts atomic work and AC facets from source input, records optional named repos, proposes assignments and cites configured evidence. It creates no epic files and invokes the deterministic `finalize` CLI as its final action. The finalizer groups by canonical identity, preserves all work/ownership/priority fields and computes scope dependencies and snapshot digest. It can validate references and cited source identity; semantic correctness of the evidence and prose remains an explicit review/evaluation responsibility.
- [ ] **5. Run the same tests; require all pass.** Verify unresolved JSON is retained and no epic drafts are created by the planner/finalizer.
- [ ] **6. Commit:** `git commit --signoff -m "feat: plan repository scopes before epic drafting"`.

### Task 3: Enforce repository planning in dispatch, polling and resume

**Files:** Modify `scripts/pipeline_state.py`, `scripts/pipeline_workload.py`, `scripts/check_decompose_progress.py`, `skills/epic-decompose/SKILL.md`, `tests/test_workload_pipeline.py`, `tests/test_check_decompose_progress.py`, `scripts/generate_run_report.py`.

**Interfaces:** Reuse existing `phase_config`, `validate_inputs`, `validate_completed`
and `bound_workload`. Add `PLAN_REPOSITORIES` to the relevant phase enum, agent
configuration, main sequence, completed-phase validation and poller. The phase
fetches configured Git sources and prepares context before agent launch;
the agent's final CLI call writes the
completed final plan before polling can finish. Collection revalidates that plan.
Expose `REPOSITORY_PLAN` and `MAPPING_SNAPSHOT_DIGEST` to downstream agents.

- [ ] **1. Write failing dispatch tests.** The enabled sequence is FETCH → PLAN_REPOSITORIES → DECOMPOSE → existing review/revision cycle. `test_draft_not_launched_without_ready_repository_plan` asserts zero draft launches for missing, partial or blocked output. `test_changed_mapping_snapshot_cannot_resume` changes inventory, strategy or evidence after completion and expects invalidation. `test_one_blocked_repository_plan_does_not_stop_other_strategy` preserves PR #40's per-source isolation.
- [ ] **2. Run:** `python -m pytest tests/test_workload_pipeline.py tests/test_check_decompose_progress.py -q`; new cases must fail.
- [ ] **3. Integrate the phase.** Special-case the shared repository planner in `phase_config` rather than trying to load a nonexistent domain `PlanningPolicy.plan_repositories` file. Incomplete proposals remain pending; the poller reads only an atomically finalized plan. Valid unresolved output becomes blocked/error status with its persisted report and no DECOMPOSE launch. Test that finalization precedes polling completion, avoiding a collection/polling deadlock. Existing wait-for-wave behavior, timeouts and branch handling remain intact. Resume never silently accepts a different digest or restarts model work against changed inputs. Replanning invalidates downstream artifacts/reviews and occurs as a new planning attempt. All registered workloads enabling the policy follow this sequence, including the default RHAISTRAT invocation.
- [ ] **4. Run the same tests; require all pass.** Extend run reporting with planning status/reason and artifact references; make reporting readable when no epic files exist.
- [ ] **5. Commit:** `git commit --signoff -m "feat: enforce repository planning before decomposition"`.

### Task 4: Draft, review and revise epics within repository scopes

**Files:** Modify `scripts/artifact_utils.py`, `scripts/frontmatter.py`, shared decompose/review/revise prompts, RHAI v1 decompose/review/revise/artifacts policies, `tests/test_artifact_utils.py`, `tests/test_frontmatter_cli.py`, `tests/test_workload_pipeline.py`. Extend `tests/test_repository_plan.py` and `scripts/repository_plan.py`.

**Interfaces:** Add `repository_scope`, `work_item_ids`, `target_repository`,
`mapping_snapshot_digest`, `components` to epic metadata, required conditionally
for repository-mode Implementation epics. Add `repository_plan_digest` and
`reviewed_decomposition_digest` to review metadata. Add
`decomposition_digest(plan: dict, artifacts_dir: Path, source_key: str) -> str`;
it hashes plan, epic bodies/core metadata and summary, excluding only
submission-written `jira_key` and transient completion/revision flags.

- [ ] **1. Write failing producer-contract tests.** Reject two same-target implementation epics in an effective plan, an AC work item assigned to the wrong scope, missing work IDs, forged canonical identity, a branch escaping its scenario and a review digest from an older body. A merged code/docs scope must retain documentation accuracy ACs. Multiple canonical components survive frontmatter round-trip with the first retained as `component`.
- [ ] **2. Run:** `python -m pytest tests/test_artifact_utils.py tests/test_frontmatter_cli.py tests/test_repository_plan.py tests/test_workload_pipeline.py -q`; new cases must fail.
- [ ] **3. Implement metadata and policy changes together.** DECOMPOSE reads the ready plan and drafts its repository scopes. Replace component/team/subsystem/priority/docs rules that would recreate same-repo siblings. Required special work stays inside the repository scope with its ACs; mixed scopes have no misleading docs-only implementation label. Investigations remain distinct where justified. Update triage so “small” or “docs-only” cannot collapse several repository scopes into one epic. Summaries retain source-wide integration checks and traceability.
- [ ] **4. Enforce review and revision invariants.** Wrong/missing target, cross-repo modification scope, missing AC coverage, duplicate repo scope or mismatched snapshot is a zero-score blocking defect under the existing rubric; do not add a parallel score system. The reviewer compares prose to original source and inventory evidence, not only IDs. Revision preserves repository boundaries; a repository-plan defect requires replanning and fresh review. Final passing review stamps both current digests. Any semantic artifact change after review invalidates the pass.
- [ ] **5. Run the same tests; require all pass.** Mark tests using prepared agent outputs as contract tests; they do not demonstrate actual model compliance. Model proof belongs to Task 6.
- [ ] **6. Commit:** `git commit --signoff -m "feat: create and review epics within repository boundaries"`.

### Task 5: Publish the reviewed target with the initial Jira epic

**Files:** Modify `scripts/submit.py`, `scripts/workload_submit.py`, `scripts/generate_html_report.py`, `tests/test_workload_submit.py`, `tests/test_submit.py`, `tests/test_workload_e2e.py`.

**Interfaces:** Keep `_build_plan` and `preflight` entry points. Repository-mode
plan entries add the inventory-derived target label and complete `components`
list. Preflight calls `assert_context_current`, `validate_epic_scopes` and checks
review digests before any Jira mutation. Recovery's `_verify_issue` compares
actual controlled repository labels to the reviewed target.

- [ ] **1. Write failing wire-level tests using PR #40's local Jira substitute.** `test_initial_create_contains_one_matching_repo_label` checks the POST body itself, canonical target in the published description/artifact, all components and unchanged workflow labels. Parameterize invalid/missing target, unresolved plan, expired or changed sources, stale review, and an altered body; assert zero Jira writes for each. Test that default invocation cannot bypass a repository-enabled workload's checks.
- [ ] **2. Add recovery tests.** A dropped create response followed by retry reuses the journal and exact existing epic. Unknown/multiple/mismatched target labels on a recovered issue fail; no second create or implicit relabel occurs. Preserve unrelated live labels. Once a partial submission exists, a changed target requires explicit reconciliation rather than a duplicate create. Historical target-less artifacts cannot enter repository-mode submission.
- [ ] **3. Run:** `python -m pytest tests/test_workload_submit.py tests/test_submit.py tests/test_workload_e2e.py -q`; new cases must fail.
- [ ] **4. Implement publication/preflight/recovery.** Derive the controlled label from inventory rather than model-authored labels; add it to the initial issue create request. Include mapping/plan digests in submission fingerprints and publish evidence with artifacts. Refresh configured Git refs through `fetch_git_sources` and compare resolved commits/manifests with the reviewed binding before writes; apply the declared freshness policy and PR #40's live strategy check. Show target, inventory revision and unresolved reasons in reports. Repository-enabled default invocations use the same preflight; no legacy fallback accepts incomplete targets.
- [ ] **5. Run the same tests; require all pass.** This tests Jira creation through a mock transport; production Jira creation is not part of implementation verification.
- [ ] **6. Commit:** `git commit --signoff -m "feat: publish repository-scoped epics with validated targets"`.

### Task 6: Prove creation-time behavior and activate prepared workloads

**Files:** Create `tests/test_repository_creation_e2e.py`, `tests/fixtures/repository-planning/`, `eval/repository-planning/README.md`, `eval/scripts/check_repository_plan.py`. Modify `tests/test_workload_e2e.py` and `docs/workload-pipeline.md`. Add registered workload configuration and versioned `workloads/repositories/rhai/v1/` data only after source/inventory ownership and contribution policy are verified.

**Interfaces:** Add `evaluate_repository_run(run_dir: Path, expected_path: Path) -> dict`
in `eval/scripts/check_repository_plan.py`, with CLI `RUN_DIR --expected FILE`.
It returns counts/defects for target correctness, scope purity, work/AC coverage,
grouping, dependencies and expected unresolved outcomes; exit nonzero on a failed
hard condition. Record semantic review findings alongside deterministic results.
Keep raw real-strategy inputs and transcripts out of committed fixtures using
the existing anonymization/staging conventions.

- [ ] **1. Write a failing integrated test before updating fixtures.** Feed a synthetic approved strategy through FETCH, repository planning, drafting, review/revision and local Jira creation. Assert one operator issue contains both manager/cloudmanager work IDs, repo-local ACs and one target label; a dashboard/operator strategy yields two issues. An alternate workload uses a differently structured JSON source with no RHAI-specific dependency. Include a mutation with a correct operator label but dashboard modification ACs and require a failed review/evaluation outcome.
- [ ] **2. Run:** `python -m pytest tests/test_repository_creation_e2e.py -q`; require the new test fails. Implement the missing integration, staging copies, evaluator and documentation; run it again and require pass. Explicitly distinguish deterministic fake-agent fixtures from model results.
- [ ] **3. Establish production input readiness.** Resolve AISDLC-546's pending contribution inventory/source ownership and freshness policy, plus operator namespace and guideline publication destination. Configure the RHAI mapping document's maintained Git URL/path and Architecture Context Git URL/release paths; the original mapping reference is a Google Doc, so verify its Git copy/location exists rather than claiming the assumption is already fulfilled. Owners verify expected answers from source intent, not historical PR outcomes. Verify at least one real non-RHAI case with a different Git-hosted source structure. These are delivery prerequisites; implementation and synthetic tests can progress independently.
- [ ] **4. Run fresh model evaluations from strategy input.** Use the selected PR #40-derived workload, pinned code/policy/model/source revisions, the new PLAN_REPOSITORIES stage and the complete decompose/review/revise loop. Do not feed expected targets, historical PR outcomes or old drafts into generation. Run the operator case, a cross-repository case and the verified non-RHAI case. Use dry-run submission or the local Jira substitute. Record baseline separately, input/output hashes, transcripts, actual model/runtime, semantic review findings and evaluation results. Every agreed hard condition must pass; unresolved expected cases must remain unresolved. A production run adapted to staged Jira input must say so.
- [ ] **5. Enable `planning.repository_policy` in the prepared registered workloads and verify default invocation enforcement.** Do not activate a workload whose inventory or owner expectations are still pending. Keep test-only alternate workloads out of the production registry. Re-run the focused integration checks after enabling configuration.
- [ ] **6. Run required repository checks once:** `python -m pytest tests/ -v --tb=short` on Python 3.11 and 3.12 using the existing CI matrix; `python eval/scripts/scan_real_pii.py` for any real-case fixture changes; `git diff --check`. Verify new files ship in the Fullsend package and reports retain blocked plans. Record failures honestly; do not count unit-test passes as model evaluation passes.
- [ ] **7. Commit:** `git commit --signoff -m "test: verify repository-oriented epic creation end to end"`. Before any push, verify every new commit has an author-matching DCO sign-off. Publish through the feature PR with validation results and the required PR disclosure footer. No automatic merge or deployment.

## Definition of done

| Evidence | Required result |
| --- | --- |
| Phase ordering | A validated repository plan exists before any implementation epic is drafted |
| Linked Git evidence | Repository/document links are fetched automatically and bound to resolved commits; changed refs invalidate the plan |
| Operator example | One operator implementation epic covers manager and cloudmanager, with their tests/ACs |
| Cross-repo example | Each affected repository gets its own complete implementation epic; real dependencies survive |
| Prose and coverage review | No required work disappears; no epic's modification scope crosses its target repository |
| Publication | Initial Jira create has exactly the matching target label and canonical target evidence |
| Failure cases | Missing/conflicting/expired evidence, changed bindings and invalid targets produce blocked output and no Jira writes |
| Reuse | Alternate synthetic workload passes isolation; one owner-verified real non-RHAI run passes actual planning/review |
| Regression | Existing suite and package checks pass; recovery does not duplicate issues |

## Delivery boundaries and current status

Implementation now runs on `jira/AISDLC-547-repository-oriented-epics`, based on
PR #40 head `424bffd790afa96a91244654a59f4c3d11800307`, following the user's later
explicit instruction to branch from that PR. Tasks 1–5 are implemented; Task 6
adds the evaluator, isolated Jira integration, model harness and documentation.
No production workload is activated by this change. Source/inventory approval
and verified real-case expectations remain pending, so production readiness is
not claimed. The implementation does not alter live Jira or deploy Fullsend.

The implementation is AISDLC-547. AISDLC-548 and AISDLC-4 consume the producer
contract and deploy execution separately; their code is not bundled here.
AISDLC-549 can reuse the evaluator. AISDLC-546's earlier replay is useful as the
negative baseline, not acceptance evidence for this feature.
