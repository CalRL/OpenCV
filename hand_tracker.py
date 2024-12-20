import cv2 as cv
import mediapipe as mp
import numpy as np
from typing import List, Optional
from wifi_handler import WiFiClientHandler
import threading


class HandTracker:
    def __init__(self,
                 main,
                 max_hands: int = 2,
                 detection_confidence: float = 0.7,
                 tracking_confidence: float = 0.5,
                 hitbox_margin: int = 20,
                 ):
        """
        Initialize HandTracker with configurable parameters and optional WiFi connection

        Args:
            host (Optional[str]): WiFi host address. None disables WiFi connection.
            port (Optional[int]): WiFi port number. None disables WiFi connection.
            max_hands (int): Maximum number of hands to detect
            detection_confidence (float): Minimum detection confidence
            tracking_confidence (float): Minimum tracking confidence
            hitbox_margin (int): Margin around palm for finger detection
        """
        # WiFi Communication Setup
        self.client_handler = None
        try:
            print(f"Connecting to arduino")
            self.client_handler = WiFiClientHandler(main)
            print("Handler created")
            self.client_handler.connect()
            print("WiFi connection established.")

            self.messages = []
            self.listening_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
            self.listening_thread.start()

        except Exception as e:
            print(f"Failed to establish WiFi connection: {e}")
            raise

        # Hand Detection Constants
        self.finger_tips = [4, 8, 12, 16, 20]
        self.finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
        self.palm_points = [0, 1, 5, 9, 13, 17]
        self.hitbox_margin = int(hitbox_margin + hitbox_margin/100)

        # Hand Detection State
        self.state = 0

        # MediaPipe Setup
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils

        # Hands Model Configuration
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )

    def listen_for_messages(self):
        """
        Loop to continuously call receive_message.
        """
        while True:
            message = self.client_handler.receive_message()
            if message:
                self.messages.append(message)

    def draw_polygon(self, frame, hand_landmarks):
        """
        Draw a polygon around the palm using convex hull and minimum area rectangle.

        Args:
            frame: Input video frame
            hand_landmarks: MediaPipe hand landmarks
        """
        # Extract palm points and convert to pixel coordinates
        points = np.array([[int(hand_landmarks.landmark[i].x * frame.shape[1]),
                            int(hand_landmarks.landmark[i].y * frame.shape[0])]
                           for i in [0, 1, 5, 9, 13, 17]], dtype=np.int32)

        # Calculate convex hull
        hull = cv.convexHull(points)

        # Find minimum area rectangle
        rect = cv.minAreaRect(hull)

        # Convert rectangle to box points
        box = cv.boxPoints(rect)
        box = np.int0(box)

        # Draw polygon on the frame
        cv.polylines(frame, [box], isClosed=True, color=(0, 255, 0), thickness=2)

    def calculate_bounding_box(self, palm_coords):
        """
        Calculate bounding box with margin for palm landmarks.

        Args:
            palm_coords (List[tuple]): Coordinates of palm landmarks

        Returns:
            List[int]: Bounding box coordinates [x_min, x_max, y_min, y_max]
        """
        x_min = min([coord[0] for coord in palm_coords]) - self.hitbox_margin
        x_max = max([coord[0] for coord in palm_coords]) + self.hitbox_margin
        y_min = min([coord[1] for coord in palm_coords]) - self.hitbox_margin
        y_max = max([coord[1] for coord in palm_coords]) + self.hitbox_margin

        return [x_min, x_max, y_min, y_max]

    def detect_raised_fingers(self,
                              hand_landmarks,
                              frame_width: int,
                              frame_height: int,
                              frame) -> List[str]:
        """
        Detect raised fingers based on palm hitbox.

        Args:
            hand_landmarks: MediaPipe hand landmarks
            frame_width (int): Width of video frame
            frame_height (int): Height of video frame
            frame: Current video frame

        Returns:
            List[str]: Names of raised fingers
        """
        raised_fingers = []

        # Get palm landmarks and convert to pixel coordinates
        palm_landmarks = [hand_landmarks.landmark[i] for i in self.palm_points]
        palm_coords = [(int(lm.x * frame_width), int(lm.y * frame_height)) for lm in palm_landmarks]

        # Calculate bounding box
        coords = self.calculate_bounding_box(palm_coords)

        # Clamp hitbox coordinates
        x_min = max(0, coords[0])
        x_max = min(frame_width, coords[1])
        y_min = max(0, coords[2])
        y_max = min(frame_height, coords[3])

        # Visualize palm hitbox
        cv.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 255), 2)

        # Check finger tips against hitbox
        for idx in range(5):
            tip = self.finger_tips[idx]
            tip_landmark = hand_landmarks.landmark[tip]
            tip_x = int(tip_landmark.x * frame_width)
            tip_y = int(tip_landmark.y * frame_height)

            # If tip is outside hitbox, consider finger raised
            if not (x_min <= tip_x <= x_max and y_min <= tip_y <= y_max):
                raised_fingers.append(self.finger_names[idx])

        return raised_fingers

    def process_frame(self, frame):
        """
        Process a single video frame for hand tracking

        Args:
            frame: Input video frame

        Returns:
            tuple: Processed frame and hand landmarks (if detected)
        """
        frame_height, frame_width, _ = frame.shape
        frame = cv.flip(frame, 1)
        rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

        # Detect hands
        results = self.hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
                )

                # Draw polygon around palm
                self.draw_polygon(frame, hand_landmarks)

                # Detect raised fingers
                hands = []
                raised_fingers = self.detect_raised_fingers(hand_landmarks, frame_width, frame_height, frame)
                hands.append(raised_fingers)

                # State and message handling (only if WiFi is connected)
                if self.client_handler:
                    if raised_fingers:
                        if len(raised_fingers) == 2 and "Index" in raised_fingers and "Pinky" in raised_fingers and self.state != 1:
                            self.state = 1
                            message = "STATE1"
                            self.client_handler.send_message(message)
                        elif self.state != 1 and not raised_fingers:
                            self.state = 0
                    elif self.state != 0:
                        self.state = 0

        return frame
    def run(self):
        """
        Main tracking loop
        """
        cap = cv.VideoCapture(0)

        try:
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    print("Ignoring empty camera frame.")
                    continue

                processed_frame = self.process_frame(frame)
                cv.imshow("Hand Tracking", processed_frame)

                if cv.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            # Disconnect WiFi only if a connection was established
            if self.client_handler:
                self.client_handler.disconnect()
            cap.release()
            cv.destroyAllWindows()

    # Rest of the existing methods remain the same...
