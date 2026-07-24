# Chatbot guardrail latency profile 

Throwaway latency experiment — **not part of the app build, do not commit** unless you decide to.
Compares one chat turn in two architectures against the real `claude` CLI:

- **Pattern A** — 3 separate one-shot `claude -p` processes (input guardrail haiku → main sonnet → output guardrail haiku). Pays Node cold start ×3.
- **Pattern B** — 1 persistent `--input-format stream-json` process, 3 stages as sequential messages. Cold start ×1.

## Files
- **`latency_compare.png`** — both graphs in one image (the one to paste into a doc / ADO).
- `latency_pattern_A.png` / `latency_pattern_B.png` — each graph on its own.
- `latency-report.html` — interactive version of the two graphs (open in a browser). Self-contained.
- `latency_bench.py` — the harness. Spawns the real CLI, measures per stage. Does **not** touch app code.
- `analyze.py` — aggregates `results.json` → console summary + `chartdata.json`.
- `plot.py` — renders the PNGs from `results.json` (`python plot.py`).
- `results.json` / `chartdata.json` — the captured data (N=5).

Each bar segment is a mean over 5 iterations; each dot is one iteration's stage total (variance).

## Re-run
```bash
python latency_bench.py -n 5 -o results.json
python analyze.py            # prints means, writes chartdata.json
```
Set `CLAUDE_BIN` env var if the CLI is not at the default WinGet path.

## Headline (N=5)
Pattern A ≈ 49.9 s/turn · Pattern B ≈ 26.6 s/turn (B ~47% faster). Only ~4.6 s of that is cold
start — the main loss in A is the guardrails' time-to-first-token (~10 s for a one-word haiku
verdict, cold + un-cached each spawn). See the report for the per-stage breakdown and caveats.
