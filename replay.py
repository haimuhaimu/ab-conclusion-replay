"""Audit and replay a fixed experiment's saved predictions using only stdlib."""
import argparse
import hashlib
import json
import math
import random
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from scoring import LABELS, align, load_json, score

ROOT = Path(__file__).resolve().parent
VERSION = "abjudge-replay-1"
FILES = frozenset({"benchmark.jsonl", "base.predictions.jsonl", "lora.predictions.jsonl",
                   "historical_base.metrics.json", "historical_lora.metrics.json",
                   "experiment.json"})
HISTORICAL_FIELDS = frozenset({
    "count", "correct", "overall_accuracy", "macro_f1", "per_category_accuracy",
    "per_category_support", "structured_output_validity", "validity_accuracy",
    "diagnostic_recoverable_json", "diagnostic_category_accuracy",
    "diagnostic_validity_accuracy", "diagnostic_joint_accuracy", "calibration_coverage",
    "ece_10", "brier_score", "confusion_matrix", "overall_accuracy_ci95",
})


def encode(value):
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)+"\n"


def _read(path):
    if path.is_symlink():
        raise ValueError(f"symlink evidence is forbidden: {path.name}")
    if not path.is_file():
        raise ValueError(f"missing evidence file: {path.name}")
    return path.read_bytes()


def _json(blob, name):
    try:
        return load_json(blob.decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f"invalid JSON in {name}: {exc}") from exc


def _rows(blob, name):
    rows = []
    for line, text in enumerate(blob.splitlines(), 1):
        row = _json(text, f"{name}:{line}")
        if type(row) is not dict:
            raise ValueError(f"{name}:{line} must be a JSON object")
        rows.append(row)
    return rows


def _lineage(experiment, manifest):
    """Internal consistency, not authentication: a manifest is not a signature."""
    def require(condition):
        if not condition:
            raise ValueError("lineage mismatch")

    try:
        base, lora, training = (experiment[k] for k in ("base", "lora", "training"))
        require(experiment["version"] == VERSION)
        require(base["stage"] == "base" and lora["stage"] == "adapter")
        require(base["training_run"] is None and lora["training_run"] == training["run_id"])
        for key in ("model_id", "model_revision"):
            require(base[key] == lora[key] == training[key])
        require(base["seed"] == lora["seed"] == training["resolved_config"]["seed"])
        require(base["generation_config"] == lora["generation_config"])
        benchmark_hash = manifest["files"]["benchmark.jsonl"]["sha256"]
        require(base["dataset_sha256"] == lora["dataset_sha256"] == training["benchmark_sha256"] == benchmark_hash)
        require(base["prediction_count"] == lora["prediction_count"] == manifest["rows"])
        require(all(run["status"] == "completed" for run in (base, lora, training)))
        times = [datetime.fromisoformat(run[key]) for run in (base, training, lora)
                 for key in ("started_at", "completed_at")]
        require(all(t.tzinfo is not None for t in times))
        require(all(a < b for a, b in zip(times, times[1:])))
        sources = experiment["sources"]
        require(set(sources) == FILES - {"experiment.json"})
        for name, source in sources.items():
            require(source["sha256"] == manifest["files"][name]["sha256"])
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ValueError("experiment lineage/provenance mismatch") from exc


def load_bundle(directory):
    directory = Path(directory)
    if directory.is_symlink():
        raise ValueError("symlink evidence directory is forbidden")
    manifest = _json(_read(directory/"manifest.json"), "manifest.json")
    if (type(manifest) is not dict or set(manifest) != {"bundle_version", "rows", "files"}
            or manifest["bundle_version"] != VERSION or type(manifest["rows"]) is not int
            or manifest["rows"] != 120 or type(manifest["files"]) is not dict
            or set(manifest["files"]) != FILES):
        raise ValueError("manifest schema/allowlist mismatch")
    blobs = {}
    for name in sorted(FILES):
        spec = manifest["files"][name]
        if (type(spec) is not dict or set(spec) != {"bytes", "sha256"}
                or type(spec["bytes"]) is not int or spec["bytes"] < 0
                or type(spec["sha256"]) is not str or len(spec["sha256"]) != 64):
            raise ValueError(f"manifest entry malformed: {name}")
        blob = _read(directory/name)
        if hashlib.sha256(blob).hexdigest() != spec["sha256"]:
            raise ValueError(f"hash mismatch: {name}")
        if len(blob) != spec["bytes"]:
            raise ValueError(f"byte count mismatch: {name}")
        blobs[name] = blob
    # Parse only after every declared file is present and hashed.
    bundle = {name: (_rows(blob, name) if name.endswith(".jsonl") else _json(blob, name))
              for name, blob in blobs.items()}
    _lineage(bundle["experiment.json"], manifest)
    benchmark = bundle["benchmark.jsonl"]
    if (len(benchmark) != manifest["rows"]
            or not all(type(row.get("category")) is str for row in benchmark)
            or Counter(row.get("category") for row in benchmark) != Counter({label: 12 for label in LABELS})):
        raise ValueError("benchmark count or category balance mismatch")
    for row in benchmark:
        scenario = row.get("scenario")
        fields = {"background", "metric_results", "segment_results", "conclusion"}
        if (row.get("split") != "benchmark" or type(scenario) is not dict
                or set(scenario) != fields
                or not all(type(v) is str and v.strip() for v in scenario.values())):
            raise ValueError("benchmark scenario/split malformed")
    for name in ("historical_base.metrics.json", "historical_lora.metrics.json"):
        if type(bundle[name]) is not dict or set(bundle[name]) != HISTORICAL_FIELDS:
            raise ValueError(f"historical metric schema incomplete or unexpected: {name}")
    bundle["manifest"] = manifest
    return bundle


