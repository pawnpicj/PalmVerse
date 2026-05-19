import hashlib
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

READING_LIBRARY = {
    "heart_line": [
        {
            "type_id": "heart_balance_01",
            "title": "เส้นหัวใจแห่งความสมดุล",
            "description": "คุณมองความรักด้วยความมั่นคง จริงใจ และให้เกียรติความรู้สึกของอีกฝ่าย ความสัมพันธ์ที่ดีสำหรับคุณคือความสัมพันธ์ที่มีทั้งเหตุผลและความอบอุ่น",
        },
        {
            "type_id": "heart_deep_feeling_02",
            "title": "เส้นหัวใจแห่งความรู้สึกลึกซึ้ง",
            "description": "คุณเป็นคนรับรู้ความรู้สึกละเอียด มีความผูกพันลึกกับคนสำคัญ และมักทุ่มเทกับความสัมพันธ์เมื่อไว้ใจแล้ว จุดแข็งคือความจริงใจ แต่ควรเว้นพื้นที่ให้ตัวเองพักใจด้วย",
        },
        {
            "type_id": "heart_independent_03",
            "title": "เส้นหัวใจรักอิสระ",
            "description": "คุณรักแบบมีพื้นที่ของตัวเอง ไม่ชอบถูกเร่งหรือบังคับ ความสัมพันธ์ที่เหมาะคือคนที่คุยกันตรงไปตรงมา เคารพเส้นแบ่ง และเดินไปด้วยกันโดยไม่กดดัน",
        },
        {
            "type_id": "heart_protective_04",
            "title": "เส้นหัวใจผู้ปกป้อง",
            "description": "คุณมีแนวโน้มดูแลคนรักและคนใกล้ตัวอย่างจริงจัง บางครั้งรับภาระความรู้สึกของคนอื่นมากเกินไป หากบาลานซ์การให้กับการรับได้ ความรักจะมั่นคงมาก",
        },
    ],
    "head_line": [
        {
            "type_id": "head_analytical_creative",
            "title": "เส้นสมองนักคิดเชิงกลยุทธ์",
            "description": "คุณคิดเป็นระบบ มองเห็นทางเลือกหลายทาง และมีพลังในการแก้ปัญหาเฉพาะหน้า จุดเด่นคือการผสมเหตุผลกับจินตนาการได้ดี",
        },
        {
            "type_id": "head_practical_02",
            "title": "เส้นสมองนักลงมือทำ",
            "description": "คุณเหมาะกับงานที่ต้องเห็นผลจริง ชอบตัดสินใจจากข้อมูลที่จับต้องได้ และมักทำให้เรื่องซับซ้อนกลายเป็นขั้นตอนที่จัดการได้",
        },
        {
            "type_id": "head_intuitive_03",
            "title": "เส้นสมองสัญชาตญาณไว",
            "description": "คุณอ่านบรรยากาศและเจตนาของคนได้ไว มีเซนส์กับจังหวะและโอกาส แต่ควรตรวจข้อมูลสำคัญอีกชั้นก่อนตัดสินใจเรื่องใหญ่",
        },
        {
            "type_id": "head_focus_builder_04",
            "title": "เส้นสมองผู้สร้างระบบ",
            "description": "คุณมีพลังโฟกัสเมื่อเจอเป้าหมายที่ชัดเจน เหมาะกับการสร้างสิ่งที่ต้องใช้ความต่อเนื่อง วางโครง และค่อยๆ ปรับให้แข็งแรง",
        },
    ],
    "life_line": [
        {
            "type_id": "life_energetic_travel",
            "title": "Life Line เปี่ยมพลังและการเดินทาง",
            "description": "คุณมีพลังชีวิตดีและมักเติบโตเมื่อได้เจอสภาพแวดล้อมใหม่ การเดินทาง ย้ายที่ หรือเปลี่ยนบทบาทอาจเปิดโอกาสสำคัญให้คุณ",
        },
        {
            "type_id": "life_grounded_02",
            "title": "เส้นชีวิตมั่นคงและค่อยเป็นค่อยไป",
            "description": "คุณเป็นคนสร้างฐานชีวิตได้ดี ชอบความแน่นอน และเก่งกับการสะสมผลลัพธ์ระยะยาว ความสำเร็จของคุณมักมาจากวินัยมากกว่าโชคชั่วคราว",
        },
        {
            "type_id": "life_adaptive_03",
            "title": "เส้นชีวิตนักปรับตัว",
            "description": "คุณรับมือการเปลี่ยนแปลงได้ดี แม้บางช่วงจะเหมือนต้องเริ่มใหม่ แต่คุณมีความสามารถในการเรียนรู้เร็วและหาทางรอดจากข้อจำกัด",
        },
        {
            "type_id": "life_resilient_04",
            "title": "เส้นชีวิตใจแกร่ง",
            "description": "คุณผ่านแรงกดดันได้มากกว่าที่ตัวเองคิด จุดแข็งคือความอดทนและการกลับมาตั้งหลักได้ไว เมื่อมีเป้าหมายที่ใช่ คุณจะไปได้ไกล",
        },
    ],
    "fate_line": [
        {
            "type_id": "fate_self_made_01",
            "title": "เส้นวาสนาสร้างทางเอง",
            "description": "เส้นทางของคุณเด่นเรื่องการสร้างโอกาสด้วยตัวเอง ไม่จำเป็นต้องเดินตามสูตรเดิม หากกล้าจัดระบบชีวิตและเลือกสนามที่ถนัด วาสนาจะเปิดจากการลงมือ",
        },
        {
            "type_id": "fate_turning_point_02",
            "title": "เส้นวาสนาจุดเปลี่ยน",
            "description": "ชีวิตมีจังหวะเปลี่ยนทางที่สำคัญเป็นระยะ การตัดสินใจบางครั้งอาจดูเสี่ยง แต่ถ้าคุณเตรียมข้อมูลดี จุดเปลี่ยนนั้นจะกลายเป็นโอกาส",
        },
        {
            "type_id": "fate_support_03",
            "title": "เส้นวาสนาจากผู้สนับสนุน",
            "description": "คุณมีเกณฑ์เติบโตผ่านเครือข่าย คนแนะนำ หรือทีมที่ดี การเลือกคนร่วมทางจึงสำคัญมาก เพราะคนที่ใช่จะช่วยเร่งจังหวะความสำเร็จ",
        },
    ],
}

