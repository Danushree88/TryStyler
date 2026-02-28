import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import cv2
import numpy as np
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions
from mediapipe.tasks.python.core.base_options import BaseOptions
import urllib.request

tryon_bp = Blueprint("tryon", __name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "tryon_uploads")
RESULT_FOLDER = os.path.join(os.getcwd(), "static", "tryon_results")
MODELS_FOLDER = os.path.join(os.getcwd(), "models")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
os.makedirs(MODELS_FOLDER, exist_ok=True)

ALLOWED_EXT = {"jpg", "jpeg", "png"}
MODEL_PATH = os.path.join(MODELS_FOLDER, "face_landmarker.task")

# Download model if not present
if not os.path.exists(MODEL_PATH):
    print("Downloading face_landmarker.task model...")
    urllib.request.urlretrieve(
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
        MODEL_PATH
    )
    print("Model downloaded.")

def allowed_file(fname):
    return "." in fname and fname.rsplit(".", 1)[1].lower() in ALLOWED_EXT

@tryon_bp.route("/tryon", methods=["POST"])
def tryon():
    if "image" not in request.files:
        return jsonify({"error": "No image in request"}), 400

    file = request.files["image"]
    accessory_path = request.form.get("accessory_path")
    if not accessory_path:
        return jsonify({"error": "Missing accessory_path"}), 400

    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid image"}), 400

    fname = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, fname)
    file.save(input_path)

    accessory_full = os.path.join(os.getcwd(), "static", accessory_path)

    try:
        output_rel = apply_glasses_tryon(input_path, accessory_full)
    except Exception as e:
        print("Try-on error:", e)
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "message": "Try-on successful",
        "result_path": f"/static/tryon_results/{output_rel}"
    })


def remove_white_background(img_bgra):
    bgr = img_bgra[:, :, :3]
    white_mask = (bgr[:, :, 0] > 200) & (bgr[:, :, 1] > 200) & (bgr[:, :, 2] > 200)
    img_bgra[white_mask, 3] = 0
    return img_bgra


def apply_glasses_tryon(face_img_path, glasses_png_path):
    face_img = cv2.imread(face_img_path, cv2.IMREAD_UNCHANGED)
    glasses_png = cv2.imread(glasses_png_path, cv2.IMREAD_UNCHANGED)

    if face_img is None or glasses_png is None:
        raise ValueError(f"Could not load images. Face: {face_img_path}, Glasses: {glasses_png_path}")

    if face_img.ndim == 3 and face_img.shape[2] == 4:
        face_img = cv2.cvtColor(face_img, cv2.COLOR_BGRA2BGR)

    h_img, w_img = face_img.shape[:2]

    # --- MediaPipe new Tasks API ---
    options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        num_faces=1
    )

    with FaceLandmarker.create_from_options(options) as landmarker:
        rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_image)

    if not result.face_landmarks:
        raise ValueError("No face detected")

    landmarks = result.face_landmarks[0]

    def lm(idx):
        pt = landmarks[idx]
        return int(pt.x * w_img), int(pt.y * h_img)

    # Precise landmark indices
    left_eye_outer  = lm(33)
    left_eye_inner  = lm(133)
    right_eye_inner = lm(362)
    right_eye_outer = lm(263)
    left_temple     = lm(234)
    right_temple    = lm(454)

    # Glasses width = temple to temple
    glasses_width = int(abs(right_temple[0] - left_temple[0]) * 1.05)

    scale = glasses_width / glasses_png.shape[1]
    glasses_height = int(glasses_png.shape[0] * scale)

    glasses_resized = cv2.resize(glasses_png, (glasses_width, glasses_height), interpolation=cv2.INTER_AREA)

    # Add alpha channel if missing
    if glasses_resized.ndim == 2:
        glasses_resized = cv2.cvtColor(glasses_resized, cv2.COLOR_GRAY2BGRA)
    elif glasses_resized.shape[2] == 3:
        glasses_resized = cv2.cvtColor(glasses_resized, cv2.COLOR_BGR2BGRA)

    glasses_resized = remove_white_background(glasses_resized)

    # Position centered on temples, vertically at eye center
    center_x = (left_temple[0] + right_temple[0]) // 2
    eye_center_y = (left_eye_outer[1] + left_eye_inner[1] +
                    right_eye_inner[1] + right_eye_outer[1]) // 4

    top_left_x = center_x - glasses_width // 2
    top_left_y = eye_center_y - glasses_height // 2

    overlay_image(face_img, glasses_resized, top_left_x, top_left_y)

    out_name = os.path.basename(face_img_path).rsplit(".", 1)[0] + "_tryon.png"
    out_path = os.path.join(RESULT_FOLDER, out_name)
    cv2.imwrite(out_path, face_img)

    return out_name


def overlay_image(base_img, overlay_rgba, x, y):
    h, w = overlay_rgba.shape[:2]

    if x < 0:
        overlay_rgba = overlay_rgba[:, -x:]
        w += x
        x = 0
    if y < 0:
        overlay_rgba = overlay_rgba[-y:, :]
        h += y
        y = 0
    if x + w > base_img.shape[1]:
        overlay_rgba = overlay_rgba[:, : base_img.shape[1] - x]
        w = overlay_rgba.shape[1]
    if y + h > base_img.shape[0]:
        overlay_rgba = overlay_rgba[: base_img.shape[0] - y, :]
        h = overlay_rgba.shape[0]

    if h <= 0 or w <= 0:
        return

    bgr_overlay = overlay_rgba[:, :, :3]
    alpha = overlay_rgba[:, :, 3] / 255.0
    alpha = alpha[..., None]

    roi = base_img[y:y+h, x:x+w]
    base_img[y:y+h, x:x+w] = (alpha * bgr_overlay + (1 - alpha) * roi).astype(np.uint8)