def verify_historical(actual, historical, path="historical", allow_extra=True):
    """Every historical field must match; additional replay diagnostics are allowed."""
    if type(historical) is dict:
        if type(actual) is not dict:
            raise ValueError(f"{path}: object mismatch")
        if not allow_extra and set(actual) != set(historical):
            raise ValueError(f"{path}: incomplete or unexpected object fields")
        for key, expected in historical.items():
            if key not in actual:
                raise ValueError(f"{path}.{key}: missing recomputed value")
            verify_historical(actual[key], expected, f"{path}.{key}", allow_extra=False)
    elif type(historical) is list:
        if type(actual) is not list or len(actual) != len(historical):
            raise ValueError(f"{path}: list mismatch")
        for i, (a, b) in enumerate(zip(actual, historical)):
            verify_historical(a, b, f"{path}[{i}]", allow_extra=False)
    elif type(historical) in (int, float):
        if type(actual) not in (int, float) or not math.isclose(actual, historical, rel_tol=0, abs_tol=1e-12):
            raise ValueError(f"{path}: numeric mismatch ({actual!r} != {historical!r})")
    elif type(actual) is not type(historical) or actual != historical:
        raise ValueError(f"{path}: value mismatch")


def _bootstrap(benchmark, parsed):
    # Historical row-IID procedure, seed=42, 2,000 draws, floor-index quantiles.
    # Reproduced for parity only; shared templates violate independent-row intuition.
    correct = [int(p["strict_valid"] and p["recovered"]["failure_type"] == c["category"])
               for c, p in zip(benchmark, parsed)]
    rng = random.Random(42)
    estimates = sorted(sum(rng.choice(correct) for _ in correct)/len(correct) for _ in range(2000))
    return [estimates[int(0.025*1999)], estimates[int(0.975*1999)]]


def _markdown(metrics):
    base, lora = metrics["base"], metrics["lora"]
    lines = ["# Saved-prediction replay: Base → 100-row LoRA smoke", "",
             "Offline metric recomputation only. No model inference, training, or new capability claim.", "",
             "| Metric (denominator: 120 unless noted) | Base | LoRA | Delta (pp) |",
             "|---|---:|---:|---:|"]
    rows = [("Strict exact accuracy", "overall_accuracy"),
            ("Plain JSON object", "json_object_validity"),
            ("Plain JSON schema compliance", "json_schema_compliance"),
            ("Strict contract (schema + valid/category consistency)", "structured_output_validity"),
            ("Recovered category accuracy (diagnostic)", "diagnostic_category_accuracy"),
            ("Recovered joint accuracy (diagnostic)", "diagnostic_joint_accuracy"),
            ("Strict boolean accuracy", "validity_accuracy"),
            ("Recovered boolean accuracy (diagnostic)", "diagnostic_validity_accuracy")]
    for title, key in rows:
        lines.append(f"| {title} | {100*base[key]:.1f}% | {100*lora[key]:.1f}% | {100*(lora[key]-base[key]):+.1f} |")
    lines += ["", f"Macro F1: {base['macro_f1']:.4f} → {lora['macro_f1']:.4f} (fixed ten labels; malformed predictions count as errors).",
              "", "All historical scalar, per-category, confusion-matrix and bootstrap fields match (absolute tolerance 1e-12).",
              "The preserved historical name `structured_output_validity` includes semantic field consistency, not just JSON syntax.",
              "All 120 Base answers are fenced. LoRA has 120 schema-compliant objects, but two contradictory valid/category pairs.",
              "", "## Per-category strict accuracy", "",
              "| Gold category | Support | Base | LoRA | LoRA errors |", "|---|---:|---:|---:|---:|"]
    for label in LABELS:
        n = base["per_category_support"][label]
        acc = lora["per_category_accuracy"][label]
        lines.append(f"| {label} | {n} | {100*base['per_category_accuracy'][label]:.1f}% | {100*acc:.1f}% | {round(n*(1-acc))} |")
    lines += ["", "## Interpretation and limits", "",
              "- Strict accuracy rises 0/120 → 22/120; recovered category recognition falls 24/120 → 22/120 (-1.7 pp). This is primarily evidence of output-contract learning, not general reasoning improvement.",
              "- LoRA emits data_leakage 68/120 times and valid_conclusion zero times. It says valid=false 118 times; the two valid=true outputs contradict their failure labels. Never literally describe this as always-false.",
              "- The invalid gold prior is 108/120 = 90%. Strict boolean accuracy equals that prior; recovered boolean accuracy is 110/120 = 91.7%. Neither is an adequate ten-way capability metric.",
              "- LoRA confidence is 1.0 in every recovered answer. ECE/Brier are both 0.813559 over 118 strict-valid answers; Base calibration is unavailable under strict parsing. Coverage differs, so these are not a clean calibration comparison.",
              "- Every training target also used confidence=1.0, despite defining confidence as correctness probability. That supervision is flawed; calibration cannot be claimed.",
              "- Train and benchmark reuse category builder functions. Split-prefixed template-family names and different seeds do not establish template isolation. Exact-hash alignment prevents accidental file mixing, not semantic leakage.",
              "- Numeric rates, p-values and intervals were not all derived from common raw observations. Generator-provided labels are not an expert-reviewed statistical gold standard. Category ambiguity remains.",
              "- One 100-row training run, one seed, one synthetic benchmark: no stable improvement or generalization claim. Historical row-IID bootstrap intervals are reproduced only for parity and may understate uncertainty with shared templates.",
              "- Explanations are preserved for inspection, not graded for factual correctness by this evaluator. No v2 training was performed in this replay.",
              "", "See [METHOD.md](../METHOD.md) for scoring definitions and [NEXT_EXPERIMENT.md](../NEXT_EXPERIMENT.md) for hypotheses, data design and pre-registered checks.", ""]
    return "\n".join(lines)


