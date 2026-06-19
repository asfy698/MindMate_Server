import requests
import sounddevice as sd
import cv2
import threading
from scipy.io.wavfile import write
from gtts import gTTS
import pygame
import time
import os

# ----------------------------------
# AUDIO PLAYER
# ----------------------------------

pygame.mixer.init()

# ----------------------------------
# SERVER ADDRESS
# ----------------------------------

SERVER = "http://127.0.0.1:8000"

current_emotion = "none"
current_confidence = 0

# ----------------------------------
# AUDIO SETTINGS
# ----------------------------------

SAMPLERATE = 16000
DURATION = 5

print("===================================")
print("MindMate Client Started")
print("===================================")

def emotion_loop():

    global current_emotion
    global current_confidence

    cap = cv2.VideoCapture(0)

    while True:

        ret, frame = cap.read()

        if not ret:
            continue

        cv2.imwrite(
            "frame.jpg",
            frame
        )

        try:

            with open(
                "frame.jpg",
                "rb"
            ) as f:

                response = requests.post(

                    f"{SERVER}/emotion",

                    files={
                        "file": f
                    }
                )

            data = response.json()

            current_emotion = data[
                "emotion"
            ]       

            current_confidence = data[
                "confidence"
            ]

            all_emotions = data[
                "all_emotions"
            ]

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

            cv2.imshow(
                "MindMate Emotion",
                frame
            )

            cv2.waitKey(1)

        except:

            pass

        time.sleep(1)

        threading.Thread(
            target=emotion_loop,
            daemon=True
        ).start()

        print(
            "\nCamera Started"
        )

        input(
            "\nPress ENTER when ready..."
        )

        response = requests.post(

        f"{SERVER}/emotion_greeting",

        data={
            "emotion": current_emotion
        }
    )

    data = response.json()

    greeting = data["reply"]

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
# ----------------------------------
# MAIN LOOP
# ----------------------------------

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
                files={
                    "file": f
                }
            )

        if response.status_code != 200:

            print(
                "\nServer Error:",
                response.status_code
            )

            continue

        data = response.json()

        transcript = data.get(
            "transcript",
            ""
        )

        reply = data.get(
            "reply",
            ""
        )

        print(
            f"\nEmotion: "
            f"{current_emotion} "
            f"({current_confidence}%)"
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

            filename = (
                f"response_{int(time.time())}.mp3"
            )

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

            # small pause after speaking
            time.sleep(1)

            # cleanup old audio file
            try:

                os.remove(
                    filename
                )

            except:

                pass

        else:

            print(
                "\nEmpty AI reply."
            )

    except KeyboardInterrupt:

        print(
            "\nConversation Stopped."
        )

        break

    except Exception as e:

        print(
            "\nCLIENT ERROR:"
        )

        print(
            str(e)
        )

        time.sleep(1)