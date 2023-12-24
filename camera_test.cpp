#include <stdio.h>
#include <opencv2/opencv.hpp>
#include <opencv2/imgproc/types_c.h>

using namespace cv;
using namespace std;
//
//g++ -o simple_opencv -Wall -std=c++11 camera_test.cpp -I/usr/include/opencv4/ -L/usr/local/lib/ -lopencv_
//core -lopencv_highgui -lopencv_imgproc -lopencv_videoio
//
int main(int argc, char** argv)
{
  VideoCapture cap("v4l2src device=/dev/video0 ! video/x-raw,width=640,height=360,format=MJPEG,framerate=260/1 ! videoconvert ! video/x-raw,format=BGR ! appsink");

  if (!cap.isOpened())
    {
      cout << "Failed to open camera." << endl;
      return -1;
    }

  for(;;)
    {
      Mat frame;
      cap >> frame;
      imshow("original", frame);
      waitKey(1);
    }

  cap.release();
}