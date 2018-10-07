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
depth_image_size = (424, 512)
color_image_size = (1080, 1920)
color_image_shape = (color_image_size[0], color_image_size[1], 4)
color_size = color_image_size[0] * color_image_size[1]


class Color2CameraMap():
    def __init__(self, depth_frame):
        self._depth_frame = depth_frame
        depth_frame_ptr = np.ctypeslib.as_ctypes(depth_frame.flatten())
        # create camera space points for each pixel in the color frame
        TYPE_CameraSpacePointArray = PyKinectV2._CameraSpacePoint * color_size
        self._camera_points = TYPE_CameraSpacePointArray()
        error_state = kinect._mapper.MapColorFrameToCameraSpace(
            depth_frame.size, depth_frame_ptr, color_size, self._camera_points)
        if error_state != 0:
            raise OSError("error {} in mapping: MapcolorFrameToCamera.".format(
                error_state))

    def make_color_image(self, divide_by=6):
        image = np.zeros((int(color_image_size[0] / divide_by),
                          int(color_image_size[1] / divide_by)), np.uint8)
        for iy in range(0, color_image_size[0], divide_by):
            for ix in range(0, color_image_size[1], divide_by):
                z = float(self._camera_points[iy * 1920 + ix].z)
                if math.isinf(z) or math.isnan(z):
                    z = 0
                image[int(iy / divide_by), int(ix / divide_by)] = int(
                    (z / 9.0) * 255)  # map 9 meters
        # apply a color map
        colored = cv2.applyColorMap(image, cv2.COLORMAP_HOT)
        return colored

    def get_camera_point(self, color_point):
        # find the coordinate in the image
        index = color_point[1] * color_image_size[1] + color_point[0]
        camera_point = self._camera_points[index]
        return [
            float(camera_point.x),
            float(camera_point.y),
            float(camera_point.z)
        ]

    def get_camera_points(self, color_points):
        r = []
        for p in color_points:
            r.append(self.get_camera_point(p))
        return r


kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color
                                         | PyKinectV2.FrameSourceTypes_Depth)

font = cv2.FONT_HERSHEY_SIMPLEX
        
while (1):
    if kinect.has_new_depth_frame():
        depth_frame = kinect.get_last_depth_frame()

        try:
            map = Color2CameraMap(depth_frame)
            divide_by = 6
            img = map.make_color_image(divide_by)

            # points are in (x,y)
            sample_point = [ int(1920/2), int(1080/2)]
            sample_point = [480, 240]
            p3d = map.get_camera_point( sample_point )
            print(p3d)
            # draw a reference circle at pt
            scaled_point = ( int( sample_point[0]/divide_by), int(sample_point[1]/divide_by) )
            cv2.circle(img, scaled_point, int(30/divide_by), (255,255,255))
            # print the distance.
            cv2.putText(img," {0:.3f}".format(p3d[2]), scaled_point, font, 8/divide_by,(255,255,255),2,cv2.LINE_AA)
            cv2.imshow('color', img)

        except OSError as err:
            print(err)

    if (cv2.waitKey(1) == 27):
        cv2.destroyAllWindows()
        kinect.close()
        break
