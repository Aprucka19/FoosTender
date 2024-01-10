
from picamera2 import Picamera2, Preview
import time
import cv2 as cv
import pprint
from libcamera import Transform, controls


def show_image(title, image):
        bgr = cv.cvtColor(image, cv.COLOR_YUV2BGR_I420)
        cv.imshow(title, bgr)
        key = cv.waitKey(30) & 0xFF
        if key == ord('q'):
            raise KeyboardInterrupt("Program Terminated")


picam2 = Picamera2()
mode = picam2.sensor_modes[0]
config = picam2.create_video_configuration(
    sensor={'output_size': mode['size'], 'bit_depth': mode['bit_depth']},
controls={"FrameDurationLimits": (8333, 8333), "Brightness": 0.0, "AwbEnable": False, "AwbMode": controls.AwbModeEnum.Indoor, "ExposureValue": 4.0},
transform=Transform(hflip=1, vflip=1),
lores={"size": (320,240)}, 
encode="lores",
display="lores",
buffer_count=6)


picam2.configure(config)


print(f"PERMITTED FRAME RATES: {picam2.camera_controls['FrameDurationLimits']} \n ----------------")
pprint.pprint(picam2.camera_config)



#pprint.pprint(picam2.sensor_modes)

#raise KeyboardInterrupt

picam2.start()
# cap = cv.VideoCapture("/dev/video0", cv.CAP_V4L2)

time.sleep(5)

print("Starting Test:")
counter = 0
show_img = True
init_time = time.time()

try:
    while True:
        image = picam2.capture_array("lores")
        bgr = cv.cvtColor(image, cv.COLOR_YUV2BGR_I420)
        if bgr is not None:
            bgr = None
            counter += 1
        # ret, image = cap.read()
        if show_img:
            show_image("Current View", image)

except KeyboardInterrupt:
    print("Program Terminated \n \n")
finally:
    dt = time.time() - init_time
    print(f"Average: {counter/dt}")
    cv.destroyAllWindows()





# SETTING A CAMERA MODE

# mode = picam2.sensor_modes[0]
# config = picam2.create_preview_configuration(sensor={'output_size': mode['size'], 'bit_depth':
# mode['bit_depth']})
# picam2.configure(config)
