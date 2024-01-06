import cv2 as cv
import numpy as np
import time
from VideoEngine import VideoEngine
from Stepper import Stepper
DIR = 13
STEP = 18
ENA = 26
STOP = 21

# Variable to store the cropping rectangle
cropping_rectangle = None

# Initialize video capture
#cap = cv.VideoCapture('Videos/fast_shot.avi')
#cap = cv.VideoCapture('Videos/fast_shot.avi')
#cap = cv.VideoCapture('Videos/fast_shot_LED.avi')
cap = cv.VideoCapture('Videos/dribble_slow_shot_LED.avi')

step = Stepper(ENA, STEP, DIR, STOP)
step.initialize()


if not cap.isOpened():
    print("Error: Could not open video.")
else:
    # Get the resolution of the video
    frame_width = cap.get(cv.CAP_PROP_FRAME_WIDTH)
    frame_height = cap.get(cv.CAP_PROP_FRAME_HEIGHT)
    print(f"Resolution: {int(frame_width)} x {int(frame_height)}")

    # Get frames per second
    fps = cap.get(cv.CAP_PROP_FPS)
    print(f"FPS: {fps}")

    # Get the total number of frames in the video
    frame_count = cap.get(cv.CAP_PROP_FRAME_COUNT)
    print(f"Total Number of Frames: {frame_count}")

    # Get the codec information
    fourcc = cap.get(cv.CAP_PROP_FOURCC)
    codec = "".join([chr((int(fourcc) >> 8 * i) & 0xFF) for i in range(4)])
    print(f"Codec: {codec}")

try:
    init_time = time.time()
    counter = 0
    engine = VideoEngine(verbose=False)

    while True:
        for i in range(0,1):
            success, img = cap.read()
        if not success: break
        gk_pos = engine.get_gk_target_pos(img)
        step.move(gk_pos)
        counter += 1
        
except KeyboardInterrupt:
    print("Program Terminated")

finally:
    dt = time.time() - init_time
    print(f"Average: {counter/dt}")
    # Release resources
    cap.release()
    cv.destroyAllWindows()
    step.cleanup()