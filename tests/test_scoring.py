import json
import math
import unittest

from scoring import LABELS, align, parse_output, score


def output(label="valid_conclusion", valid=True, confidence=0.8):
    return dict(valid=valid, failure_type=label, confidence=confidence,
                explanation="Test evidence.")


def case(i, label):
    return dict(id=str(i), category=label,
                target=output(label, label == "valid_conclusion"))


def record(c, obj=None, raw=None):
    return dict(id=c["id"], gold_category=c["category"],
                gold_valid=c["target"]["valid"],
                raw_output=raw if raw is not None else json.dumps(obj))


class ParserTests(unittest.TestCase):
    def test_fence_is_diagnostic_only(self):
        raw = json.dumps(output())
        plain = parse_output(raw)
        fenced = parse_output("```json\n" + raw + "\n```")
        self.assertTrue(plain["strict_valid"])
        self.assertFalse(fenced["json_object_valid"])
        self.assertFalse(fenced["schema_valid"])
        self.assertEqual(fenced["recovered"], output())

    def test_schema_and_pairing_are_distinct(self):
        parsed = parse_output(json.dumps(output("data_leakage", True)))
        self.assertTrue(parsed["json_object_valid"])
        self.assertTrue(parsed["schema_valid"])
        self.assertFalse(parsed["strict_valid"])
        self.assertFalse(parsed["pair_consistent"])

    def test_no_prose_or_multiple_objects_recovery(self):
        for raw in ["Answer: " + json.dumps(output()), "{}{}", "[]", "null", ""]:
            with self.subTest(raw=raw):
                self.assertFalse(parse_output(raw)["strict_valid"])
                self.assertIsNone(parse_output(raw)["recovered"])

    def test_rejects_missing_extra_wrong_type_range_and_unknown_label(self):
        variants = [dict(output(), valid="true"), dict(output(), confidence=True),
                    dict(output(), confidence=1.1), dict(output(), confidence=-0.1),
                    dict(output(), confidence="0.8"), dict(output(), explanation=" "),
                    dict(output(), failure_type="unknown"), dict(output(), extra=1)]
        missing = output(); del missing["explanation"]; variants.append(missing)
        for obj in variants:
            with self.subTest(obj=obj):
                self.assertIsNone(parse_output(json.dumps(obj))["recovered"])

    def test_duplicate_keys_and_nonfinite_are_rejected(self):
        for raw in [json.dumps(output()).replace('"valid": true', '"valid": false,"valid": true'),
                    json.dumps(output(confidence=float("nan"))),
                    json.dumps(output(confidence=float("inf"))),
                    json.dumps(output(confidence=10**1000)),
                    json.dumps(output()).replace('0.8', '1e999')]:
            with self.subTest(raw=raw):
                self.assertIsNone(parse_output(raw)["recovered"])


class AlignmentTests(unittest.TestCase):
    def setUp(self):
        self.cases = [case(0, "valid_conclusion"), case(1, "data_leakage")]
        self.rows = [record(c, c["target"]) for c in self.cases]

    def test_complete_aligned_records(self):
        self.assertEqual(len(align(self.cases, self.rows)), 2)

    def test_rejects_empty_missing_extra_duplicate_and_shuffled(self):
        for rows in [[], self.rows[:1], self.rows + self.rows[:1],
                     [self.rows[0], self.rows[0]], list(reversed(self.rows))]:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                align(self.cases, rows)
        with self.assertRaises(ValueError):
            align([], [])

    def test_rejects_gold_mismatch_and_raw_wrong_type(self):
        for changes in [dict(gold_valid=False), dict(gold_category="confounding"),
                        dict(raw_output=None)]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                align(self.cases, [dict(self.rows[0], **changes), self.rows[1]])

    def test_rejects_invalid_ground_truth(self):
        self.cases[0]["target"]["valid"] = False
        with self.assertRaises(ValueError):
            align(self.cases, self.rows)

    def test_cached_parse_is_checked_not_used_for_scoring(self):
        rows = [dict(r, strict_valid=True, prediction=c["target"], parse_error=None)
                for c, r in zip(self.cases, self.rows)]
        rows[0]["prediction"] = output("confounding", False)
        with self.assertRaisesRegex(ValueError, "cached"):
            align(self.cases, rows)

    def test_cached_prediction_types_cannot_equal_valid_json_by_coercion(self):
        rows = [dict(r, strict_valid=True, prediction=dict(c["target"]), parse_error=None)
                for c, r in zip(self.cases, self.rows)]
        rows[0]["prediction"]["valid"] = 1
        with self.assertRaisesRegex(ValueError, "cached"):
            align(self.cases, rows)

    def test_invalid_cached_parse_error_must_be_nonblank_text(self):
        c = self.cases[0]
        for error in ({"nonsense": 1}, True, " ", None):
            row = dict(record(c, raw="broken"), strict_valid=False, prediction=None, parse_error=error)
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, "cached"):
                align([c], [row])


class MetricTests(unittest.TestCase):
    def test_hand_computed_metrics_all_ten_classes(self):
        cases = [case(i, label) for i, label in enumerate(LABELS)]
        rows = [record(c, c["target"]) for c in cases]
        rows[0] = record(cases[0], output(LABELS[1], False))
        rows[2] = record(cases[2], raw="not json")
        m = score(cases, rows)
        self.assertEqual(m["overall_accuracy"], 0.8)
        self.assertAlmostEqual(m["macro_f1"], 0.7666666666666667)
        self.assertEqual(m["structured_output_validity"], 0.9)
        self.assertAlmostEqual(m["ece_10"], abs(8/9 - 0.8))
        self.assertAlmostEqual(m["brier_score"], (8*0.04+0.64)/9)
        self.assertEqual(m["per_category_accuracy"][LABELS[2]], 0)

    def test_malformed_predictions_stay_in_denominator(self):
        cases = [case(0, "valid_conclusion"), case(1, "data_leakage")]
        rows = [record(cases[0], output()), record(cases[1], raw="broken")]
        m = score(cases, rows)
        self.assertEqual(m["diagnostic_category_accuracy"], 0.5)
        self.assertEqual(m["calibration_coverage"], 0.5)
        self.assertEqual(m["confusion_matrix"]["data_leakage"], {"__invalid__": 1})

    def test_all_invalid_outputs_calibration_is_unavailable(self):
        c = case(0, "data_leakage")
        m = score([c], [record(c, raw="broken")])
        self.assertIsNone(m["ece_10"])
        self.assertIsNone(m["brier_score"])

    def test_boundary_confidence_one_enters_last_bin(self):
        c = case(0, "data_leakage")
        m = score([c], [record(c, output("confounding", False, 1.0))])
        self.assertEqual(m["ece_10"], 1)
        self.assertEqual(m["brier_score"], 1)


if __name__ == "__main__":
    unittest.main()
