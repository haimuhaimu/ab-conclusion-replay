# Publication boundary — pending one owner decision

Proposed repository: `haimuhaimu/ab-conclusion-replay`. No repository has been created and no public push has been made. Existing unrelated public repositories are not suitable containers; a private training-history repository will not have its visibility changed.

Proposed license: MIT for the newly authored replay code, tests and documentation; CC BY 4.0 for the original synthetic benchmark, to the extent the owner holds the necessary rights. Saved model outputs and historical measurements retain explicit provenance; do not assert ownership of upstream weights or treat the model's license as a blanket data license. These are proposals only. No license grant is applied before owner confirmation.

## Exact candidate allowlist

- `.gitignore`
- `.github/workflows/replay.yml`
- `README.md`, `METHOD.md`, `EXAMPLES.md`, `NEXT_EXPERIMENT.md`, `PUBLICATION.md`, `VALIDATION.md`
- `scoring.py`, `replay.py`
- `tests/test_scoring.py`, `tests/test_replay.py`
- `evidence/manifest.json`
- `evidence/benchmark.jsonl`
- `evidence/base.predictions.jsonl`
- `evidence/lora.predictions.jsonl`
- `evidence/historical_base.metrics.json`
- `evidence/historical_lora.metrics.json`
- `evidence/experiment.json`
- `reports/metrics.json`, `reports/comparison.md`, `reports/badcases.jsonl`

Evidence hashes are in `evidence/manifest.json`; provenance lists original relative source paths and hashes. Reports are deterministic derived artifacts, not new experiments. The benchmark and raw outputs are synthetic experiment material with English scenario text, not user/company analytics records. Raw outputs may be factually wrong; that is the purpose of the case study.

Excluded: model weights/tokenizers/adapters, checkpoints, training/validation datasets, loss logs, entire original `runs/`, environment directories, caches, keys, private notes, local audit files, synced project sources, chat history, personal/workplace paths, and portfolio site changes. A focused local Git commit is not publication.

Before publication: confirm repository name, license choices and this allowlist; apply actual license notices with appropriate provenance; revalidate; then create only the agreed repository/branch and a Draft PR. Do not merge automatically. The author account must be reverified as `haimuhaimu` (GitHub numeric ID 242566181), Chen Quan / 陈全. Never substitute another available authenticated account.
