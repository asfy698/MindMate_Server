import os
import requests
import cv2
import sounddevice as sd
from scipy.io.wavfile import write
from gtts import gTTS
from picamera2 import Picamera2
from libcamera import Transform
import psutil
import pygame


def initialize_camera():
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (1640, 1232)},
        transform=Transform()
    )
    picam2.configure(config)
    picam2.start()
    return picam2


def capture_emotion_frame(frame, size=(320, 240), quality=50):
    resized = cv2.resize(frame, size)
    _, img_encoded = cv2.imencode(
        ".jpg",
        resized,
        [cv2.IMWRITE_JPEG_QUALITY, quality]
    )
    return img_encoded.tobytes()


def send_emotion_request(server, frame_bytes, timeout=20):
    response = requests.post(
        f"{server}/emotion",
        files={
            "file": (
                "frame.jpg",
                frame_bytes,
                "image/jpeg"
            )
        },
        timeout=timeout
    )
    response.raise_for_status()
    return response.json()


def draw_emotion_overlay(
    frame,
    current_emotion,
    current_confidence,
    all_emotions,
    fps,
    latency,
    capture_time,
    cpu,
    ram
):
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
    return frame


def should_send_alert(emotion, confidence):
    return emotion in ["sad", "fear", "angry"] and confidence >= 80


def send_alert(server, emotion, confidence, timeout=5):
    requests.post(
        f"{server}/send_alert",
        data={
            "emotion": emotion,
            "confidence": confidence
        },
        timeout=timeout
    )


def record_audio(path, duration, samplerate):
    audio = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="float32"
    )
    sd.wait()
    write(path, samplerate, audio)
    return path


def send_chat_audio(server, audio_path, emotion):
    with open(audio_path, "rb") as audio_file:
        response = requests.post(
            f"{server}/chat",
            files={"file": audio_file},
            data={"emotion": emotion}
        )
    response.raise_for_status()
    return response.json()


def speak_text(text, filename, lang="en"):
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.wait(100)
    try:
        os.remove(filename)
    except OSError:
        pass
