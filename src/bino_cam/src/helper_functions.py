#!/usr/bin/env python

import os
import numpy as np
import cv2
from math import sqrt
import shlex
import sys
import rospy
import roslib
import subprocess
import signal
from cv_bridge import CvBridge, CvBridgeError
from std_msgs.msg import Header
from sensor_msgs.msg import Image, CameraInfo, PointCloud2
import sensor_msgs.point_cloud2 as pc2
from ug_stereomatcher.msg import CamerasSync

__width = 1280/2 
__height = 720

__calibrationWidth = __width
__calibrationHeight = __height
__leftCalibration = None
__rightCalibration = None
__bridge = CvBridge()
__proc = None
__pubAcquireImages = None
__pubImageLeft = None
__pubImageRight = None
__imageQueue = []
__lastPointCloud = None

def getFrames(cams):
	return (getFrame(cams[0]), getFrame(cams[1]))

def getFrame(cam):
	try:
		ret, frame = cam.read()
		return frame
	except:
		return None

def getHeight():
	return __height
	
def getWidth():
	return __width
		
def disableAutoFocus():
	## If that doesn't work try, sudo apt-get install v4l-utils
	os.system('v4l2-ctl -d 0 -c focus_auto=0')
	os.system('v4l2-ctl -d 0 -c focus_absolute=20')
	os.system('v4l2-ctl -d 1 -c focus_auto=0')
	os.system('v4l2-ctl -d 1 -c focus_absolute=20')

def setFocus(cam, focus):
	os.system('v4l2-ctl -d '+ str(cam) +' -c focus_absolute=' + str(focus))

def setCameraResolutions(cams, w, h):
	if(__cameraValid(cams[0])):
		__setCameraResolution(cams[0], w, h)
	if(__cameraValid(cams[1])):
		__setCameraResolution(cams[1], w, h)

#----------------------------------------------------------------------------------#

def __cameraValid(cam):
	return (cam is not None) and cam.isOpened()

def __setCameraResolution(cam, w, h):
	global __width, __height 
	cam.set(3, w)
	cam.set(4, h)
	__width = int(cam.get(3))
	__height = int(cam.get(4))

####################################################################################

def setCameraResolutions16x9(cams, h):
	w = 16 * (h/9)
	if(__cameraValid(cams[0])):
		__setCameraResolution(cams[0], w, h)
	if(__cameraValid(cams[1])):
		__setCameraResolution(cams[1], w, h)

def sideBySide(frames):
	image = None
	imagePart1 = returnValidImage(frames[0], (__width, __height) )
	imagePart2 = returnValidImage(frames[1], (__width, __height) )
	image = np.hstack((imagePart1, imagePart2))
	return image

def returnValidImage(image, resolution):
	if image is not None:
		return image
	else:
		blank_image = np.zeros((resolution[1], resolution[0], 3), np.uint8)
		return blank_image

def redGreen(distance, frames):
	image = None
	imagePart1 = __getRedImage(frames[0])
	imagePart2 = __getGreenBlueImage(frames[1])
	image = __combineImages(distance, imagePart1, imagePart2)
	return image
	
#----------------------------------------------------------------------------------#

def __getRedImage(image=None): 
	red = np.zeros((__height, __width, 3), np.uint8)
	if image is not None:
		red[:,:,2] = image[:,:,2]	#(B, G, R)
	return red
	
def __getGreenBlueImage(image=None): 
	greenBlue = np.zeros((__height, __width, 3), np.uint8)
	if image is not None:
		greenBlue[:,:,:2] = image[:,:,:2]	# (B, G, R)
	return  greenBlue

def __combineImages(distance, image1, image2):
	width = image1.shape[1]
	height = image1.shape[0]
	totalWidth = width + distance
	image = np.zeros((height, totalWidth, 3), np.uint8)
	image[:, :width, 2] = image1[:, :, 2]
	image[:, distance:, :2] = image2[:, :, :2]
	return image
	
####################################################################################

def correctedSideBySide(frames):
	image = None
	imagePart1 = __returnCorrectedImage(__leftCalibration, frames[0])
	imagePart2 = __returnCorrectedImage(__rightCalibration, frames[1])
	image = __combineDifferentResolutionImages(imagePart1, imagePart2)
	return image
	
#----------------------------------------------------------------------------------#

def __returnCorrectedImage(settings=None, image=None):
	if((settings is None) or (image is None)):
		return returnValidImage(None, (__calibrationWidth, __calibrationHeight))
	
	ret, mtx, dist, rvecs, tvecs = settings
	
	image = __resize(image, (__calibrationWidth, __calibrationHeight))
	
	newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (__calibrationWidth, __calibrationHeight), 1, (__calibrationWidth, __calibrationHeight))
	
	image = cv2.undistort(image, mtx, dist, None, newcameramtx)
	
	x,y,w,h = roi
	image = image[y:y+h, x:x+w]
	
	return returnValidImage(image, (__calibrationWidth, __calibrationHeight))

