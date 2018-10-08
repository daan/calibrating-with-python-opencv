import numpy as np
import cv2
import sys
import argparse

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", help="path to output image file(s)")
ap.add_argument("-r", "--resolution", type=str, default="1280x720", help="resolution")
ap.add_argument("-c", "--camera", type=str, default="0", help="camera by id")

args = vars(ap.parse_args())

print(args["output"])
print(args["resolution"])

wh = args["resolution"].split("x")
width = int(wh[0])
height = int(wh[1])

camera = 0

print("opening video capture device {}".format(camera))
cap = cv2.VideoCapture(int(camera))
print("resolution {} by {} ".format(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT ))))

count = 0

while(True):
    ret, frame = cap.read()
    frame = cv2.resize(frame, (width, height))
    #frame = cv2.flip(frame,1)
    cv2.imshow('frame', frame)

    key = cv2.waitKey(10)
    print(key)
    if key == 32:
        print("take picture")
        count += 1
        cv2.imwrite("frame_{}.jpg".format(count), frame)

    elif key != -1:
        break

cap.release()

cv2.destroyAllWindows()




