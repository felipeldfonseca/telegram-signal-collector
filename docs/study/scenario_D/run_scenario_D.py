import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / 'study_data'
FILES = sorted(DATA_DIR.glob('signals_*.csv'))

WIN_PNL = 2
LOSS_PNL = -6
DAILY_GOAL = 12
DAILY_STOP = -36
TRADING_HOURS = range(17, 24)
WR_THRESHOLD = 75  # pause if prev WR <= 75


def is_win(row):
    return row['result'] == 'W' and row['attempt'] in (1.0, 2.0)


def stats(hour_df):
    total = len(hour_df)
    wins = hour_df['is_win'].sum()
    losses = total - wins
    # last 10 signals loss count
    last10 = hour_df.tail(10)
    losses_last10 = len(last10) - last10['is_win'].sum()
    return {
        'total': total,
        'losses': losses,
        'loss_pct': losses / total * 100 if total else 0,
        'wr': wins / total * 100 if total else 0,
        'losses_last10': losses_last10,
    }


def should_pause(prev):
    if prev['total'] < 10:
        return True
    if prev['losses_last10'] >= 3 or prev['loss_pct'] > 30:
        return True
    if prev['wr'] <= WR_THRESHOLD:
        return True
    return False


def simulate_day(df_day):
    cum = 0
    logs = []
    hour_stats = {h: stats(df_day[df_day['hour'] == h]) for h in range(16, 24)}
    for h in TRADING_HOURS:
        prev = hour_stats.get(h - 1, {'total': 0, 'losses': 0, 'loss_pct': 0, 'wr': 0, 'losses_last10': 0})
        curr = hour_stats.get(h, {'total': 0, 'losses': 0, 'loss_pct': 0, 'wr': 0, 'losses_last10': 0})

        if should_pause(prev):
            logs.append((h, 'PAUSE', 0, 0, 0, cum, prev['wr'], curr['wr']))
        else:
            wins = losses = 0
            pnl = 0
            for _, op in df_day[df_day['hour'] == h].iterrows():
                if op['is_win']:
                    wins += 1
                    pnl += WIN_PNL
                    cum += WIN_PNL
                else:
                    losses += 1
                    pnl += LOSS_PNL
                    cum += LOSS_PNL
                if cum >= DAILY_GOAL or cum <= DAILY_STOP:
                    break
            logs.append((h, 'TRADE', wins, losses, pnl, cum, prev['wr'], curr['wr']))

        if cum >= DAILY_GOAL or cum <= DAILY_STOP:
            break

    return cum, logs


def main():
    frames=[]
    for fp in FILES:
        d=pd.read_csv(fp,dtype={'attempt':'float'})
        d['timestamp']=pd.to_datetime(d['timestamp'])
        d['date']=d['timestamp'].dt.date
        d['hour']=d['timestamp'].dt.hour
        d['is_win']=d.apply(is_win,axis=1)
        frames.append(d)
    data=pd.concat(frames,ignore_index=True)

    total=0
    for date, g in data.groupby('date'):
        pnl,logs=simulate_day(g)
        total+=pnl
        print(f"\n=== {date} === P&L {pnl:+.2f}")
        for h,act,w,l,p,c,prevwr,currwr in logs:
            if act=='PAUSE':
                print(f"  {h:02d}:00 PAUSE (prev WR {prevwr:.1f}%, curr WR {currwr:.1f}%) | Cum {c:+.2f}")
            else:
                print(f"  {h:02d}:00 wins:{w} losses:{l} P&L:{p:+.2f} (prev WR {prevwr:.1f}%, curr WR {currwr:.1f}%) | Cum {c:+.2f}")
    print("\nTOTAL P&L across 6 days:",f"{total:+.2f}")

if __name__=='__main__':
    main() 