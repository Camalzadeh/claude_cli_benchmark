import json
d = json.load(open("results.json", encoding="utf-8"))
STAGES = ["input_guardrail", "main_agent", "output_guardrail"]

def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs)/len(xs), 1) if xs else 0.0

# ── Pattern A per-stage components (cold, ttft, gen, overhead) ──
print("=== PATTERN A (3 processes) — per-stage means over 5 iters ===")
A = {}
for st in STAGES:
    rows = [next(s for s in it["stages"] if s["name"] == st) for it in d["patternA"]]
    cold = mean([r["cold_start_ms"] for r in rows])
    ttft = mean([r["ttft_ms"] for r in rows])
    gen = mean([r["gen_ms"] for r in rows])
    total = mean([r["total_ms"] for r in rows])
    over = round(max(0.0, total - cold - ttft - gen), 1)
    A[st] = dict(cold=cold, ttft=ttft, gen=gen, overhead=over, total=total)
    print(f"{st:18} cold={cold:>7} ttft={ttft:>7} gen={gen:>7} over={over:>7} total={total:>8}")
a_turn = mean([it["turn_total_ms"] for it in d["patternA"]])
a_cold_total = sum(A[st]["cold"] for st in STAGES)
print(f"TURN TOTAL mean = {a_turn}   (of which cold-start x3 = {round(a_cold_total,1)})")

print("\n=== PATTERN B (1 persistent process) — means over 5 iters ===")
b_cold = mean([it["cold_start_ms"] for it in d["patternB"]])
print(f"cold_start (once) = {b_cold}")
B = {}
for st in STAGES:
    rows = [next(s for s in it["stages"] if s["name"] == st) for it in d["patternB"]]
    ttft = mean([r["ttft_ms"] for r in rows])
    gen = mean([r["gen_ms"] for r in rows])
    total = mean([r["msg_total_ms"] for r in rows])
    over = round(max(0.0, total - ttft - gen), 1)
    B[st] = dict(ttft=ttft, gen=gen, overhead=over, total=total)
    print(f"{st:18} ttft={ttft:>7} gen={gen:>7} over={over:>7} msg_total={total:>8}")
b_turn = mean([it["turn_total_ms"] for it in d["patternB"]])
print(f"cold_start_once = {b_cold}")
print(f"TURN TOTAL mean = {b_turn}")

print(f"\n=== HEADLINE ===")
print(f"A turn mean = {a_turn}ms   B turn mean = {b_turn}ms   B saves {round(a_turn-b_turn,1)}ms ({round(100*(a_turn-b_turn)/a_turn)}%)")
print(f"Cold-start alone: A pays {round(a_cold_total,1)}ms, B pays {b_cold}ms -> cold-start saving = {round(a_cold_total-b_cold,1)}ms")
print(f"So of the {round(a_turn-b_turn,1)}ms saved, only {round(a_cold_total-b_cold,1)}ms is cold-start; the rest is warm-context guardrail speedup.")

# Emit compact chart data (means + raw points) for the artifact
chart = {
    "meta": d["meta"],
    "A": {"stages": A, "turn_mean": a_turn, "cold_total": round(a_cold_total,1),
          "raw": [{"iter": it["iter"], "warmup": it["warmup"], "turn": it["turn_total_ms"],
                   "stages": {s["name"]: {"cold": s["cold_start_ms"], "ttft": s["ttft_ms"], "gen": s["gen_ms"], "total": s["total_ms"]} for s in it["stages"]}}
                  for it in d["patternA"]]},
    "B": {"cold_once": b_cold, "stages": B, "turn_mean": b_turn,
          "raw": [{"iter": it["iter"], "warmup": it["warmup"], "turn": it["turn_total_ms"], "cold": it["cold_start_ms"],
                   "stages": {s["name"]: {"ttft": s["ttft_ms"], "gen": s["gen_ms"], "total": s["msg_total_ms"]} for s in it["stages"]}}
                  for it in d["patternB"]]},
}
json.dump(chart, open("chartdata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("\nWrote chartdata.json")
