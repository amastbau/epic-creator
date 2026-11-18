# Repository planning evaluations

`tests/test_repository_creation_e2e.py` runs the real dispatcher, frontmatter
commands, review binding, reports and publication against a local HTTPS Jira
substitute. Prepared agent outputs cover operator grouping, cross-repository
dependencies and a second workload reading JSON ownership evidence. These are
contract tests, not evidence of model compliance or verified real ownership.

The evaluator compares a completed run with independent expectations:

```bash
python3 eval/scripts/check_repository_plan.py RUN_DIR --expected expected.json
```

```json
{
  "source_key": "EXAMPLE-9001",
  "scopes": {
    "operator": {
      "requirement_refs": ["HLR-1", "HLR-2"],
      "acceptance_refs": ["AC-1", "AC-2"],
      "required_patterns": ["[Mm]anager", "[Cc]loudmanager"],
      "forbidden_patterns": ["Modify Dashboard source"]
    }
  },
  "dependencies": []
}
```

For blocked cases use `unresolved_reasons` instead of `scopes`. Counts report
work, requirements, repositories, epics and dependencies. Structural contracts,
source bindings and review content bindings must pass. Required/forbidden text
patterns are explicit regression checks, not a general semantic verifier.
Expected source references can be defined before generation, independently of
model-chosen work item IDs. Prepared-output tests may additionally assert exact
`work_item_ids`.
Reviewers still inspect full source intent, scope and acceptance criteria; a
correct target label cannot establish that an epic's prose belongs in that repo.

Fresh model runs are opt-in (`REPOSITORY_E2E_MODEL=1`) and keep raw responses,
actual model/runtime, input hashes and local Jira requests in the temporary run
workspace. Generation receives the strategy, actual selected prompts/policies,
inventory and pinned evidence, never expected targets or old drafts. Review
runs use a fresh model context. Model credentials stay in the CLI environment;
Jira credentials are stripped before invoking the model. No live Jira writes
are used. Preserve evidence outside Git or under ignored `eval/runs/`.

RHAI activation and real-case acceptance remain gated on a verified maintained
Git mapping document, approved contribution inventory (including operator
namespace and guideline destination), owner-verified expected answers and a
real non-RHAI case. Synthetic model runs do not replace those prerequisites.
