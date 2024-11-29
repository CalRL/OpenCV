import cv2 as cv
import mediapipe as mp
import numpy as np
from wifi_handler import WiFiClientHandler
HOST = "192.168.4.1"
PORT = 80

client_handler = WiFiClientHandler(HOST, PORT)
client_handler.connect()


# Initialize Mediapipe hands model
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Set up video capture
cap = cv.VideoCapture(0)

finger_tips = [4, 8, 12, 16, 20]
finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
palm_points = [0, 1, 5, 9, 13, 17]

hitbox_margin = 20
state = 0


def draw_polygon(frame, hand_landmarks):
    points = np.array([[int(hand_landmarks.landmark[i].x * frame.shape[1]),
                        int(hand_landmarks.landmark[i].y * frame.shape[0])]
                       for i in [0, 1, 5, 9, 13, 17]], dtype=np.int32)

    hull = cv.convexHull(points)

    rect = cv.minAreaRect(hull)

    box = cv.boxPoints(rect)
    box = np.int0(box)

    cv.polylines(frame, [box], isClosed=True, color=(0, 255, 0), thickness=2)

def calculate_bounding_box(palm_coords):
    x_min = min([coord[0] for coord in palm_coords]) - hitbox_margin
    x_max = max([coord[0] for coord in palm_coords]) + hitbox_margin

    y_min = min([coord[1] for coord in palm_coords]) - hitbox_margin
    y_max = max([coord[1] for coord in palm_coords]) + hitbox_margin

    return [x_min, x_max, y_min, y_max]

def detect_raised_fingers_with_hitbox(hand_landmarks, frame_width, frame_height, frame):
    raised_fingers = []

    # Get palm landmarks (landmarks for wrist and base of each finger)
    palm_landmarks = [hand_landmarks.landmark[i] for i in palm_points]
    # Convert palm landmarks to absolute pixel coordinates
    palm_coords = [(int(lm.x * frame_width), int(lm.y * frame_height)) for lm in palm_landmarks]

    # Calculate the bounding rectangle around the palm
    coords = calculate_bounding_box(palm_coords)

    # Clamp hitbox coordinates to stay within frame dimensions
    x_min = max(0, coords[0])
    x_max = min(frame_width, coords[1])
    y_min = max(0, coords[2])
    y_max = min(frame_height, coords[3])

    # Visualize the wider palm hitbox
    cv.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 255), 2)

    # Check if finger tips are inside the hitbox
    for idx in range(5):  # Check all fingers
        tip = finger_tips[idx]
        tip_landmark = hand_landmarks.landmark[tip]
        tip_x = int(tip_landmark.x * frame_width)
        tip_y = int(tip_landmark.y * frame_height)

        # If the tip is outside the hitbox, consider the finger raised
        if not (x_min <= tip_x <= x_max and y_min <= tip_y <= y_max):
            raised_fingers.append(finger_names[idx])

    return raised_fingers


with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
) as hands:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        frame_height, frame_width, _ = frame.shape

        # Flip the frame horizontally for a selfie-view display
        frame = cv.flip(frame, 1)
        # Convert the color from BGR to RGB for Mediapipe
        rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

        # Process the frame and detect hands
        results = hands.process(rgb_frame)

        # Check if hands are detected
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks on the frame
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
                )

                # Detect raised fingers with wider hitbox logic
                raised_fingers = detect_raised_fingers_with_hitbox(hand_landmarks, frame_width, frame_height, frame)
                if raised_fingers:
                    if len(raised_fingers) == 5 and state != 1:
                        state = 1
                        client_handler.send_message("Raised")

                    # if "Middle" in raised_fingers and len(raised_fingers) == 5:
                    #     text = "Gesture detected: Middle finger raised!"
                    # else:
                    #     text = "Raised: " + ", ".join(raised_fingers)
                    # cv.putText(frame, text, (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv.LINE_AA)
                elif state != 0:
                    state = 0
                    client_handler.send_message("Not raised")
                else:
                    cv.putText(frame, "No fingers raised", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2,
                               cv.LINE_AA)

        # Display the frame with hand landmarks
        cv.imshow("Hand Tracking", frame)

        # Break the loop if 'q' is pressed
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
client_handler.disconnect()
cap.release()
cv.destroyAllWindows()
