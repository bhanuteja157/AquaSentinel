from pathlib import Path
from dataclasses import dataclass
from typing import Optional


SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
}


@dataclass
class IngestedSSSFile:
    """
    Represents one SSS input file after ingestion.

    Metadata is optional because ordinary image files may not
    contain sonar navigation/depth information.
    """

    original_path: Path
    filename: str
    file_type: str

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    depth: Optional[float] = None
    timestamp: Optional[str] = None
    survey_line: Optional[str] = None

    @property
    def metadata_available(self) -> bool:
        return any(
            value is not None
            for value in [
                self.latitude,
                self.longitude,
                self.depth,
                self.timestamp,
                self.survey_line,
            ]
        )

    @property
    def metadata_status(self) -> str:
        if self.metadata_available:
            return "Metadata available"

        return "Metadata unavailable"


class IngestionService:
    """
    Handles validation and basic ingestion of SSS input files.

    This service deliberately does not perform AI inference.
    """

    def validate_file(self, file_path: Path) -> None:
        """
        Validate that the input file exists and has a supported format.
        """

        if not file_path.exists():
            raise FileNotFoundError(
                f"Input file not found: {file_path}"
            )

        if not file_path.is_file():
            raise ValueError(
                f"Input path is not a file: {file_path}"
            )

        extension = file_path.suffix.lower()

        if extension not in SUPPORTED_IMAGE_EXTENSIONS:
            supported = ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS))

            raise ValueError(
                f"Unsupported SSS file type: {extension}. "
                f"Supported image types: {supported}"
            )

    def ingest(self, file_path: Path) -> IngestedSSSFile:
        """
        Validate and create an ingestion record.

        No metadata is invented here.
        """

        self.validate_file(file_path)

        return IngestedSSSFile(
            original_path=file_path,
            filename=file_path.name,
            file_type=file_path.suffix.lower().lstrip("."),
        )