app = FastAPI(title="PalmVerse API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8088",
        "http://127.0.0.1:8088",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
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
    try:
        rgb_image = np.ascontiguousarray(rgb_image)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        options = mp_vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(HAND_MODEL_PATH)),
            running_mode=mp_vision.RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.55,
        )

        with mp_vision.HandLandmarker.create_from_options(options) as landmarker:
            result = landmarker.detect(mp_image)
    except Exception as exc:
        return {
            "available": True,
            "hand_detected": False,
            "handedness": None,
            "landmarks": [],
            "error": f"mediapipe detection failed: {type(exc).__name__}: {exc}",
        }

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


def extract_image_features(contents: bytes, hand_detection: dict) -> dict:
    features = {
        "brightness": 0.0,
        "contrast": 0.0,
        "edge_density": 0.0,
        "palm_spread": 0.0,
        "image_valid": False,
    }

    if cv2 is not None and np is not None:
        image_buffer = np.frombuffer(contents, dtype=np.uint8)
        image = cv2.imdecode(image_buffer, cv2.IMREAD_GRAYSCALE)

        if image is not None:
            edges = cv2.Canny(image, 80, 160)
            features.update(
                {
                    "brightness": round(float(image.mean()), 3),
                    "contrast": round(float(image.std()), 3),
                    "edge_density": round(float((edges > 0).mean()), 6),
                    "image_valid": True,
                }
            )

    landmarks = hand_detection.get("landmarks") or []
    if landmarks:
        xs = [point["x"] for point in landmarks]
        ys = [point["y"] for point in landmarks]
        features["palm_spread"] = round((max(xs) - min(xs)) * (max(ys) - min(ys)), 6)

    return features


def stable_index(seed: str, salt: str, modulo: int) -> int:
    digest = hashlib.sha256(f"{seed}:{salt}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % modulo


def build_reading(contents: bytes, user_hand: str, hand_detection: dict) -> dict:
    features = extract_image_features(contents, hand_detection)
    image_hash = hashlib.sha256(contents).hexdigest()
    seed = "|".join(
        [
            image_hash,
            user_hand,
            str(len(contents)),
            str(features["brightness"]),
            str(features["contrast"]),
            str(features["edge_density"]),
            str(features["palm_spread"]),
            str(hand_detection.get("handedness")),
        ]
    )

    analysis = {}
    for line_name, readings in READING_LIBRARY.items():
        analysis[line_name] = readings[stable_index(seed, line_name, len(readings))]

    return {
        "engine": "deterministic_image_v1",
        "image_hash": image_hash[:16],
        "features": features,
        "analysis": analysis,
    }


@app.post("/api/v1/scan-palm")
async def scan_palm(
    image: Annotated[UploadFile, File()],
    user_hand: Annotated[str, Form()] = "right",
) -> dict:
    contents = await image.read()
    normalized_hand = "left" if user_hand == "left" else "right"
    hand_detection = detect_hand_landmarks(contents)
    reading = build_reading(contents, normalized_hand, hand_detection)

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
            "reading_engine": {
                "name": reading["engine"],
                "image_hash": reading["image_hash"],
                "features": reading["features"],
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
            "analysis": reading["analysis"],
        },
    }
