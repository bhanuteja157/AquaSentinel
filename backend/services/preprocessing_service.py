from pathlib import Path

import cv2
import numpy as np


class PreprocessingService:
    """
    Preprocesses Side-Scan Sonar imagery for AI inference.

    The original input image is never modified.
    """

    def preprocess(
        self,
        input_path: Path,
        output_path: Path,
    ) -> Path:
        """
        Create an enhanced copy of an SSS image.

        Pipeline:
        1. Read image
        2. Convert to grayscale
        3. Light denoising
        4. CLAHE contrast enhancement
        5. Normalization
        6. Save enhanced image
        """

        if not input_path.exists():
            raise FileNotFoundError(
                f"Input image not found: {input_path}"
            )

        image = cv2.imread(
            str(input_path),
            cv2.IMREAD_GRAYSCALE,
        )

        if image is None:
            raise ValueError(
                f"Could not read image: {input_path}"
            )

        # Light noise reduction.
        denoised = cv2.GaussianBlur(
            image,
            (3, 3),
            0,
        )

        # Local contrast enhancement.
        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8),
        )

        enhanced = clahe.apply(denoised)

        # Normalize intensity range to 0-255.
        normalized = cv2.normalize(
            enhanced,
            None,
            alpha=0,
            beta=255,
            norm_type=cv2.NORM_MINMAX,
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        success = cv2.imwrite(
            str(output_path),
            normalized,
        )

        if not success:
            raise IOError(
                f"Could not save preprocessed image: {output_path}"
            )

        return output_path