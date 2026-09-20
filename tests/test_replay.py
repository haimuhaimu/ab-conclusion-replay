import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from replay import build_reports, load_bundle, verify_historical
from scoring import align

ROOT = Path(__file__).resolve().parents[1]


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.evidence = Path(self.temp.name)/"evidence"
        shutil.copytree(ROOT/"evidence", self.evidence)

    def _rehash(self, name):
        path = self.evidence/"manifest.json"
        m = json.loads(path.read_text())
        m["files"][name]["sha256"] = hashlib.sha256((self.evidence/name).read_bytes()).hexdigest()
        m["files"][name]["bytes"] = (self.evidence/name).stat().st_size
        path.write_text(json.dumps(m))

    def _update_source_hash(self, name):
        path = self.evidence/"experiment.json"
        experiment = json.loads(path.read_text())
        digest = hashlib.sha256((self.evidence/name).read_bytes()).hexdigest()
        experiment["sources"][name]["sha256"] = digest
        path.write_text(json.dumps(experiment))
        self._rehash("experiment.json")

    def test_real_history_matches_recomputed_values(self):
        b = load_bundle(self.evidence)
        reports = build_reports(b)
        result = json.loads(reports["metrics.json"])
        self.assertEqual(result["base"]["overall_accuracy"], 0)
        self.assertEqual(result["lora"]["correct"], 22)
        self.assertAlmostEqual(result["lora"]["macro_f1"], 0.14191176470588235)
        self.assertAlmostEqual(result["lora"]["structured_output_validity"], 118/120)
        self.assertEqual(result["lora"]["json_schema_compliance"], 1)
        self.assertEqual(result["lora"]["recovered_prediction_distribution"]["data_leakage"], 68)
        self.assertTrue(result["historical_metrics_match"])

    def test_missing_hash_mismatch_and_wrong_manifest_schema_fail(self):
        (self.evidence/"base.predictions.jsonl").write_text("{}\n")
        with self.assertRaisesRegex(ValueError, "hash"):
            load_bundle(self.evidence)
        (self.evidence/"base.predictions.jsonl").unlink()
        with self.assertRaises(ValueError):
            load_bundle(self.evidence)
        (self.evidence/"manifest.json").write_text("[]")
        with self.assertRaises(ValueError):
            load_bundle(self.evidence)

    def test_manifest_cannot_omit_or_escape_expected_files(self):
        p = self.evidence/"manifest.json"; m = json.loads(p.read_text())
        del m["files"]["benchmark.jsonl"]
        m["files"]["../private-note"] = {"sha256": "0"*64}
        p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError, "allowlist"):
            load_bundle(self.evidence)

    def test_symlink_cannot_stand_in_for_evidence(self):
        p = self.evidence/"base.predictions.jsonl"
        original = p.read_bytes(); p.unlink()
        external = Path(self.temp.name)/"external"; external.write_bytes(original)
        p.symlink_to(external)
        with self.assertRaisesRegex(ValueError, "symlink"):
            load_bundle(self.evidence)

    def test_rehashed_reordering_and_relabeled_gold_are_still_rejected(self):
        p = self.evidence/"base.predictions.jsonl"
        rows = p.read_text().splitlines()
        rows[0], rows[1] = rows[1], rows[0]
        p.write_text("\n".join(rows)+"\n"); self._rehash(p.name)
        self._update_source_hash(p.name)
        with self.assertRaisesRegex(ValueError, "order"):
            build_reports(load_bundle(self.evidence))

    def test_lineage_mismatch_is_rejected_even_with_new_hash(self):
        p = self.evidence/"experiment.json"; m = json.loads(p.read_text())
        m["lora"]["model_revision"] = "other"
        p.write_text(json.dumps(m)); self._rehash(p.name)
        with self.assertRaisesRegex(ValueError, "lineage"):
            load_bundle(self.evidence)

    def test_reports_repeat_byte_for_byte_and_do_not_omit_errors(self):
        b = load_bundle(self.evidence)
        first = build_reports(b); second = build_reports(b)
        self.assertEqual(first, second)
        badcases = [json.loads(l) for l in first["badcases.jsonl"].splitlines()]
        self.assertEqual(len(badcases), 218)
        self.assertTrue(all("scenario" in r and "raw_output" in r for r in badcases))
        self.assertIn("-1.7", first["comparison.md"])

    def test_different_historical_score_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "historical"):
            verify_historical({"overall_accuracy": 0.1}, {"overall_accuracy": 0.2})

    def test_empty_historical_metrics_cannot_vacuously_pass_parity(self):
        name = "historical_base.metrics.json"
        (self.evidence/name).write_text("{}")
        self._rehash(name); self._update_source_hash(name)
        with self.assertRaisesRegex(ValueError, "historical"):
            build_reports(load_bundle(self.evidence))

    def test_partial_historical_category_vector_cannot_pass_parity(self):
        name = "historical_base.metrics.json"
        p = self.evidence/name; m = json.loads(p.read_text())
        del m["per_category_accuracy"]["selection_bias"]
        p.write_text(json.dumps(m)); self._rehash(name); self._update_source_hash(name)
        with self.assertRaisesRegex(ValueError, "historical"):
            build_reports(load_bundle(self.evidence))

    def test_output_cannot_be_written_inside_evidence(self):
        destination = self.evidence/"new_reports"
        r = subprocess.run([sys.executable, "-S", str(ROOT/"replay.py"),
                            "--evidence", str(self.evidence), "--output", str(destination)],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("inside the evidence", r.stderr)
        self.assertFalse(destination.exists())

    def test_wrong_category_type_is_an_actionable_input_error(self):
        name = "benchmark.jsonl"; p = self.evidence/name
        rows = [json.loads(line) for line in p.read_text().splitlines()]
        rows[0]["category"] = []
        p.write_text("\n".join(json.dumps(row) for row in rows)+"\n")
        self._rehash(name); self._update_source_hash(name)
        e = self.evidence/"experiment.json"; experiment = json.loads(e.read_text())
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        experiment["base"]["dataset_sha256"] = digest
        experiment["lora"]["dataset_sha256"] = digest
        experiment["training"]["benchmark_sha256"] = digest
        e.write_text(json.dumps(experiment)); self._rehash(e.name)
        with self.assertRaisesRegex(ValueError, "benchmark"):
            load_bundle(self.evidence)

    def test_lineage_chronology_must_show_baseline_before_training(self):
        p = self.evidence/"experiment.json"; m = json.loads(p.read_text())
        m["training"]["started_at"] = m["base"]["started_at"]
        p.write_text(json.dumps(m)); self._rehash(p.name)
        with self.assertRaisesRegex(ValueError, "lineage"):
            load_bundle(self.evidence)

    def test_optimized_python_does_not_disable_lineage_validation(self):
        p = self.evidence/"experiment.json"; m = json.loads(p.read_text())
        m["lora"]["model_revision"] = "other"
        p.write_text(json.dumps(m)); self._rehash(p.name)
        r = subprocess.run([sys.executable, "-S", "-O", str(ROOT/"replay.py"),
                            "--evidence", str(self.evidence), "--example", "benchmark.selection_bias.000"],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("lineage", r.stderr)

    def test_rehashed_malformed_jsonl_is_not_silently_skipped(self):
        p = self.evidence/"benchmark.jsonl"
        p.write_text(p.read_text()+"\n"); self._rehash(p.name)
        with self.assertRaisesRegex(ValueError, "benchmark.jsonl:121"):
            load_bundle(self.evidence)

    def test_cli_example_is_selected_by_exact_id(self):
        command = [sys.executable, "-S", str(ROOT/"replay.py"),
                   "--evidence", str(self.evidence), "--example"]
        r = subprocess.run(command+["benchmark.selection_bias.000"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        case = json.loads(r.stdout)
        self.assertIn("raw_output", case["base"])
        self.assertIn("scenario", case)
        r = subprocess.run(command+["unknown"], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)

    def test_cli_is_offline_no_site_packages_and_prevents_overwrite(self):
        destination = Path(self.temp.name)/"result"
        command = [sys.executable, "-S", str(ROOT/"replay.py"),
                   "--evidence", str(self.evidence), "--output", str(destination)]
        r = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("already exists", r.stderr)
        r = subprocess.run([sys.executable, "-S", str(ROOT/"replay.py"),
                            "--evidence", str(self.evidence), "--check", str(destination)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        (destination/"comparison.md").write_text("incorrect")
        r = subprocess.run([sys.executable, "-S", str(ROOT/"replay.py"),
                            "--evidence", str(self.evidence), "--check", str(destination)],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)

    def test_missing_input_leaves_no_output(self):
        (self.evidence/"benchmark.jsonl").unlink()
        destination = Path(self.temp.name)/"result"
        r = subprocess.run([sys.executable, "-S", str(ROOT/"replay.py"),
                            "--evidence", str(self.evidence), "--output", str(destination)],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
