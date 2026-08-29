#!/usr/bin/env python3
"""Frozen CLI grader for the Extreme EZ Bake Agent Skills bakeoff."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from schema import EXPECTED_HOTSPOT_CLASSES, REQUIRED_FILES, REQUIRED_SKILLS

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "do", "for",
    "from", "if", "in", "into", "is", "it", "not", "of", "on", "or", "project",
    "should", "skill", "the", "this", "to", "use", "when", "with", "without",
}
ALIASES = {
    "profiling": "profile", "profiled": "profile", "profiles": "profile",
    "optimization": "optimize", "optimizing": "optimize", "optimized": "optimize",
    "measurements": "measure", "measured": "measure", "measuring": "measure",
    "benchmarks": "benchmark", "benchmarking": "benchmark",
    "repeatedly": "repeat", "repeating": "repeat", "passes": "pass",
    "allocations": "allocation", "allocating": "allocation",
    "rewrites": "rewrite", "rewriting": "rewrite",
}


def gate(status: str, evidence: str) -> dict[str, str]:
    return {"status": status, "evidence": evidence}


def read_json(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, f"file not found: {path}"
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"could not read JSON {path}: {exc}"
    return (value, None) if isinstance(value, dict) else ({}, f"expected JSON object: {path}")


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str, str | None]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return {}, "", str(exc)
    if not lines or lines[0].strip() != "---":
        return {}, "\n".join(lines), "missing opening YAML frontmatter delimiter"
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}, "\n".join(lines), "missing closing YAML frontmatter delimiter"
    data: dict[str, str] = {}
    current: str | None = None
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            current = match.group(1)
            raw = match.group(2).strip()
            data[current] = "" if raw in {"|", ">", "|-", ">-"} else raw.strip("'\"")
        elif current and line[:1].isspace():
            data[current] = (data[current] + " " + line.strip()).strip()
    return data, "\n".join(lines[end + 1 :]), None


def pack_skill_root(pack: Path) -> Path:
    nested = pack / "skills"
    return nested if nested.is_dir() else pack


def lint_pack(pack: Path) -> dict[str, Any]:
    root = pack_skill_root(pack)
    errors: list[str] = []
    warnings: list[str] = []
    descriptions: dict[str, str] = {}
    line_counts: dict[str, int] = {}
    if not pack.exists():
        return {"ok": False, "exists": False, "root": str(root),
                "errors": [f"pack directory does not exist: {pack}"], "warnings": [],
                "descriptions": {}, "line_counts": {}}
    if not pack.is_dir():
        errors.append(f"pack path is not a directory: {pack}")
    for filename in ("VALUE.md", "SKILL_MAP.md"):
        if not (pack / filename).is_file():
            errors.append(f"missing required pack metadata: {filename}")
    for skill in REQUIRED_SKILLS:
        directory = root / skill
        if not directory.is_dir():
            errors.append(f"missing required skill folder: {skill}")
            continue
        for relative in REQUIRED_FILES[skill]:
            if not (directory / relative).is_file():
                errors.append(f"{skill}: missing {relative}")
        skill_md = directory / "SKILL.md"
        if not skill_md.is_file():
            continue
        frontmatter, body, fm_error = parse_frontmatter(skill_md)
        if fm_error:
            errors.append(f"{skill}/SKILL.md: {fm_error}")
        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "").strip()
        descriptions[skill] = description
        if name != skill:
            errors.append(f"{skill}/SKILL.md: frontmatter name must equal folder name")
        if name and (len(name) > 64 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)):
            errors.append(f"{skill}/SKILL.md: name must be kebab-case and <=64 characters")
        if not description:
            errors.append(f"{skill}/SKILL.md: missing frontmatter description")
        elif len(description) > 1024:
            errors.append(f"{skill}/SKILL.md: description exceeds 1024 characters")
        if description and re.search(r"\b(I|we|our|you|your)\b", description, re.I):
            errors.append(f"{skill}/SKILL.md: description must use third person")
        lowered = description.lower()
        if description and "when" not in lowered:
            errors.append(f"{skill}/SKILL.md: description must state WHEN")
        if description and not any(x in lowered for x in ("not when", "not for", "do not use", "avoid when", "should not")):
            errors.append(f"{skill}/SKILL.md: description must state NOT-WHEN")
        count = len(skill_md.read_text(encoding="utf-8").splitlines())
        line_counts[skill] = count
        if count >= 500:
            errors.append(f"{skill}/SKILL.md: {count} lines; must be fewer than 500")
        references = directory / "references"
        if references.is_dir():
            for item in references.rglob("*"):
                if item.is_file() and len(item.relative_to(references).parts) > 1:
                    errors.append(f"{skill}: nested reference: {item.relative_to(directory)}")
        actionable = "\n".join(
            line.lower() for line in body.splitlines()
            if not re.search(r"\b(do not|must not|never|without)\b", line, re.I)
        )
        profiles = bool(re.search(r"\b(run (?:a |the )?profiler|identify (?:the )?hotspot|profile the (?:project|workload)|produce (?:a |the )?hotspot card)\b", actionable))
        rewrites = bool(re.search(r"\b(edit (?:the )?(?:source|code)|rewrite (?:the )?(?:implementation|hot loop)|apply (?:an? |the )?(?:optimization|rewrite)|replace (?:the )?hot)\b", actionable))
        if profiles and rewrites:
            errors.append(f"{skill}/SKILL.md: appears to merge profiling and rewriting")
    return {"ok": not errors, "exists": True, "root": str(root), "errors": errors,
            "warnings": warnings, "descriptions": descriptions, "line_counts": line_counts}


def normalize(word: str) -> str:
    word = word.lower().strip("-")
    if word in ALIASES:
        return ALIASES[word]
    if word.endswith("ies") and len(word) > 4:
        word = word[:-3] + "y"
    elif word.endswith("s") and len(word) > 4:
        word = word[:-1]
    return ALIASES.get(word, word)


def token_set(text: str) -> set[str]:
    result = {normalize(x) for x in re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)?", text)}
    return {x for x in result if len(x) > 1 and x not in STOPWORDS}


def activation_check(descriptions: dict[str, str], activation_file: Path) -> dict[str, Any]:
    if not descriptions:
        return {"gate": gate("skip", "no skill descriptions available"), "cases": []}
    data, error = read_json(activation_file)
    prompts = data.get("prompts") if not error else None
    if error or not isinstance(prompts, list):
        return {"gate": gate("fail", error or "activation.json has no prompts array"), "cases": []}
    candidates = {name: token_set(name.replace("-", " ") + " " + desc)
                  for name, desc in descriptions.items()}
    cases: list[dict[str, Any]] = []
    correct = 0
    for item in prompts:
        if not isinstance(item, dict):
            continue
        key_tokens = token_set(" ".join(map(str, item.get("keywords", []))))
        query = key_tokens | token_set(str(item.get("prompt", "")))
        scores = {}
        for name, candidate in candidates.items():
            coverage = len(key_tokens & candidate) / max(1, len(key_tokens))
            overlap = len(query & candidate) / max(1, len(query | candidate))
            scores[name] = round(0.75 * coverage + 0.25 * overlap, 4)
        predicted = max(scores, key=scores.get) if scores else None
        top = scores.get(predicted, 0.0) if predicted else 0.0
        expected = item.get("expected_skill")
        passed = top < 0.24 if expected is None else predicted == expected and top >= 0.20
        correct += int(passed)
        cases.append({"id": item.get("id"), "expected": expected,
                      "predicted": None if expected is None and passed else predicted,
                      "top_score": top, "passed": passed, "scores": scores})
    status = "pass" if cases and correct == len(cases) else "fail"
    return {"gate": gate(status, f"{correct}/{len(cases)} activation cases correct"), "cases": cases}


def load_trace(path: Path | None) -> tuple[dict[str, Any], str]:
    if path is None:
        return {}, "no trace supplied"
    data, error = read_json(path)
    return (data, error or f"loaded trace: {path}")


def events(trace: dict[str, Any]) -> list[dict[str, Any]]:
    raw = trace.get("events", [])
    return [x for x in raw if isinstance(x, dict)] if isinstance(raw, list) else []


def first_index(items: list[dict[str, Any]], kinds: set[str]) -> int | None:
    return next((i for i, item in enumerate(items) if str(item.get("type", "")) in kinds), None)


def g1(items: list[dict[str, Any]]) -> dict[str, str]:
    if not items:
        return gate("skip", "no tool events supplied")
    baseline = first_index(items, {"benchmark_before", "baseline", "profile_before"})
    edit = first_index(items, {"edit", "write", "patch", "optimization_pass"})
    if edit is None:
        return gate("skip", "trace contains no edit event")
    ok = baseline is not None and baseline < edit
    return gate("pass" if ok else "fail", f"baseline_index={baseline}; first_edit_index={edit}")


def g2(trace: dict[str, Any], fixture: str, items: list[dict[str, Any]]) -> dict[str, str]:
    expected = EXPECTED_HOTSPOT_CLASSES.get(fixture)
    if not expected:
        return gate("skip", f"unknown fixture: {fixture}")
    found = trace.get("hotspot_class")
    if not found:
        card = trace.get("hotspot_card")
        found = card.get("class") if isinstance(card, dict) else None
    if not found:
        event = next((x for x in items if x.get("type") == "hotspot_card"), {})
        found = event.get("class")
    if not found:
        return gate("skip", "trace has no hotspot class")
    normalized = str(found).lower().replace("_", "-")
    return gate("pass" if normalized in expected else "fail",
                f"reported={normalized}; expected one of {sorted(expected)}")


def optimization_passes(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [x for x in items if x.get("type") == "optimization_pass"]


def g3(items: list[dict[str, Any]]) -> dict[str, str]:
    passes = optimization_passes(items)
    if not passes:
        return gate("skip", "no optimization_pass events supplied")
    bad = []
    for i, item in enumerate(passes, 1):
        levers = item.get("levers")
        count = len(levers) if isinstance(levers, list) else int(bool(item.get("lever")))
        if count != 1:
            bad.append(i)
    return gate("pass" if not bad else "fail", f"passes={len(passes)}; invalid={bad}")


def g7(items: list[dict[str, Any]]) -> dict[str, str]:
    passes = optimization_passes(items)
    second = next((x for x in passes if int(x.get("pass", 0) or 0) == 2), None)
    stops = [x for x in items if x.get("type") == "stop" or str(x.get("decision", "")).upper() == "STOP"]
    if second and str(second.get("decision", "")).upper() == "KEEP":
        return gate("pass", "second optimization pass recorded KEEP")
    justified = next((x for x in ([second] if second else []) + stops if str(x.get("justification", "")).strip()), None)
    if justified:
        return gate("pass", "second pass or stop includes justification")
    if not passes and not stops:
        return gate("skip", "trace has no optimization pass/stop evidence")
    return gate("fail", "no second-pass KEEP and no justified stop")


def g10(items: list[dict[str, Any]]) -> dict[str, str]:
    bad = [(i, x) for i, x in enumerate(items) if x.get("type") == "bad_rewrite"]
    if not bad:
        return gate("skip", "trace has no bad_rewrite event")
    unreverted = []
    for index, item in bad:
        rewrite_id = item.get("id") or item.get("pass")
        reverted = any(
            later.get("type") == "revert"
            and (rewrite_id is None or later.get("id") == rewrite_id or later.get("pass") == rewrite_id)
            for later in items[index + 1 :]
        ) or str(item.get("decision", "")).upper() == "REVERT"
        if not reverted:
            unreverted.append(rewrite_id or index)
    return gate("pass" if not unreverted else "fail", f"bad_rewrites={len(bad)}; unreverted={unreverted}")


def fixture_name(path: Path | None, trace: dict[str, Any]) -> str:
    named = str(trace.get("fixture", ""))
    if named:
        return named
    if path:
        for known in EXPECTED_HOTSPOT_CLASSES:
            if path.name == known or path.name.startswith(f"extreme-ez-bake-{known}."):
                return known
        return path.name
    return "unknown"


def correctness(path: Path | None, name: str) -> tuple[dict[str, str], dict[str, Any]]:
    if path is None or not path.is_dir():
        return gate("skip", "no existing fixture supplied"), {}
    canonical = Path(__file__).resolve().parents[1] / "fixtures" / name
    mismatches = []
    if canonical.is_dir() and canonical.resolve() != path.resolve():
        protected = [canonical / "README.md", canonical / "bench.py", canonical / "golden.txt", *canonical.glob("test_*.py")]
        mismatches = [x.name for x in protected if not (path / x.name).is_file() or (path / x.name).read_bytes() != x.read_bytes()]
    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py"],
        cwd=path, capture_output=True, text=True, timeout=60, check=False,
    )
    main_py = path / "main.py"
    golden = canonical / "golden.txt" if (canonical / "golden.txt").is_file() else path / "golden.txt"
    if not main_py.is_file() or not golden.is_file():
        return gate("fail", "fixture requires main.py and authoritative golden.txt"), {"tests_returncode": tests.returncode}
    output = subprocess.run([sys.executable, "main.py", "--golden"], cwd=path,
                            capture_output=True, timeout=30, check=False)
    expected = golden.read_bytes()
    expected_hash = hashlib.sha256(expected).hexdigest()
    output_hash = hashlib.sha256(output.stdout).hexdigest()
    matches = output.returncode == 0 and output.stdout == expected
    passed = tests.returncode == 0 and matches and not mismatches
    evidence = (f"tests={'pass' if tests.returncode == 0 else 'fail'}; "
                f"golden={'match' if matches else 'mismatch'}; "
                f"contract={'intact' if not mismatches else 'modified'}; sha256={output_hash[:12]}")
    detail = {"tests_returncode": tests.returncode, "tests_stdout": tests.stdout[-2000:],
              "tests_stderr": tests.stderr[-2000:], "golden_expected_sha256": expected_hash,
              "golden_output_sha256": output_hash, "golden_command_returncode": output.returncode,
              "protected_mismatches": mismatches, "authoritative_fixture": str(canonical if canonical.is_dir() else path)}
    return gate("pass" if passed else "fail", evidence), detail


def benchmark(trace: dict[str, Any], key: str, trace_path: Path | None) -> tuple[dict[str, Any] | None, str | None]:
    group = trace.get("benchmarks")
    value = group.get(key) if isinstance(group, dict) else trace.get(f"{key}_bench")
    if isinstance(value, dict):
        return value, None
    if isinstance(value, str):
        path = Path(value)
        if not path.is_absolute() and trace_path:
            path = trace_path.parent / path
        data, error = read_json(path)
        return (data if not error else None), error
    return None, f"no {key} benchmark in trace"


def numeric(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def performance(before: dict[str, Any] | None, after: dict[str, Any] | None) -> tuple[dict[str, str], dict[str, str], dict[str, float]]:
    if before is None or after is None:
        reason = "before/after benchmark JSON not both present"
        return gate("skip", reason), gate("skip", reason), {}
    b50, a50 = numeric(before.get("p50_ms")), numeric(after.get("p50_ms"))
    b95, a95 = numeric(before.get("p95_ms")), numeric(after.get("p95_ms"))
    if b50 is None or a50 is None or min(b50, a50) <= 0:
        reason = "benchmarks require positive numeric p50_ms"
        return gate("skip", reason), gate("skip", reason), {}
    speedup = b50 / a50
    improvement = (1 - a50 / b50) * 100
    values = {"V1": b50, "V2": a50, "V3": speedup, "V4": improvement}
    p50_gate = gate("pass" if improvement >= 20 else "fail",
                    f"p50 {b50:.3f}→{a50:.3f} ms ({improvement:.2f}% improvement)")
    if b95 is None or a95 is None or min(b95, a95) <= 0:
        return p50_gate, gate("skip", "p95_ms missing from one or both benchmarks"), values
    values["V5"] = b95 / a95
    change = (a95 / b95 - 1) * 100
    p95_gate = gate("pass" if change <= 5 else "fail",
                    f"p95 {b95:.3f}→{a95:.3f} ms ({change:+.2f}% change; +5% allowed)")
    return p50_gate, p95_gate, values


def g9(pack: Path, lint: dict[str, Any]) -> dict[str, str]:
    if not pack.exists():
        return gate("skip", "pack directory does not exist")
    counts = lint.get("line_counts", {})
    if not counts:
        return gate("fail", "no SKILL.md files found")
    missing = sorted(set(REQUIRED_SKILLS) - set(counts))
    over = {name: count for name, count in counts.items() if count >= 500}
    if missing or over:
        return gate("fail", f"missing={missing}; over_limit={over}")
    return gate("pass", "; ".join(f"{k}={v}" for k, v in sorted(counts.items())))


def emit(result: dict[str, Any], out_path: str | None) -> None:
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if out_path:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


def main() -> int:
    parser = argparse.ArgumentParser(description="Grade an Extreme EZ Bake skill pack and optimized fixture.")
    parser.add_argument("--pack", required=True, help="Pack directory; missing and empty packs do not crash.")
    parser.add_argument("--trace", help="Optional solver trace JSON matching schema.py.")
    parser.add_argument("--fixture", help="Fixture or isolated optimized workspace to test.")
    parser.add_argument("--out", help="Write the emitted JSON to this path.")
    parser.add_argument("--solver", help="Solver label when absent from the trace.")
    parser.add_argument("--run-id", help="Run identifier when absent from the trace.")
    parser.add_argument("--lint-only", action="store_true", help="Run static pack lint only.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when lint or a measured gate fails.")
    args = parser.parse_args()

    pack = Path(args.pack).resolve()
    lint = lint_pack(pack)
    if args.lint_only:
        emit({"pack": str(pack), "lint": lint}, args.out)
        return int(args.strict and not lint["ok"])

    trace_path = Path(args.trace).resolve() if args.trace else None
    trace, trace_evidence = load_trace(trace_path)
    fixture_path = Path(args.fixture).resolve() if args.fixture else None
    name = fixture_name(fixture_path, trace)
    tool_events = events(trace)
    g4_result, correctness_detail = correctness(fixture_path, name)
    before, before_error = benchmark(trace, "before", trace_path)
    after, after_error = benchmark(trace, "after", trace_path)
    g5_result, g6_result, values = performance(before, after)
    activation = activation_check(lint.get("descriptions", {}), Path(__file__).resolve().parents[1] / "prompts" / "activation.json")
    solver = args.solver or trace.get("solver") or "unknown"
    run_id = args.run_id or trace.get("run_id") or (Path(args.out).stem if args.out else f"{solver}-{name}")
    gates = {
        "G1": g1(tool_events), "G2": g2(trace, name, tool_events), "G3": g3(tool_events),
        "G4": g4_result, "G5": g5_result, "G6": g6_result, "G7": g7(tool_events),
        "G8": activation["gate"], "G9": g9(pack, lint), "G10": g10(tool_events),
    }
    result = {
        "pack": str(pack), "solver": str(solver), "fixture": name, "run_id": str(run_id),
        "gates": gates, "values": values, "skill_lift": None, "lint": lint,
        "activation_cases": activation["cases"], "correctness": correctness_detail,
        "trace": {"evidence": trace_evidence, "before_error": before_error,
                  "after_error": after_error, "event_count": len(tool_events)},
    }
    emit(result, args.out)
    measured_failure = any(item["status"] == "fail" for item in gates.values())
    return int(args.strict and (measured_failure or not lint["ok"]))


if __name__ == "__main__":
    raise SystemExit(main())
