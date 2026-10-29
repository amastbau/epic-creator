---
title: "2. Single-repository targets for implementation epics"
status: Proposed
topics:
  - workloads
  - jira
  - repositories
  - routing
  - provenance
---

# 2. Single-repository targets for implementation epics

Date: 2026-10-22
Updated: 2026-10-29 — clarify the single-target Jira contract and add the October 26 mapping and harness-routing proposals.

## Status

Proposed — awaiting review with Bill and the Jira/project owners. The options and open questions below are not settled decisions.

## Context

AISDLC-90 defines how Epic Creator assigns implementation epics to repositories so that Fullsend can run code generation in the correct repository. AISDLC-4 requires each implementation epic to identify exactly one canonical target repository from an approved inventory; each eligible epic produces one code-agent invocation and one pull request. AISDLC-4 permits a dedicated Jira field or another explicitly defined, parseable description value. It does not require a list-valued target. The earlier implementation plan's list representation is a proposal and must be reconciled with this contract before implementation.

The October 26, 2026 meeting notes describe the one-repository restriction as enforced and attribute the proposal to Eder, to simplify merge workflows. Amos proposed using an LLM with repository descriptions to help identify the target. The discussion also considered a static mapping table and Architecture Context documentation. The notes make an ADR and coordination with Bill the next steps; they do not record an approved mapping method.

In the follow-up Slack discussion, bkorren proposed that each harness define an entity source query against Jira. The routing alternatives were separate Jira projects per repository, with each harness querying its project, or a shared project with a Jira field such as Component populated upstream and harness queries scoped to the matching values. bkorren also pointed to ADR 98 and related open ADRs as relevant context that does not fully settle the entity-source query. The linked RHAISTRAT-2376 example spans several components and delivery areas. It illustrates why a broad feature may need repository-specific implementation epics; it does not change the one-repository contract for each implementation epic.

The Fullsend poller currently receives a workflow-wide target repository and does not read a per-epic repository field. Fullsend's Jira guide describes repository-specific polling with JQL. Epic Creator and Fullsend therefore need to agree on a machine-readable value and matching harness query before the contract can be implemented.

The inspected RHOAI Architecture Context entry for RHODS Operator records that component's repository and branch and lists repositories used for managed-component manifests. That is component and manifest-source metadata; it does not map Jira components or implementation epics to code-generation targets. The separate [RHAI component-to-repository mapping notes](https://docs.google.com/document/d/1Hv34Ci58_BIhWmWJXKE34w2ZlQrQWMeg_fjvMsv4Erk/edit?tab=t.0#heading=h.wdwmerquvvbx) are the direct candidate source, but their contents have not been verified because Google API access was denied in this work session.

A Jira component, repository description, or Architecture Context entry can help classify work, but none alone necessarily identifies the authorized code-generation target. In particular, an upstream/downstream repository relationship is not proof that either repository is the intended contribution target.

## Decision drivers

- Enforce one canonical repository, one code-agent invocation, and one pull request per implementation epic.
- Make repository assignment auditable and validate it against an approved inventory.
- Let each harness query only the implementation epics assigned to its repository.
- Preserve component and architecture evidence without treating it as an implicit repository target.
- Stop visibly on missing, ambiguous, conflicting, malformed, stale, or unapproved mappings.

## Options

### Mapping source and resolution

1. **Have an LLM choose a repository directly from repository descriptions.** This can interpret broad feature language, but direct model selection is variable and difficult to make an auditable authority. It can also confuse related repositories, forks, or upstream/downstream lineage.
2. **Map Jira Components to repositories with a static table.** This is deterministic and reviewable when component relationships are verified. It requires an owner and change process, and components may describe teams or architecture areas rather than a one-to-one repository boundary.
3. **Use Architecture Context as the sole mapping source.** The inspected RHODS Operator page records its repository and branch and lists managed-component manifest sources. This describes component and deployment metadata; it does not define a Jira-to-code-generation-target rule. Other Architecture Context entries may provide useful evidence, but their mapping authority and completeness would need verification.
4. **Use a grounded LLM with both RHAI sources.** Give the model the epic's verified Jira fields, the approved repository inventory, the RHAI component-to-repository mapping notes, and relevant Architecture Context entries. The model selects one repository and cites the source evidence it used; deterministic validation checks that the result is exactly one canonical identity from the approved inventory. This can connect epic language to both component mappings and architecture metadata, while depending on accurate, accessible sources and explicit abstention behavior.

### Jira and harness routing

1. **Use a distinct Jira project per repository.** Each harness can query its project's issues. This keeps queries simple if project boundaries already match repository boundaries, but it makes project placement an upstream routing decision and may not fit projects organized by product or team.
2. **Use one shared project and a target field or Component filter.** Epic Creator writes the target upstream and each harness queries its assigned value. A dedicated single-valued target field makes the repository explicit; using Component directly requires proving that the relevant values map unambiguously to repositories.
3. **Use project scope as a coarse filter and an explicit target field as the dispatch authority.** Harnesses may keep project-specific JQL where useful, while every implementation epic still carries one exact target value. This supports existing project boundaries without making project placement or a multi-valued component the only repository contract.

