from wifi_handler import WiFiClientHandler

HOST = "192.168.4.1"
PORT = 80

WiFiClientHandler(HOST, PORT).connect()



<<<<<<< Updated upstream
=======
    # Get palm landmarks (landmarks for wrist and base of each finger)
    palm_landmarks = [hand_landmarks.landmark[i] for i in [0, 1, 5, 9, 13, 17]]

    # Convert palm landmarks to absolute pixel coordinates
    palm_coords = [(int(lm.x * frame_width), int(lm.y * frame_height)) for lm in palm_landmarks]

    # Calculate the bounding rectangle around the palm
    x_min = min([coord[0] for coord in palm_coords]) - margin
    x_max = max([coord[0] for coord in palm_coords]) + margin
    y_min = min([coord[1] for coord in palm_coords]) - margin
    y_max = max([coord[1] for coord in palm_coords]) + margin

    # Clamp hitbox coordinates to stay within frame dimensions
    x_min = max(0, x_min)
    x_max = min(frame_width, x_max)
    y_min = max(0, y_min)
    y_max = min(frame_height, y_max)

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
                raised_fingers = detect_raised_fingers_with_hitbox(hand_landmarks, frame_width, frame_height, frame, margin=25)
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
>>>>>>> Stashed changes
