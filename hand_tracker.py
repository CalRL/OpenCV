import cv2 as cv
import mediapipe as mp
import numpy as np
from typing import List, Optional

from wifi_handler import WiFiClientHandler, send_message
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
        self.main = main
        self.config = self.main.get_config()
        self.mode = self.config["tracker"]["mode"]
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

    def detect_in_box(self, hand_landmarks, frame_width, frame_height):
        """
        Check if all hand landmarks fall into the specified positional box.

        Args:
            hand_landmarks: MediaPipe hand landmarks
            frame_width (int): Width of the video frame
            frame_height (int): Height of the video frame

        Returns:
            bool: True if all landmarks are within the box, False otherwise.
        """
        # Get box configuration
        box_x_min, box_y_min, box_x_max, box_y_max = self.get_box_boundaries(frame_width, frame_height)

        # Convert all landmarks to pixel coordinates
        landmark_coords = [(int(lm.x * frame_width), int(lm.y * frame_height)) for lm in hand_landmarks.landmark]

        # Check if all landmarks are inside the box
        all_in_box = all(
            box_x_min <= x <= box_x_max and
            box_y_min <= y <= box_y_max
            for x, y in landmark_coords
        )

        return all_in_box


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

    def get_box_boundaries(self, frame_width, frame_height):
        """
        Calculate the boundaries of the box based on the configuration.

        Args:
            frame_width (int): Width of the video frame
            frame_height (int): Height of the video frame

        Returns:
            tuple: (box_x_min, box_y_min, box_x_max, box_y_max)
        """
        tracker_config = self.config.get("tracker", {})
        box_config = tracker_config.get("box", {"width": 640, "height": 480, "x": 320, "y": 420})

        # Fixed box size and center position
        box_width = box_config.get("width", 640)
        box_height = box_config.get("height", 480)
        box_center_x = box_config.get("x", frame_width // 2)
        box_center_y = box_config.get("y", frame_height // 2)

        # Calculate box boundaries
        box_x_min = int(box_center_x - box_width / 2)
        box_y_min = int(box_center_y - box_height / 2)
        box_x_max = int(box_center_x + box_width / 2)
        box_y_max = int(box_center_y + box_height / 2)

        return box_x_min, box_y_min, box_x_max, box_y_max


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

        # Always visualize the box if mode is BOX
        if self.mode == "BOX":
            box_x_min, box_y_min, box_x_max, box_y_max = self.get_box_boundaries(frame_width, frame_height)
            cv.rectangle(frame, (box_x_min, box_y_min), (box_x_max, box_y_max), (255, 255, 0), 2)

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

                if self.mode == "GESTURE":
                    # Detect raised fingers
                    raised_fingers = self.detect_raised_fingers(hand_landmarks, frame_width, frame_height, frame)
                    if raised_fingers:
                        if len(raised_fingers) == 2 and "Index" in raised_fingers and "Pinky" in raised_fingers and self.state != 1:
                            self.state = 1
                            command = "FLIPSTATE"
                            timer = self.main.start_timer()
                            message = timer + ":" + command
                            self.client_handler.send_message(message)
                        # More accessible than pinky AND index
                        # # For people with arthritis for example
                        elif len(raised_fingers) == 1 and "Index" in raised_fingers and self.state != 1:
                            self.state = 1
                            command = "FLIPSTATE"
                            timer = self.main.start_timer()
                            message = timer + ":" + command
                            self.client_handler.send_message(message)

                        elif self.state == 1 and not raised_fingers:
                            self.state = 0
                    elif self.state != 0:
                        self.state = 0

                elif self.mode == "BOX":
                    # Check if all landmarks are in the box
                    all_in_box = self.detect_in_box(hand_landmarks, frame_width, frame_height)

                    if all_in_box and self.state != 1:
                        self.state = 1
                        command = "FLIPSTATE"
                        timer = self.main.start_timer()
                        message = f"{timer}:{command}"
                        self.client_handler.send_message(message)

                    elif self.state == 1 and not all_in_box:
                        self.state = 0
        return frame

    def run(self):
        """
        Main tracking loop
        """
        frame_height: int = self.config["tracker"]["frame_height"]
        frame_width: int = self.config["tracker"]["frame_width"]
        thread_count: int = self.config["tracker"]["max_threads"]
        framerate: int = self.config["tracker"]["framerate"]

        cv.setUseOptimized(True)
        cv.setNumThreads(thread_count)

        cap = cv.VideoCapture(0, cv.CAP_DSHOW)
        cap.set(cv.CAP_PROP_FRAME_WIDTH, frame_width)
        cap.set(cv.CAP_PROP_FRAME_HEIGHT, frame_height)
        cap.set(cv.CAP_PROP_FPS, framerate)

        try:
            is_s_pressed = False
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    print("Ignoring empty camera frame.")
                    continue

                processed_frame = self.process_frame(frame)
                cv.imshow("Hand Tracking", processed_frame)

                key = cv.waitKey(1) & 0xFF

                # Kill process if key is pressed
                if key in [ord('q'), ord('Q')]:
                    break
                # Get the state and log it to db
                elif key in [ord('s'), ord('S')]:
                    if not is_s_pressed:
                        get_state(self.main.start_timer())
                        is_s_pressed = True
                # Prevent the user from accidentally sending multiple requests
                # To not accidentally DoS the device
                elif key != ord('s'):
                    is_s_pressed = False
        finally:
            # Disconnect WiFi only if a connection was established
            if self.client_handler:
                self.client_handler.disconnect()
            cap.release()
            cv.destroyAllWindows()


def get_state(timer_id):
    send_message(f"{timer_id}:GETSTATE")
