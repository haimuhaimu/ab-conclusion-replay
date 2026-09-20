# Validation record

Date: 2026-09-20. This records local verification of the replay package, not a new model experiment.

## Verified locally

- 34 standard-library unit/integration tests pass under Python 3.11.15, 3.12.14 and 3.14.6 with `-S` (site-packages disabled).
- All three versions reproduce the committed report bytes with `python3 -S replay.py --check reports`.
- Recomputed Base and LoRA metrics match all 17 historical top-level fields, including every category, confusion matrix and row-bootstrap interval; absolute floating tolerance 1e-12. Originals were not rewritten.
- 120 benchmark rows and 120 predictions per run align exactly; all ten categories have support 12. All 218 strict errors are exported (120 Base, 98 LoRA).
- Baseline strict accuracy 0/120, LoRA 22/120. Recovered category accuracy 24/120 → 22/120. Schema compliance 0/120 → 120/120; strict contract 0/120 → 118/120.
- Missing files, corrupt hashes, wrong allowlists, symlinks, malformed JSONL, changed IDs/gold, stale cached parsing, inconsistent run lineage, omitted historical fields and output-overwrite attempts are covered. Python `-O` cannot disable lineage validation.
- The original private experiment's separate 44-test suite passes using an available Python 3.12 runtime and its already-installed dependencies. No package installation or training was needed; the old virtualenv launcher itself was not repaired.
- A local source inventory confirms 17 original source/config/data/result files remain hash-identical. The five copied historical evidence files are byte-identical to their source files.
- Candidate text files were scanned for local home/workplace paths, email addresses, common token patterns and private-key markers; no matches. This is an explicit allowlist review plus heuristic scan, not a proof that arbitrary data is safe to publish.

## Independent local review

A separate read-only reviewer checked source, tests, evidence alignment and scientific claims, and independently recomputed the key counts. Review findings exposed cache type coercion / malformed error-text acceptance and incomplete nested historical metrics. Regression tests were added before fixes; schema checks and exact nested key-set comparisons now reject them. Error-string wording is intentionally not compared across parser implementations, and this limit is documented.

The reviewer is a software review agent, not an expert statistical adjudicator of the benchmark. Its review does not repair the shared-template or generator-ground-truth limitations.

## CI and non-claims

The GitHub Actions workflow is prepared with read-only repository permissions and a pinned official checkout action (v4 SHA verified on 2026-09-20). It uses the Ubuntu runner's Python, disables site-packages, and runs tests/replay inside a network namespace after checkout. It installs no model or Python packages.

At the pre-publication checkpoint, remote CI had not run: there was no public repository, push or Draft PR. The Linux namespace execution path was not exercised on the macOS host. Local successful replay does not imply remote CI success. Publication-time results are recorded below only after the actual remote run completes.

No inference, SFT, CUDA test, GPU job, new checkpoint, model download, paid call or benchmark improvement was performed in this packaging task. Calibration and stable generalization remain unproven. The owner authorized publication on 2026-09-20 with the scope and licenses in `PUBLICATION.md`; no automatic PR merge is authorized.
