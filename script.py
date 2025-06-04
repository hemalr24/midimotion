import cv2
import mido
import mediapipe as mp
import threading
import time

MIDI_PORT = '2- KATANA 1'

TONE_CONFIGS = {
    1: {
        "amp_type": 0x00,  
        "cc": [
            ("GAIN", 21, 0),
            ("BOOSTER", 16, 0),
            ("MOD", 17, 0),
            ("FX", 18, 0),
            ("DELAY", 19, 0),
            ("REVERB", 20, 0),
            ("MASTER", 22, 90)
        ]
    },
    2: {
        "amp_type": 0x00,  
        "cc": [
            ("GAIN", 21, 50),
            ("BOOSTER", 16, 0),
            ("MOD", 17, 0),
            ("FX", 18, 0),
            ("DELAY", 19, 0),
            ("REVERB", 20, 127),
            ("MASTER", 22, 90)
        ]
    },
    3: {
        "amp_type": 0x01, 
        "cc": [
            ("GAIN", 21, 64),
            ("BOOSTER", 16, 0),
            ("MOD", 17, 127),
            ("FX", 18, 0),
            ("DELAY", 19, 0),
            ("REVERB", 20, 0),
            ("MASTER", 22, 90)
        ]
    }
}

def send_amp_type(port, amp_type_byte):
    base = [0x41, 0x00, 0x00, 0x00, 0x20, 0x12, 0x01, 0x00, 0x00]
    checksum = (128 - (sum(base[6:] + [amp_type_byte]) % 128)) % 128
    msg = mido.Message('sysex', data=base + [amp_type_byte, checksum])
    port.send(msg)
    print(f"Set amp type to {amp_type_byte:#02x}")

def apply_tone_config(port, config):
    try:
        send_amp_type(port, config["amp_type"])
        time.sleep(0.05)
    except Exception as e:
        print(f"SysEx error: {e}")

    for name, cc, val in config["cc"]:
        try:
            msg = mido.Message('control_change', control=cc, value=val)
            port.send(msg)
            print(f"Sent {name} (CC#{cc}) = {val}")
            time.sleep(0.01)
        except Exception as e:
            print(f"CC error (CC#{cc}): {e}")

def count_fingers(hand_landmarks):
    tip_ids = [8, 12, 16]   
    pip_ids = [6, 10, 14]   
    count = 0
    for tip, pip in zip(tip_ids, pip_ids):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            count += 1
    return count

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Camera could not be opened")
    exit()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

try:
    midi_port = mido.open_output(MIDI_PORT)
except Exception as e:
    print(f"Failed to open MIDI port: {e}")
    cap.release()
    exit()

prev_count = -1

while True:
    ret, frame = cap.read()
    if not ret:
        break

    image = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    image = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    if results.multi_hand_landmarks:
        for hand in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(image, hand, mp_hands.HAND_CONNECTIONS)
            fingers = count_fingers(hand)

            if fingers in TONE_CONFIGS and fingers != prev_count:
                print(f"Detected {fingers} fingers → applying tone")
                threading.Thread(
                    target=apply_tone_config,
                    args=(midi_port, TONE_CONFIGS[fingers]),
                    daemon=True
                ).start()
                prev_count = fingers

    cv2.imshow("Finger Tone Control", image)
    if cv2.waitKey(5) & 0xFF == 27:
        break

cap.release()
midi_port.close()
cv2.destroyAllWindows()
