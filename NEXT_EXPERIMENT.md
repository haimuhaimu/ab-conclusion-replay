# Next experiment: hypotheses, not a promised improvement

No new data generation, training, inference, paid service or GPU work is performed by this replay. The proposals below require a separately authorized run and should be fixed before viewing its confirmatory evaluation.

## Observed failure → hypothesis → intervention → check

| Evidence from the smoke run | Hypothesis, not established cause | New data/control design | Pre-registered measurement |
|---|---|---|---|
| Base fences 120/120; LoRA plain schema 120/120 | Format learning accounts for much of strict-score gain | A format-focused control with no new reasoning evidence; fixed prompt/parser | Strict contract and recovered category scores separately |
| LoRA data_leakage 68/120; seven classes 0/12 correct | Labels overlap in language; model uses generic causal/leakage cues | Matched contrastive pairs, same surface vocabulary but different assignment/timing mechanism | Per-category recall, macro F1, collapse distribution on unseen structural families |
| Zero valid_conclusion labels; binary-invalid prior 90% | Binary balance encourages rejection; limited positive boundaries | Compare 50/50 valid-invalid with ten-way balanced data at the same training budget | Valid recall, invalid false-accept rate, balanced binary accuracy, ten-way macro F1 |
| Underpowered versus insignificant remain confused despite 12/12 underpowered successes | Low-power wording is a shortcut and dominant-label policy is ambiguous | Predeclare category precedence; independently recomputed intervals/p-values; matched claim-strength contrasts | Confusion within that pair on unseen phrasing, plus human rubric agreement |
| All training and LoRA confidences equal 1.0 | Constant targets teach certainty rather than uncertainty | Do not invent soft confidence labels; specify a held-out calibration procedure or defer confidence claims | ECE/Brier with coverage, reliability bins, proper validation/test separation |

## Gate 1: repair ground truth and split design

Keep every existing file frozen. Treat this 120-row benchmark as exposed regression data; do not alter labels in place. Build a new version with numerical summaries derived from internally consistent raw observations or explicitly stated assumptions. Have ambiguous cases adjudicated against a written rubric; use a second reviewer and record disagreements if available. Do not claim expert review before it happens.

Partition by causal/statistical scenario structure and template family **before** generating variants. Do not merely prefix the same builder with train/test names. Add same-vocabulary opposite-label pairs and wording without giveaway terms. Check exact duplication, semantic similarity and hidden common builders. Reserve a fresh 200-case confirmatory holdout, balanced ten ways, inaccessible to training generation; freeze manifest and hashes before any new model selection.

## Gate 2: minimal controlled comparison

Freeze model revision, prompt, parser, training budget and generation configuration. First measure the unchanged Base and existing smoke adapter on the new holdout only when an evaluation run is authorized. Evaluate negative priors explicitly. Data-v1 and data-v2 comparisons should each start from the same Base to isolate data changes; continued training from v1 is a distinct experiment requiring a matched-compute control.

Use approximately 1,000 curated training examples for the next full round, with separate validation and no copied benchmark badcases. Test one focused intervention first (recommended: valid/invalid boundary plus contrastive failure mechanisms), rather than changing distribution, label definitions, hyperparameters and prompt at once. The historical 1,000-row draft is not assumed adequate merely because it exists: it retains shared-generator and confidence-design concerns.

Pre-register seeds (for example 42, 43, 44), primary metric (ten-way macro F1), structured-output coverage, recovered category accuracy, valid recall, false-accept rate, and uncertainty reporting. Use family-level uncertainty estimates when there are enough independent families; state limitations otherwise. Keep data size and optimizer-step budget comparable across ablations.

## Gate 3: accept evidence, including regressions

After each run retain dataset/model revisions, configuration, seed, loss curve, checkpoint, predictions, aggregate metrics and complete badcases. Use validation to form the next hypothesis; inspect confirmatory results only at declared checkpoints. Once a holdout is used for detailed data design, retire it to the regression suite for future claims.

Success means a measured, repeatable improvement on the fixed primary metric without hiding regressions in valid conclusions or contract compliance. Do not substitute lower loss, higher JSON compliance or a favorable single seed for this criterion. If recognition falls again, retain it and test whether label ambiguity, training imbalance, overfitting or insufficient capacity explains the pattern; these remain hypotheses until controlled comparisons distinguish them.
