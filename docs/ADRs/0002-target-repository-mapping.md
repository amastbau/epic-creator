---
title: "2. List-valued repository targets for implementation epics"
status: Proposed
topics:
  - workloads
  - jira
  - repositories
  - provenance
---

# 2. List-valued repository targets for implementation epics

Date: 2026-10-22

## Status

Proposed — awaiting review. The implementation must not treat unresolved items below as settled decisions.

## Context

AISDLC-90 calls for each implementation epic to carry a typed, machine-readable list of approved repository targets and evidence that makes the mapping auditable. The list must preserve the full result even when the current executor cannot act on every target.

(Fullsend's current Jira poller uses a workflow-wide `--target-repo` and has no per-epic repository field, so the initial integration can dispatch only one target; a list prepares the contract for future multi-repository support without changing the value type.)

The current AISDLC-4 contract also scopes an implementation epic to one repository and one invocation/PR. The repository assignment therefore needs to be explicit, checked against an approved inventory, and compatible with today's single-target dispatch behavior. It must distinguish repositories by provider, host, namespace, and repository name so that forks and similarly named repositories are not conflated.

The implementation plan proposes classifying Jira content against a finite architecture-area catalog and then resolving the classification through approved mapping data. The plan and the ADLC handbook do not name who maintains that catalog. This ADR does not assign a person or team to it.

## Options

1. **Use a scalar repository value.** This matches today's one-repository execution limit, but cannot preserve a multi-repository mapping and would require changing the value type when fan-out becomes available.
2. **Use a repository list from the start and gate current dispatch.** This preserves complete mapping results while allowing today's consumer to accept only a single-item list.
3. **Enable multi-repository dispatch immediately.** This would require an explicit fan-out contract in Fullsend and a compatible update to AISDLC-4; current behavior does not provide that support.

## Decision

Propose option 2.

- Every typed implementation-epic artifact uses `repository_targets: RepositoryIdentity[]`, including the one-target case. A target identifies its provider, host, namespace, and repository name, and must match an approved repository inventory. Reject duplicate identities; do not collapse a list to its first item.
- A resolved assignment is a nonempty list of unique approved targets and carries mapping evidence. An unresolved assignment carries its reason and any candidates, has no dispatchable target, and blocks handoff. A multi-repository assignment preserves every matching target and is not dispatchable through the current Fullsend consumer.
- Where architecture-area classification is used, the classifier may select only keys from a finite, versioned catalog and must cite the Jira fields supporting the classification. Repository selection is deterministic mapping against approved data; the classifier does not nominate repositories. The catalog's maintainer and change process remain undecided pending review.
- The initial Fullsend integration must read and validate the list, and dispatch only when it contains exactly one approved target. It must reject absent, malformed, unresolved, unapproved, or multi-item assignments; it must never silently truncate a multi-item list. The current poller does not yet read a per-epic repository field.
- Until AISDLC-4 and Fullsend define multi-repository execution, a genuine cross-repository deliverable is represented by linked repository-specific implementation epics. Add dependency links only for real prerequisites. Investigation epics remain exempt from the repository-target requirement unless the cross-system contract requires otherwise.
- The Jira representation must preserve the list shape and allow Fullsend to validate the target. Whether this is a dedicated Jira field or a stable parseable description block, and the exact field/encoding, remain open for agreement with the AISDLC-4 and Fullsend contract owners before implementation.

## Consequences

- Single-target assignments use the same list type as future multi-target assignments.
- Review artifacts can retain complete multi-repository results while current dispatch fails closed on lists longer than one.
- Mapping evidence must identify the Jira-field evidence, classification/catalog revision when applicable, repository-map revision and rule, and the resolved canonical target identities. Changes to those inputs must invalidate stale planning evidence.
- Before implementation, reviewers must settle the catalog maintainer and change process, verified Jira classifier inputs, exact Jira serialization, canonical identity rules, and a named non-RHAI pilot with stakeholder-verified examples. The current plan does not settle these items.
- Any Fullsend consumer change belongs in the Fullsend-owned change and must be reviewed against the AISDLC-4 contract.

## References

- [AISDLC-90 — Tag implementation epics with target repositories](https://redhat.atlassian.net/browse/AISDLC-90)
- [AISDLC-4 — Epic-to-repository contract](https://redhat.atlassian.net/browse/AISDLC-4)
- [Fullsend poll CLI at the inspected revision](https://github.com/fullsend-ai/fullsend/blob/a2be1678c5dbd9361a77f04de5ec260320e4fb9f/internal/cli/poll.go)
- [Fullsend Jira poll types at the inspected revision](https://github.com/fullsend-ai/fullsend/blob/a2be1678c5dbd9361a77f04de5ec260320e4fb9f/internal/jirapoll/types.go)
- [Fullsend PR #8616](https://github.com/fullsend-ai/fullsend/pull/8616) — reference for the repository's ADR format; its decision is separate from this proposal.
