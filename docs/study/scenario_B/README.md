# Scenario B – Continuous Operation (No Pause, No Hourly Stop)

Rules implemented:
1. Trade every signal from 17:00–23:00; do **not** stop inside the hour after a loss or after three wins.
2. Outcome per signal: +$2 on `W` (attempt 1/2), –$6 on any loss or attempt 3.
3. Day ends immediately at +$12 (goal) or –$36 (stop-loss).

## Results (6-day clean dataset)
| Date | P&L |
|------|-----|
| 2025-06-27 | **+$12** |
| 2025-06-28 | **–$36** |
| 2025-06-29 | **+$12** |
| 2025-06-30 | **+$12** |
| 2025-07-01 | **+$12** |
| 2025-07-02 | **+$12** |
| **Total** | **+$24** |

## Interpretation
* Removing the intra-hour stop transforms the strategy from –$60 (Scenario A) to +$24 despite a brutal –$36 day.
* Good-momentum days (29 – 30 Jun, 1 Jul) reach the +$12 cap quickly.
* The daily hard stop at –$36 limits worst-case damage.

This serves as the new benchmark to test pause rules (Scenarios C–F) and risk tweaks (G–I).
