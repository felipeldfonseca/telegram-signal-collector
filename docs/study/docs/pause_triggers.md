There are three distinct criteria defined in your system. If any of these conditions are met for the previous hour, the system recommends pausing.

1. Insufficient Data
This is a safety rule to prevent making decisions based on a tiny, unreliable sample of trades.

Rule: The total number of operations in the previous hour was less than 10.
Reasoning: With too few signals, the calculated win rate isn't statistically meaningful and could be dangerously misleading.

2. Unfavorable Market Conditions (High Loss Rate)
This rule acts as a primary filter to detect a high-risk environment where even recovery attempts (G1) are failing and stop losses are being hit.

Rule 1: The percentage of losses is greater than 30%.

Rule 2: 3 or more losses out of the 10 last signals before the next trading hour.

3. Low Win Rate (The Dynamic Filter from our Study)
This is the performance-based filter we tested extensively. It pauses trading if the previous hour's performance doesn't meet a specific profitability threshold.
Rule: The Win Rate of the previous hour falls below a set percentage.

Examples Tested:
Scenario C: Pause if WR < 80%
Scenario D: Pause if WR < 75%
Scenario F: Pause if WR < 70%

Reasoning: This rule ensures that you only trade when the recent, proven performance indicates that market conditions are stable and favorable.