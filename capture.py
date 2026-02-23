import cv2
import os
import sys
import time  # For delays

# Default dataset directory
dataset_dir = "dataset"
os.makedirs(dataset_dir, exist_ok=True)

# Get student_id and student_name from command-line args (if provided by main.py)
if len(sys.argv) == 3:
    student_id = sys.argv[1].strip()
    student_name = sys.argv[2].strip()
    print(f"[INFO] Using args: Student ID '{student_id}', Name '{student_name}'")
else:
    # Fallback for standalone run
    student_id = input("Enter Roll Number (exact, e.g. 24060104200006): ").strip()
    student_name = input("Enter Name: ").strip()

# Validate inputs
if not student_id or not student_name:
    print("[ERROR] Student ID and Name are required!")
    sys.exit(1)

# Create student folder
folder = os.path.join(dataset_dir, student_id)
os.makedirs(folder, exist_ok=True)

# Load face cascade classifier
face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(face_cascade_path)
if face_cascade.empty():
    print("[ERROR] Could not load face cascade. Check OpenCV installation.")
    sys.exit(1)

# Initialize camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[ERROR] Camera not available. Check if it's connected and not in use.")
    sys.exit(1)

# Multi-angle setup: Define poses and targets
poses = [
    {"name": "Front View", "target": 20, "instruction": "Turn straight ahead (front face)"},
    {"name": "Left Side", "target": 15, "instruction": "Turn your head to the LEFT (profile view)"},
    {"name": "Right Side", "target": 15, "instruction": "Turn your head to the RIGHT (profile view)"}
]

print(f"[INFO] Capturing multi-angle faces for: {student_id} ({student_name})")
print("[INFO] Total target: 50 images across 3 angles.")
print("[INFO] Tips: Good lighting, change expressions/background. Press 'q' to quit anytime.")

# Count existing images (only .jpg, .png, .jpeg) - but for multi-angle, we'll start fresh or add to existing
existing_images = [f for f in os.listdir(folder) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
total_existing = len(existing_images)
print(f"[INFO] Found {total_existing} existing images. We'll add new ones with angle labels.")

# Track captures per pose (initialize counters)
pose_counters = [0] * len(poses)  # How many captured for each pose
current_pose_index = 0
total_captured = 0
max_total = sum(pose["target"] for pose in poses)  # 50

# Main capture loop
while total_captured < max_total:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Failed to grab frame from camera.")
        break
    
    # Convert to grayscale for detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
    
    current_pose = poses[current_pose_index]
    pose_name = current_pose["name"]
    pose_target = current_pose["target"]
    pose_count = pose_counters[current_pose_index]
    
    # Check if current pose is complete, move to next
    if pose_count >= pose_target:
        current_pose_index += 1
        if current_pose_index >= len(poses):
            break  # All poses done
        current_pose = poses[current_pose_index]
        pose_name = current_pose["name"]
        pose_target = current_pose["target"]
        pose_count = pose_counters[current_pose_index]
        print(f"[INFO] {poses[current_pose_index - 1]['name']} complete! Now: {current_pose['instruction']}")
    
    detected = False
    for (x, y, w, h) in faces:
        detected = True
        if pose_count < pose_target:
            pose_counters[current_pose_index] += 1
            total_captured += 1
            # Extract and resize face
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (200, 200))
            # Save with pose label in filename
            fname = os.path.join(folder, f"{student_name}_{pose_name}_{total_captured}.jpg")
            cv2.imwrite(fname, face_img)
            
            # Draw rectangle and label on frame
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"{pose_name}: {pose_count}/{pose_target}", (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Small delay to avoid duplicate frames
            time.sleep(0.2)  # Slightly longer delay for better variety
        
        else:
            # Still draw if face detected but pose full
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)  # Red if full
            cv2.putText(frame, f"{pose_name} FULL - Next Pose", (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # Overlay instructions on the entire frame (top of window)
    instruction_text = f"Current: {pose_name} - {current_pose['instruction']}"
    if not detected:
        instruction_text += " | No face detected - Position properly!"
    cv2.putText(frame, instruction_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    
    # Progress bar-like text
    total_progress = f"Total: {total_captured}/{max_total}"
    cv2.putText(frame, total_progress, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Show the frame
    cv2.imshow("Multi-Angle Face Capture - Press 'q' to stop", frame)
    
    # Check for 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()

# Summary
new_captured = total_captured
print(f"[INFO] Session complete!")
for i, pose in enumerate(poses):
    print(f"  - {pose['name']}: {pose_counters[i]}/{pose['target']} images")
print(f"Total new images: {new_captured} (Grand total in folder: {total_existing + new_captured})")
print(f"[INFO] Files saved with labels like '{student_name}_Front View_5.jpg' for easy identification.")