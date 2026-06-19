import requests
import sounddevice as sd
import cv2
import threading
from scipy.io.wavfile import write
from gtts import gTTS
import pygame
import time
import os
import face_recognition
import pickle
import sys
print(sys.version)

pygame.mixer.init()

SERVER = "http://127.0.0.1:8000"

current_emotion = "none"
current_confidence = 0

with open(
    "child_face.pkl",
    "rb"
) as f:

    child_encoding = pickle.load(f)

SAMPLERATE = 16000
DURATION = 5

print("===================================")
print("MindMate Client Started")
print("===================================")

def emotion_loop():

    global current_emotion
    global current_confidence

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Camera failed to open")
        return

    while True:

        ret, frame = cap.read()

        if not ret:
            continue

        try:

            cv2.imwrite("frame.jpg", frame)

            with open("frame.jpg", "rb") as f:

                response = requests.post(
                    f"{SERVER}/emotion",
                    files={"file": f}
                )

            data = response.json()

            current_emotion = data.get(
                "emotion",
                "none"
            )

            current_confidence = data.get(
                "confidence",
                0
            )

            all_emotions = data.get(
                "all_emotions",
                {}
            )

            y_pos = 40

            for emotion_name, value in all_emotions.items():

                cv2.putText(
                    frame,
                    f"{emotion_name}: {value:.0f}%",
                    (20, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 0, 0),
                    2
                )

                y_pos += 25

            cv2.putText(
                frame,
                f"Main: {current_emotion} ({current_confidence:.0f}%)",
                (20, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            if (
                current_emotion in ["sad", "fear", "angry"]
                and current_confidence >= 80
            ):

                requests.post(
                    f"{SERVER}/send_alert",
                    data={
                        "emotion": current_emotion,
                        "confidence": current_confidence
                    }
                )

            cv2.imshow(
                "MindMate Emotion",
                frame
            )

        except Exception as e:

            print("Emotion Error:", e)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        time.sleep(1)

threading.Thread(
    target=emotion_loop,
    daemon=True
).start()

print("\nCamera Started")

print("\nPress S to capture emotion...")

while True:

    key = input().lower().strip()

    if key == "s":

        print(
            f"\nDetected Emotion: {current_emotion} "
            f"({current_confidence:.0f}%)"
        )

        break

try:

    print("SENDING TO SERVER:", current_emotion)

    response = requests.post(
        f"{SERVER}/emotion_greeting",
        data={
            "emotion": current_emotion
        }
    )

    greeting = response.json().get(
        "reply",
        "Hello."
    )

    print(
        "\nMindMate:",
        greeting
    )

    tts = gTTS(
        text=greeting,
        lang="en"
    )

    tts.save(
        "greeting.mp3"
    )

    pygame.mixer.music.load(
        "greeting.mp3"
    )

    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

except Exception as e:

    print("Greeting Error:", e)

print("\nConversation Mode Activated")

while True:

    try:

        print("\nListening...")

        audio = sd.rec(
            int(DURATION * SAMPLERATE),
            samplerate=SAMPLERATE,
            channels=1,
            dtype="float32"
        )

        sd.wait()

        write(
            "voice.wav",
            SAMPLERATE,
            audio
        )

        with open(
            "voice.wav",
            "rb"
        ) as f:

            response = requests.post(
                f"{SERVER}/chat",
                files={"file": f},
                data={
                    "emotion": current_emotion
                }
            )

        data = response.json()

        transcript = data.get(
            "transcript",
            ""
        )

        reply = data.get(
            "reply",
            ""
        )

        reply_lower = reply.lower()

        if "move forward" in reply_lower:

            requests.post(
                f"{SERVER}/move_forward"
            )

        elif "move backward" in reply_lower:

            requests.post(
                f"{SERVER}/move_backward"
            )

        else:

            requests.post(
                f"{SERVER}/stop"
            )

        print(
            f"\nEmotion: {current_emotion} ({current_confidence}%)"
        )

        print(
            "\nYou:",
            transcript
        )

        print(
            "\nMindMate:",
            reply
        )

        if reply.strip():

            filename = f"response_{int(time.time())}.mp3"

            tts = gTTS(
                text=reply,
                lang="en"
            )

            tts.save(
                filename
            )

            pygame.mixer.music.load(
                filename
            )

            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            try:
                os.remove(filename)
            except:
                pass

    except KeyboardInterrupt:

        print("\nConversation Stopped.")
        break

    except Exception as e:

        print("\nCLIENT ERROR:")
        print(str(e))
        time.sleep(1)
