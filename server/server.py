# from random import random

# from fastapi import FastAPI, UploadFile, File, Form
# from llama_cpp import Llama
# from faster_whisper import WhisperModel
# import cv2
# import numpy as np
# from fer import FER
# import requests
# from twilio.rest import Client

# TWILIO_ACCOUNT_SID = ""
# TWILIO_AUTH_TOKEN = ""
# TWILIO_WHATSAPP_NUMBER = ""
# PARENT_WHATSAPP_NUMBER = ""
# ESP32_IP = "192.168.1.15"

# app = FastAPI()

# # LLM
# llm = Llama(
#     model_path=r"C:\MindMate_Server\models\gemma-4-E2B-it-qat-UD-Q4_K_XL.gguf",
#     n_ctx=4096,
#     n_gpu_layers=-1,
#     verbose=False
# )

# # TTS
# whisper_model = WhisperModel(
#     "large-v3",
#     device="cuda",
#     compute_type="float16"
# )

# # Face Emotion Recognition
# emotion_detector = FER(mtcnn=False)

# #Routes
# @app.get("/")
# def root():
#     return {"status": "MindMate Server Running"}

# @app.post("/emotion")
# # Image file -> bytes -> Dominant Emotion + Confidence
# async def emotion(file: UploadFile = File(...)):
#     try:
#         image_bytes = await file.read()
#         npimg = np.frombuffer(image_bytes, np.uint8)
#         frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
#         results = emotion_detector.detect_emotions(frame)

#         if not results:
#             return {"emotion": "none", "confidence": 0, "all_emotions": {}}

#         emotions = results[0]["emotions"]
#         dominant = max(emotions, key=emotions.get)

#         return {
#             "emotion": dominant,
#             "confidence": round(emotions[dominant] * 100, 1),
#             "all_emotions": {k: round(v * 100, 1) for k, v in emotions.items()}
#         }

#     except Exception as e:
#         print("EMOTION ERROR:", e)
#         return {"emotion": "error", "confidence": 0, "all_emotions": {}}

# @app.post("/emotion_greeting")
# # Emotion -> Greeting response mapping   
# async def emotion_greeting(emotion: str = Form(...)):

#     emotion = emotion.lower().strip()

#     responses = {

#         "sad": [
#             "You are stronger than you think and brighter days are ahead.",
#             "Every difficult moment will pass. Keep believing in yourself.",
#             "Take one step at a time. You are doing better than you realize.",
#             "You have overcome challenges before and you can do it again.",
#             "I believe in you. Keep going and do not give up."
#         ],

#         "fear": [
#             "You are safe and capable. Trust yourself.",
#             "Take a deep breath. You can handle this.",
#             "Courage is moving forward even when you feel afraid.",
#             "You are braver than you think.",
#             "Believe in yourself. You have what it takes."
#         ],

#         "angry": [
#             "Take a deep breath and stay calm.",
#             "Pause for a moment and let your mind relax.",
#             "Every problem can be solved with patience.",
#             "Stay calm and focus on what you can control.",
#             "A peaceful mind helps you make better decisions."
#         ],

#         "happy": [
#             "It is wonderful to see you happy today.",
#             "Keep smiling and enjoy this beautiful moment.",
#             "Your happiness can brighten the day of others.",
#             "That positive energy looks great on you.",
#             "I am glad you are feeling happy today."
#         ],

#         "neutral": [
#             "Hello, I hope you are having a wonderful day.",
#             "Welcome back. I am happy to see you.",
#             "Hello, let's make today a great day.",
#             "Nice to see you. How are you feeling today?",
#             "I am here whenever you need me."
#         ]
#     }

#     reply = random.choice(
#         responses.get(
#             emotion,
#             responses["neutral"]
#         )
#     )

#     print("EMOTION =", emotion)
#     print("GREETING =", reply)

#     return {
#         "reply": reply
#     }

# @app.post("/chat")
# # Audio file -> Transcription -> LLM Response
# async def chat(
#     file: UploadFile = File(...),
#     emotion: str = Form("neutral")
# ):
#     try:
#         with open("input.wav", "wb") as f:
#             f.write(await file.read())
#         segments, info = whisper_model.transcribe("input.wav")

#         user_text = ""
#         for segment in segments:
#             user_text += segment.text

#         user_text = user_text.strip()

#         prompt = f"""
#         You are MindMate.
#         Current child emotion:
#         {emotion}
#         If the emotion is sad:        Be comforting.
#         If the emotion is happy:        Be cheerful.
#         If the emotion is angry:        Be calm and patient.
#         If the emotion is fear:        Be reassuring.
#         If the emotion is neutral:        Be friendly.
#         User:        {user_text}

#         Reply briefly in 2 sentances sound like air hostest being friendly to client.
#         """

#         print("\n========== DEBUG ==========")
#         print("USER TEXT:", user_text)
#         print("PROMPT:", prompt)

#         output = llm(
#             prompt,
#             max_tokens=250,
#             temperature=0.7,
#             top_p=0.95,
#             stop=[]
#         )

#         print("RAW OUTPUT:", output)
#         reply = output["choices"][0]["text"]

#         print("RAW REPLY =", repr(reply))
#         reply = reply.strip()

#         if reply == "":
#             reply = "I am sorry, I did not catch that. Can you please repeat?"

#         print("REPLY:", repr(reply))
#         print("===========================\n")

#         return {
#             "transcript": user_text,
#             "reply": reply
#         }

#     except Exception as e:
#         print("CHAT ERROR:", e)
#         return {"transcript": "", "reply": ""}


# @app.post("/send_alert")
# # whattsapp alert to parent if child is in distress (sad, angry, fear), emotion and confidence details
# async def send_alert(
#     emotion: str = Form(...),
#     confidence: float = Form(...)
# ):

#     message = (
#         f"MindMate Alert\n\n"
#         f"Child emotion: {emotion}\n"
#         f"Confidence: {confidence}%"
#     )

#     client = Client(
#         TWILIO_ACCOUNT_SID,
#         TWILIO_AUTH_TOKEN
#     )

#     client.messages.create(
#         from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
#         body=message,
#         to=f"whatsapp:{PARENT_WHATSAPP_NUMBER}"
#     )

#     return {
#         "status": "alert_sent"
#     }


# @app.post("/move_forward")
# async def move_forward():
#     print("################### FORWARD COMMAND RECEIVED ###################")
#     requests.get(
#         f"http://{ESP32_IP}/forward"
#     )
#     return {"status": "forward"}    


# @app.post("/move_backward")
# async def move_backward():
#     print("################### BACKWARD COMMAND RECEIVED ###################")
#     requests.get(
#         f"http://{ESP32_IP}/backward"
#     )

#     return {
#         "status": "backward"
#     }


# @app.post("/stop")
# async def stop_robot():
#     print("################### STOP COMMAND RECEIVED ###################")
#     requests.get(
#         f"http://{ESP32_IP}/stop"
#     )

#     return {
#         "status": "stop"
#     }