import requests
import sounddevice as sd
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

# ----------------------------------
# AUDIO SETTINGS
# ----------------------------------

SAMPLERATE = 16000
DURATION = 5

print("===================================")
print("MindMate Client Started")
print("===================================")

input(
    "\nPress ENTER to start conversation..."
)

print(
    "\nConversation Mode Activated"
)

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