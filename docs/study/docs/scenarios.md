Summary of Tested Scenarios & Key Learnings

This study evolved from a simple baseline to a more complex, high-risk, high-reward strategy.

⚠️ **Data-note (cleaned dataset)**  
To keep the back-tests 100 % aligned with our business rules, **any row that was originally a *third attempt* (G2) and marked as `W` has been converted to `L`,** and its `attempt` field cleared.  
Thus the study files contain *no* G2 wins; every third attempt is treated as an outright loss.

For all of those scenarios (A through G), the core financial and goal structure was precisely as you described:

- Profit Structure: The model was based on making a +$2 profit per successful trade. This was achieved with a $2 stake on the first attempt or a $4 stake on the second attempt (G1) to recover the initial loss and secure the $2 profit.

- Hourly Goal: The objective for any given hour of trading was to achieve 3 successful trades, reaching a +$6 profit for that session.

- Daily Goal: The overall goal for the day was to have two successful hourly sessions, for a total daily profit of +$12.

Scenarios A, B, C, D, E, and F all operated under these exact rules.

The only exception in that list was Scenario G (Aggressive Capitalization), which tested a specific change to the risk side of the equation:
- It kept the same profit goals (+$6 per hour, +$12 per day).
- However, it increased the hourly stop loss from -$6 to -$12.

Scenario I was the only one I raised the daily goal of the day ($18), while mantaining the $36 dollar stop loss.

Scenarios:

Scenario A: Original "Martingale Conservador" (Baseline)
Hypothesis: The original strategy, run continuously from 17:00 to 23:00, serves as the performance benchmark.
Insight: The base strategy without any hourly filter is unprofitable over the test period.

Scenario B: Continuous Operation (Theoretical)
Hypothesis: A slight variation of the baseline, this confirmed that operating without any pause logic leads to losses.
Insight: Validated the need for a dynamic filter to avoid poor market conditions.

Scenario C: The Pause Breakthrough? (80% WR Threshold)
Hypothesis: Pausing trading for an hour if the previous hour's Win Rate (WR) is below 80% will preserve capital and improve profitability.
Insight: This was the crucial breakthrough. The core idea of pausing based on recent performance is highly effective and profitable.

Scenario D: The "Sweet Spot"? (75% WR Threshold)
Hypothesis: Lowering the pause threshold to 75% might be the optimal balance, capturing more trading opportunities than the 80% rule without taking on excessive risk.
Insight: A 75% threshold was significantly more profitable than 80%, suggesting a "sweet spot" exists.

Scenario E: 30-Minute Window (Theoretical)
Hypothesis: A more reactive 30-minute analysis window could adapt to market changes faster.
Insight: We discussed this but concluded it would likely be too "twitchy" and vulnerable to short-term noise. The hourly window provides more stability.

Scenario F: The Aggressive Filter (70% WR Threshold)
Hypothesis: Lowering the threshold even further to 70% might capture even more good hours.
Insight: While profitable, it was less effective than the 75% threshold. However, this scenario led to a crucial discovery about why the filter works (see below).

Scenario G: Aggressive Capitalization (Increased Stop Loss)
Hypothesis: With the confidence of the 70% filter, perhaps allowing a larger hourly stop loss (-$12 instead of -$6) could amplify gains.
Insight: No improvement. The increased risk did not yield a better return, as it amplified both wins and losses equally. Sticking to a tight stop loss is critical.

Scenario H: Asymmetrical Risk (Increased Stakes, Same Target)
Hypothesis: Increasing stakes to $3/$6 while keeping the same daily target ($12) might reach the goal faster.
Insight: Unfavorable risk/reward. The higher capital risk was not justified for the same potential reward, leading to lower overall profitability.

Scenario I: High Risk / High Reward (The Champion)
Hypothesis: To justify higher stakes ($3/$6), the daily profit target must also be increased proportionally (to $18).
Insight: This was the most profitable scenario. When increasing risk, the potential reward must also be increased to create a favorable strategy. This suggests a more aggressive, but still rule-based, approach can yield the best results.