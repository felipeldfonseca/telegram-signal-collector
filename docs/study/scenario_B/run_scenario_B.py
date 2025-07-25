import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / 'study_data'
FILES = sorted(DATA_DIR.glob('signals_*.csv'))

WIN_PNL = 2      # +$2 per win
LOSS_PNL = -6    # -$6 per loss (any L or attempt 3)
DAILY_GOAL = 12  # stop if cumulative >= +12
DAILY_STOP = -36 # stop if cumulative <= -36
TRADING_HOURS = range(17, 24)  # 17..23


def is_win(row):
    return row['result'] == 'W' and row['attempt'] in (1.0, 2.0)


def process_day(df_day):
    cum = 0
    logs = []
    for hour in TRADING_HOURS:
        hour_df = df_day[df_day['hour'] == hour]
        wins = 0
        losses = 0
        pnl_hour = 0
        for _, op in hour_df.iterrows():
            if is_win(op):
                wins += 1
                pnl_hour += WIN_PNL
            else:
                losses += 1
                pnl_hour += LOSS_PNL
            cum += WIN_PNL if is_win(op) else LOSS_PNL
            if cum >= DAILY_GOAL or cum <= DAILY_STOP:
                break  # reach cut-off mid-hour
        logs.append((hour, wins, losses, pnl_hour, cum))
        if cum >= DAILY_GOAL or cum <= DAILY_STOP:
            break
    return cum, logs


def main():
    frames = []
    for fp in FILES:
        d = pd.read_csv(fp, dtype={'attempt': 'float'})
        d['timestamp'] = pd.to_datetime(d['timestamp'])
        d['date'] = d['timestamp'].dt.date
        d['hour'] = d['timestamp'].dt.hour
        frames.append(d)
    data = pd.concat(frames, ignore_index=True)

    summary = []
    for date, df_day in data.groupby('date'):
        pnl, logs = process_day(df_day)
        summary.append({'date': date, 'pnl': pnl})
        print(f"\n=== {date} ===  P&L: ${pnl:+.2f}")
        for h, w, l, p, c in logs:
            print(f"  {h:02d}:00 wins:{w} losses:{l} P&L:{p:+.2f} | Cum:{c:+.2f}")
    total = sum(d['pnl'] for d in summary)
    print("\n======================")
    print("TOTAL P&L across 6 days:", f"${total:+.2f}")
    pd.DataFrame(summary).to_csv(Path(__file__).with_name('summary.csv'), index=False)

if __name__ == '__main__':
    main() 