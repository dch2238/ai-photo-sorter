"""Download lightweight YuNet and SFace models if not present."""
import os, urllib.request

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))

MODELS = {
    "face_detection_yunet_2023mar.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "face_recognition_sface_2021dec.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
}

def ensure_models():
    os.makedirs(MODELS_DIR, exist_ok=True)
    for name, url in MODELS.items():
        dest = os.path.join(MODELS_DIR, name)
        if not os.path.exists(dest) or os.path.getsize(dest) < 10000:
            print(f"Downloading {name}...")
            urllib.request.urlretrieve(url, dest)
            print(f"Downloaded {name} ({os.path.getsize(dest)/(1024*1024):.1f} MB)")
        else:
            print(f"Model {name} already present.")

if __name__ == "__main__":
    ensure_models()
