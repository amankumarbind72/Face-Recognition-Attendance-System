import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import os
import subprocess
import sys  # For sys.executable
import shutil  # For delete/rename
import json  # For labels.json update
from datetime import datetime, timedelta  # For manual attendance and date range
import csv  # For reading/writing CSV

def add_student():
    roll = entry_roll.get().strip()
    name = entry_name.get().strip()
    if not roll or not name:
        messagebox.showerror("Error", "Enter Roll No and Name")
        return
    folder = f"dataset/{roll}"
    if os.path.exists(folder):
        messagebox.showerror("Error", f"Student {roll} already exists!")
        return
    os.makedirs(folder, exist_ok=True)
    messagebox.showinfo("Success", f"Student {name} ({roll}) added! Now capture images.")
    subprocess.Popen([sys.executable, "capture.py", roll, name])

def delete_student():
    roll = entry_roll.get().strip()
    if not roll:
        messagebox.showerror("Error", "Enter Roll No")
        return
    folder = f"dataset/{roll}"
    if os.path.exists(folder):
        shutil.rmtree(folder)
        labels_path = "labels.json"
        if os.path.exists(labels_path):
            with open(labels_path, 'r') as f:
                label_names = json.load(f)
            for k, v in list(label_names.items()):
                if roll in v:
                    del label_names[k]
            with open(labels_path, 'w') as f:
                json.dump(label_names, f, indent=4)
        messagebox.showinfo("Deleted", f"Student {roll} deleted. Retrain model.")
    else:
        messagebox.showerror("Error", "Student not found")

def update_student():
    old_roll = simpledialog.askstring("Update Student", "Enter Old Roll No:")
    if not old_roll:
        return
    old_folder = f"dataset/{old_roll}"
    if not os.path.exists(old_folder):
        messagebox.showerror("Error", "Old student not found!")
        return
    
    new_roll = simpledialog.askstring("Update Student", "Enter New Roll No (leave blank to keep old):")
    new_roll = new_roll.strip() if new_roll else old_roll
    
    new_name = simpledialog.askstring("Update Student", "Enter New Name:")
    if not new_name:
        messagebox.showerror("Error", "New Name required!")
        return
    
    new_folder = f"dataset/{new_roll}"
    try:
        if new_roll != old_roll:
            os.rename(old_folder, new_folder)
            messagebox.showinfo("Info", f"Folder renamed from {old_roll} to {new_roll}. Images intact.")
        
        labels_path = "labels.json"
        if os.path.exists(labels_path):
            with open(labels_path, 'r') as f:
                label_names = json.load(f)
            updated = False
            for k, v in label_names.items():
                if old_roll in v:
                    label_names[k] = f"{new_roll}_{new_name}"
                    updated = True
            if updated:
                with open(labels_path, 'w') as f:
                    json.dump(label_names, f, indent=4)
                messagebox.showinfo("Success", f"Labels updated for {new_roll}_{new_name}")
            else:
                messagebox.showwarning("Warning", "No label entry found. Retrain after update.")
        
        messagebox.showinfo("Success", f"Student updated to {new_roll}_{new_name}. Recapture images recommended. Retrain model.")
    except Exception as e:
        messagebox.showerror("Error", f"Update failed: {str(e)}")

def manual_attendance():
    attendance_file = "attendance.csv"
    if not os.path.exists(attendance_file):
        with open(attendance_file, 'w') as f:
            f.write("Timestamp,Roll_Name,Status\n")
    
    student = simpledialog.askstring("Manual Attendance", "Enter Student (Roll_Name, e.g., 24060104200006_Aman kumar):")
    if not student:
        return
    
    date_str = simpledialog.askstring("Manual Attendance", "Enter Date (YYYY-MM-DD, or blank for today):")
    date_str = date_str.strip() if date_str else datetime.now().strftime("%Y-%m-%d")
    
    time_str = simpledialog.askstring("Manual Attendance", "Enter Time (HH:MM:SS, or blank for now):")
    time_str = time_str.strip() if time_str else datetime.now().strftime("%H:%M:%S")
    
    timestamp = f"{date_str} {time_str}"
    status = simpledialog.askstring("Manual Attendance", "Status (Present/Absent):").strip()
    if not status:
        status = "Present"
    
    try:
        with open(attendance_file, 'a') as f:
            f.write(f"{timestamp},{student},{status}\n")
        messagebox.showinfo("Success", f"Manual attendance added: {student} - {status} at {timestamp}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add: {str(e)}")

