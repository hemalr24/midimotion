import cv2
import mediapipe as mp
import mido

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1) 
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    cv2.imshow("Hand Gesture Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

def is_fist(landmarks):
    tip_ids = [4, 8, 12, 16, 20]  # Thumb and fingers' tip landmarks
    for tip in tip_ids:
        if landmarks.landmark[tip].y < landmarks.landmark[tip - 2].y:
            return False
    return True

midi_output = mido.open_output('BOSS KATANA')

def change_channel(channel=1):
    midi_output.send(mido.Message('control_change', control=0x50, value=channel))

def set_gain(level):
    midi_output.send(mido.Message('control_change', control=0x51, value=level))

if is_fist(hand_landmarks):
    set_gain(30)
