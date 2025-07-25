import pandas as pd
from pathlib import Path

DATA_DIR = Path('docs/strategy/martin gale/study/study_data')
FILES = sorted(DATA_DIR.glob('signals_*.csv'))

TRADING_START = 17  # inclusive
TRADING_END = 23    # inclusive (17:00-23:59)
PREV_START = 16     # we need previous hour

# Load and concat
frames = []
for fp in FILES:
    df = pd.read_csv(fp, dtype={'attempt': 'float'})
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    frames.append(df)

df_all = pd.concat(frames, ignore_index=True)

# Define win / loss according to rules
def classify(row):
    if row['result'] == 'W' and row['attempt'] in (1.0, 2.0):
        return 'win'
    else:
        return 'loss'

df_all['outcome'] = df_all.apply(classify, axis=1)

# Compute WR per date & hour
wr_stats = (
    df_all.groupby(['date', 'hour'])
          .agg(total=('outcome', 'size'), wins=('outcome', lambda x: (x=='win').sum()))
)
wr_stats['wr'] = wr_stats['wins'] / wr_stats['total'] * 100
wr_stats = wr_stats.reset_index()

# Build pairs (prev_hour, next_hour)
pairs = []
for date, group in wr_stats.groupby('date'):
    hourly = group.set_index('hour')
    for h in range(PREV_START, TRADING_END):  # 16..22
        if h in hourly.index and (h+1) in hourly.index and TRADING_START <= h+1 <= TRADING_END:
            prev_wr = hourly.at[h, 'wr']
            next_wr = hourly.at[h+1, 'wr']
            pairs.append({'prev_wr': prev_wr, 'next_wr': next_wr})

pairs_df = pd.DataFrame(pairs)

# Metrics
cond_prev75 = pairs_df['prev_wr'] > 75
cond_next75 = pairs_df['next_wr'] > 75
prob = (cond_prev75 & cond_next75).sum() / cond_prev75.sum() * 100 if cond_prev75.sum() else float('nan')

avg_next_prev75 = pairs_df.loc[cond_prev75, 'next_wr'].mean()
cond_prev70 = pairs_df['prev_wr'] > 70
avg_next_prev70 = pairs_df.loc[cond_prev70, 'next_wr'].mean()

print("Total hour pairs analysed:", len(pairs_df))
print(f"P(next WR > 75 | prev WR > 75): {prob:.1f}%")
print(f"Average next WR | prev WR > 75: {avg_next_prev75:.1f}%")
print(f"Average next WR | prev WR > 70: {avg_next_prev70:.1f}%") 