def __resize(image, target):
	width = image.shape[1]
	height = image.shape[0]
	invfx = width/target[0]
	invfy = height/target[1]
	
	if((width%target[0]) > (target[0]/2.0)):
		invfx += 1
	if((height%target[1]) > (target[1]/2.0)):
		invfy += 1
	
	fx = 1.0/float(invfx)
	fy = 1.0/float(invfy)
	
	return cv2.resize(image, (0, 0), fx=fx, fy=fy) 

def __combineDifferentResolutionImages(image1, image2):
	widthDifference = image1.shape[1] - image2.shape[1]
	heightDifference = image1.shape[0] - image2.shape[0]
	black  = np.array([0], dtype=np.uint8)
	
	if(widthDifference != 0):
		if (widthDifference < 0):
			width = abs(widthDifference)
			height = image1.shape[0]
			bufferArray = np.repeat( black, (width*height*3))
			bufferArray = bufferArray.reshape((height, width, 3))
			image1 = np.hstack((bufferArray, image1))
		else:
			width = abs(widthDifference)
			height = image2.shape[0]
			bufferArray = np.repeat( black, (width*height*3))
			bufferArray = bufferArray.reshape((height, width, 3))
			image2 = np.hstack((image2, bufferArray))
	
	if(heightDifference != 0):
		if(heightDifference < 0):
			width = image1.shape[1]
			height = abs(heightDifference)
			black  = np.array([0], dtype=np.uint8)
			bufferArray = np.repeat( black, (width*height*3))
			bufferArray = bufferArray.reshape((height, width, 3))
			image1 = np.vstack((image1, bufferArray))
		else:
			width = image2.shape[1]
			height = abs(heightDifference)
			bufferArray = np.repeat( black, (width*height*3))
			bufferArray = bufferArray.reshape((height, width, 3))
			image2 = np.vstack((image2, bufferArray))
	
	return np.hstack((image1, image2))
	
####################################################################################

def initializePointCloud():
	global __rosImageSource, __imageQueue
	__imageQueue = []
	__launchMatcherNode()
	__initializeROSTopics()
	__rosImageSource = rospy.Subscriber('output_pointcloud', PointCloud2, __collectPointCloudData)

#----------------------------------------------------------------------------------#

def __launchMatcherNode():
	global __proc
	__proc = subprocess.Popen(['roslaunch', 'bino_cam', 'matcher_nodes.launch'])

def __initializeROSTopics():
	global __pubAcquireImages, __pubImageLeft, __pubImageRight
	__pubAcquireImages = rospy.Publisher("acquire_images", CamerasSync, queue_size=10)
	__pubImageLeft = ( rospy.Publisher("input_left_image", Image, queue_size=30), rospy.Publisher("camera_info_left", CameraInfo, queue_size=30) )
	__pubImageRight = ( rospy.Publisher("input_right_image", Image, queue_size=30), rospy.Publisher("camera_info_right", CameraInfo, queue_size=30) )

def __collectPointCloudData(data):
	global __imageQueue
	iterData = pc2.read_points(data)
	points = []
	height = sqrt((data.width/float(16))*9)
	width = 16 * ( height/float(9) )
	height = int(height)
	width = int(width)
	maxDist = 0
	for i in range(width):
		intermediate = []
		for j in range(height):
			point = next(iterData)
			if(point[3]>maxDist):
				maxDist=point[3]
			intermediate.append(point[3])
		points.append(intermediate)
	
	image = __constructDepthImage(width, height, maxDist, points)
	image = np.swapaxes(image, 0, 1)
	__imageQueue.append(image)

def __constructDepthImage(width, height, maxDist, points):
	for i in range(width):
		for j in range(height):
			point = points[i][j]
			value = (point/maxDist) * 255
			points[i][j] = (0, int(value), 0)
	image = np.array(points, dtype=np.uint8)
	for i in range(width):
		for j in range(height):
			image[i][j] = tuple(image[i][j])
	return image

####################################################################################

def destroyPointCloud():
	global __proc
	__proc.send_signal(signal.SIGINT)

def getImageFromROS(frames):
	global __imageQueue, __lastPointCloud
	cameraSync = CamerasSync()
	cameraSync.data = "full"
	cameraSync.timeStamp = rospy.Time.now()
	__pubAcquireImages.publish(cameraSync)
	__pubImageLeft[0].publish(__constructROSImage(frames[0], cameraSync.timeStamp))
	__pubImageLeft[1].publish(__constructROSCameraInfo(__leftCalibration, cameraSync.timeStamp))
	__pubImageRight[0].publish(__constructROSImage(frames[1], cameraSync.timeStamp))
	__pubImageRight[1].publish(__constructROSCameraInfo(__rightCalibration, cameraSync.timeStamp))
	image = None
	try:
		image = __imageQueue.pop(0)
	except:
		# print "helper_functions, getImageFromROS: Empty Queue"
		image = __lastPointCloud

	__lastPointCloud = image
	return returnValidImage(image, (__width, __height))

#----------------------------------------------------------------------------------#

