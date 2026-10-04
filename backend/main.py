from pathlib import Path
import shutil
import uuid

import torch

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from pydantic import BaseModel

from backend.services.ai_service import AIService
from backend.services.ingestion_service import IngestionService

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = BASE_DIR / "ai" / "weights" / "best_detector.pt"

UPLOAD_DIR = BASE_DIR / "backend" / "uploads"

OUTPUT_DIR = BASE_DIR / "backend" / "outputs"

DETECTION_DIR = OUTPUT_DIR / "detections"

REPORT_DIR = OUTPUT_DIR / "reports"


# ============================================================
# CREATE DIRECTORIES
# ============================================================

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DETECTION_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="AquaSentinel API",
    description="AI-powered Side-Scan Sonar anomaly detection API",
    version="0.2.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# AI SERVICE
# ============================================================

print("=" * 60)
print("AquaSentinel Backend")
print("=" * 60)

print(f"Model path : {MODEL_PATH}")
print(f"CUDA       : {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"GPU        : {torch.cuda.get_device_name(0)}")

print("\nLoading YOLO AI service...")

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH}"
    )

ai_service = AIService(MODEL_PATH)

ingestion_service = IngestionService()

print("AI service loaded successfully.")


# ============================================================
# REPORT DATA MODEL
# ============================================================

class ReportRequest(BaseModel):
    filename: str
    detections: list[dict]
    detection_count: int
    device: str
    confirmed_count: int
    rejected_count: int
    review_count: int

    mission_latitude: float = 13.3457
    mission_longitude: float = 77.1012


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "project": "AquaSentinel",
        "status": "running",
        "device": (
            torch.cuda.get_device_name(0)
            if torch.cuda.is_available()
            else "CPU"
        ),
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    model_info = ai_service.get_info()

    return {
        "status": "healthy",
        "model_loaded": ai_service is not None,
        "cuda_available": torch.cuda.is_available(),
        "model": model_info,
    }


# ============================================================
# GET ANNOTATED IMAGE
# ============================================================

@app.get("/outputs/{filename}")
def get_output_image(filename: str):

    safe_filename = Path(filename).name

    image_path = DETECTION_DIR / safe_filename

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Annotated image not found.",
        )

    return FileResponse(image_path)


# ============================================================
# DOWNLOAD ANNOTATED IMAGE
# ============================================================

@app.get("/download-output/{filename}")
def download_output_image(filename: str):

    safe_filename = Path(filename).name

    image_path = DETECTION_DIR / safe_filename

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Annotated image not found.",
        )

    return FileResponse(
        image_path,
        media_type="image/jpeg",
        filename=f"aquasentinel_annotated_{safe_filename}",
    )


# ============================================================
# AI ANALYSIS
# ============================================================

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):

    # --------------------------------------------------------
    # Original filename
    # --------------------------------------------------------

    original_name = file.filename or "uploaded_image"

    extension = Path(original_name).suffix.lower()

    # --------------------------------------------------------
    # Allowed image formats
    # --------------------------------------------------------

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
    }

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image format.",
        )

    # --------------------------------------------------------
    # Generate unique filenames
    # --------------------------------------------------------

    file_id = uuid.uuid4().hex

    input_filename = f"{file_id}{extension}"

    input_path = UPLOAD_DIR / input_filename

    annotated_filename = f"{file_id}.jpg"

    annotated_path = DETECTION_DIR / annotated_filename

    # --------------------------------------------------------
    # Save uploaded image
    # --------------------------------------------------------

    try:

        with input_path.open("wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        # Validate and register the ingested SSS file
        ingestion = ingestion_service.ingest(
            input_path
        )

    except (FileNotFoundError, ValueError) as error:

        if input_path.exists():
            input_path.unlink()

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        if input_path.exists():
            input_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Could not save uploaded image: {error}",
        )

    # --------------------------------------------------------
    # AI inference
    # --------------------------------------------------------

    try:

        detections = ai_service.analyze(
            input_path=input_path,
            annotated_path=annotated_path,
        )

    except Exception as error:

        if input_path.exists():
            input_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"AI inference failed: {error}",
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "filename": original_name,
        "file_type": ingestion.file_type,
        "metadata_status": ingestion.metadata_status,
        "detections": detections,
        "detection_count": len(detections),
        "annotated_image": f"/outputs/{annotated_filename}",
        "device": (
            torch.cuda.get_device_name(0)
            if torch.cuda.is_available()
            else "CPU"
        ),
    }


