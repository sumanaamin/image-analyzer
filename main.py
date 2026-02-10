import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from PIL import Image
import io

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024

AZURE_KEY = os.getenv("AZURE_VISION_KEY")

# 👉 Your FULL endpoint already includes /analyze
VISION_URL = os.getenv("AZURE_VISION_ENDPOINT")

# OCR endpoint (derive from same base)
OCR_URL = VISION_URL.replace("analyze", "ocr")


@app.route("/analyze", methods=["POST"])
def analyze():

    if "image" not in request.files:
        return jsonify({"error": "No image"}), 400

    file = request.files["image"]
    img_bytes = file.read()

    # ---- Metadata ----
    img = Image.open(io.BytesIO(img_bytes))
    metadata = {
        "width": img.width,
        "height": img.height,
        "format": img.format
    }

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_KEY,
        "Content-Type": "application/octet-stream"
    }

    params = {
        "visualFeatures": "Description,Objects,Tags"
    }

    # ---- ANALYZE ----
    vision_res = requests.post(
        VISION_URL,
        headers=headers,
        params=params,
        data=img_bytes
    ).json()

    # ---- OCR ----
    ocr_res = requests.post(
        OCR_URL,
        headers=headers,
        data=img_bytes
    ).json()

    extracted_text = []

    if "regions" in ocr_res:
        for region in ocr_res["regions"]:
            for line in region["lines"]:
                words = [w["text"] for w in line["words"]]
                extracted_text.append(" ".join(words))

    output = {
        "caption": vision_res.get("description", {}).get("captions", []),
        "tags": vision_res.get("tags", []),
        "objects": vision_res.get("objects", []),
        "text": extracted_text,
        "metadata": metadata
    }

    return jsonify(output)


if __name__ == "__main__":
    app.run(debug=True)
