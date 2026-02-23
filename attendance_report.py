# attendance_report.py
import os
import pandas as pd

ATT_DIR = "attendance"
STUDENTS_FILE = "students.csv"
OUTPUT_FILE = "attendance_summary.csv"

def generate_report():
    if not os.path.exists(ATT_DIR):
        print("[ERROR] Attendance folder not found!")
        return
    
    # load students info (so we can attach name)
    students_df = pd.read_csv(STUDENTS_FILE, dtype=str).set_index("RollNo")
    
    attendance_count = {}

    # loop through all CSV files in attendance folder
    for fname in os.listdir(ATT_DIR):
        if fname.endswith(".csv") and fname.startswith("attendance_"):
            path = os.path.join(ATT_DIR, fname)
            try:
                df = pd.read_csv(path, dtype=str)
                if "ROLL NO" not in df.columns:
                    continue
                for roll in df["ROLL NO"].astype(str):
                    attendance_count[roll] = attendance_count.get(roll, 0) + 1
            except Exception as e:
                print(f"[WARN] Skipping {fname}: {e}")
    
    # prepare summary DataFrame
    summary = []
    for roll, count in attendance_count.items():
        name = students_df.loc[roll]["Name"] if roll in students_df.index else "Unknown"
        summary.append({"ROLL NO": roll, "NAME": name, "TOTAL_PRESENT": count})
    
    summary_df = pd.DataFrame(summary).sort_values("ROLL NO")
    summary_df.to_csv(OUTPUT_FILE, index=False)
    print(f"[INFO] Attendance summary saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_report()
