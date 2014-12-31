import numpy as np
import cv2
import glob

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((6*7,3), np.float32)
objp[:,:2] = np.mgrid[0:7,0:6].T.reshape(-1,2)

# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

patternSize = (7,6)

cam = cv2.VideoCapture(0)

while(len(imgpoints) < 5):
	ret1, img = cam.read()
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	
	ret = False
	# Find the chess board corners
	ret, corners = cv2.findChessboardCorners(gray, patternSize, None)

	# If found, add object points, image points (after refining them)
	if ret == True:
		objpoints.append(objp)

		cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
		imgpoints.append(corners)

		# Draw and display the corners
		cv2.drawChessboardCorners(img, patternSize, corners, ret)
		
	cv2.imshow('img',img)
	cv2.waitKey(1)

cv2.waitKey(10000)
cv2.destroyAllWindows()