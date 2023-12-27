import cv2 as cv
import numpy as np
import time

def detect_balls(frame):

    # Convert the image to HSV color space
    hsv_frame = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

    # Define range of pink color in HSV
    lower_pink = np.array([0, 90, 50])
    upper_pink = np.array([10, 175, 255])

    # Threshold the HSV image to get only pink colors
    mask = cv.inRange(hsv_frame, lower_pink, upper_pink)

    # Find contours of pink areas
    contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
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

    return frame

def pre_process(frame):
    # Pre-process the image. Convert to HSV, crop.
    frame = cv.resize(frame, (640, 480))

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
cap = cv.VideoCapture('Videos/fast_shot_LED.avi')


#cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
#cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

#time.sleep(2)

# Variable to store the cropping rectangle
cropping_rectangle = None

try:
    init_time = time.time()
    counter = 0

    while True:
        success, img = cap.read()
        if not success: break

        # Only pre_process on the first frame
        if cropping_rectangle is None:
            cropped_img, (x, y, w, h) = pre_process(img)
            cropping_rectangle = (x, y, w, h)
            img = cropped_img
        else:
            # Crop the image using the previously determined cropping rectangle
            x, y, w, h = cropping_rectangle
            img = img[y:y+h, x:x+w]

        img = detect_balls(img)

        cv.imshow("img", img)
        cv.waitKey(30)
        counter += 1

except KeyboardInterrupt:
    print("Program Terminated")

finally:
    dt = time.time() - init_time
    print(f"Average: {counter/dt}")
    # Release resources
    cap.release()
    cv.destroyAllWindows()