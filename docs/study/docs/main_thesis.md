Your Main Thesis: Proven False, But With a Deeper Insight

Your investigation into the filter's effectiveness was the most important part of this study.

Your Thesis: "A high win-rate hour (>75%) reliably predicts another high win-rate hour."
The Reality: This was proven false. The probability of a >75% WR hour being followed by another >75% WR hour is **55.0%** — essentially a coin-flip.

The REAL Insight (The Gold): The power of the filter is not in predicting great hours, but in effectively avoiding terrible ones.

When the previous hour's WR was >75%, the average WR of the next hour was a very strong **78.9%**.

Also, when the previous hour's WR was >70%, the average WR of the next hour was an impressive **75.9%**.

This tells us that while a good hour doesn't guarantee another great hour, it strongly indicates that market conditions are stable and the next hour is highly unlikely to be a disaster. The pause logic acts as a powerful defensive shield.

## Follow-On Performance by Threshold (clean 6-day sample)

| Threshold | #Pairs (prev > T) | P(next > T) | Avg next-hour WR |
|-----------|------------------|-------------|------------------|
| 70 %      | **27**           | **74.1 %**  | **75.9 %**       |
| 75 %      | **20**           | **55.0 %**  | **78.9 %**       |
| 80 %      | **13**           | **53.8 %**  | **83.5 %**       |

### Interpretation
1. **Is > 70 % as safe as > 75 %?**  
   • Safety = “How likely is the next hour to remain at or above the same threshold.”  
   • At 70 % the follow-on hour stays ≥ 70 % in **74 %** of cases – clearly more reliable than the 55 % hold-rate for ≥ 75 %.  
   • Although the average WR is a bit lower at 70 % (75.9 % vs 78.9 %), you gain seven extra eligible hours (27 vs 20).  
   ➜ For steady conditions with more trading opportunities, **70 % is the more dependable safety filter.**

2. **What happens at > 80 %?**  
   • The next hour holds ≥ 80 % only **53.8 %** of the time – essentially the same coin-flip behaviour as 75 %.  
   • When it does hold, performance is stellar (avg 83.5 %).  
   • However, there are only 13 such occurrences across five of the six test days, so trading frequency would be very low.

### Practical Take-away
• **70 % threshold** – best defensive reliability (74 % hold-rate) and most opportunities.  
• **75 % threshold** – middle ground: slightly higher quality but fewer signals.  
• **80 % threshold** – highest quality when it appears, but no better predictability than 75 % and far fewer events.

Hence, for a mechanical pause rule designed to *avoid bad hours* while still providing enough volume, the ≥ 70 % criterion emerges as the safest and most practical choice in this dataset.

---

## "Golden-Hour" Application  
While the ≥ 70 % filter should remain the default safety gate, the data reveals that a **previous-hour WR above 80 % is a rare but powerful signal**:

* Occurs only 13 times in six days (≈ one or two per day on average).
* The follow-on hour holds ≥ 80 % just 54 % of the time, yet its **average WR is 83 – 84 %**.
* Only 2 of the 13 follow-up hours drop below 75 %, so the downside is still limited.

👉 **Implementation idea**  
Treat a > 80 % hour as a “golden-hour” flag:
1. Keep the conservative stake/stop system under normal ≥ 70 % conditions.  
2. If the previous hour’s WR > 80 %, temporarily allow a higher stake size **or** a wider hourly stop to capitalise on the exceptionally good environment.  
3. Revert to normal rules once the golden-hour window closes.

This hybrid approach preserves defense while opportunistically exploiting the very best market stretches.