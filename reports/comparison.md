# Saved-prediction replay: Base → 100-row LoRA smoke

Offline metric recomputation only. No model inference, training, or new capability claim.

| Metric (denominator: 120 unless noted) | Base | LoRA | Delta (pp) |
|---|---:|---:|---:|
| Strict exact accuracy | 0.0% | 18.3% | +18.3 |
| Plain JSON object | 0.0% | 100.0% | +100.0 |
| Plain JSON schema compliance | 0.0% | 100.0% | +100.0 |
| Strict contract (schema + valid/category consistency) | 0.0% | 98.3% | +98.3 |
| Recovered category accuracy (diagnostic) | 20.0% | 18.3% | -1.7 |
| Recovered joint accuracy (diagnostic) | 0.0% | 18.3% | +18.3 |
| Strict boolean accuracy | 0.0% | 90.0% | +90.0 |
| Recovered boolean accuracy (diagnostic) | 53.3% | 91.7% | +38.3 |

Macro F1: 0.0000 → 0.1419 (fixed ten labels; malformed predictions count as errors).

All historical scalar, per-category, confusion-matrix and bootstrap fields match (absolute tolerance 1e-12).
The preserved historical name `structured_output_validity` includes semantic field consistency, not just JSON syntax.
All 120 Base answers are fenced. LoRA has 120 schema-compliant objects, but two contradictory valid/category pairs.

## Per-category strict accuracy

| Gold category | Support | Base | LoRA | LoRA errors |
|---|---:|---:|---:|---:|
| insufficient_sample_size | 12 | 0.0% | 100.0% | 0 |
| statistically_insignificant | 12 | 0.0% | 0.0% | 12 |
| simpsons_paradox | 12 | 0.0% | 0.0% | 12 |
| selection_bias | 12 | 0.0% | 0.0% | 12 |
| confounding | 12 | 0.0% | 0.0% | 12 |
| metric_mismatch | 12 | 0.0% | 0.0% | 12 |
| data_leakage | 12 | 0.0% | 41.7% | 7 |
| correlation_vs_causation | 12 | 0.0% | 41.7% | 7 |
| experiment_contamination | 12 | 0.0% | 0.0% | 12 |
| valid_conclusion | 12 | 0.0% | 0.0% | 12 |

## Interpretation and limits

- Strict accuracy rises 0/120 → 22/120; recovered category recognition falls 24/120 → 22/120 (-1.7 pp). This is primarily evidence of output-contract learning, not general reasoning improvement.
- LoRA emits data_leakage 68/120 times and valid_conclusion zero times. It says valid=false 118 times; the two valid=true outputs contradict their failure labels. Never literally describe this as always-false.
- The invalid gold prior is 108/120 = 90%. Strict boolean accuracy equals that prior; recovered boolean accuracy is 110/120 = 91.7%. Neither is an adequate ten-way capability metric.
- LoRA confidence is 1.0 in every recovered answer. ECE/Brier are both 0.813559 over 118 strict-valid answers; Base calibration is unavailable under strict parsing. Coverage differs, so these are not a clean calibration comparison.
- Every training target also used confidence=1.0, despite defining confidence as correctness probability. That supervision is flawed; calibration cannot be claimed.
- Train and benchmark reuse category builder functions. Split-prefixed template-family names and different seeds do not establish template isolation. Exact-hash alignment prevents accidental file mixing, not semantic leakage.
- Numeric rates, p-values and intervals were not all derived from common raw observations. Generator-provided labels are not an expert-reviewed statistical gold standard. Category ambiguity remains.
- One 100-row training run, one seed, one synthetic benchmark: no stable improvement or generalization claim. Historical row-IID bootstrap intervals are reproduced only for parity and may understate uncertainty with shared templates.
- Explanations are preserved for inspection, not graded for factual correctness by this evaluator. No v2 training was performed in this replay.

See [METHOD.md](../METHOD.md) for scoring definitions and [NEXT_EXPERIMENT.md](../NEXT_EXPERIMENT.md) for hypotheses, data design and pre-registered checks.