def build_reports(bundle):
    benchmark = bundle["benchmark.jsonl"]
    metrics = {"replay_version": VERSION, "input_manifest": bundle["manifest"],
               "historical_metrics_match": True,
               "bootstrap_method": "historical row-IID, seed 42, 2000 samples; parity only"}
    badcases = []
    for name in ("base", "lora"):
        records = bundle[name+".predictions.jsonl"]
        parsed = align(benchmark, records)
        result = score(benchmark, records)
        result["overall_accuracy_ci95"] = _bootstrap(benchmark, parsed)
        verify_historical(result, bundle["historical_"+name+".metrics.json"])
        metrics[name] = result
        for case, row, p in zip(benchmark, records, parsed):
            if p["strict_valid"] and p["recovered"]["failure_type"] == case["category"]:
                continue
            badcases.append(dict(run=name, id=case["id"], gold=case["target"],
                                 scenario=case["scenario"], raw_output=row["raw_output"],
                                 parsed=p, error_kind="category" if p["strict_valid"] else "output_contract"))
    return {"metrics.json": encode(metrics), "comparison.md": _markdown(metrics),
            "badcases.jsonl": "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False)+"\n" for row in badcases)}


def example(bundle, identifier):
    benchmark = bundle["benchmark.jsonl"]
    index = next((i for i, c in enumerate(benchmark) if c["id"] == identifier), None)
    if index is None:
        raise ValueError(f"unknown example ID: {identifier}")
    case = benchmark[index]
    result = dict(id=identifier, scenario=case["scenario"], gold=case["target"])
    for name in ("base", "lora"):
        rows = bundle[name+".predictions.jsonl"]
        parsed = align(benchmark, rows)
        result[name] = dict(raw_output=rows[index]["raw_output"], parsed=parsed[index])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=ROOT/"evidence")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--output", type=Path, help="new output directory; never overwrites")
    action.add_argument("--check", type=Path, help="compare every report byte with existing outputs")
    action.add_argument("--example", help="print both raw answers for an exact benchmark ID")
    args = parser.parse_args(argv)
    try:
        bundle = load_bundle(args.evidence)
        reports = build_reports(bundle)  # Full audit before writing or showing an example.
        if args.example is not None:
            print(encode(example(bundle, args.example)), end="")
        elif args.check is not None:
            for name, text in reports.items():
                if _read(args.check/name) != text.encode("utf-8"):
                    raise ValueError(f"recomputed report differs: {name}")
            print("PASS: all report bytes match; historical metrics match.")
        else:
            destination = args.output
            if destination.exists() or destination.is_symlink():
                raise ValueError("output directory already exists; choose a new path")
            if destination.resolve().is_relative_to(args.evidence.resolve()):
                raise ValueError("output must not be inside the evidence directory")
            destination.mkdir(parents=True, exist_ok=False)
            for name, text in reports.items():
                with (destination/name).open("x", encoding="utf-8", newline="\n") as stream:
                    stream.write(text)
            print("PASS: wrote metrics.json, comparison.md and badcases.jsonl; historical metrics match.")
    except (ValueError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
