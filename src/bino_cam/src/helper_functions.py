
import os
import numpy as np
import cv2
import shlex
import sys

__width = 1280/2 
__height = 720

__leftCalibration = None
__rightCalibration = None

def getFrames(cams):
	return (getFrame(cams[0]), getFrame(cams[1]))

def getFrame(cam):
	try:
		ret, frame = cam.read()
		return frame
	except:
		return None

def getDistance(window, taskbarName):
	position = cv2.getTrackbarPos(taskbarName, window)
	if(position == -1):
		return 0
	else:
		return position

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

def setCameraResolutions16x9(cams, h):
	w = 16 * (h/9)
	if(__cameraValid(cams[0])):
		__setCameraResolution(cams[0], w, h)
	if(__cameraValid(cams[1])):
		__setCameraResolution(cams[1], w, h)

def sideBySide(frames):
	image = None
	imagePart1 = returnValidImage(frames[0])
	imagePart2 = returnValidImage(frames[1])
	image = np.hstack((imagePart1, imagePart2))
	return image

def redGreen(distance, frames):
	image = None
	imagePart1 = __getRedImage(frames[0])
	imagePart2 = __getGreenBlueImage(frames[1])
	image = __combineImages(distance, imagePart1, imagePart2)
	return image

def correctedSideBySide(frames):
	image = None
	imagePart1 = __returnCorrectedImage(__leftCalibration, frames[0])
	imagePart2 = __returnCorrectedImage(__rightCalibration, frames[1])
	image = np.hstack((imagePart1, imagePart2))
	return image	

def returnValidImage(image):
	if image != None:
		return image
	else:
		blank_image = np.zeros((__height, __width, 3), np.uint8)
		return blank_image

def calibrateLeft(objpoints, imgpoints):
	global __leftCalibration
	__leftCalibration = __calibrate(objpoints, imgpoints)

def calibrateRight(objpoints, imgpoints):
	global __rightCalibration
	__rightCalibration = __calibrate(objpoints, imgpoints)
	
def openSavedCalibration(filename, camNo):
	global __leftCalibration, __rightCalibration
	
	left = (camNo==0)
	
	calibrationFile = file(filename, 'rt')
	lexer = shlex.shlex(calibrationFile)
	lexer.wordchars += ".-"
	
	cameraMatrix = None
	distortion = None
	rectification = None
	projection = None
	
	token = None
	while token != lexer.eof:
		token = lexer.get_token()
		
		__cam = __cameraMatrix(token, lexer)
		if(__cam != None):
			cameraMatrix = __cam
		
		__dist = __distortion(token, lexer)
		if(__dist != None):
			distortion = __dist
		
		__rect = __rectification(token, lexer)
		if(__rect != None):
			rectification = __rect
		
		__proj = __projection(token, lexer)
		if(__proj != None):
			projection = __proj
	
	if(cameraMatrix==None or distortion==None or rectification==None or projection==None):
		return
	
	if(left):
		__leftCalibration = (1, cameraMatrix, distortion, rectification, projection)
	else:
		__rightCalibration = (1, cameraMatrix, distortion, rectification, projection)

def __cameraValid(cam):
	return cam != None and cam.isOpened()

def __setCameraResolution(cam, w, h):
	global __width, __height 
	cam.set(3, w)
	cam.set(4, h)
	__width = int(cam.get(3))
	__height = int(cam.get(4))

def __getRedImage(image=None): 
	red = np.zeros((__height, __width, 3), np.uint8)
	if image != None:
		red[:,:,2] = image[:,:,2]	#(B, G, R)
	return red
	
def __getGreenBlueImage(image=None): 
	greenBlue = np.zeros((__height, __width, 3), np.uint8)
	if image != None:
		greenBlue[:,:,:2] = image[:,:,:2]	# (B, G, R)
	return  greenBlue

def __combineImages(distance, image1, image2):
	totalWidth = __width + distance
	image = np.zeros((__height, totalWidth, 3), np.uint8)
	image[:, :__width, 2] = image1[:, :, 2]
	image[:, distance:, :2] = image2[:, :, :2]
	return image

def __returnCorrectedImage(settings=None, image=None):
	if(settings==None or image==None):
		return returnValidImage(None)
	
	ret, mtx, dist, rvecs, tvecs = settings
	
	newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (__width, __height), 0, (__width, __height))
	
	dst = cv2.undistort(image, mtx, dist, None, newcameramtx)
	
	return returnValidImage(image)

def __calibrate(objpoints, imgpoints):
	return cv2.calibrateCamera(objpoints, imgpoints, (__width, __height), None, None)

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