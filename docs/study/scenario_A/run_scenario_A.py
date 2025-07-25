import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / 'study_data'
FILES = sorted(DATA_DIR.glob('signals_*.csv'))

STAKE_WIN = 2  # profit per win
HOURLY_WIN_TARGET = 3
HOURLY_STOP_LOSS = -6
DAILY_WIN_HOURS_TARGET = 2  # 2 winning hours -> +12
DAILY_STOP_LOSS_HOURS = 3   # 3 losing hours -> -36

TRADING_HOURS = range(17, 24)  # 17..23 inclusive


def classify(row):
    return row['result'] == 'W' and row['attempt'] in (1.0, 2.0)


def simulate_day(df_day):
    cumulative_pnl = 0
    hour_logs = []

    for hour in TRADING_HOURS:
        hour_df = df_day[df_day['hour'] == hour]
        if hour_df.empty:
            hour_logs.append((hour, 0, 0, 0))
            continue

        pnl_hour = 0
        wins = 0
        losses = 0
        for _, op in hour_df.iterrows():
            if classify(op):
                wins += 1
                pnl_hour += STAKE_WIN
                if wins == HOURLY_WIN_TARGET:
                    break
            else:
                losses += 1
                pnl_hour += HOURLY_STOP_LOSS
                break  # stop after first loss

        cumulative_pnl += pnl_hour
        hour_logs.append((hour, wins, losses, pnl_hour))

        if cumulative_pnl >= 12 or cumulative_pnl <= -36:
            break  # daily goal or stop reached

    return cumulative_pnl, hour_logs


def main():
    frames = []
    for fp in FILES:
        df = pd.read_csv(fp, dtype={'attempt': 'float'})
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        frames.append(df)
    data = pd.concat(frames, ignore_index=True)

    summary = []
    for date, df_day in data.groupby('date'):
        pnl, logs = simulate_day(df_day)
        summary.append({'date': date, 'pnl': pnl})
        print(f"\n=== {date} ===  P&L: ${pnl:+.2f}")
        for h, w, l, p in logs:
            print(f"  {h:02d}:00  wins:{w} losses:{l}  P&L:{p:+.2f}")
    total = sum(d['pnl'] for d in summary)
    print("\n======================")
    print("TOTAL P&L across 6 days:", f"${total:+.2f}")

    # save summary
    pd.DataFrame(summary).to_csv(Path(__file__).with_name('summary.csv'), index=False)

if __name__ == "__main__":
    main() 