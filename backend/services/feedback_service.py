from pathlib import Path
import json
from typing import Any


class FeedbackService:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.storage_path.exists():
            self.storage_path.write_text("[]", encoding="utf-8")

    def get_all(self) -> list[dict[str, Any]]:
        try:
            data = json.loads(
                self.storage_path.read_text(encoding="utf-8")
            )

            if isinstance(data, list):
                return data

            return []

        except (json.JSONDecodeError, OSError):
            return []

    def save(self, record: dict[str, Any]) -> dict[str, Any]:
        records = self.get_all()

        detection_index = record.get("detectionIndex")

        # During the current prototype workflow, one detection should
        # have one current human-verification record. If that detection
        # already exists, update it instead of appending another record.
        if detection_index is not None:
            matching_indexes = [
                index
                for index, existing in enumerate(records)
                if existing.get("detectionIndex") == detection_index
                and existing.get("aiClass") == record.get("aiClass")
                and existing.get("aiConfidence") == record.get("aiConfidence")
            ]

            if matching_indexes:
                # Replace the first matching record and remove older
                # duplicates created by the previous append-only version.
                first_index = matching_indexes[0]
                records[first_index] = record

                records = [
                    existing
                    for index, existing in enumerate(records)
                    if index == first_index or index not in matching_indexes[1:]
                ]
            else:
                records.append(record)
        else:
            records.append(record)

        self.storage_path.write_text(
            json.dumps(records, indent=2),
            encoding="utf-8",
        )

        return record
