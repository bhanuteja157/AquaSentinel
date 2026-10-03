from pathlib import Path

import torch
from ultralytics import YOLO


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = BASE_DIR / "ai" / "weights" / "best_detector.pt"
IMAGE_DIR = BASE_DIR / "ai" / "outputs" / "preprocessing"
OUTPUT_DIR = BASE_DIR / "ai" / "outputs" / "preprocessed_detection"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


print("=" * 60)
print("AquaSentinel - Preprocessed SSS AI Test")
print("=" * 60)

DEVICE = 0 if torch.cuda.is_available() else "cpu"

print(f"PyTorch : {torch.__version__}")
print(f"CUDA    : {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"GPU     : {torch.cuda.get_device_name(0)}")

print("\nLoading model...")

model = YOLO(str(MODEL_PATH))

print("Model loaded.\n")


test_images = [
    "preprocessed_01_pipeline.jpg",
    "preprocessed_02_shipwreck.jpg",
    "preprocessed_03_mine_cylinder.jpg",
    "preprocessed_04_ghost_net.jpg",
    "preprocessed_05_empty_seabed.jpg",
]


for image_name in test_images:

    image_path = IMAGE_DIR / image_name

    print("-" * 60)
    print(f"IMAGE: {image_name}")

    if not image_path.exists():
        print(f"  ERROR: Image not found: {image_path}")
        continue

    results = model.predict(
        source=str(image_path),
        imgsz=640,
        conf=0.10,
        device=DEVICE,
        save=True,
        project=str(OUTPUT_DIR),
        name="results",
        exist_ok=True,
        verbose=False,
    )

    result = results[0]

    if result.boxes is None or len(result.boxes) == 0:

        print("  No detections")

    else:

        print(f"  Detections: {len(result.boxes)}")

        for box in result.boxes:

            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            class_name = result.names[class_id]

            print(
                f"  → {class_name} "
                f"({confidence:.3f})"
            )


print("\n" + "=" * 60)
print("PREPROCESSED AI TEST COMPLETE")
print("=" * 60)

print("\nResults saved to:")
print(OUTPUT_DIR)