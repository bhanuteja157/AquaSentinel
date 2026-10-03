from pathlib import Path

import cv2
import numpy as np


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_DIR = BASE_DIR / "ai" / "test_images"
OUTPUT_DIR = BASE_DIR / "ai" / "outputs" / "preprocessing"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


TEST_IMAGES = [
    "01_pipeline.jpg",
    "02_shipwreck.jpg",
    "03_mine_cylinder.jpg",
    "04_ghost_net.jpg",
    "05_empty_seabed.jpg",
]


def lee_filter(image, window_size=7):
    """
    Simple Lee speckle filter for grayscale SSS imagery.
    """

    image = image.astype(np.float32)

    mean = cv2.boxFilter(
        image,
        ddepth=-1,
        ksize=(window_size, window_size),
    )

    mean_square = cv2.boxFilter(
        image * image,
        ddepth=-1,
        ksize=(window_size, window_size),
    )

    variance = mean_square - (mean * mean)
    variance = np.maximum(variance, 0)

    noise_variance = np.mean(variance)

    weights = variance / (variance + noise_variance + 1e-8)

    filtered = mean + weights * (image - mean)

    filtered = np.clip(filtered, 0, 255)

    return filtered.astype(np.uint8)


def clahe_enhance(image):
    """
    CLAHE contrast enhancement.
    """

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    return clahe.apply(image)


def preprocess_sss(image_path, output_path):
    """
    Convert SSS image to grayscale,
    apply Lee filtering,
    then CLAHE enhancement.
    """

    image = cv2.imread(str(image_path))

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {image_path}"
        )

    grayscale = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    filtered = lee_filter(
        grayscale,
        window_size=7,
    )

    enhanced = clahe_enhance(filtered)

    cv2.imwrite(
        str(output_path),
        enhanced,
    )


print("=" * 60)
print("AquaSentinel - SSS Preprocessing Test")
print("=" * 60)

print(f"Input directory : {INPUT_DIR}")
print(f"Output directory: {OUTPUT_DIR}")

print("\nProcessing images...\n")


for image_name in TEST_IMAGES:

    input_path = INPUT_DIR / image_name

    output_path = OUTPUT_DIR / f"preprocessed_{image_name}"

    print(f"Processing: {image_name}")

    if not input_path.exists():
        print(f"  ERROR: File not found: {input_path}")
        continue

    try:

        preprocess_sss(
            input_path,
            output_path,
        )

        print(f"  Saved: {output_path}")

    except Exception as error:

        print(f"  ERROR: {error}")


print("\n" + "=" * 60)
print("PREPROCESSING COMPLETE")
print("=" * 60)