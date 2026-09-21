# Chatbot guardrail latency profile

How much does a guardrailed chat turn cost in wall-clock time when each stage is its own
process, versus one process kept alive across the stages? Measured against the real
`claude` CLI, not a mock.

- **Pattern A** - three separate one-shot `claude -p` processes: input guardrail (haiku),
  main answer (sonnet), output guardrail (haiku). Pays the Node cold start three times.
- **Pattern B** - one persistent `--input-format stream-json` process, the same three
  stages sent as sequential messages. Pays the cold start once.

## Headline (N = 5)

| | per turn |
| :--- | :--- |
| Pattern A | ~49.9 s |
| Pattern B | ~26.6 s |

Pattern B is about **47% faster**, and only ~4.6 s of the difference is cold start. The
real loss in A is the guardrails' time-to-first-token: roughly 10 s for a one-word verdict,
because each spawn starts cold and un-cached.

[**Read the full report**](https://camalzadeh.github.io/claude_cli_benchmark/) - per-stage
breakdown, variance and the caveats that matter.

## Files

- `index.html` - the interactive report (self-contained; this is what the link above serves).
- `latency_compare.png` - both graphs in one image.
- `latency_pattern_A.png`, `latency_pattern_B.png` - each graph on its own.
- `latency_bench.py` - the harness. Spawns the real CLI and measures each stage.
- `analyze.py` - aggregates `results.json` into a console summary and `chartdata.json`.
- `plot.py` - renders the PNGs from `results.json`.
- `results.json`, `chartdata.json` - the captured timings (N = 5).

## Re-running it

```bash
python latency_bench.py -n 5 -o results.json
python analyze.py            # prints the means, writes chartdata.json
python plot.py               # redraws the PNGs
```

Set `CLAUDE_BIN` if the `claude` CLI is not on your `PATH`.

## What the prompts are

The three prompts in `latency_bench.py` - input guardrail, assistant persona, output
guardrail - are **stand-ins**. The published numbers were measured with a private prompt
set of the same shape and roughly the same size, which is what the latency depends on; the
text itself is not reproduced here. `results.json` keeps the timings and not the replies,
for the same reason.

Each bar segment is a mean over 5 iterations, and each dot is one iteration's stage total,
so the spread is visible. Iteration 0 is a flagged warm-up.
