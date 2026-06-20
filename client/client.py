import os
import sys
import platform
import threading
import time
import cv2
import pygame
import psutil
import requests

import utils


SERVER = "http://192.168.1.4:8000"
SAMPLERATE = 16000
DURATION = 5

current_emotion = "none"
current_confidence = 0
all_emotions = {}
latency = 0.0

emotion_interval = 0.5
last_emotion_time = 0.0

pygame.mixer.init()


def print_environment_info():
    print(platform.machine())
    print(sys.version)


def request_emotion_update(picam2):
    global current_emotion, current_confidence, all_emotions, latency, last_emotion_time

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    cap_start = time.time()
    frame = picam2.capture_array()
    capture_time = (time.time() - cap_start) * 1000
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    if time.time() - last_emotion_time > emotion_interval:
        last_emotion_time = time.time()
        frame_bytes = utils.capture_emotion_frame(frame)
        t0 = time.time()
        data = utils.send_emotion_request(SERVER, frame_bytes)
        latency = (time.time() - t0) * 1000

        current_emotion = data.get("emotion", current_emotion)
        current_confidence = data.get("confidence", current_confidence)
        all_emotions = data.get("all_emotions", all_emotions)

    return frame, capture_time, cpu, ram


def render_emotion_frame(frame, fps, capture_time, cpu, ram):
    return utils.draw_emotion_overlay(
        frame,
        current_emotion,
        current_confidence,
        all_emotions,
        fps,
        latency,
        capture_time,
        cpu,
        ram,
    )


def maybe_send_alert():
    if utils.should_send_alert(current_emotion, current_confidence):
        try:
            utils.send_alert(SERVER, current_emotion, current_confidence)
        except Exception as error:
            print("Alert Error:", error)

# CAMERA -> FER
def emotion_loop():
    # Initialize Camera
    try:
        picam2 = utils.initialize_camera()
    except Exception as e:
        print("Camera Init Error:", e)
        return
    print("Camera Started")
    print(picam2.camera_properties)

    # Performance tracking
    fps_counter = 0
    fps_start = time.time()
    fps = 0
    perf_log_every = 2.0
    last_perf_log = 0.0

    # Emotion Loop
    while True:
        try:
            frame, capture_time, cpu, ram = request_emotion_update(picam2)

            fps_counter += 1
            if time.time() - fps_start >= 1.0:
                fps = fps_counter
                fps_counter = 0
                fps_start = time.time()

            # Emotion of Frame 
            frame = render_emotion_frame(frame, fps, capture_time, cpu, ram)
            maybe_send_alert()
            cv2.imshow("MindMate Emotion", frame)

            if time.time() - last_perf_log >= perf_log_every:
                last_perf_log = time.time()
                print(
                    f"Perf | FPS={fps} | Capture={capture_time:.1f}ms | "
                    f"Server={latency:.1f}ms | CPU={cpu:.1f}% | RAM={ram:.1f}%"
                )

        except Exception as e:
            print("Emotion Error:", e)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


def send_emotion_greeting():
    try:
        print("SENDING TO SERVER:", current_emotion)
        response = requests.post(
            f"{SERVER}/emotion_greeting",
            data={"emotion": current_emotion},
            timeout=10,
        )
        response.raise_for_status()
        greeting = response.json().get("reply", "Hello.")
        print("\nMindMate:", greeting)
        utils.speak_text(greeting, "greeting.mp3")
    except Exception as error:
        print("Greeting Error:", error)


def send_command_for_transcript(transcript_lower):
    if "move forward" in transcript_lower:
        print("FORWARD COMMAND")
        requests.post(f"{SERVER}/move_forward", timeout=5)
        return

    if "move backward" in transcript_lower:
        print("BACKWARD COMMAND")
        requests.post(f"{SERVER}/move_backward", timeout=5)
        return

    requests.post(f"{SERVER}/stop", timeout=5)


def run_conversation_loop():
    # Loop listen phase -> STT -> reply -> speak
    while True:
        try:
            # Listen
            print("\nListening...")
            audio_path = utils.record_audio("voice.wav", DURATION, SAMPLERATE)
            data = utils.send_chat_audio(SERVER, audio_path, current_emotion)
            try:
                os.remove(audio_path)
            except OSError:
                pass
            
            # STT
            transcript = data.get("transcript", "")
            reply = data.get("reply", "")
            transcript_lower = transcript.lower()

            print("TRANSCRIPT =", repr(transcript))
            print("TRANSCRIPT_LOWER =", repr(transcript_lower))

            # Text -> Movement Commands
            send_command_for_transcript(transcript_lower) # Movement
            print("\nYou:", transcript)
            print("\nMindMate:", reply)

            # Text -> Speech
            if reply.strip():
                filename = f"response_{int(time.time())}.mp3"
                utils.speak_text(reply, filename)

        except KeyboardInterrupt:
            print("\nConversation Stopped.")
            break
        except Exception as error:
            print("\nCLIENT ERROR:")
            print(error)
            time.sleep(1)


def main():
    print("===================================")
    print("MindMate Client Started")
    print("===================================")
    print_environment_info()

# Run emotion loop
    threading.Thread(target=emotion_loop, daemon=True).start()

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

    send_emotion_greeting()
    print("\nConversation Mode Activated")
    run_conversation_loop()


if __name__ == "__main__":
    main()
