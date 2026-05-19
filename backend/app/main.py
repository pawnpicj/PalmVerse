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
        {
            "type_id": "heart_warm_dialogue_05",
            "title": "เส้นหัวใจนักสื่อสารอบอุ่น",
            "description": "คุณต้องการความรักที่พูดคุยกันได้ทุกเรื่อง ไม่ชอบปล่อยให้ความเงียบกลายเป็นกำแพง จุดเด่นคือการอธิบายความรู้สึกอย่างนุ่มนวล หากฝึกฟังโดยไม่รีบแก้ปัญหา ความสัมพันธ์จะลึกและมั่นคงขึ้น",
        },
        {
            "type_id": "heart_slow_trust_06",
            "title": "เส้นหัวใจค่อยเป็นค่อยไป",
            "description": "คุณไม่ได้เปิดใจง่าย แต่เมื่อเชื่อใจแล้วจะจริงจังและซื่อสัตย์มาก ความรักของคุณเติบโตจากเวลา การกระทำสม่ำเสมอ และความปลอดภัยทางใจ ระวังคาดหวังให้คนอื่นเข้าใจโดยไม่บอกความต้องการของตัวเอง",
        },
        {
            "type_id": "heart_romantic_vision_07",
            "title": "เส้นหัวใจโรแมนติกมีภาพฝัน",
            "description": "คุณมีมุมอ่อนไหวและมองความรักเป็นแรงบันดาลใจ ชอบความใส่ใจเล็กๆ ที่ทำให้รู้สึกพิเศษ จุดที่ควรระวังคือการคาดหวังสูงเกินจริง ความรักจะดีเมื่อภาพฝันเดินคู่กับการคุยเรื่องจริงในชีวิตประจำวัน",
        },
        {
            "type_id": "heart_clear_boundary_08",
            "title": "เส้นหัวใจขอบเขตชัดเจน",
            "description": "คุณรักได้เต็มที่เมื่อมีพื้นที่และความเคารพซึ่งกันและกัน คุณไม่เหมาะกับความสัมพันธ์ที่คลุมเครือหรือดึงพลังใจมากเกินไป การตั้งขอบเขตไม่ได้ทำให้รักน้อยลง แต่ช่วยให้รักเติบโตอย่างสบายใจ",
        },
        {
            "type_id": "heart_healing_09",
            "title": "เส้นหัวใจเยียวยา",
            "description": "คุณมีพลังปลอบโยนคนรอบตัว และมักเป็นที่พึ่งทางใจให้คนสำคัญ ความรักของคุณมีความเมตตาสูง แต่ต้องไม่ลืมว่าคุณไม่จำเป็นต้องรักษาทุกบาดแผลของคนอื่น เลือกความสัมพันธ์ที่ดูแลคุณกลับด้วย",
        },
        {
            "type_id": "heart_brave_honest_10",
            "title": "เส้นหัวใจซื่อตรงกล้ารัก",
            "description": "คุณเป็นคนรักชัดเจน ตรงไปตรงมา และไม่ชอบเกมทางอารมณ์ เมื่อรู้สึกจริงจะพร้อมแสดงออกผ่านการกระทำ จุดแข็งคือความจริงใจ จุดที่ต้องระวังคือการพูดตรงเกินไปในเวลาที่อีกฝ่ายยังอ่อนไหว",
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
        {
            "type_id": "head_fast_connector_05",
            "title": "เส้นสมองเชื่อมโยงไว",
            "description": "คุณจับความสัมพันธ์ของข้อมูลได้เร็ว มองเห็นแพทเทิร์นที่คนอื่นอาจมองข้าม เหมาะกับงานที่ต้องวิเคราะห์ภาพรวมและแปลเรื่องยากให้เข้าใจง่าย ระวังคิดเร็วเกินจนข้ามรายละเอียดสำคัญบางจุด",
        },
        {
            "type_id": "head_deep_researcher_06",
            "title": "เส้นสมองนักค้นลึก",
            "description": "คุณไม่พอใจกับคำตอบผิวเผิน ชอบขุดหาสาเหตุและโครงสร้างที่อยู่เบื้องหลัง เหมาะกับงานวิจัย วิเคราะห์ วางแผน หรือแก้ปัญหาซับซ้อน หากจัดเวลาพักสมองดีๆ ความคิดจะเฉียบคมมากขึ้น",
        },
        {
            "type_id": "head_creative_story_07",
            "title": "เส้นสมองนักเล่าเรื่อง",
            "description": "คุณมีพรสวรรค์ในการจัดความคิดให้มีภาพ มีอารมณ์ และสื่อสารกับคนได้ดี เหมาะกับงานคอนเทนต์ การออกแบบ การสอน หรือการนำเสนอ จุดแข็งคือทำให้ข้อมูลธรรมดากลายเป็นสิ่งที่คนจดจำได้",
        },
        {
            "type_id": "head_calm_decision_08",
            "title": "เส้นสมองตัดสินใจนิ่ง",
            "description": "คุณมักไม่ตื่นตามกระแสง่ายๆ ก่อนตัดสินใจจะชั่งน้ำหนักและดูความเสี่ยงรอบด้าน เหมาะกับบทบาทที่ต้องถือความรับผิดชอบสูง จุดที่ควรระวังคืออย่ารอความมั่นใจเต็มร้อยจนโอกาสดีผ่านไป",
        },
        {
            "type_id": "head_experimenter_09",
            "title": "เส้นสมองนักทดลอง",
            "description": "คุณเรียนรู้ดีที่สุดจากการลงมือ ลอง ปรับ และสังเกตผลจริง ความคิดของคุณยืดหยุ่นและไม่ติดกรอบเดิม เหมาะกับงานสร้างผลิตภัณฑ์ งานเทคนิค หรือสิ่งที่ต้องแก้ปัญหาหน้างานอย่างต่อเนื่อง",
        },
        {
            "type_id": "head_people_strategy_10",
            "title": "เส้นสมองอ่านคนอ่านเกม",
            "description": "คุณเข้าใจแรงจูงใจของคนและมองเกมความสัมพันธ์ในทีมได้ดี เหมาะกับการเจรจา บริหารคน หรือประสานงานหลายฝ่าย หากใช้ความสามารถนี้ด้วยความตรงไปตรงมา คุณจะเป็นคนที่คนอื่นไว้ใจมาก",
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
        {
            "type_id": "life_steady_growth_05",
            "title": "เส้นชีวิตเติบโตสม่ำเสมอ",
            "description": "จังหวะชีวิตของคุณเด่นเรื่องการสะสมทีละขั้น ไม่จำเป็นต้องพุ่งเร็วแต่ไปได้ไกลเมื่อมีระบบและวินัย สิ่งสำคัญคือเลือกเป้าหมายที่คุ้มค่ากับเวลา เพราะพลังของคุณเหมาะกับเกมระยะยาว",
        },
        {
            "type_id": "life_new_chapter_06",
            "title": "เส้นชีวิตเปิดบทใหม่",
            "description": "คุณมีเกณฑ์เปลี่ยนจังหวะชีวิตจากการเรียนรู้สิ่งใหม่ ย้ายบริบท หรือรับบทบาทที่ไม่คุ้นเคย ช่วงเริ่มต้นอาจเหนื่อย แต่เมื่อจับทางได้ คุณจะพบตัวตนเวอร์ชันที่มั่นใจกว่าเดิม",
        },
        {
            "type_id": "life_social_energy_07",
            "title": "เส้นชีวิตเติมพลังจากผู้คน",
            "description": "พลังชีวิตของคุณมักดีขึ้นเมื่ออยู่ในสภาพแวดล้อมที่มีคนสนับสนุนและแลกเปลี่ยนกัน คุณเหมาะกับชุมชน ทีม หรือโปรเจกต์ที่ได้ร่วมมือ ระวังรับพลังของคนรอบตัวมากเกินจนลืมจังหวะของตัวเอง",
        },
        {
            "type_id": "life_quiet_power_08",
            "title": "เส้นชีวิตพลังเงียบ",
            "description": "คุณอาจไม่ใช่คนแสดงออกแรงตลอดเวลา แต่มีพลังภายในที่มั่นคงและอึดกว่าที่เห็น เหมาะกับการสร้างผลงานเงียบๆ แล้วให้ผลลัพธ์พูดแทน จุดแข็งคือความสม่ำเสมอและความละเอียดในสิ่งที่ทำ",
        },
        {
            "type_id": "life_balance_keeper_09",
            "title": "เส้นชีวิตผู้รักษาสมดุล",
            "description": "ชีวิตของคุณดีขึ้นเมื่อจัดสมดุลระหว่างงาน ความสัมพันธ์ และเวลาส่วนตัว หากด้านใดด้านหนึ่งกินพื้นที่มากเกินไป พลังจะตกเร็วกว่าปกติ การวางตารางพักไม่ใช่ความขี้เกียจ แต่เป็นกลยุทธ์สำคัญของคุณ",
        },
        {
            "type_id": "life_bold_restart_10",
            "title": "เส้นชีวิตกล้าเริ่มใหม่",
            "description": "คุณมีความสามารถในการตัดสินใจเปลี่ยนทางเมื่อรู้ว่าสิ่งเดิมไม่ตอบโจทย์ แม้การเริ่มใหม่จะทำให้คนอื่นกังวล แต่สำหรับคุณมันคือการคืนพลังให้ชีวิต หากเตรียมแผนรองรับดี จะเปลี่ยนผ่านได้อย่างสง่างาม",
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
        {
            "type_id": "fate_craft_mastery_04",
            "title": "เส้นวาสนาจากความเชี่ยวชาญ",
            "description": "วาสนาของคุณเด่นเมื่อยอมลงลึกกับทักษะใดทักษะหนึ่งจนเป็นของจริง โอกาสสำคัญมักมาเมื่อคนเห็นคุณภาพงานและความน่าเชื่อถือ การฝึกฝนซ้ำๆ จะกลายเป็นประตูที่เปิดกว้างในอนาคต",
        },
        {
            "type_id": "fate_public_voice_05",
            "title": "เส้นวาสนาเสียงของตัวเอง",
            "description": "คุณมีโอกาสเติบโตจากการแสดงมุมมอง ความคิด หรือผลงานให้คนเห็นมากขึ้น ไม่จำเป็นต้องดังทันที แต่การสื่อสารอย่างสม่ำเสมอจะพาคนและโอกาสที่ตรงทางเข้ามาใกล้",
        },
        {
            "type_id": "fate_crossroad_choice_06",
            "title": "เส้นวาสนาทางแยกสำคัญ",
            "description": "ชีวิตคุณมีจุดที่ต้องเลือกเส้นทางมากกว่าหนึ่งครั้ง ทางที่ใช่อาจไม่ใช่ทางที่ง่ายที่สุด แต่จะให้พื้นที่เติบโตมากกว่าเดิม ให้ดูทั้งเหตุผล ความรู้สึก และผลระยะยาวก่อนตัดสินใจ",
        },
        {
            "type_id": "fate_team_builder_07",
            "title": "เส้นวาสนาผู้สร้างทีม",
            "description": "โอกาสของคุณเด่นเมื่อได้รวมคนที่มีความสามารถต่างกันให้เดินไปทางเดียวกัน คุณอาจไม่ได้ชนะด้วยการทำทุกอย่างเอง แต่ชนะด้วยการจัดบทบาท สร้างความไว้ใจ และทำให้คนอยากร่วมมือ",
        },
        {
            "type_id": "fate_hidden_opportunity_08",
            "title": "เส้นวาสนาโอกาสที่ซ่อนอยู่",
            "description": "บางโอกาสของคุณไม่ได้มาแบบเสียงดัง แต่มาในรูปของงานเล็ก คนรู้จัก หรือคำชวนที่ดูธรรมดา หากสังเกตสัญญาณให้ดี สิ่งเล็กๆ อาจต่อยอดเป็นทางใหญ่กว่าที่คาด",
        },
        {
            "type_id": "fate_independent_path_09",
            "title": "เส้นวาสนาเส้นทางอิสระ",
            "description": "คุณเหมาะกับเส้นทางที่มีอิสระในการตัดสินใจและออกแบบวิธีทำงานของตัวเอง ยิ่งคุณรู้จุดแข็งและตั้งมาตรฐานชัด โอกาสจะยิ่งวิ่งเข้าหา ระวังเพียงอย่าแบกทุกอย่างไว้คนเดียว",
        },
        {
            "type_id": "fate_late_bloom_10",
            "title": "เส้นวาสนาเบ่งบานตามเวลา",
            "description": "ความสำเร็จของคุณอาจไม่ได้มาเร็วที่สุด แต่มีแนวโน้มมั่นคงและชัดขึ้นเมื่อประสบการณ์ตกผลึก สิ่งที่เคยดูเป็นทางอ้อมจะกลายเป็นทุนชีวิตสำคัญ อย่าเร่งตัวเองจนลืมเห็นพัฒนาการที่เกิดขึ้นแล้ว",
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
