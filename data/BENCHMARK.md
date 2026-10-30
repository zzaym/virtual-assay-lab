# Fixed-seed demonstration results

Pre-registered world seeds 42–51 for each baseline; seeds 42–44 for the real OAuth Codex `gpt-5.6-luna` agent. All see the same seeded pairs, fixed latent member, inventory, response sampling and 288-well cap. Baselines generate real Echo CSV and use the same PyLabRobot detection/reader path. Every baseline uses 282 wells: two 96-well exploration plates plus a 90-well independent confirmation plate (18 per required group). Agents allocate their own budgets.

| Seed | Random | Coarse → refine | GP-UCB | Codex agent | Agent wells |
|---|---:|---:|---:|---:|---:|
| 42 | 26.89 | 22.50 | 8.75 | 15.80 | 156 |
| 43 | 1.02 | 40.94 | 30.95 | 25.85 | 165 |
| 44 | 0.00 | 0.00 | 1.64 | 0.00 | 147 |

| Baseline, 10 seeds | Mean score | Median score | Minimum | Maximum |
|---|---:|---:|---:|---:|
| Random | 14.05 | 9.22 | 0 | 38.91 |
| Coarse → refine | 20.09 | 22.74 | 0 | 40.94 |
| GP-UCB | 15.08 | 12.11 | 0 | 33.55 |

These small samples demonstrate task execution and fair comparison, not statistically established strategy superiority. The agent is not required to beat a baseline. Budget usage differs by agent choice, and scores are separate from efficiency. Three agent seeds do not support a general performance claim.

The seed 44 agent's observed confirmation HSA was slightly positive (~0.014), but hidden expected HSA was -0.0021, so its score was zero. No positive hit is manufactured. It submitted a measured candidate, rather than using the explicit `no_hit` option.

The first UI smoke run failed before consuming wells due to a server job-insertion bug. Its full trajectory remains in history; the service was fixed and HTTP job regression coverage added before the registered completed runs. An earlier baseline attempt hit the same bug and is also preserved. These infrastructure attempts are not silently counted as successful completed experiments. All 30 completed baseline episodes and all three completed agent episodes are included in the JSON reports and replay archive.

Machine-readable evidence: `baseline-results.json`, `agent-results.json`, experiment IDs and their replays. The agent protocol/code/event files are preserved with timestamps. The first validation agents received drug IDs; compound-name and target annotations were subsequently added to the public observation/UI without changing any response or score.
