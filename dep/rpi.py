import cv2 as cv
import mediapipe as mp
import subprocess
import numpy as np
import os

# Force OpenCV to use X11 backend for GUI
os.environ["QT_QPA_PLATFORM"] = "xcb"

mode = input("RPI Mode? [Y/N]").strip()

if mode.lower() == "y":
    process = subprocess.Popen(
        [
            "libcamera-vid",
            "--width", "640",
            "--height", "480",
            "--framerate", "30",
            "--output", "-",
            "--codec", "mjpeg",
            "--nopreview"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=10
    )
else:
    cv.setUseOptimized(True)

    
    print('Optimized: ', cv.useOptimized())
    print('OpenCL: ', cv.ocl.useOpenCL())
    
    cap = cv.VideoCapture(0, cv.CAP_V4L2)
    cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv.CAP_PROP_FPS, 8)
# Mediapipe initialization
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
finger_tips = [4, 8, 12, 16, 20]
finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

def detect_raised_fingers_with_hitbox(hand_landmarks, frame_width, frame_height, frame, margin=20):
    raised_fingers = []
    palm_landmarks = [hand_landmarks.landmark[i] for i in [0, 1, 5, 9, 13, 17]]
    palm_coords = [(int(lm.x * frame_width), int(lm.y * frame_height)) for lm in palm_landmarks]

    x_min = max(0, min(coord[0] for coord in palm_coords) - margin)
    x_max = min(frame_width, max(coord[0] for coord in palm_coords) + margin)
    y_min = max(0, min(coord[1] for coord in palm_coords) - margin)
    y_max = min(frame_height, max(coord[1] for coord in palm_coords) + margin)

    cv.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 255), 2)

    for idx in range(5):
        tip = finger_tips[idx]
        tip_landmark = hand_landmarks.landmark[tip]
        tip_x, tip_y = int(tip_landmark.x * frame_width), int(tip_landmark.y * frame_height)

        if not (x_min <= tip_x <= x_max and y_min <= tip_y <= y_max):
            raised_fingers.append(finger_names[idx])

    return raised_fingers

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.3
) as hands:
    while True:
        if mode.lower() == "y":
            raw_frame = process.stdout.read(1024 * 1024)  # Dynamically read up to 1MB
            if not raw_frame:
                print("No frame received. Exiting...")
                break

            frame = cv.imdecode(np.frombuffer(raw_frame, dtype=np.uint8), cv.IMREAD_COLOR)
            if frame is None:
                print("Failed to decode frame. Skipping...")
                continue
        else:
            success, frame = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

        frame_height, frame_width, _ = frame.shape
        frame = cv.flip(frame, 1)
        rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )
                raised_fingers = detect_raised_fingers_with_hitbox(hand_landmarks, frame_width, frame_height, frame)
                if raised_fingers:
                    cv.putText(frame, f"Raised: {', '.join(raised_fingers)}", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv.LINE_AA)

        cv.imshow("Hand Tracking", frame)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

if mode.lower() != "y":
    cap.release()
else:
    process.terminate()
cv.destroyAllWindows()
