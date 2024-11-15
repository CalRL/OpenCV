import cv2 as cv
import mediapipe as mp

# Initialize Mediapipe hands model
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Set up video capture
cap = cv.VideoCapture(0)

finger_tips = [4, 8, 12, 16, 20]
finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]


def detect_raised_fingers(hand_landmarks):
    raised_fingers = []

    # Calculate the palm bounding box
    palm_landmarks = [hand_landmarks.landmark[i] for i in [0, 5, 9, 13, 17]]
    min_x = min([lm.x for lm in palm_landmarks])
    max_x = max([lm.x for lm in palm_landmarks])
    min_y = min([lm.y for lm in palm_landmarks])
    max_y = max([lm.y for lm in palm_landmarks])

    # Thumb is considered raised if it's outside the palm bounding box and visible
    thumb_tip = hand_landmarks.landmark[4]
    if not (min_x <= thumb_tip.x <= max_x and min_y <= thumb_tip.y <= max_y):
        raised_fingers.append("Thumb")

    # Check other fingers
    for idx in range(1, 5):  # Skip thumb (idx = 0)
        tip = finger_tips[idx]
        tip_landmark = hand_landmarks.landmark[tip]

        # Finger is considered raised if:
        # 1. Tip is above its lower joint (normal finger raise check).
        # 2. Tip is outside the palm bounding box.
        if (tip_landmark.y < hand_landmarks.landmark[tip - 2].y and
                not (min_x <= tip_landmark.x <= max_x and min_y <= tip_landmark.y <= max_y)):
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

        # Flip the frame horizontally for a later selfie-view display
        frame = cv.flip(frame, 1)
        # Convert the color from BGR to RGB for Mediapipe
        rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

        # Process the frame and detect hands
        results = hands.process(rgb_frame)

        # Check if hands are detected
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks on the original frame
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
                )

                # Detect raised fingers
                raised_fingers = detect_raised_fingers(hand_landmarks)
                if raised_fingers:
                    if "Middle" in raised_fingers and len(raised_fingers) == 1:
                        text = "Gesture detected: Middle finger raised!"
                    else:
                        text = "Raised: " + ", ".join(raised_fingers)
                    cv.putText(frame, text, (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv.LINE_AA)
                else:
                    cv.putText(frame, "No fingers raised", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2,
                               cv.LINE_AA)

        # Display the frame with hand landmarks
        cv.imshow("Hand Tracking", frame)

        # Break the loop if 'q' is pressed
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv.destroyAllWindows()
