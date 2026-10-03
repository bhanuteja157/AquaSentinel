from pathlib import Path

import torch
from ultralytics import YOLO


# ============================================================
# AQUASENTINEL - FIRST SSS AI INFERENCE
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = BASE_DIR / "ai" / "weights" / "best_detector.pt"
IMAGE_PATH = BASE_DIR / "ai" / "test_images" / "02_shipwreck.jpg"
OUTPUT_DIR = BASE_DIR / "ai" / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("AquaSentinel - SSS AI Detection Test")
print("=" * 60)

# GPU check
print(f"PyTorch version : {torch.__version__}")
print(f"CUDA available  : {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"GPU             : {torch.cuda.get_device_name(0)}")
    DEVICE = 0
else:
    print("GPU             : Not available")
    DEVICE = "cpu"

# Check files
print("\nChecking files...")
print(f"Model: {MODEL_PATH}")
print(f"Image: {IMAGE_PATH}")

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

if not IMAGE_PATH.exists():
    raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")

print("Files found.")

# Load model
print("\nLoading DRISHTI model...")

model = YOLO(str(MODEL_PATH))

print("Model loaded successfully.")

# Run inference
print("\nRunning AI inference...")

results = model.predict(
    source=str(IMAGE_PATH),
    imgsz=640,
    conf=0.10,
    device=DEVICE,
    save=True,
    project=str(OUTPUT_DIR),
    name="first_test",
    exist_ok=True,
)

# Display detections
print("\n" + "=" * 60)
print("DETECTION RESULTS")
print("=" * 60)

total_detections = 0

for result in results:

    if result.boxes is None or len(result.boxes) == 0:
        print("No detections found.")
        continue

    for box in result.boxes:

        total_detections += 1

        class_id = int(box.cls[0])
        confidence = float(box.conf[0])

        class_name = result.names[class_id]

        x1, y1, x2, y2 = box.xyxy[0].tolist()

        print(f"Target #{total_detections}")
        print(f"  Class       : {class_name}")
        print(f"  Confidence  : {confidence:.3f}")
        print(
            f"  Bounding box: "
            f"({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})"
        )
        print()

print("=" * 60)
print(f"Total detections: {total_detections}")
print("=" * 60)

print("\nAnnotated image saved to:")
print(OUTPUT_DIR / "first_test")

print("\nAquaSentinel AI test completed.")