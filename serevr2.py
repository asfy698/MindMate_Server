from fastapi import FastAPI, UploadFile, File, Form
from llama_cpp import Llama
from faster_whisper import WhisperModel

import cv2
import numpy as np
from fer import FER

app = FastAPI()

# ----------------------------------
# GEMMA
# ----------------------------------

llm = Llama(
    model_path=r"C:\MindMate_Server\models\gemma-4-E2B-it-UD-Q4_K_XL.gguf",
    n_ctx=4096,
    n_gpu_layers=-1,
    verbose=False
)

# ----------------------------------
# WHISPER
# ----------------------------------

whisper_model = WhisperModel(
    "large-v3",
    device="cuda",
    compute_type="float16"
)

emotion_detector = FER(
    mtcnn=False
)

# ----------------------------------
# ROOT
# ----------------------------------

@app.get("/")
def root():

    return {
        "status": "MindMate Server Running"
    }

# ----------------------------------
# CHAT
# ----------------------------------

@app.post("/chat")
async def chat(
    file: UploadFile = File(...),
    emotion: str = Form("neutral")
):

    try:

        temp_file = "input.wav"

        with open(
            temp_file,
            "wb"
        ) as f:

            f.write(
                await file.read()
            )

        # -------------------------
        # WHISPER
        # -------------------------

        segments, info = whisper_model.transcribe(
            temp_file
        )

        user_text = ""

        for segment in segments:

            user_text += segment.text

        user_text = user_text.strip()

        print("\n===================================")
        print("USER:")
        print(user_text)
        print("===================================")

        # -------------------------
        # GEMMA PROMPT
        # -------------------------

        prompt = f"""
Question: {user_text}

Answer:
"""

        output = llm(
            prompt,
            max_tokens=150,
            temperature=0.7,
            echo=False
        )

        print("\n===================================")
        print("RAW GEMMA OUTPUT:")
        print(output)
        print("===================================")

        reply = output["choices"][0]["text"].strip()

        print("\n===================================")
        print("AI REPLY:")
        print(reply)
        print("===================================")

        return {
            "transcript": user_text,
            "reply": reply
        }

    except Exception as e:

        print("\nSERVER ERROR:")
        print(str(e))

        return {
            "transcript": "",
            "reply": "",
            "error": str(e)
        }


@app.post("/emotion")
async def emotion(
    file: UploadFile = File(...)
):

    image_bytes = await file.read()

    npimg = np.frombuffer(
        image_bytes,
        np.uint8
    )

    frame = cv2.imdecode(
        npimg,
        cv2.IMREAD_COLOR
    )

    results = emotion_detector.detect_emotions(
        frame
    )

    if not results:

        return {
            "emotion": "none",
            "confidence": 0
        }

    emotions = results[0]["emotions"]

    dominant = max(
        emotions,
        key=emotions.get
    )

    return {

    "emotion": dominant,

    "confidence": round(
        emotions[dominant] * 100,
        1
    ),

    "all_emotions": {

        key: round(
            value * 100,
            1
        )

        for key, value in emotions.items()
    }
}