"""Pure-Python scoring of saved outputs; no inference, training or network."""
import json
import math
import re
from collections import Counter

LABELS = (
    "insufficient_sample_size", "statistically_insignificant", "simpsons_paradox",
    "selection_bias", "confounding", "metric_mismatch", "data_leakage",
    "correlation_vs_causation", "experiment_contamination", "valid_conclusion",
)
KEYS = {"valid", "failure_type", "confidence", "explanation"}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("non-finite JSON constant")


def load_json(text):
    """Reject ambiguous duplicate keys and non-standard NaN/Infinity literals."""
    return json.loads(text, object_pairs_hook=_unique_object,
                      parse_constant=_reject_constant)


def _schema_valid(obj):
    return (
        type(obj) is dict and set(obj) == KEYS
        and type(obj["valid"]) is bool
        and type(obj["failure_type"]) is str and obj["failure_type"] in LABELS
        and type(obj["confidence"]) in (int, float)
        and 0 <= obj["confidence"] <= 1 and math.isfinite(obj["confidence"])
        and type(obj["explanation"]) is str and bool(obj["explanation"].strip())
    )


def parse_output(raw):
    """Separate JSON syntax/schema from validity/category consistency."""
    text = raw.strip()
    try:
        plain = load_json(text)
    except ValueError:
        plain = None
    bare_object = type(plain) is dict
    schema = _schema_valid(plain)
    recovered = plain if schema else None
    fenced = re.fullmatch(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            candidate = load_json(fenced.group(1))
            recovered = candidate if _schema_valid(candidate) else None
        except ValueError:
            pass
    pair = (recovered["valid"] == (recovered["failure_type"] == "valid_conclusion")
            if recovered is not None else False)
    return dict(json_object_valid=bare_object, schema_valid=schema,
                pair_consistent=pair, strict_valid=bool(schema and pair),
                recovered=recovered, fenced=bool(fenced))


def align(benchmark, records):
    """Fail closed on incomplete, relabelled, reordered or stale cached records."""
    if not benchmark or len(benchmark) != len(records):
        raise ValueError("non-empty benchmark and equal prediction counts required")
    ids = set()
    parsed = []
    for case, row in zip(benchmark, records):
        if type(case) is not dict or type(row) is not dict:
            raise ValueError("case and prediction must be objects")
        identifier = case.get("id")
        target = case.get("target")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError("invalid or duplicate benchmark id")
        ids.add(identifier)
        if not _schema_valid(target) or case.get("category") != target["failure_type"]:
            raise ValueError("invalid benchmark category/target")
        if target["valid"] != (case["category"] == "valid_conclusion"):
            raise ValueError("contradictory benchmark target")
        if row.get("id") != identifier:
            raise ValueError("prediction IDs must match benchmark order exactly")
        if (row.get("gold_category") != case["category"]
                or type(row.get("gold_valid")) is not bool
                or row["gold_valid"] != target["valid"]):
            raise ValueError("prediction gold fields disagree with benchmark")
        if type(row.get("raw_output")) is not str:
            raise ValueError("raw_output must be a string")
        result = parse_output(row["raw_output"])
        cache_keys = {"strict_valid", "prediction", "parse_error"}
        if cache_keys & row.keys():
            if not cache_keys <= row.keys():
                raise ValueError("incomplete cached parse fields")
            expected = result["recovered"] if result["strict_valid"] else None
            if (type(row["strict_valid"]) is not bool
                    or row["strict_valid"] != result["strict_valid"]
                    or (expected is not None and not _schema_valid(row["prediction"]))
                    or row["prediction"] != expected
                    or (result["strict_valid"] and row["parse_error"] is not None)
                    or (not result["strict_valid"]
                        and (type(row["parse_error"]) is not str or not row["parse_error"].strip()))):
                raise ValueError("cached parse disagrees with freshly parsed raw_output")
        parsed.append(result)
    return parsed


def score(benchmark, records):
    parsed = align(benchmark, records)
    n = len(benchmark)
    confusion = {label: Counter() for label in LABELS}
    support = Counter(c["category"] for c in benchmark)
    correct = Counter()
    strict_correct = strict_count = validity_correct = 0
    recovered_count = recovered_category = recovered_joint = recovered_validity = 0
    distribution = Counter()
    calibrations = []
    for c, p in zip(benchmark, parsed):
        gold = c["category"]
        obj = p["recovered"]
        prediction = obj["failure_type"] if p["strict_valid"] else "__invalid__"
        confusion[gold][prediction] += 1
        exact = bool(p["strict_valid"] and prediction == gold)
        strict_correct += exact
        correct[gold] += exact
        strict_count += p["strict_valid"]
        if p["strict_valid"]:
            validity_correct += obj["valid"] == c["target"]["valid"]
            calibrations.append((obj["confidence"], int(exact)))
        if obj is not None:
            recovered_count += 1
            cat_ok = obj["failure_type"] == gold
            valid_ok = obj["valid"] == c["target"]["valid"]
            recovered_category += cat_ok
            recovered_validity += valid_ok
            recovered_joint += cat_ok and valid_ok
            distribution[obj["failure_type"]] += 1
        else:
            distribution["__invalid__"] += 1
    f1 = []
    for label in LABELS:
        tp = confusion[label][label]
        fp = sum(row[label] for gold, row in confusion.items() if gold != label)
        fn = support[label] - tp
        f1.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0)
    ece = brier = None
    if calibrations:
        bins = [[] for _ in range(10)]
        for confidence, outcome in calibrations:
            bins[min(int(confidence*10), 9)].append((confidence, outcome))
        ece = sum(abs(sum(y-c for c, y in bucket))/len(calibrations)
                  for bucket in bins if bucket)
        brier = sum((c-y)**2 for c, y in calibrations)/len(calibrations)
    return {
        "count": n, "correct": strict_correct,
        "overall_accuracy": strict_correct/n,
        "macro_f1": sum(f1)/len(LABELS),
        "per_category_accuracy": {label: correct[label]/support[label]
                                  if support[label] else 0.0 for label in LABELS},
        "per_category_support": {label: support[label] for label in LABELS},
        "structured_output_validity": strict_count/n,
        "validity_accuracy": validity_correct/n,
        "json_object_validity": sum(p["json_object_valid"] for p in parsed)/n,
        "json_schema_compliance": sum(p["schema_valid"] for p in parsed)/n,
        "diagnostic_recoverable_json": recovered_count/n,
        "diagnostic_category_accuracy": recovered_category/n,
        "diagnostic_validity_accuracy": recovered_validity/n,
        "diagnostic_joint_accuracy": recovered_joint/n,
        "calibration_coverage": len(calibrations)/n,
        "ece_10": ece, "brier_score": brier,
        "confusion_matrix": {label: dict(sorted(row.items()))
                             for label, row in confusion.items()},
        "recovered_prediction_distribution": dict(sorted(distribution.items())),
        "invalid_gold_prior": sum(not c["target"]["valid"] for c in benchmark)/n,
        "recovered_pair_contradictions": sum(p["recovered"] is not None
                                              and not p["pair_consistent"] for p in parsed),
        "confidence_one_count": sum(p["recovered"] is not None
                                    and p["recovered"]["confidence"] == 1 for p in parsed),
    }
