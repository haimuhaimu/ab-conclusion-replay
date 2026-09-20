# Inspectable examples, not a cherry-picked evaluation

The complete strict-error set is [reports/badcases.jsonl](reports/badcases.jsonl). These three IDs illustrate distinct phenomena; none changes metric denominators or benchmark labels.

## 1. A category repaired on this template

```bash
python3 -S replay.py --example benchmark.insufficient_sample_size.000
```

The scenario explicitly reports low prospective power and a wide interval, then claims no meaningful effect. The generator label is `insufficient_sample_size`. Base calls it `data_leakage` inside a fence; LoRA returns `insufficient_sample_size` in plain JSON. This is a recorded success on this case, not proof of transferable statistical reasoning. Training and benchmark share the builder and an explicit power cue. The scenario's numerical summaries were not independently validated against raw observations.

## 2. Formatting repaired while category recognition regressed

```bash
python3 -S replay.py --example benchmark.selection_bias.000
```

Users opt in to a beta, and adopters already differ before exposure. Base names `selection_bias` but says `valid=true`, with an internally mistaken numerical explanation; it also uses a fence. LoRA removes the fence and says false, but calls the case `data_leakage`. A bare-JSON-only check would miss the semantic failure. This is why strict, recovered category and recovered joint scores are separate.

## 3. A schema-valid but contradictory answer

```bash
python3 -S replay.py --example benchmark.valid_conclusion.006
```

LoRA raw answer:

```json
{"valid":true,"failure_type":"statistically_insignificant","confidence":1.0,"explanation":"The study establishes an effect but it cannot establish statistical significance."}
```

This is valid JSON with valid field types, but violates `valid iff valid_conclusion`. It fails the strict output contract. The same inconsistency occurs in `benchmark.valid_conclusion.010`; these are the only two LoRA `valid=true` answers. Saying the model “always outputs false” is therefore inaccurate.

Every recovered LoRA answer, including the wrong ones, has confidence=1.0, matching the flawed constant-confidence training targets. This is a warning about supervision design, not evidence of certainty. Across all 120 cases, recovered category accuracy decreased 20.0% → 18.3%; the favorable first example does not negate that measured result.
