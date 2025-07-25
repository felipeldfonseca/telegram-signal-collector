# Scenario D – Pause if Previous-Hour WR ≤ 75 %

Scenario D lowers the win-rate filter to 75 % while retaining the same defensive
aids used in Scenario C.

Pause the next hour when **ANY** of the following is true for the previous hour:

1. Fewer than **10** signals
2. ≥ **3** losses in its last 10 signals **or** loss-rate > 30 %
3. Win-rate ≤ **75 %**

Once an hour is cleared to trade we have tested two execution modes.

| Variant | Stake ladder | In-hour limits | Daily limits | 6-day P&L |
| ------- | ------------ | -------------- | ------------ | ---------- |
| Continuous (full-hour) | $2 / $4 | none | +$12 / –$36 | **+$60** |
| Hourly-cap | $2 / $4 | +$6 / –$12 | +$12 / –$36 | **+$30** |

### Notes
* The **full-hour** variant matches Scenario C (80 % filter) profit despite the
  lower WR threshold, finishing **+$60** with 5 winning hours and zero stop-outs.
* Adding a **+6 / –12** cap per hour roughly halves the total edge to **+$30**.
  The cap rarely prevents large draw-downs (they were already filtered out)
  but often cuts the upside once an hour starts well.
* Neither variant hit the –$36 daily stop in the 6-day sample.
* Lowering the WR threshold from 80 %→75 % increases trading frequency only
  marginally; the quality filter is still strong enough to avoid bad hours.

---

Scripts:
* `run_scenario_D.py` – continuous trading during qualifying hours.
* `run_scenario_D_hourly.py` – trades until ±$6/–$12 is reached each hour.

Both scripts print **previous-hour** and **current-hour** win-rates for full
transparency and use the fixed `should_pause` logic (no AND/OR bug).
