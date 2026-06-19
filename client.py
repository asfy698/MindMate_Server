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
import platform
import psutil
from picamera2 import Picamera2
from libcamera import Transform

print(platform.machine())
print(sys.version)

pygame.mixer.init()

SERVER = "http://192.168.1.4:8000"

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

current_emotion = "none"
current_confidence = 0

emotion_interval = 0.5
last_emotion_time = 0

all_emotions = {}
latency = 0

def emotion_loop():
    global all_emotions
    global latency
    global last_emotion_time
    global current_emotion
    global current_confidence

    try:
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(
            # main={"size": (640, 480)},
            # main={"size": (1280,720)},
            # main={"size": (1920, 1080)},
            main={"size": (1640, 1232)},

            
            # controls={"ScalerCrop": (0, 0, 3280, 2464)},
            transform=Transform()
        )
        picam2.configure(config)
        picam2.start()
    except Exception as e:
        print("Camera Init Error:", e)
        return

    print("Camera Started")
    fps_counter = 0
    fps_start = time.time()
    fps = 0
    perf_log_every = 2.0
    last_perf_log = 0
    print(picam2.camera_properties)
    while True:

        cap_start = time.time()
        frame = picam2.capture_array()
        capture_time = (time.time() - cap_start) * 1000
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        fps_counter += 1

        if time.time() - fps_start >= 1:
            fps = fps_counter
            fps_counter = 0
            fps_start = time.time()
        try:
           
            latency = latency

            if time.time() - last_emotion_time > emotion_interval:
                
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory().percent

                last_emotion_time = time.time()

                emotion_frame = cv2.resize(
                    frame,
                    (320, 240)
                )

                _, img_encoded = cv2.imencode(
                    ".jpg",
                    emotion_frame,
                    [cv2.IMWRITE_JPEG_QUALITY, 50]
                )

                t0 = time.time()

                response = requests.post(
                    f"{SERVER}/emotion",
                    files={
                        "file": (
                            "frame.jpg",
                            img_encoded.tobytes(),
                            "image/jpeg"
                        )
                    },
                    timeout=20  
                )

                latency = (time.time() - t0) * 1000

                data = response.json()

                current_emotion = data.get(
                    "emotion",
                    current_emotion
                )

                current_confidence = data.get(
                    "confidence",
                    current_confidence
                )

                all_emotions = data.get(
                    "all_emotions",
                    all_emotions
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

            cv2.putText(
                frame,
                f"FPS: {fps}",
                (20, 460),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Server: {latency:.0f} ms",
                (20, 430),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Capture: {capture_time:.0f} ms",
                (20, 400),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"CPU:{cpu:.0f}% RAM:{ram:.0f}%",
                (20, 370),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            if time.time() - last_perf_log >= perf_log_every:
                last_perf_log = time.time()

                print(
                    f"Perf | FPS={fps} | Capture={capture_time:.1f}ms | "
                    f"Server={latency:.1f}ms | CPU={cpu:.1f}% | RAM={ram:.1f}%"
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
                    },
                    timeout=5
                )

            cv2.imshow(
                "MindMate Emotion",
                frame
            )

        except Exception as e:

            print("Emotion Error:", e)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

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
