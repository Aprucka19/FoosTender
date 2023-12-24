import cv2 as cv
import numpy as np
import time

def detect_balls(frame):
    # Convert to grayscale
    gray_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur
    blurred_frame = cv.GaussianBlur(gray_frame, (9, 9), 2)
    
    # Detect circles using Hough Transform
    circles = cv.HoughCircles(blurred_frame, cv.HOUGH_GRADIENT, 1, 100, param1=100, param2=30, minRadius=75, maxRadius=400)
    
    return circles

# Initialize video capture
cap = cv.VideoCapture(0)

cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)

cap.set(cv.CAP_PROP_FRAME_HEIGHT, 360)

time.sleep(2)

#cap.set(cv.CAP_PROP_EXPOSURE, -8.0)

while True:
    ret, frame = cap.read()
    if not ret: break

    cv.imshow("frame", frame)

    # Break the loop when 'q' is pressed
    if cv.waitKey(1) & 0xFF == ord('q'): break

# Release resources
cap.release()
cv.destroyAllWindows()
