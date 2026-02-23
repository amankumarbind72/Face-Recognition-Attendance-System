# recognize.py
import cv2, os, time, json, threading
import numpy as np
import pandas as pd
from datetime import datetime, date
import tkinter as tk
from tkinter import messagebox

# --------------------------- Config ---------------------------
marked_students = set()  # already marked list
MODEL_PATH = "model/face_model.yml"
LABELS_PATH = "model/labels.json"
STUD_CSV = "students.csv"
ATT_DIR = "attendance"
os.makedirs(ATT_DIR, exist_ok=True)

COOLDOWN = 60  # seconds
LAST_MARK = {}

# ------------------------- Load Data -------------------------
students_df = pd.read_csv(STUD_CSV, dtype=str).set_index("RollNo")

if not os.path.exists(MODEL_PATH) or not os.path.exists(LABELS_PATH):
    print("[ERROR] Model or labels.json not found. Run train.py first.")
    exit(1)

with open(LABELS_PATH, "r") as f:
    label_map = json.load(f)

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(MODEL_PATH)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# ------------------------ Functions --------------------------
def show_popup(name, roll):
    def _popup():
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Attendance Marked", f"{name}\nRoll: {roll}\nMarked Present")
        root.destroy()
    threading.Thread(target=_popup, daemon=True).start()

def append_attendance(rollno):
    today = date.today().isoformat()
    fname = os.path.join(ATT_DIR, f"attendance_{today}.csv")
    
    if not os.path.exists(fname):
        df = pd.DataFrame(columns=["SR NO","TIMESTAMP","NAME","ROLL NO","TOPIC","Field"])
        df.to_csv(fname, index=False)
    
    df = pd.read_csv(fname, dtype=str)

    # Avoid duplicate marking
    if (df["ROLL NO"] == str(rollno)).any():
        return

    name = students_df.loc[str(rollno)]["Name"] if str(rollno) in students_df.index else str(rollno)
    field = students_df.loc[str(rollno)]["Field"] if str(rollno) in students_df.index else ""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    topic = "Face Recognition Based Smart Attendance"
    sr_no = len(df) + 1

    new_row = {"SR NO": sr_no, "TIMESTAMP": timestamp, "NAME": name,
               "ROLL NO": rollno, "TOPIC": topic, "Field": field}
    
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(fname, index=False)
    print(f"[MARKED] {name} ({rollno}) at {timestamp}")
    show_popup(name, rollno)

# ------------------------- Main Loop -------------------------
def main():
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("[ERROR] Camera not detected!")
        return

    print("[INFO] Recognition started. Press 'q' to quit.")

    while True:
        ret, frame = cam.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, (200, 200))
            try:
                label_id, confidence = recognizer.predict(face)
            except Exception as e:
                continue

            if confidence < 60:  # recognized
                roll_no = label_map.get(str(label_id), str(label_id))
                name = students_df.loc[roll_no]["Name"] if roll_no in students_df.index else "Unknown"
                now_ts = time.time()
                last = LAST_MARK.get(roll_no, 0)

                if roll_no not in marked_students:
                    # First time marking
                    append_attendance(roll_no)
                    marked_students.add(roll_no)
                    LAST_MARK[roll_no] = now_ts
                    print(f"[INFO] Attendance successfully marked for {name} ({roll_no})")
                else:
                    # Already marked
                    if now_ts - last > COOLDOWN:
                        LAST_MARK[roll_no] = now_ts  # reset cooldown timer
                    # No repeated [SKIPPED] print

                # Draw rectangle and name
                cv2.putText(frame, name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255,0,0), 2)

            else:
                # Unknown face
                cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255,0,0), 2)

        cv2.imshow("Recognition - Press q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

# ------------------------- Run -----------------------------
if __name__ == "__main__":
    main()
