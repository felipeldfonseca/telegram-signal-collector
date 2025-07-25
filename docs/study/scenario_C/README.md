# Scenario C – Pause if Previous-Hour WR ≤ 80 %

This scenario layers the first performance filter on top of the continuous-signals engine:

1. **Pause rules** (checked at the start of every trading hour)
   * < 10 signals in previous hour  → **PAUSE**
   * Loss rate > 30 %  *or* ≥ 3 losses in last 10 signals → **PAUSE**
   * Previous-hour win-rate ≤ **80 %** → **PAUSE**
2. If none of the above fire → trade every signal in the hour ( +$2 win, −$6 loss ).
3. Daily cut-offs remain ± $12 / −$36.

## Results (6-day sample)
Variant | Stake ladder | Daily goal | Total P&L
------- | ------------ | ---------- | ---------
Conservative | $2 / $4 | +$12 | **+$60**
Aggressive “golden-hour” | $4 / $8 | +$24 | **+$120**

### Notes
* Golden-hour trades fire only when the previous hour had WR > 80 %. In the 6-day sample just **5 qualifying hours** appeared – but they added up to **+$120**.
* Conservative mode traded 5 winning hours as well, finishing **+$60** while pausing the majority of the time.
* Neither variant hit the −$36 daily stop on any day, confirming the pause rules’ defensive power.
