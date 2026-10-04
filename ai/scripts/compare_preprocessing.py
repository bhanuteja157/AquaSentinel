import sys
from pathlib import Path

# Add the AquaSentinel project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.ai_service import AIService
from backend.services.preprocessing_service import PreprocessingService


TEST_DIR = PROJECT_ROOT / "ai" / "test_images"
OUTPUT_DIR = PROJECT_ROOT / "backend" / "outputs"
MODEL_PATH = PROJECT_ROOT / "ai" / "weights" / "best_detector.pt"

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
}


def main():
    # Create services
    ai_service = AIService(MODEL_PATH)
    preprocessing_service = PreprocessingService()

    # Find test images
    images = sorted(
        path
        for path in TEST_DIR.iterdir()
        if path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not images:
        print("No test images found.")
        return

    print()
    print("=" * 70)
    print("AquaSentinel — RAW vs PREPROCESSED TEST")
    print("=" * 70)

    for image_path in images:
        print()
        print(f"IMAGE: {image_path.name}")
        print("-" * 70)

        # --------------------------------------------------
        # RAW IMAGE
        # --------------------------------------------------

        raw_output = OUTPUT_DIR / f"{image_path.stem}_raw_test.jpg"

        raw_detections = ai_service.analyze(
            input_path=image_path,
            annotated_path=raw_output,
        )

        print("RAW:")
        print(raw_detections)

        # --------------------------------------------------
        # PREPROCESSING
        # --------------------------------------------------

        enhanced_path = (
            OUTPUT_DIR / f"{image_path.stem}_preprocessed.jpg"
        )

        preprocessing_service.preprocess(
            input_path=image_path,
            output_path=enhanced_path,
        )

        # --------------------------------------------------
        # PREPROCESSED IMAGE
        # --------------------------------------------------

        enhanced_output = (
            OUTPUT_DIR / f"{image_path.stem}_preprocessed_ai.jpg"
        )

        enhanced_detections = ai_service.analyze(
            input_path=enhanced_path,
            annotated_path=enhanced_output,
        )

        print("PREPROCESSED:")
        print(enhanced_detections)

    print()
    print("=" * 70)
    print("COMPARISON COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()