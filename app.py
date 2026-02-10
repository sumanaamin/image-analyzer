import streamlit as st
import requests
import pandas as pd
from PIL import Image, ImageDraw

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Image Analyzer", layout="centered")

st.title("🖼️ Image Analyzer")
st.write("Upload an image to detect caption, objects, tags and text")

# ================= UPLOAD =================
uploaded = st.file_uploader(
    "Upload Image (Max 4MB)",
    type=["jpg", "jpeg", "png"]
)

# ================= IF IMAGE =================
if uploaded:

    # ---- File size check ----
    if uploaded.size > 4 * 1024 * 1024:
        st.error("File must be under 4MB")
        st.stop()

    # ---- Preview ----
    st.subheader("Preview")
    st.image(uploaded, width=300)

    # ---- Call Backend ----
    with st.spinner("Analyzing image..."):
        try:
            res = requests.post(
                "http://127.0.0.1:5000/analyze",
                files={"image": uploaded.getvalue()},
                timeout=60
            )
            data = res.json()
        except Exception as e:
            st.error(f"Backend connection failed: {e}")
            st.stop()

    st.success("✅Analysis Complete")

    # ================= CAPTION =================
    st.subheader("Caption")

    captions = data.get("caption", [])
    if captions:
        st.info(f"{captions[0]['text']}")
    else:
        st.write("No caption found")

    # ================= METADATA =================
    st.subheader("📌Metadata")

    metadata = data.get("metadata", {})

    if metadata:
        meta_df = pd.DataFrame(
            [(str(k), str(v)) for k, v in metadata.items()],
            columns=["Property", "Value"]
        )
        st.table(meta_df)
    else:
        st.write("No metadata")

    # ================= TAGS =================
    st.subheader("🏷️Tags")

    tags = data.get("tags", [])

    if tags:
        tag_df = pd.DataFrame(
            [(str(t["name"]), str(t["confidence"])) for t in tags],
            columns=["Tag", "Confidence"]
        )
        st.table(tag_df)
    else:
        st.write("No tags found")

    # ================= OCR =================
    st.subheader("Extracted Text (OCR)")

    texts = data.get("text", [])

    if texts:
        for t in texts:
            st.write("•", t)
    else:
        st.write("No text detected")

    # ================= OBJECTS =================
    st.subheader("Objects Detected")

    objects = data.get("objects", [])

    if objects:

        img = Image.open(uploaded)
        draw = ImageDraw.Draw(img)

        rows = []

        for obj in objects:
            r = obj["rectangle"]
            x, y, w, h = r["x"], r["y"], r["w"], r["h"]

            # Draw bounding box
            draw.rectangle(
                [x, y, x+w, y+h],
                outline="red",
                width=3
            )

            rows.append(
                (str(obj["object"]), str(obj["confidence"]))
            )

        st.image(img, caption="Detected Objects")

        obj_df = pd.DataFrame(
            rows,
            columns=["Object", "Confidence"]
        )

        st.table(obj_df)

    else:
        st.write("No objects detected")

