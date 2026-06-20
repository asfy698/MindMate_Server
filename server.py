from fastapi import FastAPI, UploadFile, File, Form
from llama_cpp import Llama
from faster_whisper import WhisperModel
import cv2
import numpy as np
from fer import FER
from twilio.rest import Client
import requests

app = FastAPI()

TWILIO_ACCOUNT_SID = ""
TWILIO_AUTH_TOKEN = ""
TWILIO_WHATSAPP_NUMBER = ""
PARENT_WHATSAPP_NUMBER = ""

ESP32_IP = "192.168.1.15"

llm = Llama(
    model_path=r"C:\MindMate_Server\models\gemma-4-E2B-it-UD-Q4_K_XL.gguf",
    n_ctx=4096,
    n_gpu_layers=-1,
    verbose=False
)

whisper_model = WhisperModel(
    "large-v3",
    device="cuda",
    compute_type="float16"
)

emotion_detector = FER(mtcnn=False)

@app.get("/")
def root():
    return {"status": "MindMate Server Running"}

@app.post("/emotion")
async def emotion(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        npimg = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        results = emotion_detector.detect_emotions(frame)

        if not results:
            return {"emotion": "none", "confidence": 0, "all_emotions": {}}

        emotions = results[0]["emotions"]
        dominant = max(emotions, key=emotions.get)

        return {
            "emotion": dominant,
            "confidence": round(emotions[dominant] * 100, 1),
            "all_emotions": {k: round(v * 100, 1) for k, v in emotions.items()}
        }

    except Exception as e:
        print("EMOTION ERROR:", e)
        return {"emotion": "error", "confidence": 0, "all_emotions": {}}

@app.post("/emotion_greeting")
async def emotion_greeting(emotion: str = Form(...)):

    print("################################")
    print("EMOTION RECEIVED =", repr(emotion))
    print("################################")

    emotion = emotion.lower().strip()

    if emotion == "sad":

        return {
            "reply": "I know things may feel difficult right now, but you are stronger than you think and better days are ahead."
        }

    elif emotion == "fear":

        return {
            "reply": "You are safe, capable and brave. Take one step at a time and trust yourself."
        }

    elif emotion == "angry":

        return {
            "reply": "Take a deep breath. Stay calm and remember that every problem can be solved patiently."
        }

    elif emotion == "happy":

        print("EMOTION RECEIVED =", emotion)

        return {
            "reply": "It is wonderful to see you happy today. Keep smiling and enjoy the moment."
        }

    else:

        return {
            "reply": "Hello. I am MindMate. I hope you are having a wonderful day."
        }

@app.post("/chat")
async def chat(
    file: UploadFile = File(...),
    emotion: str = Form("neutral")
):
    try:
        with open("input.wav", "wb") as f:
            f.write(await file.read())

        segments, info = whisper_model.transcribe("input.wav")

        user_text = ""
        for segment in segments:
            user_text += segment.text

        user_text = user_text.strip()

        prompt = f"""
        You are MindMate.

        Current child emotion:
        {emotion}

        If the emotion is sad:
        Be comforting.

        If the emotion is happy:
        Be cheerful.

        If the emotion is angry:
        Be calm and patient.

        If the emotion is fear:
        Be reassuring.

        If the emotion is neutral:
        Be friendly.

        User:
        {user_text}

        Reply briefly.
        """

        print("\n========== DEBUG ==========")
        print("USER TEXT:", user_text)
        print("PROMPT:", prompt)

        output = llm(
            prompt,
            max_tokens=150,
            temperature=0.7,
            top_p=0.95,
            stop=[]
        )

        print("RAW OUTPUT:", output)

        reply = output["choices"][0]["text"]

        print("RAW REPLY =", repr(reply))

        reply = reply.strip()

        if reply == "":
            reply = "Thank you for talking with me. I am always here to help."

        print("REPLY:", repr(reply))
        print("===========================\n")

        return {
            "transcript": user_text,
            "reply": reply
        }

    except Exception as e:
        print("CHAT ERROR:", e)
        return {"transcript": "", "reply": ""}


@app.post("/send_alert")
async def send_alert(
    emotion: str = Form(...),
    confidence: float = Form(...)
):

    message = (
        f"MindMate Alert\n\n"
        f"Child emotion: {emotion}\n"
        f"Confidence: {confidence}%"
    )

    client = Client(
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN
    )

    client.messages.create(
        from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
        body=message,
        to=f"whatsapp:{PARENT_WHATSAPP_NUMBER}"
    )

    return {
        "status": "alert_sent"
    }


@app.post("/move_forward")
async def move_forward():

    requests.get(
        f"http://{ESP32_IP}/forward"
    )

    return {
        "status": "forward"
    }


@app.post("/move_backward")
async def move_backward():

    requests.get(
        f"http://{ESP32_IP}/backward"
    )

    return {
        "status": "backward"
    }


@app.post("/stop")
async def stop_robot():

    requests.get(
        f"http://{ESP32_IP}/stop"
    )

    return {
        "status": "stop"
    }