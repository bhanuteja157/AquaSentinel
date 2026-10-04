from pathlib import Path

import torch
from ultralytics import YOLO


class AIService:
    def __init__(self, model_path: Path):
        self.model_path = model_path

        self.device = (
            0 if torch.cuda.is_available() else "cpu"
        )

        self.device_name = (
            torch.cuda.get_device_name(0)
            if torch.cuda.is_available()
            else "CPU"
        )

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {self.model_path}"
            )

        print("Loading YOLO model...")
        print(f"Model path : {self.model_path}")
        print(f"Device     : {self.device_name}")

        self.model = YOLO(str(self.model_path))

        print("YOLO model loaded successfully.")

    def get_info(self) -> dict:
        """
        Return information about the loaded AI model
        and the inference configuration.
        """

        return {
            "model_path": str(self.model_path),
            "task": self.model.task,
            "input_size": 640,
            "confidence_threshold": 0.10,
            "device": self.device_name,
            "classes": self.model.names,
        }

    def analyze(
        self,
        input_path: Path,
        annotated_path: Path,
    ) -> list[dict]:

        results = self.model.predict(
            source=str(input_path),
            imgsz=640,
            conf=0.10,
            device=self.device,
            verbose=False,
        )

        result = results[0]

        result.save(
            filename=str(annotated_path)
        )

        detections = []

        if result.boxes is not None:
            for box in result.boxes:

                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                coordinates = box.xyxy[0].tolist()

                detections.append(
                    {
                        "class": result.names[class_id],
                        "confidence": round(
                            confidence,
                            4,
                        ),
                        "bbox": [
                            round(float(coordinates[0]), 2),
                            round(float(coordinates[1]), 2),
                            round(float(coordinates[2]), 2),
                            round(float(coordinates[3]), 2),
                        ],
                    }
                )

        return detections