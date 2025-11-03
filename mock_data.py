import time
import random

events = ["Normal Operation", "Tamper Detected", "Magnetic Interference", "Bypass Attempt"]

while True:
    print(random.choice(events))
    time.sleep(2)
