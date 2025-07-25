import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / 'study_data'
FILES = sorted(DATA_DIR.glob('signals_*.csv'))

WIN_PNL = 2
LOSS_PNL = -6
DAILY_GOAL = 12
DAILY_STOP = -36
TRADING_HOURS = range(17, 24)  # 17-23 inclusive
WR_THRESHOLD = 80  # pause below/ equal 80


def is_win(row):
    return row['result'] == 'W' and row['attempt'] in (1.0, 2.0)


def hour_stats(hour_df):
    total = len(hour_df)
    wins = hour_df['is_win'].sum()
    losses = total - wins
    last10 = hour_df.tail(10)
    losses_last10 = len(last10) - last10['is_win'].sum()
    wr = wins / total * 100 if total else 0.0
    return {
        'total': total,
        'losses': losses,
        'loss_pct': losses / total * 100 if total else 0.0,
        'wr': wr,
        'losses_last10': losses_last10,
    }


def should_pause(prev):
    # Pause if ANY of these conditions are met:
    # 1. Less than 10 signals in previous hour
    if prev['total'] < 10:
        return True
    
    # 2. 3 or more losses in last 10 signals of previous hour
    if prev['losses_last10'] >= 3:
        return True
    
    # 3. Previous hour win rate is less than 80%
    if prev['wr'] < WR_THRESHOLD:
        return True
    
    # If none of the pause conditions are met, continue trading
    return False


def process_day(df_day):
    cum = 0
    logs = []
    # compute stats dictionary for quick lookup
    stats_by_hour = {}
    for h in range(16, 24):
        hour_df = df_day[df_day['hour'] == h]
        stats_by_hour[h] = hour_stats(hour_df)
    for hour in TRADING_HOURS:
        prev_stats = stats_by_hour.get(hour - 1, {'total': 0, 'losses': 0, 'loss_pct': 0, 'wr': 0})
        curr_stats = stats_by_hour.get(hour, {'total': 0, 'losses': 0, 'loss_pct': 0, 'wr': 0})
        if should_pause(prev_stats):
            logs.append((hour, 'PAUSE', 0, 0, 0, cum, prev_stats['wr'], curr_stats['wr']))
        else:
            wins = 0
            losses = 0
            pnl_hour = 0
            for _, op in df_day[df_day['hour'] == hour].iterrows():
                if op['is_win']:
                    wins += 1
                    pnl_hour += WIN_PNL
                else:
                    losses += 1
                    pnl_hour += LOSS_PNL
                cum += WIN_PNL if op['is_win'] else LOSS_PNL
                if cum >= DAILY_GOAL or cum <= DAILY_STOP:
                    break
            logs.append((hour, 'TRADE', wins, losses, pnl_hour, cum, prev_stats['wr'], curr_stats['wr']))
        if cum >= DAILY_GOAL or cum <= DAILY_STOP:
            break
    return cum, logs


def main():
    frames = []
    for fp in FILES:
        df = pd.read_csv(fp, dtype={'attempt': 'float'})
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        df['is_win'] = df.apply(is_win, axis=1)
        frames.append(df)
    data = pd.concat(frames, ignore_index=True)

    summary = []
    for date, df_day in data.groupby('date'):
        pnl, logs = process_day(df_day)
        summary.append({'date': date, 'pnl': pnl})
        print(f"\n=== {date} === P&L: ${pnl:+.2f}")
        for h, action, w, l, p, c, prev_wr, curr_wr in logs:
            if action == 'PAUSE':
                print(f"  {h:02d}:00  PAUSE  (prev WR {prev_wr:.1f}%, curr WR {curr_wr:.1f}%) | Cum:{c:+.2f}")
            else:
                print(f"  {h:02d}:00  wins:{w} losses:{l} P&L:{p:+.2f} (prev WR {prev_wr:.1f}%, curr WR {curr_wr:.1f}%) | Cum:{c:+.2f}")
    total = sum(d['pnl'] for d in summary)
    print("\n======================")
    print("TOTAL P&L across 6 days:", f"${total:+.2f}")
    pd.DataFrame(summary).to_csv(Path(__file__).with_name('summary.csv'), index=False)

if __name__ == '__main__':
    main() 