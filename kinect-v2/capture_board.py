from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime

import time
import numpy as np
import cv2
import math
import json

import sys
import os

import argparse

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("folder", help="folder to save images")
ap.add_argument("-f", "--force", action="store_true", help="force overwrite in folder")

args = vars(ap.parse_args())

# make folder
target_folder = args['folder']
if os.path.isdir(target_folder):
    if args['force'] == False:
        print("{}: error: folder {} exists. Use --force to overwrite files.".format(os.path.basename(sys.argv[0]), target_folder))
        sys.exit()
else:
    os.makedirs(target_folder)




charuco_square_length = 140.0 / 1000 # chessboard square side length (normally in meters)
charuco_marker_length = 88.0 / 1000 # marker side length (same unit than squareLength)
squaresX = 5
squaresY = 7
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
board = cv2.aruco.CharucoBoard_create(squaresX,squaresY,charuco_square_length,charuco_marker_length,dictionary)

depth_image_size = (424, 512)
color_image_size = (1080, 1920)
color_image_shape = (color_image_size[0], color_image_size[1], 4)
color_size = color_image_size[0] * color_image_size[1]


# TODO: make a helper file (this is the same code as detect_charuco) 
def find_charuco_board(img, board, dictionary):
    corner_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.00001)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, dictionary) 


    if len(corners)>0:
        for corner in corners:
            cv2.cornerSubPix(gray, corner, winSize=(3,3), zeroZone=(-1,-1), criteria=corner_criteria)        
        ret, detectedCorners, detectedIds = cv2.aruco.interpolateCornersCharuco(corners,ids,gray,board)

        if detectedIds is None:
            return [], []

        if len(detectedCorners) != len(detectedIds):
            print("should not happen")
            return [],[]
        if detectedCorners is not None and detectedIds is not None and len(detectedCorners)>3:
             return detectedCorners, detectedIds
    return [], []    

# TODO: make a helper file (this is the same code as color_3d.py) 
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

    def get_camera_point(self, color_point, isFlipped = False):
        if isFlipped:
            color_point[0] = color_image_size[1] - color_point[0]
        # find the coordinate in the 3D map
        index = int(color_point[1] * color_image_size[1] + color_point[0])
        camera_point = self._camera_points[index]
        return [
            float(camera_point.x),
            float(camera_point.y),
            float(camera_point.z)
        ]



kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Depth)

font = cv2.FONT_HERSHEY_SIMPLEX

p3d = None
p2d = None
p2d = [480, 240]

corners3d = []
corners = []
ids = []

count = 0

while(1):
    if kinect.has_new_depth_frame():
        depth_frame = kinect.get_last_depth_frame()

        if p2d != None: 
            try:
                map = Color2CameraMap(depth_frame)            
                p3d = map.get_camera_point( p2d, True )    
                corners3d = []
                for c in corners:
                    x = round(c[0][0]) 
                    y = round(c[0][1])
                    c3d = map.get_camera_point( [x,y], True )  
                    corners3d.append(c3d)
            except OSError as err:
                print(err)
                p3d = None
        else:
            p3d = None

    if kinect.has_new_color_frame():
        color_frame = kinect.get_last_color_frame()
        color_frame = color_frame.reshape(color_image_shape)

        color_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGRA2BGR)
        color_flipped = cv2.flip(color_frame,1)

        color_org = color_flipped.copy()


        corners, ids = find_charuco_board(color_flipped, board, dictionary)
        if len(corners) > 0:
            cv2.aruco.drawDetectedCornersCharuco(color_flipped, corners, ids)
        
            # draw lines to depict the first marker (id_0 if not obstructed.....)
            x,y = corners[0][0][0], corners[0][0][1]
            p2d = [round(x),round(y)]
            cv2.line(color_flipped, (0,y),(1920,y),(0,0,255),2)
            cv2.line(color_flipped, (x,0),(x,1080),(255,0,0),2)            

            cv2.circle(color_flipped, (p2d[0], p2d[1]), 100, (255,255,255))

        if p2d != None and p3d != None:
            # draw the coordinates
            cv2.putText(color_flipped,"{0:.3f}".format(p3d[0]), (100,200), font, 4,(0,0,255), 6, cv2.LINE_AA)
            cv2.putText(color_flipped,"{0:.3f}".format(p3d[1]), (100,400), font, 4,(0,255,0), 6, cv2.LINE_AA)
            cv2.putText(color_flipped,"{0:.3f}".format(p3d[2]), (100,600), font, 4,(255,0,0), 6, cv2.LINE_AA)


        cv2.imshow('color',color_flipped)
    
    key = cv2.waitKey(1)

    if key == 27:
        cv2.destroyAllWindows()
        kinect.close()
        break
    elif key == 32:
        print("take picture")
        print(len(ids), len(corners3d))
        cv2.imwrite("{}/frame_{}_annotated.jpg".format(target_folder, count), color_flipped)

        cv2.imwrite("{}/frame_{}.jpg".format(target_folder, count), color_org)
        #write the coords
        points = []
        for i in range(len(ids)):
            p = {}
            p['id'] = str(ids[i][0])
            p['x'] = corners3d[i][0]
            p['y'] = corners3d[i][1]
            p['z'] = corners3d[i][2]
            points.append(p)
        json_data = { "charucoCorners": points }
        with open("{}/frame_{}.json".format(target_folder, count), 'w') as f:
            json.dump(json_data, f)
        count += 1

        

        


