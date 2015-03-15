#!/usr/bin/env python

import os
import numpy as np
import cv2
import shlex
import sys

__width = 1280/2 
__height = 720

__calibrationWidth = __width
__calibrationHeight = __height
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

def getHeight():
	return __height
	
def getWidth():
	return __width

def getCalibrationHeight():
	return __calibrationHeight
	
def getCalibrationWidth():
	return __calibrationWidth

def getLeftCalibration():
	return __leftCalibration

def getRightCalibration():
	return __rightCalibration
		
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
	
	(width, height, cameraMatrix, distortion, rectification, projection) = __parseSingleCalibrationOstFile(filename)
	
	if((width is None) or (height  is None) or (cameraMatrix is None) or (distortion is None) or (rectification is None) or (projection is None)):
		return
	
	__setCalibrationResolution(width, height)
	
	if(left):
		__leftCalibration = (1, cameraMatrix, distortion, rectification, projection)
	else:
		__rightCalibration = (1, cameraMatrix, distortion, rectification, projection)

#----------------------------------------------------------------------------------#

def __parseSingleCalibrationOstFile(filename):
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
	
	return __createFloatArrayFromTokens(lexer, (3,4))

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

def openSavedStereoCalibration(filename):
	global __leftCalibration, __rightCalibration
	
	(width, height, leftCalibration, rightCalibration) = __parseStereoCalibrationOstFile(filename)
	 
	if((width is None) or (height  is None) or (leftCalibration is None) or (rightCalibration  is None)):
		return
	
	(cameraMatrix, distortion, rectification, projection) = leftCalibration
	(rCameraMatrix, rDistortion, rRectification, rProjection) = rightCalibration
	
	__setCalibrationResolution(width, height)
	
	__leftCalibration = (1, cameraMatrix, distortion, rectification, projection)
	__rightCalibration = (1, rCameraMatrix, rDistortion, rRectification, rProjection)

#----------------------------------------------------------------------------------#

def __parseStereoCalibrationOstFile(filename):
	calibrationFile = file(filename, 'rt')
	lexer = shlex.shlex(calibrationFile)
	lexer.wordchars += ".-"
	
	width = None
	height = None
	cameraMatrix = None
	distortion = None
	rectification = None
	projection = None
	
	rWidth = None
	rHeight = None
	rCameraMatrix = None
	rDistortion = None
	rRectification = None
	rProjection = None
	
	token = None
	while token != lexer.eof:
		token = lexer.get_token()
		
		__w = __widthParser(token, lexer)
		if(__w is not None):
			if(width is None):
				width = __w
			elif(rWidth is None):
				rWidth = __w
		
		__h = __heightParser(token, lexer)
		if(__h is not None):
			if(height is None):
				height = __h
			elif(rHeight is None):
				rHeight = __h
		
		__cam = __cameraMatrix(token, lexer)
		if(__cam is not None):
			if(cameraMatrix is None):
				cameraMatrix = __cam
			elif(rCameraMatrix is None):
				rCameraMatrix = __cam
		
		__dist = __distortion(token, lexer)
		if(__dist is not None):
			if(distortion is None):
				distortion = __dist
			elif(rDistortion is None):
				rDistortion = __dist
		
		__rect = __rectification(token, lexer)
		if(__rect is not None):
			if(rectification is None):
				rectification = __rect
			elif(rRectification is None):
				rRectification = __rect
		
		__proj = __projection(token, lexer)
		if(__proj is not None):
			if(projection is None):
				projection = __proj
			elif(rProjection is None):
				rProjection = __proj
	
	leftCalibration = (cameraMatrix, distortion, rectification, projection)
	rightCalibration = (rCameraMatrix, rDistortion, rRectification, rProjection)
	
	if((width is None) or (height  is None) or (cameraMatrix is None) or (distortion is None) or (rectification is None) or (projection is None)):
		leftCalibration = None
	if((rWidth is None) or (rHeight  is None) or (rCameraMatrix is None) or (rDistortion is None) or (rRectification is None) or (rProjection is None)):
		rightCalibration = None
	
	return (min(width, rWidth), min(height, rHeight), leftCalibration, rightCalibration)

####################################################################################
