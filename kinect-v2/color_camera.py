from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime

import time
import numpy as np
import cv2
import math



#   opencv images are matrices and row-major-order (row, column)
#   opencv pts and coordinates are (x,y)
#
#   x left to right
#   y top to bottom
#
depth_image_size = (424,512)
color_image_size = (1080,1920)
color_image_shape = (color_image_size[0],color_image_size[1],4)
color_size = color_image_size[0] * color_image_size[1]


class Color2CameraMap():
    def __init__(self, depth_frame):
        self._depth_frame = depth_frame

    def make_color_image(self, scale = 6):
        pass
    def get_camera_point(self, color_point):
        pass
    def get_camera_points(self, color_points):
        pass



kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Depth)



def makeZMap(depth_frame, scale = 8):
    depth_frame_ptr = np.ctypeslib.as_ctypes(depth_frame.flatten())

    # create camera space points for each pixel in the color frame
    TYPE_CameraSpacePointArray = PyKinectV2._CameraSpacePoint * color_size
    cameraPoints = TYPE_CameraSpacePointArray()

    image = np.zeros((int(color_image_size[0]/scale),int(color_image_size[1]/scale)),np.uint8)
        
    error_state = kinect._mapper.MapColorFrameToCameraSpace(depth_frame.size, depth_frame_ptr, color_size, cameraPoints)
    if error_state == 0:
        for iy in range(0,color_image_size[0], scale):
            for ix in range(0,color_image_size[1],scale):                
                z = float(cameraPoints[iy*1920 + ix].z)
                if math.isinf(z) or math.isnan(z):
                    z = 0
                image[int(iy/scale),int(ix/scale)] = int((z / 9.0) * 255)
        print(float(cameraPoints[0].z) )
        colored = cv2.applyColorMap(image, cv2.COLORMAP_HOT)


        center = (int(color_image_size[1]/(2*scale)), int(color_image_size[0]/(2*scale)))
        cv2.circle(colored, center, int(30/scale), (255,255,255))

        cv2.circle(colored, (10,100), int(30/scale), (255,255,255))

        z = float(cameraPoints[540*1920 + 540].z)

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(colored," {0:.3f}".format(z), center, font, 0.5,(255,255,255),2,cv2.LINE_AA)

        
        return colored

    return None

depth_frame_colorized = None
color_frame_flipped = None

while(1):
    if kinect.has_new_depth_frame():
        depth_frame = kinect.get_last_depth_frame()
        print(depth_frame.shape)
        mapping = makeZMap(depth_frame)

        #depth_frame = depth_frame.reshape(depth_image_size)
        #depth_frame = depth_frame * (256.0/np.amax(depth_frame))
        #depth_frame_colorized = cv2.applyColorMap(np.uint8(depth_frame), cv2.COLORMAP_AUTUMN)        

        if mapping is not None:
            cv2.imshow('color', mapping)


    #if kinect.has_new_color_frame():
        #color_frame = kinect.get_last_color_frame()
        #color_frame = color_frame.reshape(color_image_shape)
        #color_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGRA2BGR)
        #color_frame_flipped = cv2.flip(color_frame,1)

    if (cv2.waitKey(1) == 27):
        cv2.destroyAllWindows()
        kinect.close()
        break