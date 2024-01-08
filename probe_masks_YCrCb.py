import cv2 as cv
import numpy as np
import time
from picamera2 import Picamera2, Preview
import pprint
from libcamera import Transform


def generate_ycrcb_ranges(component, start, end, step):
    # Generate ranges for the specified YCrCb component
    return [(low, high) for low in range(start, end, step) for high in range(low, end, step) if low < high]

def probe_masks(frame, probetype):
    # Convert the image to YCrCb color space
    ycrcb_frame = cv.cvtColor(frame, cv.COLOR_BGR2YCrCb)

    # Define ranges for each component of YCrCb
    Y_ranges = generate_ycrcb_ranges('Y', 0, 255, 15)
    Cr_ranges = generate_ycrcb_ranges('Cr', 0, 90, 30)
    Cb_ranges = generate_ycrcb_ranges('Cb', 0, 90, 30)

    # Select the ranges based on probe type
    selected_ranges = {
        'Y': Y_ranges,
        'Cr': Cr_ranges,
        'Cb': Cb_ranges
    }.get(probetype, [])

    # Calculate the number of masks to display
    num_masks = len(selected_ranges)

    # Determine the size of the grid
    grid_size = int(np.ceil(np.sqrt(num_masks)))

    # Create a canvas to draw all masks
    mask_height, mask_width = frame.shape[:2]
    canvas_height = mask_height * grid_size
    canvas_width = mask_width * (grid_size + 1)  # +1 for the original frame
    canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

    # Draw the original frame on the canvas
    canvas[:mask_height, :mask_width] = frame

    # Generate and draw all masks
    for i, (low, high) in enumerate(selected_ranges):
        # Create the lower and upper ranges based on the selected component
        if probetype == 'Y':
            lower_range = np.array([low, 0, 0])
            upper_range = np.array([high, 128, 128])
        elif probetype == 'Cr':
            lower_range = np.array([0, low, 0])
            upper_range = np.array([255, high, 128])
        elif probetype == 'Cb':
            lower_range = np.array([0, 0, low])
            upper_range = np.array([255, 128, high])

        mask = cv.inRange(ycrcb_frame, lower_range, upper_range)
        mask_colored = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)

        # Calculate the position to place the mask on the canvas
        x = (i % grid_size) * mask_width + mask_width
        y = (i // grid_size) * mask_height

        # Place the mask onto the canvas
        canvas[y:y+mask_height, x:x+mask_width] = mask_colored

        # Put the text annotation
        text = f"Low: {low}, High: {high}"
        cv.putText(canvas, text, (x + 5, y + 20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return canvas



def pre_process(frame):
    # Pre-process the image. Convert to HSV, crop.
    #frame = cv.resize(frame, (640, 480))

    # Convert the image to HSV color space
    hsv_frame = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

    # Define range of green color in HSV
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([90, 255, 255])

    # Threshold the HSV image to get only green colors.
    # Outputs outside the range are set to black.
    mask = cv.inRange(hsv_frame, lower_green, upper_green)

    # Find contours
    contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    contours = [cunt for cunt in contours if cv.contourArea(cunt) > 500]

    # Find the bounding box that encloses all contours
    if contours:
        # Initialize variables for the bounding box coordinates
        x_min = y_min = float('inf')
        x_max = y_max = 0

        
        if contours:
            hull = cv.convexHull(np.concatenate(contours))

            # Draw the convex hull as a quadrilateral
            cv.polylines(frame, [hull], True, (0, 255, 0), 2)

                # Get bounding rectangle of the convex hull
            x, y, w, h = cv.boundingRect(hull)

            # Crop the region of interest (ROI) from the original frame
            cropped_frame = frame[y:y+h, x:x+w]

            return cropped_frame, (x,y,w,h)

    return frame

def display_scrollable_canvas(canvas, window_name="Masks Probe", section_height=480*3, section_width=640*4):
    total_height, total_width = canvas.shape[:2]
    num_vertical_sections = total_height // section_height
    num_horizontal_sections = total_width // section_width

    # Start with the first section
    current_vertical_section = 0
    current_horizontal_section = 0

    while True:
        # Determine the start and end Y coordinates of the current vertical section
        start_y = current_vertical_section * section_height
        end_y = min(start_y + section_height, total_height)

        # Determine the start and end X coordinates of the current horizontal section
        start_x = current_horizontal_section * section_width
        end_x = min(start_x + section_width, total_width)

        # Extract the section from the canvas
        section = canvas[start_y:end_y, start_x:end_x]

        # Display the section
        cv.imshow(window_name, section)

        # Wait for a key press
        key = cv.waitKey(0)

        if key == ord('q'):  # Quit
            break
        elif key == ord('s'):  # Next vertical section
            current_vertical_section = min(current_vertical_section + 1, num_vertical_sections - 1)
        elif key == ord('w'):  # Previous vertical section
            current_vertical_section = max(current_vertical_section - 1, 0)
        elif key == ord('d'):  # Next horizontal section
            current_horizontal_section = min(current_horizontal_section + 1, num_horizontal_sections - 1)
        elif key == ord('a'):  # Previous horizontal section
            current_horizontal_section = max(current_horizontal_section - 1, 0)
        elif key == ord('f'):  # Finish and exit
            return


def display_scrollable_canvas2(canvas, window_name="Masks Probe", section_height=1000):
    total_height = canvas.shape[0]
    num_sections = total_height // section_height

    # Start with the first section
    current_section = 0

    while True:
        # Determine the start and end Y coordinates of the current section
        start_y = current_section * section_height
        end_y = min(start_y + section_height, total_height)

        # Extract the section from the canvas
        section = canvas[start_y:end_y, :]

        # Display the section
        cv.imshow(window_name, section)

        # Wait for a key press
        key = cv.waitKey(0)

        if key == ord('q'):  # Quit
            break
        elif key == ord('n'):  # Next section
            current_section = min(current_section + 1, num_sections - 1)
        elif key == ord('p'):  # Previous section
            current_section = max(current_section - 1, 0)
        elif key == ord('f'):  # Finish and exit
            return


# Initialize video capture
# cap = cv.VideoCapture('Videos/dribble_slow_shot.avi')
#cap = cv.VideoCapture('Videos/fast_shot.avi')
#cap = cv.VideoCapture('Videos/fast_shot_LED.avi')
#cap = cv.VideoCapture('Videos/dribble_slow_shot_LED.avi')
# if not cap.isOpened():
#     print("Error: Could not open video.")
# else:
#     # Get the resolution of the video
#     frame_width = cap.get(cv.CAP_PROP_FRAME_WIDTH)
#     frame_height = cap.get(cv.CAP_PROP_FRAME_HEIGHT)
#     print(f"Resolution: {int(frame_width)} x {int(frame_height)}")

#     # Get frames per second
#     fps = cap.get(cv.CAP_PROP_FPS)
#     print(f"FPS: {fps}")

#     # Get the total number of frames in the video
#     frame_count = cap.get(cv.CAP_PROP_FRAME_COUNT)
#     print(f"Total Number of Frames: {frame_count}")

#     # Get the codec information
#     fourcc = cap.get(cv.CAP_PROP_FOURCC)
#     codec = "".join([chr((int(fourcc) >> 8 * i) & 0xFF) for i in range(4)])
#     print(f"Codec: {codec}")

#cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
#cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

#time.sleep(2)

picam2 = Picamera2()


mode = picam2.sensor_modes[0]
config = picam2.create_video_configuration(
    sensor={'output_size': mode['size'], 'bit_depth': mode['bit_depth']},
controls={"FrameDurationLimits": (8333, 8333)},
transform=Transform(hflip=1, vflip=1),
buffer_count=6)


picam2.configure(config)
pprint.pprint(picam2.camera_config)
picam2.start()

# Variable to store the cropping rectangle

cropping_rectangle = None

try:
    init_time = time.time()
    counter = 0

    while True:
        # success, img = cap.read()
        # if not success: break
        img = picam2.capture_array("main")
        img = cv.cvtColor(img[:, :, :3], cv.COLOR_RGBA2BGR)
        cv.imwrite('arducam_img.jpg', img)
        if cropping_rectangle is None:
            cropped_img, (x, y, w, h) = pre_process(img)
            cropping_rectangle = (x, y, w, h)
            img = cropped_img
        else:
            # Crop the image using the previously determined cropping rectangle
            x, y, w, h = cropping_rectangle
            img = img[y:y+h, x:x+w]

        # Generate the canvas with masks
        canvas = probe_masks(img,'Y')

        # Display the canvas
        #cv.imshow("Masks Probe", canvas)
        display_scrollable_canvas(canvas,section_width=w*4,section_height=h*3)
        if cv.waitKey(0) & 0xFF == ord('q'):  # Break the loop if 'q' is pressed
            break



except KeyboardInterrupt:
    print("Program Terminated")

finally:
    dt = time.time() - init_time
    print(f"Average: {counter/dt}")
    # Release resources
    # cap.release()
    cv.destroyAllWindows()