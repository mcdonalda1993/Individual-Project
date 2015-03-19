#!/usr/bin/env python

import rospy
import roslib
from math import sqrt
import numpy as np
import subprocess
import signal
from cv_bridge import CvBridge, CvBridgeError
from std_msgs.msg import Header
from sensor_msgs.msg import Image, CameraInfo, PointCloud2
import sensor_msgs.point_cloud2 as pc2
from ug_stereomatcher.msg import CamerasSync

__bridge = CvBridge()
__proc = None
__pubAcquireImages = None
__pubImageLeft = None
__pubImageRight = None
__imageQueue = []
__lastPointCloud = None

def initializePointCloud():
	global __imageQueue
	__launchMatcherNode()
	__imageQueue = []
	__initializeROSTopics()
	rospy.Subscriber('output_pointcloud', PointCloud2, __collectPointCloudData)

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
	
	(maxDist, points) = __extractPointCloudData(data)

	__imageQueue.append( (maxDist, points) )

def __extractPointCloudData(data):
	iterData = pc2.read_points(data)
	points = []
	height = sqrt((data.width/float(16))*9)
	width = 16 * ( height/float(9) )
	height = int(height)
	width = int(width)
	maxDist = 0
	z = 2
	print "PointCloud data received."
	for i in range(width):
		intermediate = []
		for j in range(height):
			point = next(iterData)
			if(point[z]>maxDist):
				maxDist=point[z]
			intermediate.append(point)
		points.append(intermediate)
	
	points = np.array(points)
	points = np.swapaxes(points, 0, 1)
	print "New point cloud available"
	return (maxDist, points)

####################################################################################

def constructDepthMapImage(hotNear, maxDist, points):
	z = 2
	newPoints = []
	shape = (points.shape[0], points.shape[1], 3)
	
	for i in range(points.shape[0]):
		for j in range(points.shape[1]):
			zPoint = points[i][j][z]
			if(hotNear):
				value = (1 - (zPoint/maxDist)) * 255
			else:
				value = (zPoint/maxDist) * 255
			newPoints.append((0, int(value), 0))
	
	image = np.array(newPoints, dtype=np.uint8)
	image = np.reshape(image, shape)
	print "New Depth Map Image"
	return image

def destroyPointCloud():
	global __proc
	__proc.send_signal(signal.SIGINT)

def getDataFromROS():
	global __imageQueue, __lastPointCloud
	if( len(__imageQueue)>0 ):
		image = __imageQueue.pop(0)
	else:
		# print "helper_functions, getImageFromROS: Empty Queue"
		image = __lastPointCloud

	__lastPointCloud = image
	return image

def sendDataToROS(frames, dimensions, calibration):
	global __imageQueue, __lastPointCloud
	(leftCalibration, rightCalibration) = calibration
	if( len(__imageQueue)<10 ):
		cameraSync = CamerasSync()
		cameraSync.data = "full"
		cameraSync.timeStamp = rospy.Time.now()
		__pubAcquireImages.publish(cameraSync)
		__pubImageLeft[0].publish(__constructROSImage(frames[0], cameraSync.timeStamp))
		__pubImageLeft[1].publish(__constructROSCameraInfo(leftCalibration, dimensions, cameraSync.timeStamp))
		__pubImageRight[0].publish(__constructROSImage(frames[1], cameraSync.timeStamp))
		__pubImageRight[1].publish(__constructROSCameraInfo(rightCalibration, dimensions, cameraSync.timeStamp))

#----------------------------------------------------------------------------------#

def __constructROSImage(image, timestamp):
	image = __bridge.cv2_to_imgmsg(image, encoding="rgb8")
	image.header.stamp = timestamp
	return image

def __constructROSCameraInfo(calibration, dimensions, timestamp):
	(calibrationWidth, calibrationHeight) = dimensions
	(ret, cameraMatrix, distortion, rectification, projection) = calibration
	h = Header()
	h.stamp = timestamp
	distortion = __makeTuple(__unwrapValues(distortion))
	cameraInfo = CameraInfo()
	cameraInfo.width = calibrationWidth
	cameraInfo.height = calibrationHeight
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

def __makeTuple(array):
	return tuple(array)

####################################################################################