## Decision

Propose option 4 for mapping and option 3 for Jira routing, subject to confirmation with Bill and the Jira/project owners.

- Each implementation epic has one scalar `target_repository` value: a canonical provider, host, namespace, and repository identity from the approved inventory. It is not a multi-repository list. The preferred Jira representation is a dedicated single-valued target field. A stable parseable description block is a fallback only if the field is unavailable and AISDLC-4 owners approve the encoding.
- Once their contents and ownership are verified, use the RHAI component-to-repository mapping notes as mapping evidence and Architecture Context as relevant component/repository metadata. The inspected RHODS Operator entry alone is not a Jira-to-target mapping. The LLM may use both sources and verified Jira epic fields to select the repository directly, but it must choose from the approved inventory and return the canonical identity plus precise source references.
- Deterministic validation accepts only one canonical, approved target. If either source is unavailable or stale, the sources conflict, the epic evidence is ambiguous, or the model cannot cite support, leave the target unresolved and block publication or dispatch. Do not substitute a default or first candidate.
- The explicit `target_repository` value is the harness dispatch selector. Each harness entity source must query for its exact canonical value. A project-specific query may narrow the candidate set, but project placement cannot override a missing, malformed, or conflicting target value. Component may be used as a selector only if its mapping is verified and unambiguous; it is not the target identity by itself.
- Missing or invalid targets, conflicting Jira signals, stale mapping evidence, and multiple repository candidates remain unresolved and block publication or dispatch. They require correction or human review; no fallback selects the first candidate.
- A feature that requires implementation in multiple repositories is decomposed into repository-specific implementation epics. Link them, and add dependency edges only for actual prerequisites. Multi-repository execution requires a later change to AISDLC-4 and the Fullsend consumer contract.
- The Fullsend consumer must read and validate the per-epic target before dispatch. Its current workflow-wide target behavior is not sufficient to implement this contract; the field, serialization, JQL, and consumer change must be agreed with Bill before implementation.

## Consequences

- The Jira contract and the meeting's single-repository constraint are explicit. The list-valued representation in the implementation plan and any typed artifact proposal must be revised or explicitly reconciled with this scalar decision before implementation.
- Every dispatched implementation epic has one approved target and produces one pull request in that repository. Broad feature scope such as RHAISTRAT-2376 is split into repository-specific implementation epics where it crosses repository boundaries, with links only for real dependencies.
- Mapping evidence should record the Jira fields used, the mapping-note and Architecture Context versions/revisions, the cited source sections, the approved-inventory revision, and the selected canonical repository. Changes to those inputs invalidate stale planning evidence.
- Jira project boundaries can help scope queries, but the explicit target field remains the producer/consumer contract. Per-repository Jira projects are viable where they already match the repository inventory; they do not remove the need to validate target identity.
- The dedicated Jira field's ID and type, exact serialization, mapping-notes owner/update process and access, verified RHAI examples, model abstention/evidence format, and a named non-RHAI pilot remain open. Do not start resolver implementation until these are agreed.
- Any Fullsend consumer change belongs in the Fullsend-owned change and must be reviewed against AISDLC-4. This ADR does not authorize or implement that consumer change.

## References

- [AISDLC-90 — Tag implementation epics with target repositories](https://redhat.atlassian.net/browse/AISDLC-90)
- [AISDLC-4 — Deploy Fullsend code generation for Red Hat AI engineering](https://redhat.atlassian.net/browse/AISDLC-4)
- [RHAISTRAT-2376 — AWS Neuron Support for Red Hat AI](https://redhat.atlassian.net/browse/RHAISTRAT-2376), a multi-component feature example
- [Architecture Context repository](https://github.com/opendatahub-io/architecture-context/)
- [RHOAI 2.10 RHODS Operator architecture entry](https://github.com/opendatahub-io/architecture-context/blob/main/architecture/rhoai-2.10/rhods-operator.md) — component repository and manifest-source metadata, not an epic-target mapping
- [RHAI component-to-repository mapping notes](https://docs.google.com/document/d/1Hv34Ci58_BIhWmWJXKE34w2ZlQrQWMeg_fjvMsv4Erk/edit?tab=t.0#heading=h.wdwmerquvvbx) — direct candidate source; access/content not verified
- [Fullsend poller at the inspected revision](https://github.com/fullsend-ai/fullsend/blob/15136ebc5b31720b80a8a45220c58b0dfda9d6ec/internal/cli/poll.go)
- [Fullsend Jira integration guide at the inspected revision](https://github.com/fullsend-ai/fullsend/blob/15136ebc5b31720b80a8a45220c58b0dfda9d6ec/docs/guides/user/jira-integration.md)
- Amos Mastbaum and Eder Ignatowicz, meeting notes, 2026-10-26 (supplied in the AISDLC-90 task context)
- bkorren, follow-up Slack discussion on AISDLC-90 (supplied in the task context)
- [Fullsend PR #8616](https://github.com/fullsend-ai/fullsend/pull/8616) — reference for the repository's ADR format; its decision is separate from this proposal.
