from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

try:
    import cv2
    import numpy as np
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision
except ImportError:
    cv2 = None
    np = None
    mp = None
    mp_python = None
    mp_vision = None


BASE_DIR = Path(__file__).resolve().parent.parent
HAND_MODEL_PATH = BASE_DIR / "models" / "hand_landmarker.task"

app = FastAPI(title="PalmVerse API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8088",
        "http://127.0.0.1:8088",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def detect_hand_landmarks(contents: bytes) -> dict:
    if cv2 is None or mp is None or np is None or mp_python is None or mp_vision is None:
        return {
            "available": False,
            "hand_detected": False,
            "handedness": None,
            "landmarks": [],
            "error": "mediapipe dependencies are not installed",
        }

    if not HAND_MODEL_PATH.exists():
        return {
            "available": False,
            "hand_detected": False,
            "handedness": None,
            "landmarks": [],
            "error": f"missing model file: {HAND_MODEL_PATH}",
        }

    image_buffer = np.frombuffer(contents, dtype=np.uint8)
    image = cv2.imdecode(image_buffer, cv2.IMREAD_COLOR)

    if image is None:
        return {
            "available": True,
            "hand_detected": False,
            "handedness": None,
            "landmarks": [],
            "error": "invalid image",
        }

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
    options = mp_vision.HandLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(HAND_MODEL_PATH)),
        running_mode=mp_vision.RunningMode.IMAGE,
        num_hands=1,
        min_hand_detection_confidence=0.55,
    )

    with mp_vision.HandLandmarker.create_from_options(options) as landmarker:
        result = landmarker.detect(mp_image)

    if not result.hand_landmarks:
        return {
            "available": True,
            "hand_detected": False,
            "handedness": None,
            "landmarks": [],
            "error": None,
        }

    hand_landmarks = result.hand_landmarks[0]
    handedness = None

    if result.handedness and result.handedness[0]:
        handedness = result.handedness[0][0].category_name.lower()

    return {
        "available": True,
        "hand_detected": True,
        "handedness": handedness,
        "landmarks": [
            {
                "id": index,
                "x": round(landmark.x, 6),
                "y": round(landmark.y, 6),
                "z": round(landmark.z, 6),
            }
            for index, landmark in enumerate(hand_landmarks)
        ],
        "error": None,
    }


@app.post("/api/v1/scan-palm")
async def scan_palm(
    image: Annotated[UploadFile, File()],
    user_hand: Annotated[str, Form()] = "right",
) -> dict:
    contents = await image.read()
    normalized_hand = "left" if user_hand == "left" else "right"
    hand_detection = detect_hand_landmarks(contents)

    return {
        "status": "success",
        "data": {
            "user_hand": normalized_hand,
            "processing": {
                "mode": "mediapipe_hand" if hand_detection["hand_detected"] else "manual_template",
                "mediapipe_hand_enabled": hand_detection["available"],
                "hand_detected": hand_detection["hand_detected"],
                "handedness": hand_detection["handedness"],
                "landmarks": hand_detection["landmarks"],
                "error": hand_detection["error"],
            },
            "image": {
                "filename": image.filename,
                "content_type": image.content_type,
                "size_bytes": len(contents),
            },
            "coordinate_space": {
                "width": 430,
                "height": 570,
            },
            "suggested_lines": {
                "heart_line": {
                    "label": "Heart Line",
                    "color": "#3b82f6",
                    "points": [[72, 212], [160, 182], [260, 186], [346, 212]],
                },
                "head_line": {
                    "label": "Head Line",
                    "color": "#f97316",
                    "points": [[82, 287], [168, 298], [266, 342], [344, 412]],
                },
                "life_line": {
                    "label": "Life Line",
                    "color": "#22c55e",
                    "points": [[148, 267], [105, 347], [115, 462], [190, 562]],
                },
                "fate_line": {
                    "label": "Fate Line",
                    "color": "#eab308",
                    "points": [[225, 562], [224, 447], [230, 332], [236, 257]],
                },
            },
            "analysis": {
                "heart_line": {
                    "type_id": "heart_balance_01",
                    "title": "เส้นหัวใจแห่งความสมดุล",
                    "description": "เส้นหัวใจของคุณบ่งบอกถึงมุมมองความรักที่มั่นคง จริงใจ มีเหตุผล และให้เกียรติคนรัก",
                },
                "head_line": {
                    "type_id": "head_analytical_creative",
                    "title": "เส้นสมองนักคิดเชิงกลยุทธ์",
                    "description": "เส้นสมองของคุณสะท้อนการคิดเป็นระบบ พร้อมพลังจินตนาการและความสามารถในการปรับมุมมอง",
                },
                "life_line": {
                    "type_id": "life_energetic_travel",
                    "title": "Life Line เปี่ยมพลังและการเดินทาง",
                    "description": "เส้นชีวิตสื่อถึงพลังพื้นฐานที่ดี ความกระตือรือร้น และโอกาสในการเดินทางหรือเปลี่ยนสภาพแวดล้อม",
                },
            },
        },
    }
