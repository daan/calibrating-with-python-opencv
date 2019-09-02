from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime

import time
import math
import numpy as np
import cv2
import sys

#
# initial version ported from https://github.com/Kinect/PyKinect2/blob/master/examples/PyKinectBodyGame.py
# removed pygame dependency, draw with opencv
#
# added simple recording of 3D coordinates
#

color_image_size = (1080,1920)
color_image_shape = (1080,1920,4)

kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Body)

def draw_skeleton(color_flipped, skeleton_id, joints):
    for j in joints:
        if math.isinf(j.x) or math.isinf(j.y):
            continue
        cv2.circle(color_flipped, ( 1920-int(j.x), int(j.y)), 5, (0,0,255), -1)

joints_in_color_space = []

while(1):

    if kinect.has_new_body_frame():
        bodies = kinect.get_last_body_frame()
        if bodies is not None: 
            for i in range(0, kinect.max_body_count):
                body = bodies.bodies[i]
                if not body.is_tracked: 
                    continue 
                joints = body.joints 

                # convert joint coordinates to color space 
                joints_in_color_space = kinect.body_joints_to_color_space(joints)


                if joints[0].TrackingState != PyKinectV2.TrackingState_NotTracked and joints[0].TrackingState != PyKinectV2.TrackingState_Inferred:
                    print( joints[0].Position.x, joints[0].Position.y, joints[0].Position.z )



    

    if kinect.has_new_color_frame():
        color_frame = kinect.get_last_color_frame()
        color_frame = color_frame.reshape(color_image_shape)

        color_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGRA2BGR)
        color_flipped = cv2.flip(color_frame,1)

        draw_skeleton(color_flipped, i, joints_in_color_space)
        

        cv2.imshow('color',color_flipped)
    

    if (cv2.waitKey(1) == 27):
        cv2.destroyAllWindows()
        kinect.close()
        break