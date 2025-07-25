import os
import pandas as pd
from pathlib import Path

def sanitize_data():
    """
    Finds specific daily signal files, sanitizes them according to study rules,
    and saves them to a new 'study_data' directory.
    """
    # --- Configuration ---
    source_root = Path("data/trading ops")
    dest_root = Path("data/study_data")
    target_dates = [
        "2025-06-27", "2025-06-28", "2025-06-29", "2025-06-30",
        "2025-07-01", "2025-07-02"
    ]
    target_files = [f"signals_{date}.csv" for date in target_dates]

    # --- Execution ---
    print(f"Starting data sanitization...")
    if not dest_root.exists():
        print(f"Creating destination directory: {dest_root}")
        dest_root.mkdir(parents=True)

    # Group files by date to handle consolidation
    files_by_date = {date: [] for date in target_dates}
    for root, _, files in os.walk(source_root):
        for file in files:
            for date in target_dates:
                if file == f"signals_{date}.csv":
                    files_by_date[date].append(Path(root) / file)

    if not any(files_by_date.values()):
        print("Error: No target files found. Please check paths and dates.")
        return

    print(f"Found files to process for {len([d for d, f in files_by_date.items() if f])} dates.")

    for date, file_paths in files_by_date.items():
        if not file_paths:
            continue

        print(f"  - Processing date: {date} ({len(file_paths)} file(s))")
        
        # Consolidate all data for the date into one DataFrame
        df_list = [pd.read_csv(fp) for fp in file_paths]
        df = pd.concat(df_list, ignore_index=True)

        # 1. Change 'W' on attempt 3 to 'L' and clear attempt field
        loss_condition = (df['result'] == 'W') & (df['attempt'] == 3.0)
        df.loc[loss_condition, 'result'] = 'L'
        df.loc[df['result'] == 'L', 'attempt'] = pd.NA # Use NA for clean handling

        # 2. Clean up timestamp format
        df['timestamp'] = df['timestamp'].astype(str).str.replace(r'-\d{2}:\d{2}$', '', regex=True)

        # 3. Sort by timestamp to ensure chronological order
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(by='timestamp').reset_index(drop=True)
        
        # Save the consolidated and cleaned file to the destination
        dest_file_path = dest_root / f"signals_{date}.csv"
        df.to_csv(dest_file_path, index=False)
        print(f"    -> Saved consolidated and sanitized file to: {dest_file_path}")

    print("\nSanitization complete. Clean data is ready in 'data/study_data/'.")

if __name__ == "__main__":
    sanitize_data() 