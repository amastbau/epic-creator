#!/usr/bin/env python3
"""Evaluate a repository planning run against independently supplied expectations.

Pattern assertions supplement a semantic review; they do not prove prose quality.
Never provide this expected-answer file to generation workers.
"""
import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from artifact_utils import read_frontmatter
from repository_plan import (decomposition_digest, validate_repository_plan,
                             validate_epic_scopes)


def evaluate_repository_run(run_dir: Path, expected_path: Path) -> dict:
    defects = []
    result = {"passed": False, "defects": defects, "counts": {},
              "semantic_review": "Inspect the review artifact; deterministic checks alone do not prove scope purity."}
    try:
        expected = json.loads(Path(expected_path).read_text())
        root = Path(run_dir) / "artifacts"
        key = expected["source_key"]
        if not re.fullmatch(r"[A-Z][A-Z0-9]*-\d+", key):
            raise ValueError("Invalid expected source identity")
        plan = json.loads((root / f"repository-plans/{key}.json").read_text())
        context = json.loads((root / f"repository-plans/{key}-context.json").read_text())
        if not plan.get("ready_for_drafting"):
            actual = sorted({item["reason"] for item in plan.get("unresolved", [])})
            wanted = sorted(expected.get("unresolved_reasons", []))
            if not wanted or actual != wanted:
                defects.append(f"unresolved outcomes differ: {actual}")
            if list((root / "epic-tasks").glob(f"{key}-E*.md")):
                defects.append("blocked plan has drafted epics")
            result["counts"] = {"unresolved": len(plan.get("unresolved", [])), "epics": 0}
        else:
            validate_repository_plan(plan, context)
            epics = []
            for path in sorted((root / "epic-tasks").glob(f"{key}-*.md")):
                if re.fullmatch(rf"{re.escape(key)}-(?:BRANCH-[A-Z]-)?E\d{{3}}", path.stem):
                    data, body = read_frontmatter(path)
                    epics.append((data, body))
            validate_epic_scopes(plan, [data for data, _ in epics])
            implementations = [(data, body) for data, body in epics if data["type"] == "Implementation"]
            targets = {data["target_repository"]["inventory_key"] for data, _ in implementations}
            if targets != set(expected["scopes"]):
                defects.append(f"repository targets differ: {sorted(targets)}")
            by_id = {data["epic_id"]: data.get("target_repository", {}).get("inventory_key") for data, _ in epics}
            for target, wanted in expected["scopes"].items():
                matching = [(data, body) for data, body in implementations if data["target_repository"]["inventory_key"] == target]
                actual_work = {item for data, _ in matching for item in data["work_item_ids"]}
                if "work_item_ids" in wanted and actual_work != set(wanted["work_item_ids"]):
                    defects.append(f"work coverage differs for {target}: {sorted(actual_work)}")
                assigned = [item for item in plan["work_items"] if item["id"] in actual_work]
                for field in ("requirement_refs", "acceptance_refs"):
                    actual_refs = {ref for item in assigned for ref in item[field]}
                    if field in wanted and actual_refs != set(wanted[field]):
                        defects.append(f"{field} coverage differs for {target}: {sorted(actual_refs)}")
                for data, body in matching:
                    for pattern in wanted.get("required_patterns", []):
                        if not re.search(pattern, body):
                            defects.append(f"scope content missing for {target}: {pattern}")
                    for pattern in wanted.get("forbidden_patterns", []):
                        if re.search(pattern, body):
                            defects.append(f"scope contamination for {target}: {pattern}")
            edges = {tuple((by_id.get(dep), by_id[data["epic_id"]]))
                     for data, _ in epics for dep in data.get("dependencies", [])}
            if "dependencies" in expected and edges != {tuple(edge) for edge in expected["dependencies"]}:
                defects.append("repository dependencies differ")
            review, _ = read_frontmatter(root / f"epic-reviews/{key}-decomp-review.md")
            if (review.get("pass") is not True or review.get("repository_plan_digest") != plan["digest"]
                    or review.get("reviewed_decomposition_digest") != decomposition_digest(plan, root, key)):
                defects.append("passing review does not match current plan and scope content")
            result["counts"] = {"epics": len(epics), "implementation_epics": len(implementations),
                                "repositories": len(targets), "work_items": len(plan["work_items"]),
                                "requirements": len(plan["requirements"]), "dependencies": len(edges)}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        defects.append(f"invalid run: {exc}")
    result["passed"] = not defects
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--expected", required=True, type=Path)
    args = parser.parse_args()
    result = evaluate_repository_run(args.run_dir, args.expected)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
