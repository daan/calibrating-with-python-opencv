from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime

import time
import numpy as np
import cv2

ir_image_size = (424,512)

kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Infrared)

while(1):
    if kinect.has_new_infrared_frame():
        ir_frame = kinect.get_last_infrared_frame()
        ir_frame = ir_frame.reshape(ir_image_size)
        ir_frame = np.uint8(ir_frame/256)        
    

        cv2.imshow('ir',ir_frame)
    
    if (cv2.waitKey(1) == 27):
        cv2.destroyAllWindows()
        kinect.close()
        break