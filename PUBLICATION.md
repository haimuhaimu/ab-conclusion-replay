# Publication boundary and licenses

The owner approved public publication on 2026-09-20 in `haimuhaimu/ab-conclusion-replay`, using the 22-file allowlist below. The implementation is submitted through a Draft PR, not automatically merged. No existing private repository has its visibility changed, and unrelated public repositories are not used as containers.

The approved license grants below apply only to rights held by Chen Quan / 陈全. They do not claim ownership of upstream model weights, third-party material or rights the owner cannot grant. License notices are kept in this existing file so the public package remains exactly 22 files.

## Exact public allowlist

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

Publication checks: revalidate the allowlist, tests and report parity; verify the author account as `haimuhaimu` (GitHub numeric ID 242566181), Chen Quan / 陈全; push only the agreed repository/branches and create a Draft PR. Do not merge automatically. The default `main` branch starts with an empty bootstrap commit so the complete release can be reviewed as a PR; the original reviewed commit is preserved in the feature branch history.

## Code and documentation — MIT

SPDX-License-Identifier: MIT

This grant covers `scoring.py`, `replay.py`, `tests/`, `.github/workflows/replay.yml`, `.gitignore`, and the original Markdown documentation. It does not relabel the evidence files or model outputs as MIT software. The standard [MIT license](https://opensource.org/license/mit) follows.

Copyright (c) 2026 Chen Quan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Synthetic benchmark — CC BY 4.0

SPDX-License-Identifier: CC-BY-4.0

`evidence/benchmark.jsonl`, titled **AB Conclusion Judge benchmark_v1**, is
licensed by Chen Quan / 陈全 under [Creative Commons Attribution 4.0
International](https://creativecommons.org/licenses/by/4.0/), to the extent of
rights held by the licensor. The [legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en)
contains the governing terms. Attribution should identify Chen Quan,
benchmark_v1 and this repository, link the license, and indicate changes.

Suggested attribution: “AB Conclusion Judge benchmark_v1 — Chen Quan,
2026, https://github.com/haimuhaimu/ab-conclusion-replay, CC BY 4.0.” The public
benchmark file is unchanged from the historical source; its hash and generator
provenance are recorded in `evidence/manifest.json` and `evidence/experiment.json`.
Benchmark-derived passages in `reports/badcases.jsonl` retain this attribution
and license.

## Saved outputs, measurements and upstream material

Raw model outputs and historical measurements are preserved as audit evidence
with explicit provenance, not represented as newly authored MIT software or
expert-validated facts. No additional third-party rights are claimed. Derived
reports preserve the applicable notices for included benchmark passages and
model outputs; the code/documentation grant is not a blanket grant over every
embedded item. The model's Apache-2.0 license is not asserted to govern all
generated text. No upstream weights, tokenizer or adapter are redistributed.
