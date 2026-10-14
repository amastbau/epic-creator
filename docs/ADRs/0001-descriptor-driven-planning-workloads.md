---
title: "1. Descriptor-driven planning workloads"
status: Proposed
topics:
  - workloads
  - descriptors
  - architecture
---

# 1. Descriptor-driven planning workloads

Date: 2026-10-11
Updated: 2026-10-14 — add enablement discussion as architectural rationale.

## Status

Proposed — awaiting team review. The implementation PR is the review vehicle.

## Context

Epic Decomposer currently wires RHAI planning behavior directly into its
discovery, decomposition, review, revision, and Jira submission stages.
[AISDLC-58](https://redhat.atlassian.net/browse/AISDLC-58) defines a pluggable
planning pipeline across RFE Creator, Strategy Creator, and Epic Decomposer;
[AISDLC-61](https://redhat.atlassian.net/browse/AISDLC-61) delivers the Epic
Decomposer portion, with RHAI Initiatives as the first new production workload.

The cross-stage handoff contract has been verified against the live upstream
designs: strat-creator
[#76](https://github.com/opendatahub-io/strat-creator/pull/76) and
[#82](https://github.com/opendatahub-io/strat-creator/pull/82), and rfe-creator
[#172](https://github.com/opendatahub-io/rfe-creator/pull/172). Those designs
establish that the creators are separate peer pipelines that share descriptor
vocabulary, not code, and that gate evaluation stays in the consuming pipeline.
Handoff identity fields are station-specific: RFE Creator uses `type`,
`tracker_ref`, and `local_id`; Strategy Creator uses `strat_id`, `jira_key`,
and `source_rfe` or `source_initiative`. Its PRs #76/#82 contain the RFE
descriptor and registry; the Initiative descriptor is on
[Guy's fork](https://github.com/guyoron1/strat-creator/blob/b41aee7/types/initiative-strategy/type.yaml).
Approval is signaled by the same `strat-creator-human-sign-off` and
`strat-creator-rubric-pass` labels for both paths. RFE strategies use a
per-issue `{key}-strategy.md` attachment with description fallback.
Initiative strategies use only the newest `RHOAIENG-NNNN-strategy.md`
attachment; the description remains the Initiative's own text, and a missing
attachment means skip. These corrections are confirmed in
[AISDLC-61 comment 18872381](https://redhat.atlassian.net/browse/AISDLC-61?focusedCommentId=18872381).

### Rationale from the RFE Creator enablement session

The 2026-10-07 **ADLC Enablement Series: RFE Creator** discussion provides
additional rationale for this proposal. The source is the computer-generated
transcript supplied by the user on 2026-10-14; timestamps refer to that transcript.

- **Independent stations and explicit handoffs.** Antonin Stefanutti described
  autonomous stations coordinating through Jira as the system of record, using
  labels and human gates (06:56–09:47). This supports preserving source identity
  and provenance across peer pipelines, with each consumer enforcing its gates.
- **Flexible workload dispatch.** Shai Revivo described differing business-unit
  processes and the need for variation in dispatch from requirements to
  ready-to-code (48:21–50:47). Validated descriptors and referenced policies provide
  that variation within Epic Decomposer while keeping stage mechanics shared.
- **Deterministic checks and independent review.** Antonin advocated deterministic
  Python logic wherever possible and adversarial review of creative output in a
  fresh context, sometimes using a different model (11:06–14:40). This supports
  enforcing descriptor, provenance and review-gate rules in code while exposing
  planning content and review criteria through versioned policies.
- **Evaluation of policy changes.** Antonin described regression evaluation of
  skills and prompts, combining deterministic and model judges
  (08:21–09:47, 12:51–14:40, 28:23–31:42). Policy extraction therefore needs model
  quality evaluation against the existing Epic Creator corpus in addition to
  deterministic orchestration tests.
- **Separate runtime migration.** Antonin reported a green GitLab CI dry run with
  the Fullsend runner and gradual production migration as the next step
  (36:46–38:46). This supports keeping the workload architecture separate from
  the Fullsend runtime migration tracked in AISDLC-53.

These remarks support the architectural direction; they do not constitute team
acceptance of this ADR. The existing RFE Target Version gate, cloning and
auto-approval described in the session do not change the later verified
Initiative contract: original Initiative identity, attachment-only strategy
content, both Strategy Creator approval labels and no Target Version gate.

## Options

1. **Fork per workload.** Copy the pipeline for each new workload. Fast to
   start, but every fix and policy change must be replicated across forks.
2. **Branch on workload in shared code.** Keep one pipeline and scatter
   `if workload == ...` dispatch through the stages. Avoids forks, but
   workload-specific logic stays embedded in shared code and every new
   workload touches every stage.
3. **Wait for a shared planning engine.** Defer until a common engine exists
   across the creators. The upstream designs explicitly keep the creators as
   separate peer pipelines; the descriptor contract is the agreed integration
   point.
4. **Descriptor-driven consuming architecture.** Keep one pipeline whose
   stages resolve workload behavior from a validated, versioned descriptor
   selected once at entry.

## Decision

Epic Decomposer adopts a descriptor-driven consuming architecture.

A workload is defined by a versioned descriptor and registered in an in-repo
registry (for example `workloads/rhai-initiative.yaml`). The descriptor names
the source strategy contract, epic template and decomposition rules, review
policy, component and dependency policy, tracker destination, labels and
relationships, and evaluation set. The descriptor is data that references
reviewed in-repo policies; it does not load executable plugins.

Descriptor selection resolves once at entry and persists in pipeline state.
Jira intake selects the workload by the descriptor's `(project, issue_type)`
binding, then validates the source key and approval evidence. Strategy Creator
does not publish a workload-specific Jira marker. The Initiative path retains
the original Initiative identity (no `RHAISTRAT` clone); legacy artifacts with
no workload metadata retain the existing `RHAISTRAT` compatibility path.
Explicit workload selection or artifact metadata must agree with the source
identity. Conflicting or unknown identities fail before decomposition or
Jira writes. Initiatives have no Target Version release gate, and only the
decomposer's `epic-creator-auto-decomposed` label marks them processed;
hand-made child Epics do not prevent intake.

Every stage — fetch, decompose, review, revise, and submit — resolves its
behavior from the selected descriptor. Shared stages keep only stage procedure,
artifact locations, and safety and validation instructions. Generated
artifacts carry the workload identity and source provenance forward, and
submission preflights the descriptor identity before the first Jira write.

## Consequences

- Adding a workload means adding a validated descriptor and its policies, not
  forking the pipeline or editing shared stages.
- Descriptor validation rejects missing fields, duplicate IDs, unknown
  versions, unsafe paths, and unsupported policy references before a run
  starts.
- The existing `RHAISTRAT` discovery, artifact, DAG, review, and submission
  behavior is preserved as a compatibility path.
- Gate evaluation remains in Epic Decomposer, consistent with the
  peer-pipeline design; the reserved `inputs:` vocabulary is lint-check only.
- The Initiative no-clone path requires a `self` relation value in the handoff
  contract, ruled with AISDLC-60; the current enum is `clones | parent | link`.
- The descriptor schema must stay cohesive as workloads grow, and the
  cross-stage contract must be versioned so stations can evolve without
  lockstep releases.
- Changes to planning prompts and policies require model quality evaluations
  against the existing Epic Creator corpus. Deterministic flow tests verify
  orchestration and contracts; corpus evaluation remains outstanding for the
  extracted policies in PR #40.

Assisted-by: Codex
