import cv2 as cv
import numpy as np
import time

import cv2 as cv
import numpy as np

def detect_balls_YCrCb(frame):
    # Convert the image to YCrCb color space
    ycrcb_frame = cv.cvtColor(frame, cv.COLOR_BGR2YCrCb)

    # Define range of red color in YCrCb
    # Note: These values might need to be adjusted based on your specific use case
    lower_red = np.array([0, 150, 110])
    upper_red = np.array([135, 180, 180])

    # Create a mask for the red color range
    mask = cv.inRange(ycrcb_frame, lower_red, upper_red)

    # Find contours of red areas
    contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    contours = [cont for cont in contours if cv.contourArea(cont) > 100]
    
    if contours:
        for contour in contours:
            moments = cv.moments(contour)
            if moments["m00"] != 0:
                center_x = int(moments["m10"] / moments["m00"])
                center_y = int(moments["m01"] / moments["m00"])
                
                # Draw a cross at the center of mass
                cv.drawMarker(frame, (center_x, center_y), (0, 255, 0), markerType=cv.MARKER_CROSS, markerSize=20, thickness=2)

    return frame, mask




def detect_balls(frame):

    # Convert the image to HSV color space
    hsv_frame = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

    # Define range of pink color in HSV
    lower_range1 = np.array([130, 100, 100])
    upper_range1 = np.array([179, 200, 255])

    # Define the second range of colors in HSV
    lower_range2 = np.array([0, 150, 0])
    upper_range2 = np.array([10, 200, 255])

    # Create masks for each color range
    mask1 = cv.inRange(hsv_frame, lower_range1, upper_range1)
    mask2 = cv.inRange(hsv_frame, lower_range2, upper_range2)

    # Combine the two masks
    combined_mask = cv.bitwise_or(mask1, mask2)



    # Find contours of pink areas
    contours, _ = cv.findContours(combined_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    contours = [cunt for cunt in contours if cv.contourArea(cunt) > 70]
    
    if contours:
        for contour in contours:
            moments = cv.moments(contour)
            if moments["m00"] != 0:
                center_x = int(moments["m10"] / moments["m00"])
                center_y = int(moments["m01"] / moments["m00"])
                
                # Draw a cross at the center of mass
                cv.drawMarker(frame, (center_x, center_y), (0, 255, 0), markerType=cv.MARKER_CROSS, markerSize=20, thickness=2)
        #cv.drawContours(frame, contours, -1, (0, 255, 0), 2)

    return frame,combined_mask


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


# Initialize video capture
cap = cv.VideoCapture('Videos/dribble_slow_shot.avi')
#cap = cv.VideoCapture('Videos/fast_shot.avi')
#cap = cv.VideoCapture('Videos/fast_shot_LED.avi')
#cap = cv.VideoCapture('Videos/dribble_slow_shot_LED.avi')
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


# Variable to store the cropping rectangle
cropping_rectangle = None

try:
    init_time = time.time()
    counter = 0

    while True:
        success, img = cap.read()
        if not success: break

        if cropping_rectangle is None:
            cropped_img, (x, y, w, h) = pre_process(img)
            cropping_rectangle = (x, y, w, h)
            img = cropped_img
        else:
            # Crop the image using the previously determined cropping rectangle
            x, y, w, h = cropping_rectangle
            img = img[y:y+h, x:x+w]

        img,mask = detect_balls_YCrCb(img)

        show = False    
        if show:
            # Convert mask to a 3-channel image so it can be stacked with the color frame
            mask_colored = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)
            
            # Stack both images side-by-side
            combined_image = np.hstack((img, mask_colored))

            cv.imshow("Combined - Image and Mask", combined_image)
            if cv.waitKey(10) & 0xFF == ord('q'):  # Break the loop if 'q' is pressed
                break
        counter += 1

except KeyboardInterrupt:
    print("Program Terminated")

finally:
    dt = time.time() - init_time
    print(f"Average: {counter/dt}")
    # Release resources
    cap.release()
    cv.destroyAllWindows()