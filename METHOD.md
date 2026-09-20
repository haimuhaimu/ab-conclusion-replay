# Method, provenance and limits

## Task and target contract

Input: experiment background, metric results, segment results and one conclusion. Output: exactly one bare JSON object with exactly these fields:

```json
{"valid": false, "failure_type": "selection_bias", "confidence": 0.7, "explanation": "Evidence-specific explanation."}
```

This is a schema example, not a recorded model prediction. `valid` must be a boolean; confidence a finite number in [0,1], excluding booleans; explanation a nonblank string. Labels are the ten entries in `scoring.LABELS`. `valid` is true iff the failure type is `valid_conclusion`. The original task asks for the dominant failure, but the synthetic cases do not establish a fully adjudicated precedence rule for overlapping statistical problems.

## Three separate score layers

1. **JSON object / schema compliance**: the entire trimmed raw output must be one bare object. Schema compliance additionally checks exact keys, types, range and known label. The valid/category relation is not part of this layer.
2. **Strict output contract and headline scores**: plain schema compliance plus valid/category consistency. Strict exact accuracy requires the gold category (and consequently gold boolean). All 120 cases remain in the denominator; malformed/contradictory answers are wrong. Macro F1 is the unweighted average over all ten labels, with undefined F1 set to zero. Invalid predictions create false negatives, not an eleventh reported class.
3. **Recovered diagnostics**: optionally remove one complete enclosing Markdown fence, then apply schema checks. No prose extraction, partial JSON repair or guessed labels. Category and boolean accuracy are measured separately. Joint accuracy requires both; inconsistent recovered outputs can match one field but cannot match the consistent gold pair. This layer never changes headline scoring.

The preserved historical field `structured_output_validity` means layer 2's contract validity. Calling 98.3% merely “JSON validity” hides the two semantic contradictions: plain schema compliance is 100% after LoRA.

Duplicate JSON keys, NaN/Infinity, unknown labels and ambiguous multi-object text are rejected. The replay parser is deliberately stricter on duplicate keys/non-finite inputs than a permissive generic JSON loader. Those cases are absent from these historical outputs; all original metrics still match.

## Calibration and priors

Confidence is interpreted as the probability of joint correctness, not a failure-class probability vector. Ten equal-width ECE bins use `min(int(confidence*10), 9)`; 1.0 is in the last bin. Brier is mean squared error against binary joint correctness. Only strict-valid predictions enter calibration, and coverage is reported.

Base coverage is 0/120, so ECE/Brier are unavailable, not zero. LoRA coverage is 118/120, all confidences 1.0, with 22 correct: ECE = Brier = 96/118 = 0.813559. The training targets also fixed confidence=1.0. This is flawed supervision; neither genuine uncertainty estimation nor calibration improvement has been demonstrated.

The ten-way class counts are balanced (12 each), but binary validity is not: nine failure types create a 90% invalid prior. Constant `valid=false` therefore scores 90% in a binary-only metric. LoRA says false 118 times and true twice; its strict binary accuracy is 90%, recovered binary accuracy 91.7%, and no answer uses `valid_conclusion`.

## What the bundle verifies

- SHA-256 and byte length for a fixed six-file allowlist, plus non-symlink files.
- Run lineage: same base model/revision, benchmark hash, seed and decoding configuration; completed Base before training before adapter eval.
- Exactly 120 benchmark rows, 12 per label, correct scenario fields and split.
- Exact ID order and cardinality, unique benchmark IDs, valid gold targets, matching gold fields in prediction rows.
- Fresh parsing of raw output agrees with historical cached strict-valid flags and schema-valid predictions; cached values are not used as scoring authority. A failed parse requires a nonblank string error, but exact historical error wording is not compared across parser implementations.
- Every historical metric field matches recomputation to absolute tolerance 1e-12, including confusion matrices and historical bootstrap intervals. A mismatch stops output; it never rewrites the historical report.
- Generated JSON/Markdown/badcases are deterministic, contain no generated timestamp or absolute local path, and can be compared byte-for-byte with `--check`.

Manifest hashes detect accidental changes relative to the supplied manifest. They are **not signatures** and cannot authenticate evidence if a person deliberately rewrites the files, manifest and provenance together. Published commit identity/history is a separate trust boundary. File-level checks do not prove scientific validity or absence of semantic leakage.

Historical confidence intervals use Python `random.Random(42)`, 2,000 row-level bootstrap samples, and floor-index 2.5%/97.5% quantiles. They are reproduced for parity only. Rows share templates, so independent-row uncertainty is not a reliable generalization interval. No significance claim is based on those intervals.

## Provenance

The five original benchmark/prediction/metric files are byte-for-byte copies. `experiment.json` is an explicit metadata allowlist extracted from completed-run manifests. It records original relative source paths/hashes, generator version, seed, model revision, original package versions and training configuration. No path reveals the local home directory.

Historical timeline is stored in UTC (2026-08-30); run names use the next calendar date in UTC+8. The original 100-example training used ordinary LoRA, rank 16, alpha 32, dropout 0.05, learning rate 1e-4, one epoch, batch 1 with accumulation 5, seed 42, max length 768, no quantization. It ran on Apple M3 Pro / MPS. This replay neither runs nor validates CUDA/QLoRA.

The [pinned model card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct/blob/7ae557604adf67be50417f59c2c2f167def9a775/README.md) identifies the upstream model and its Apache-2.0 license. No model weights or tokenizer are redistributed here. That upstream license is not presented as a blanket license for this entire package.

## Scientific limitations, not implementation exceptions

Train/validation/benchmark use the same category builder functions and lexical cues. Distinct split-prefixed family names and seed ranges do not constitute structural holdout. Exact duplicate filtering and similarity thresholds cannot prove independence.

Synthetic counts, rates, intervals and p-values were not all derived from a common raw-observation dataset. Labels are generator-provided, not expert-adjudicated statistical ground truth. Overlapping categories such as underpowered versus insignificant, or selection bias versus observational causal claims, need clearer decision boundaries.

Only one smoke seed and 100 training examples were run. Explanations are available for human audit but are not automatically graded. The evidence supports a narrow engineering observation about this saved experiment, not the causal claim that SFT reliably improves statistical reasoning. The benchmark is now exposed diagnostic material; later confirmatory claims require a fresh frozen holdout.