# ============================================================
# PDF REPORT
# ============================================================

@app.post("/generate-report")
def generate_report(request: ReportRequest):

    report_id = uuid.uuid4().hex

    report_filename = (
        f"aquasentinel_report_{report_id}.pdf"
    )

    report_path = REPORT_DIR / report_filename

    document = SimpleDocTemplate(
        str(report_path),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    story = []

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "AquaSentinel",
            styles["Title"],
        )
    )

    story.append(
        Paragraph(
            "AI-Powered Underwater Marine "
            "Debris & Anomaly Detection",
            styles["Heading2"],
        )
    )

    story.append(Spacer(1, 20))

    # --------------------------------------------------------
    # Mission information
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Mission Analysis Report",
            styles["Heading2"],
        )
    )

    story.append(Spacer(1, 10))

    mission_data = [
        ["Parameter", "Value"],
        [
            "Sonar Image",
            request.filename,
        ],
        [
            "Total Detections",
            str(request.detection_count),
        ],
        [
            "Inference Device",
            request.device,
        ],
        [
            "Confirmed",
            str(request.confirmed_count),
        ],
        [
            "Rejected",
            str(request.rejected_count),
        ],
        [
            "Needs Review",
            str(request.review_count),
        ],
        [
            "Mission Latitude",
            f"{request.mission_latitude:.6f}",
        ],
        [
            "Mission Longitude",
            f"{request.mission_longitude:.6f}",
        ],
    ]

    table = Table(
        mission_data,
        colWidths=[180, 300],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#0f172a"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, -1),
                    colors.whitesmoke,
                ),
            ]
        )
    )

    story.append(table)

    story.append(Spacer(1, 25))

    # --------------------------------------------------------
    # Detection results
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "AI Detection Results",
            styles["Heading2"],
        )
    )

    story.append(Spacer(1, 10))

    if request.detections:

        detection_data = [
            [
                "Detection",
                "Class",
                "Confidence",
                "Bounding Box",
            ]
        ]

        for index, detection in enumerate(
            request.detections,
            start=1,
        ):

            detection_class = str(
                detection.get(
                    "class",
                    "Unknown",
                )
            )

            confidence = float(
                detection.get(
                    "confidence",
                    0,
                )
            )

            bbox = detection.get(
                "bbox",
                [],
            )

            bbox_text = ", ".join(
                str(round(float(value), 1))
                for value in bbox
            )

            detection_data.append(
                [
                    str(index),
                    detection_class.replace(
                        "_",
                        " ",
                    ).title(),
                    f"{confidence * 100:.1f}%",
                    bbox_text,
                ]
            )

        detection_table = Table(
            detection_data,
            colWidths=[
                55,
                120,
                90,
                215,
            ],
        )

        detection_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#0f172a"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                ]
            )
        )

        story.append(detection_table)

    else:

        story.append(
            Paragraph(
                "No target anomalies were detected.",
                styles["BodyText"],
            )
        )

    story.append(Spacer(1, 25))

    # --------------------------------------------------------
    # Disclaimer
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "<b>Important:</b> Mission coordinates shown "
            "in this prototype report are simulated "
            "demonstration coordinates unless supplied "
            "from actual mission or sonar metadata.",
            styles["BodyText"],
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            "Recovery priority is a prototype "
            "decision-support indicator derived from "
            "AI detection confidence. It is not an "
            "official ecological-risk assessment.",
            styles["BodyText"],
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "AquaSentinel Prototype • SIH 2026",
            styles["BodyText"],
        )
    )

    # --------------------------------------------------------
    # Build PDF
    # --------------------------------------------------------

    try:

        document.build(story)

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Could not generate PDF report: {error}",
        )

    return {
        "status": "success",
        "report": f"/reports/{report_filename}",
        "filename": report_filename,
    }


# ============================================================
# PDF FILE DOWNLOAD
# ============================================================

@app.get("/reports/{filename}")
def get_report(filename: str):

    safe_filename = Path(filename).name

    report_path = REPORT_DIR / safe_filename

    if not report_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Report not found.",
        )

    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=safe_filename,
    )