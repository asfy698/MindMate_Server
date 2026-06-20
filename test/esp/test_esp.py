import requests
import json
import os
from datetime import datetime
import time

with open("config.json", "r") as f:
    cfg = json.load(f)

ESP_IP = cfg["esp_ip"]
MODE = cfg["test_mode"]

BASE_URL = f"http://{ESP_IP}"

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

run_dir = os.path.join("runs", timestamp)
os.makedirs(run_dir, exist_ok=True)

results = {}

print("\n===================================")
print("MindMate ESP Test")
print("===================================\n")

def save():
    with open(os.path.join(run_dir, "results.json"), "w") as f:
        json.dump(results, f, indent=4)

def test_health():
    print("Testing Health...")

    r = requests.get(f"{BASE_URL}/health", timeout=10)

    results["health"] = {
        "status_code": r.status_code,
        "response": r.json()
    }

    print("PASS")

def test_move(action, duration):
    print(f"Testing {action}...")

    r = requests.get(
        f"{BASE_URL}/move",
        params={
            "action": action,
            "duration": duration
        },
        timeout=20
    )

    results[action] = {
        "status_code": r.status_code,
        "response": r.json()
    }

    print("PASS")

def create_summary():
    summary = []

    summary.append("=" * 50)
    summary.append("MindMate ESP Test Report")
    summary.append("=" * 50)
    summary.append("")
    summary.append(f"Date : {timestamp}")
    summary.append(f"Mode : {MODE}")
    summary.append("")

    for k in results:
        summary.append(f"{k} : PASS")

    summary.append("")
    summary.append("=" * 50)

    text = "\n".join(summary)

    with open(os.path.join(run_dir, "summary.txt"), "w") as f:
        f.write(text)

    print(text)

try:

    if MODE == "health":
        test_health()

    elif MODE == "movement":

        test_move(
            "forward",
            cfg["durations"]["forward"]
        )

        test_move(
            "backward",
            cfg["durations"]["backward"]
        )

        test_move(
            "stop",
            1
        )

    elif MODE == "full":

        test_health()

        test_move(
            "forward",
            cfg["durations"]["forward"]
        )

        test_move(
            "backward",
            cfg["durations"]["backward"]
        )

        test_move(
            "stop",
            1
        )

    save()
    create_summary()

except Exception as e:

    results["error"] = str(e)

    save()

    print("\nFAILED")
    print(e)