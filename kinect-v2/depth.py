from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime

import time
import numpy as np
import cv2

depth_image_size = (424,512)

kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Depth)

while(1):
    if kinect.has_new_depth_frame():
        depth_frame = kinect.get_last_depth_frame()
        depth_frame = depth_frame.reshape(depth_image_size)

        # map the depth frame to uint8 
        depth_frame = depth_frame * (256.0/np.amax(depth_frame))

        colorized_frame = cv2.applyColorMap(np.uint8(depth_frame), cv2.COLORMAP_JET)        
        cv2.imshow('depth',colorized_frame)
    
    if (cv2.waitKey(1) == 27):
        cv2.destroyAllWindows()
        kinect.close()
        break