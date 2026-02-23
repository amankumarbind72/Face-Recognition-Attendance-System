import cv2
import os
import numpy as np
import json
from sklearn.svm import SVC  # SVM classifier (no contrib needed)
from sklearn.preprocessing import LabelEncoder
import pickle  # For saving model

# Paths
dataset_dir = "dataset"
model_path = "svm_model.pkl"
labels_path = "labels.json"

if not os.path.exists(dataset_dir):
    print("[ERROR] Dataset folder not found. Run capture.py first.")
    exit(1)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

faces = []
labels = []
label_names = {}
label_id = 0
total_images = 0

for student_folder in os.listdir(dataset_dir):
    folder_path = os.path.join(dataset_dir, student_folder)
    if not os.path.isdir(folder_path):
        continue
    
    roll = student_folder
    images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    if not images:
        continue
    
    first_img = images[0]
    name = first_img.split('_')[0]
    student_label = f"{roll}_{name}"
    label_names[label_id] = student_label
    print(f"[INFO] Processing {student_label} ({len(images)} images)")
    
    for img_file in images:
        img_path = os.path.join(folder_path, img_file)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        
        faces_detected = face_cascade.detectMultiScale(img, 1.3, 5)
        if len(faces_detected) > 0:
            face = cv2.resize(img, (200, 200))
            faces.append(face.flatten())
            labels.append(label_id)
            total_images += 1
    
    label_id += 1

if total_images < 10:
    print("[ERROR] Not enough images.")
    exit(1)

# Train SVM (alternative to LBPH)
print(f"[INFO] Training SVM on {total_images} images...")
le = LabelEncoder()
labels_encoded = le.fit_transform(labels)
clf = SVC(kernel='linear', probability=True)
clf.fit(faces, labels_encoded)

# Save model and labels
with open(model_path, 'wb') as f:
    pickle.dump((clf, le), f)
with open(labels_path, 'w') as f:
    json.dump(label_names, f, indent=4)

print(f"[SUCCESS] SVM Training complete!")
print(f"  - Model: {model_path}")
print(f"  - Labels: {labels_path}")
print("[INFO] For recognize.py, update to load SVM instead of LBPH.")