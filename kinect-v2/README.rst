Find Chessboards with Kinect for Windows
========================================

The basic idea is to find points in the color image and use the coordinate mapper to retrieve the 3D position. 
These examples use pyKinect2 to interface with the Kinect API, and only work on Windows with the Kinect API installed.

Installation
------------

Install the kinect v2 SDK https://www.microsoft.com/en-us/download/details.aspx?id=44561
Install python, opencv and contrib (see top level readme) and install pyKinect2. <https://github.com/Kinect/pyKinect2>

note: (october 5 2018: if you install with pip, you need to overwrite the files with the ones from github....)

Examples
--------
All scripts wait until the sensor is connected. Once the video feed is shown, stop a script with the escape key.

- **color.py** shows the color frame.
- **depth.py** shows the depth frame.
- **infrared.py** shows the infrared frame.
- **detect_charuco.py** detects an charuco board in the color frame. Use board.pdf in the top level data folder.
- **color_3d** uses the coordinate mapper to get the 3D position for each pixel in the color frame. 
  The z value (away from the camera) is drawn scaled down. The depth value of the center point is indicated


- **capture_board.py** detects the charuco board and retrieves the 3D coordinates. The space key saves the image, 
  and coordinates for the board and markers in json.