def __constructROSImage(image, timestamp):
	image = __bridge.cv2_to_imgmsg(image, encoding="rgb8")
	image.header.stamp = timestamp
	return image

def __constructROSCameraInfo(calibration, timestamp):
	(ret, cameraMatrix, distortion, rectification, projection) = calibration
	h = Header()
	h.stamp = timestamp
	distortion = __makeTuple(__unwrapValues(distortion))
	cameraInfo = CameraInfo()
	cameraInfo.width = __calibrationWidth
	cameraInfo.height = __calibrationHeight
	cameraInfo.header = h
	cameraInfo.distortion_model = "plumb_bob"
	cameraInfo.D = distortion
	cameraInfo.K = cameraMatrix.flatten()
	cameraInfo.R = rectification.flatten()
	cameraInfo.P = projection.flatten()
	return cameraInfo

def __unwrapValues(array):
	shape = array.shape
	if(shape[1]==1):
		newArray = np.empty(shape[0], dtype=array[0].dtype)
		for i in range(shape[0]):
			newArray[i] = array[i][0]
		return newArray
	else:
		for i in range(shape[0]):
			array[i] = __unwrapValues(array[i])
		return array

####################################################################################

def calibrateLeft(objpoints, imgpoints):
	global __leftCalibration
	__leftCalibration = __calibrate(objpoints, imgpoints)
	
#----------------------------------------------------------------------------------#

def __calibrate(objpoints, imgpoints):
	__setCalibrationResolution(__width, __height)
	return cv2.calibrateCamera(objpoints, imgpoints, (__width, __height), None, None)

def __setCalibrationResolution(width, height):
	global __calibrationWidth, __calibrationHeight
	
	__calibrationWidth = width
	__calibrationHeight = height

####################################################################################

def calibrateRight(objpoints, imgpoints):
	global __rightCalibration
	__rightCalibration = __calibrate(objpoints, imgpoints)	
	
def openSavedCalibration(filename, camNo):
	global __leftCalibration, __rightCalibration
	
	left = (camNo==0)
	
	(width, height, cameraMatrix, distortion, rectification, projection) = __parseIniFile(filename)
	
	if((width is None) or (height  is None) or (cameraMatrix is None) or (distortion is None) or (rectification is None) or (projection is None)):
		return
	
	__setCalibrationResolution(width, height)
	
	if(left):
		__leftCalibration = (1, cameraMatrix, distortion, rectification, projection)
	else:
		__rightCalibration = (1, cameraMatrix, distortion, rectification, projection)

#----------------------------------------------------------------------------------#

def __parseIniFile(filename):
	calibrationFile = file(filename, 'rt')
	lexer = shlex.shlex(calibrationFile)
	lexer.wordchars += ".-"
	
	width = None
	height = None
	cameraMatrix = None
	distortion = None
	rectification = None
	projection = None
	
	token = None
	while token != lexer.eof:
		token = lexer.get_token()
		
		__w = __widthParser(token, lexer)
		if(__w is not None):
			width = __w
		
		__h = __heightParser(token, lexer)
		if(__h is not None):
			height = __h
		
		__cam = __cameraMatrix(token, lexer)
		if(__cam is not None):
			cameraMatrix = __cam
		
		__dist = __distortion(token, lexer)
		if(__dist is not None):
			distortion = __dist
		
		__rect = __rectification(token, lexer)
		if(__rect is not None):
			rectification = __rect
		
		__proj = __projection(token, lexer)
		if(__proj is not None):
			projection = __proj
	
	return (width, height, cameraMatrix, distortion, rectification, projection)

def __widthParser(token, lexer):
	if(token.lower() != "width"):
		return
	
	nextToken = lexer.get_token()
	return int(nextToken)

def __heightParser(token, lexer):
	if(token.lower() != "height"):
		return
	
	nextToken = lexer.get_token()
	return int(nextToken)

def __cameraMatrix(token, lexer):
	if(token.lower() != "camera"):
		return
	
	nextToken = lexer.get_token()
	if(nextToken.lower() != "matrix"):
		lexer.push_token(nextToken)
		return
		
	return __createFloatArrayFromTokens(lexer, (3,3))

def __distortion(token, lexer):
	if(token.lower() != "distortion"):
		return
	
	return __createFloatArrayFromTokens(lexer, (5,1))

def __rectification(token, lexer):
	if(token.lower() != "rectification"):
		return
	
	return __createFloatArrayFromTokens(lexer, (3,3))

def __projection(token, lexer):
	if(token.lower() != "projection"):
		return
	
	return __createFloatArrayFromTokens(lexer, (4,3))

def __createFloatArrayFromTokens(lexer, shape):
	numberOfElements = shape[0]*shape[1]
	
	matrixString = ""
	for i in range(numberOfElements-1):
		matrixString += lexer.get_token() + " "
	
	matrixString += lexer.get_token()
	
	array = np.fromstring(matrixString, dtype=np.float64, sep=" ")
	array = array.reshape(shape)
	
	return array

####################################################################################