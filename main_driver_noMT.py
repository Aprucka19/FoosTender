import cv2 as cv
import numpy as np
import time
from VideoEngine import VideoEngine
from Stepper import Stepper
from picamera2 import Picamera2, Preview
import pprint
from libcamera import Transform
import threading

DIR = 13
STEP = 18
ENA = 6
STOP = 21

LIVE_CAPTURE = True
verbose = False
timing = True

video_path = 'Videos/dribble_slow_shot_LED.avi'
# video_path = 'Videos/fast_shot.avi'
# video_path = 'Videos/fast_shot.avi'
# video_path = 'Videos/fast_shot_LED.avi'

latest_frame = None

# def pull_frame():
#     if LIVE_CAPTURE:
#         # Initialize PiCamera
#         picam2 = Picamera2()
#         mode = picam2.sensor_modes[0]
#         config = picam2.create_video_configuration(
#             sensor={'output_size': mode['size'], 'bit_depth': mode['bit_depth']},
#         controls={"FrameDurationLimits": (8333, 8333)},
#         transform=Transform(hflip=1, vflip=1),
#         lores={"size": (320,240)}, 
#         encode="lores",
#         display="lores",
#         buffer_count=6)
#         # Set the configuration and start camera
#         picam2.configure(config)
#         picam2.start()
#         # print(f"PERMITTED FRAME RATES: {picam2.camera_controls['FrameDurationLimits']} \n ----------------")
#         # pprint.pprint(picam2.camera_config)

#     else:
#         # Initialize video capture
#         cap = cv.VideoCapture(video_path)

#     while True:
#         img = picam2.capture_array("lores")
#         latest_frame = cv.cvtColor(img, cv.COLOR_YUV2BGR_I420)

    

step = Stepper(ENA, STEP, DIR, STOP, verbose, timing)
step.initialize()

if LIVE_CAPTURE:
        # Initialize PiCamera
        picam2 = Picamera2()
        mode = picam2.sensor_modes[0]
        config = picam2.create_video_configuration(
            sensor={'output_size': mode['size'], 'bit_depth': mode['bit_depth']},
        controls={"FrameDurationLimits": (8333, 8333)},
        transform=Transform(hflip=1, vflip=1),
        lores={"size": (320,240)}, 
        encode="lores",
        display="lores",
        buffer_count=6)
        # Set the configuration and start camera
        picam2.configure(config)
        picam2.start()
        # print(f"PERMITTED FRAME RATES: {picam2.camera_controls['FrameDurationLimits']} \n ----------------")
        # pprint.pprint(picam2.camera_config)

else:
    # Initialize video capture
    cap = cv.VideoCapture(video_path)

try:
    engine = VideoEngine(verbose)
    if timing:
        init_time = time.time()
        func_time = init_time
        cam_time = 0
        img_time = 0
        stepper_time = 0
        counter = 0

    while True:
        if LIVE_CAPTURE:
            img = picam2.capture_array("lores")
            img = cv.cvtColor(img, cv.COLOR_YUV2BGR_I420)
            if timing:
                cur_time = time.time()
                cam_time += cur_time - func_time
                func_time = cur_time
        else:
            success, img = cap.read()

        gk_pos = engine.get_gk_target_pos(img)
        if timing:
            cur_time = time.time()
            img_time += cur_time - func_time
            func_time = cur_time


        step.move(gk_pos)

        if timing:
            cur_time = time.time()
            stepper_time += cur_time - func_time
            func_time = cur_time

            counter += 1
        
except KeyboardInterrupt:
    print("Program Terminated")

finally:
    if timing:
        dt = time.time() - init_time
        print(f"Average FPS: {counter/dt}. Total Time: {dt}")
        print(f"Average CAM: {counter/cam_time}. Total Time: {cam_time}")
        print(f"Average IMG: {counter/img_time}. Total Time: {img_time}")
        print(f"Average STEPPER: {counter/stepper_time}. Total Time: {stepper_time}")
    # Release resources
    if not LIVE_CAPTURE: 
        cap.release()
    cv.destroyAllWindows()
    step.cleanup()