def view_attendance_summary():
    attendance_file = "attendance.csv"
    summary_file = "attendance_summary.csv"
    
    if not os.path.exists(attendance_file):
        messagebox.showerror("Error", "No attendance.csv found. Mark some attendance first.")
        return
    
    # Get date range from user
    from_date_str = simpledialog.askstring("Summary", "From Date (YYYY-MM-DD, blank for 30 days ago):")
    to_date_str = simpledialog.askstring("Summary", "To Date (YYYY-MM-DD, blank for today):")
    
    # Default: last 30 days
    if not from_date_str:
        from_date = datetime.now() - timedelta(days=30)
        from_date_str = from_date.strftime("%Y-%m-%d")
    else:
        from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
    
    if not to_date_str:
        to_date = datetime.now()
        to_date_str = to_date.strftime("%Y-%m-%d")
    else:
        to_date = datetime.strptime(to_date_str, "%Y-%m-%d")
    
    if from_date > to_date:
        messagebox.showerror("Error", "From date cannot be after To date!")
        return
    
    # Read attendance.csv
    attendance_data = []
    student_stats = {}
    try:
        with open(attendance_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts_str = row['Timestamp']
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                if from_date <= ts <= to_date:
                    student = row['Roll_Name']
                    status = row['Status']
                    if student not in student_stats:
                        student_stats[student] = {'total': set(), 'present': set(), 'absent': set()}
                    # Use date only for unique days
                    date_only = ts.strftime("%Y-%m-%d")
                    student_stats[student]['total'].add(date_only)
                    if status.lower() == 'present':
                        student_stats[student]['present'].add(date_only)
                    else:
                        student_stats[student]['absent'].add(date_only)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read CSV: {str(e)}")
        return
    
    if not student_stats:
        messagebox.showinfo("No Data", f"No attendance in range {from_date_str} to {to_date_str}")
        return
    
    # Calculate and display
    summary_text = f"Attendance Summary ({from_date_str} to {to_date_str})\n"
    summary_text += "=" * 50 + "\n\n"
    
    summary_data = []  # For CSV
    for student, stats in student_stats.items():
        total_days = len(stats['total'])
        present_days = len(stats['present'])
        absent_days = len(stats['absent'])
        percentage = (present_days / total_days * 100) if total_days > 0 else 0
        
        summary_text += f"Student: {student}\n"
        summary_text += f"  Total Days: {total_days}\n"
        summary_text += f"  Present: {present_days}\n"
        summary_text += f"  Absent: {absent_days}\n"
        summary_text += f"  Percentage: {percentage:.1f}%\n\n"
        
        summary_data.append({
            'Student': student,
            'Total': total_days,
            'Present': present_days,
            'Absent': absent_days,
            'Percentage': f"{percentage:.1f}%",
            'Date_Range': f"{from_date_str} to {to_date_str}"
        })
    
    # Show in scrolled text window
    summary_window = tk.Toplevel(root)
    summary_window.title("Attendance Summary")
    summary_window.geometry("500x400")
    
    text_area = scrolledtext.ScrolledText(summary_window, wrap=tk.WORD, width=60, height=20)
    text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    text_area.insert(tk.END, summary_text)
    text_area.config(state=tk.DISABLED)  # Read-only
    
    # Save to CSV
    try:
        with open(summary_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Student', 'Total', 'Present', 'Absent', 'Percentage', 'Date_Range'])
            writer.writeheader()
            writer.writerows(summary_data)
        messagebox.showinfo("Success", f"Summary saved to {summary_file}. Open in Excel!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save summary: {str(e)}")

def train_model():
    subprocess.Popen([sys.executable, "train.py"])

def recognize():
    subprocess.Popen([sys.executable, "recognize.py"])

# GUI Setup
root = tk.Tk()
root.title("Student Management System")
root.geometry("300x300")  # Larger for new button

tk.Label(root, text="Roll No:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
entry_roll = tk.Entry(root, width=20)
entry_roll.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Name:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
entry_name = tk.Entry(root, width=20)
entry_name.grid(row=1, column=1, padx=10, pady=5)

# Row 2: Add and Delete
tk.Button(root, text="Add Student", command=add_student, width=15).grid(row=2, column=0, padx=10, pady=5)
tk.Button(root, text="Delete Student", command=delete_student, width=15).grid(row=2, column=1, padx=10, pady=5)

# Row 3: Update and Manual
tk.Button(root, text="Update Student", command=update_student, width=15).grid(row=3, column=0, padx=10, pady=5)
tk.Button(root, text="Manual Attendance", command=manual_attendance, width=15).grid(row=3, column=1, padx=10, pady=5)

# Row 4: Train and Recognize
tk.Button(root, text="Train Model", command=train_model, width=15).grid(row=4, column=0, padx=10, pady=5)
tk.Button(root, text="Mark Attendance", command=recognize, width=15).grid(row=4, column=1, padx=10, pady=5)

# Row 5: New Summary Button
tk.Button(root, text="View Attendance Summary", command=view_attendance_summary, width=32, bg="lightblue").grid(row=5, column=0, columnspan=2, padx=10, pady=10)

root.mainloop()
