import cv2
import subprocess
import numpy as np

# Start libcamera-vid as a subprocess
process = subprocess.Popen(
    [
        "libcamera-vid",
        "--width", "640",
        "--height", "480",
        "--framerate", "30",
        "--output", "-",
        "--codec", "mjpeg"
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    bufsize=10
)

try:
    while True:
        # Read MJPEG data from stdout
        raw_frame = process.stdout.read(640 * 480 * 3)  # Adjust buffer size if needed
        if not raw_frame:
            break

        # Decode MJPEG to OpenCV frame
        frame = cv2.imdecode(np.frombuffer(raw_frame, dtype=np.uint8), cv2.IMREAD_COLOR)

        # Display the frame
        if frame is not None:
            cv2.imshow("Live Camera Feed", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    process.terminate()
    cv2.destroyAllWindows()
