# train.py
import os, cv2, json
import numpy as np

dataset_path = "dataset"
model_dir = "model"
os.makedirs(model_dir, exist_ok=True)

faces = []
labels = []
label_map = {}   # int_label -> rollno (string)
current_label = 0

# sort so mapping deterministic
for folder in sorted(os.listdir(dataset_path)):
    folder_path = os.path.join(dataset_path, folder)
    if not os.path.isdir(folder_path):
        continue
    rollno = folder.strip()
    if rollno == "":
        continue
    label_id = current_label
    label_map[str(label_id)] = rollno
    current_label += 1

    # read images
    for img_name in os.listdir(folder_path):
        img_path = os.path.join(folder_path, img_name)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        img = cv2.resize(img, (200,200))
        faces.append(img)
        labels.append(label_id)

if len(faces) == 0:
    print("[ERROR] No images found. Run capture.py first and ensure dataset folder names are RollNo.")
    exit(1)

faces = np.array(faces)
labels = np.array(labels)

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(faces, labels)

model_path = os.path.join(model_dir, "face_model.yml")
labels_path = os.path.join(model_dir, "labels.json")
recognizer.write(model_path)
with open(labels_path, "w") as f:
    json.dump(label_map, f)

print("[INFO] Training complete.")
print("[INFO] Model saved:", model_path)
print("[INFO] Labels saved:", labels_path)
