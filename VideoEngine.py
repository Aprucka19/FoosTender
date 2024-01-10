import cv2 as cv
import numpy as np
import time

class VideoEngine:
    def __init__(self, verbose=False):
        self.last_seen_center = None
        self.cropping_rectangle = None
        self.gk_bar_coords = None
        self.show = verbose
        self.PITCH_WIDTH = 25.625
        self.SERVO_LIMIT = 7
        self.left_post = (self.PITCH_WIDTH - self.SERVO_LIMIT) / 2
        self.right_post = (self.PITCH_WIDTH + self.SERVO_LIMIT) / 2
        self.pre_processed = False

    def assert_processed(self):
        if (not self.pre_processed):
            raise RuntimeError("FRAME NOT PRE-PROCESSED")
        
    def show_image(self, title, image):
        cv.imshow(title, image)
        key = cv.waitKey(0) & 0xFF
        if key == ord('q'):
            raise RuntimeError("Program Terminated")
        cv.destroyAllWindows()

    def get_gk_target_pos(self, frame):
        frame = self.process_frame(frame)
        ball_pos = np.array(self.find_ball_pos(frame))
        # Returns the desired goalkeeper position (0-7in).
        if self.gk_bar_coords == None:
            return self.SERVO_LIMIT / 2
        elif np.any(ball_pos) is None:
            return self.SERVO_LIMIT / 2
        else:
            gk_left = np.array(self.gk_bar_coords[0])
            gk_right = np.array(self.gk_bar_coords[1])

            # Transfer each point to np. Calculate the orthogonal projection.
            leftgk_to_ball = np.subtract(ball_pos, gk_left)
            gk_bar = np.subtract(gk_right, gk_left)
            projection = np.dot(leftgk_to_ball, gk_bar) / np.dot(gk_bar, gk_bar) * gk_bar

            dist = np.linalg.norm(projection) / np.linalg.norm(gk_bar) * self.PITCH_WIDTH


            if (dist < self.left_post):
                target_pos = 0
            elif (dist > self.right_post):
                target_pos = self.SERVO_LIMIT
            else:
                target_pos = dist - self.left_post

            target_pos = np.round(target_pos, 2)

            if (self.show and ball_pos is not None):
                temp_frame = frame.copy()
                ball_proj_point = tuple(np.add(gk_left, projection).astype(int))
                ball_point = tuple(ball_pos.astype(int))
                cv.line(temp_frame, self.gk_bar_coords[0], self.gk_bar_coords[1], (0, 255, 0), thickness=2)
                cv.line(temp_frame, ball_point, ball_proj_point, (0, 255, 0), thickness=2)
                self.show_image(f'Target: {target_pos} Dist: {dist}', temp_frame)

            return target_pos

    def find_ball_pos(self, frame):
        ycrcb_frame = cv.cvtColor(frame, cv.COLOR_BGR2YCrCb)
        lower_red = np.array([40, 160, 100])
        upper_red = np.array([80, 255, 255])

        mask = cv.inRange(ycrcb_frame, lower_red, upper_red)

        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours = [cont for cont in contours if cv.contourArea(cont) > 25]
        
        closest_center = None  # Initialize the closest center as None initially
        min_distance = float('inf')  # Set a very high initial minimum distance
        
        if contours:
            for contour in contours:
                moments = cv.moments(contour)
                if moments["m00"] != 0:
                    center_x = int(moments["m10"] / moments["m00"])
                    center_y = int(moments["m01"] / moments["m00"])
                    
                    current_center = (center_x, center_y)
                    
                    if self.last_seen_center:  # Check if there's a last seen center
                        distance = np.linalg.norm(np.array(self.last_seen_center) - np.array(current_center))
                        if distance < min_distance:
                            min_distance = distance
                            closest_center = current_center
                    else:
                        closest_center = current_center

            if closest_center is not None:
                self.last_seen_center = closest_center  # Update last seen center

        return self.last_seen_center


    def process_frame(self, frame):
        if self.pre_processed:
            (x, y, w, h) = self.cropping_rectangle
            cropped_frame = frame[y:y+h, x:x+w]
            return cropped_frame

        else:
            # Pre-process the image. Convert to HSV, crop.
            #frame = cv.resize(frame, (640, 480))

            # Convert the image to HSV color space
            hsv_frame = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

            # Define range of green color in HSV
            lower_green = np.array([30, 0, 5])
            upper_green = np.array([120, 255, 255])

            # Threshold the HSV image to get only green colors.
            # Outputs outside the range are set to black.
            green_mask = cv.inRange(hsv_frame, lower_green, upper_green)

            # Find contours and sort by size.
            contours, _ = cv.findContours(green_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

            contours = [cunt for cunt in contours if cv.contourArea(cunt) > 500]


            # Find the bounding box that encloses all contours
            if len(contours) >= 8:
                # Initialize variables for the bounding box coordinates
                x_min = y_min = float('inf')
                x_max = y_max = 0

                field_hull = cv.convexHull(np.concatenate(contours))

                # Get bounding rectangle of the convex hull
                x, y, w, h = cv.boundingRect(field_hull)

                # Crop the region of interest (ROI) from the original frame
                cropped_frame = frame[y:y+h, x:x+w]

                # Crop the region of interest (ROI) from the original frame
                self.cropping_rectangle = (x, y, w, h)

                # Find the 5 contours closest to the GK bar (rank by y-pos).
                # Of the middle 5, find the left and right side contours (rank by x-pos).
                middle_contours = sorted(contours, key=lambda c: cv.moments(c)['m01'] / cv.moments(c)['m00'])[-9:-5]
                left_to_right = sorted(middle_contours, key=lambda c: cv.moments(c)['m10'] / cv.moments(c)['m00'])
                left_side = left_to_right[0]
                right_side = left_to_right[-1]

                # Find two points defining the GK bar.
                left_x = left_side[left_side[:, :, 0].argmin()][0][0] - x
                left_y = left_side[left_side[:, :, 1].argmax()][0][1] - y
                left_gk = (left_x, left_y)

                right_x = right_side[right_side[:, :, 0].argmax()][0][0] - x
                right_y = right_side[right_side[:, :, 1].argmax()][0][1] - y
                right_gk = (right_x, right_y)

                self.gk_bar_coords = [left_gk, right_gk]


                # We have pre-processed
                self.pre_processed = True

                if (self.show):
                    temp_frame = frame.copy()
                    cv.polylines(temp_frame, [field_hull], True, (0, 0, 255), 4)
                    cv.drawContours(temp_frame, contours, -1, (0, 255, 0), 1)
                    cropped_temp_frame = temp_frame[y:y+h, x:x+w]
                    cv.line(cropped_temp_frame, left_gk, right_gk, (255, 0, 0), 3)
                    self.show_image("Contours and Limits. GK Bar.", cropped_temp_frame)

                return cropped_frame


        return frame