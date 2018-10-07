from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime

import time
import numpy as np
import cv2
import sys

color_image_size = (1080,1920)
color_image_shape = (1080,1920,4)

kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color)

while(1):
    if kinect.has_new_color_frame():
        color_frame = kinect.get_last_color_frame()
        color_frame = color_frame.reshape(color_image_shape)

        color_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGRA2BGR)
        color_flipped = cv2.flip(color_frame,1)


        cv2.imshow('color',color_flipped)
    
    if (cv2.waitKey(1) == 27):
        cv2.destroyAllWindows()
        kinect.close()
        break