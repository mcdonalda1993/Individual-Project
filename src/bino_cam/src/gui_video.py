#!/usr/bin/env python

import cv2
import numpy as np
import wx
import wx.lib.newevent
import abc
from camera_functions import *
from ros_functions import getDataFromROS, constructDepthMapImage, initializePointCloud, destroyPointCloud
from vtk_gui import VtkPointCloud

class VideoFeed(wx.Panel):
	
	__metaclass__ = abc.ABCMeta
	
	def __init__(self, parent, cams, fps=30):
		wx.Panel.__init__(self, parent)

		self.parent = parent
		self.Cams = cams
		image = self.GetImage()

		height, width = image.shape[:2]
		
		self.parent.FitInside()
		
		image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
		image = wx.ImageFromData(width, height, image)
		
		self.imagePanel = wx.Panel(self)
		self.image = wx.StaticBitmap(self.imagePanel)
		self.image.SetBitmap(image.ConvertToBitmap())
		
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		self.mainSizer.Add(self.imagePanel)
		
		self.SetAutoLayout(True)
		self.SetSizer(self.mainSizer)
		self.Layout()

		self.timer = wx.Timer(self)
		self.timer.Start(1000./fps)

		self.SetDoubleBuffered(True)
		self.Bind(wx.EVT_TIMER, self.NextFrame)

	def NextFrame(self, event):
		image = self.GetImage()

		height, width = image.shape[:2]
		
		image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
		image = wx.ImageFromData(width, height, image)
		
		self.image.SetBitmap(image.ConvertToBitmap())
		
		wx.YieldIfNeeded()
	
	def Show(self, show):
		if(show):
			self.timer.Start()
		else:
			self.timer.Stop()
		super(VideoFeed, self).Show(show)
	
	@abc.abstractmethod
	def GetImage(self):
		## Returns the type of image the feed is supposed to represent
		return

class SideBySide(VideoFeed):
	
	def GetImage(self):
		return sideBySide(getFrames(self.Cams))

class RedGreen(VideoFeed):
	
	distance = 0
	
	def __init__(self, parent, cams, fps=30):
		
		super(RedGreen, self).__init__(parent, cams, fps)
		
		self.slider = wx.Slider(self, size=(getWidth(), -1), minValue=0, maxValue=getWidth())
		self.slider.Bind(wx.EVT_SCROLL, self.OnSliderChanged)
		self.slider.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSliderRelease)
		
		self.mainSizer.Prepend(self.slider)
		self.Layout()	
	
	def GetImage(self):
		return redGreen(self.distance, getFrames(self.Cams))
	
	def Show(self, show):
		self.slider.Show(show)
		super(RedGreen, self).Show(show)
	
	def OnSliderChanged(self, event):
		self.distance = self.slider.GetValue()
	
	def OnSliderRelease(self, event):	
		self.parent.FitInside()
		self.parent.Layout()
		self.Refresh()

class CorrectedSideBySide(VideoFeed):
	
	def GetImage(self):
		return correctedSideBySide(getFrames(self.Cams))

class DepthMap(VideoFeed):
	
	def __init__(self, parent, cams, fps=30):
		initializePointCloud()
		super(DepthMap, self).__init__(parent, cams, fps)
	
	def GetImage(self):
		dimensions = (getCalibrationWidth(), getCalibrationHeight())
		calibrationInfo = (getLeftCalibration(), getRightCalibration())
		data = getDataFromROS(getFrames(self.Cams), dimensions, calibrationInfo)
		if(data is None):
			return returnValidImage(None, (1, 1))
		(maxDist, pointCloudData) = data
		return constructDepthMapImage(maxDist, pointCloudData)
	
	def Destroy(self):
		destroyPointCloud()
		super(DepthMap, self).Destroy()

class PointCloud(VideoFeed):
	
	def __init__(self, parent, cams, fps=30):
		self.initialized = False
		initializePointCloud()
		
		super(PointCloud, self).__init__(parent, cams, fps)
		
		self.imagePanel.Show(False)		
		
		self.vtkPointCloud = VtkPointCloud(self)
		self.vtkPointCloud.SetSize( (getWidth(), getHeight()) )
		
		self.mainSizer.Prepend(self.vtkPointCloud.GetSize(), wx.EXPAND)

		self.Layout()
		self.initialized = True
	
	def GetImage(self):
		dimensions = (getCalibrationWidth(), getCalibrationHeight())
		calibrationInfo = (getLeftCalibration(), getRightCalibration())
		data = getDataFromROS(getFrames(self.Cams), dimensions, calibrationInfo)
		if(self.initialized and data is not None):
			(maxDist, pointCloudData) = data
			self.vtkPointCloud.clearPoints()
			for i in range(pointCloudData.shape[0]):
				for j in range(pointCloudData.shape[1]):
					point = pointCloudData[i][j]
					self.vtkPointCloud.addPoint( (j, i, point[3]) )
			## May need rerender function call
		return returnValidImage(None, (1, 1))
	
	def Destroy(self):
		destroyPointCloud()
		super(PointCloud, self).Destroy()

class Calibration(VideoFeed):
	CalibrationEnded, EVT_CALIBRATION_ENDED = wx.lib.newevent.NewEvent()
	
	def __init__(self, parent, cams, pool, camNo, fps=30, tolerance=10):
		
		self.fps = fps
		# tolerance is how long the calibration should wait for cv2.findChessboardCorners
		# Larger tolerance means for more laggy video stream but easier to find corners.
		self.tolerance = tolerance
		self.steps = 0
		self.Left = (camNo == 0)
		self.__init = False
		
		# termination criteria
		self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
		self.patternSize = (9,6)

		# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
		self.objp = np.zeros((self.patternSize[1]*self.patternSize[0],3), np.float32)
		self.objp[:,:2] = np.mgrid[0:self.patternSize[0],0:self.patternSize[1]].T.reshape(-1,2)

		# Arrays to store object points and image points from all the images.
		self.objPoints = [] # 3d point in real world space
		self.imgPoints = [] # 2d points in image plane.
		
		self.pool = pool
		
		super(Calibration, self).__init__(parent, cams, fps)
		
		panel = wx.Panel(self)
		panelSizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer(panelSizer)
		
		self.cancelCalibrationButton = wx.Button(panel, label="Cancel Calibration")
		self.cancelCalibrationButton.Bind(wx.EVT_BUTTON, self.CancelCalibration)
		self.searchingToggle = wx.ToggleButton(panel, label="Enable Calibration")
		self.searchingToggle.SetValue(False)
		self.searchingToggle.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleChanged)
		
		calibrationSizer = wx.BoxSizer(wx.HORIZONTAL)
		calibrationSizer.Add(self.cancelCalibrationButton, flag=wx.EXPAND)
		calibrationSizer.Add(self.searchingToggle, flag=wx.EXPAND)
		
		font = wx.Font(20, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		self.stepsLabel = wx.StaticText(panel)
		self.stepsLabel.SetLabel("Captured Corners: 0")
		self.stepsLabel.SetFont(font)
		
		panelSizer.Add(calibrationSizer, flag=wx.EXPAND)
		panelSizer.Add(self.stepsLabel, flag=wx.EXPAND)
		self.mainSizer.Prepend(panel, flag=wx.EXPAND)
		self.Layout()
	
	def GetImage(self):
		image = returnValidImage(getFrame(self.Cams), (getWidth(), getHeight()) )
		
		if(self.__init and self.searchingToggle.GetValue()):
			
			ret = False
			gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
			
			# Find the chess board corners
			result = self.pool.apply_async(cv2.findChessboardCorners, (gray, self.patternSize, None))
			try:
				ret, corners = result.get(timeout=self.tolerance/float(self.fps))
			except:
				pass

			# If found, add object points, image points (after refining them)
			
			if ret == True:
				self.steps += 1
				
				self.UpdateLabel()
				
				self.objPoints.append(self.objp)

				cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), self.criteria)
				self.imgPoints.append(corners)

				# Draw and display the corners
				cv2.drawChessboardCorners(image, self.patternSize, corners, ret)
		
		self.__init = True
		
		return image
	
	def ToggleChanged(self, event):
		self.__UpdateCalibrationButtonBackground()
	
	def UpdateLabel(self):

		step = self.steps
		
		self.__UpdateCalibrationButtonBackground()

		self.stepsLabel.SetLabel("Captured Corners: " + str(step))
		if(step >= 10):
			self.searchingToggle.SetValue(False)
			
			if(self.Left):
				calibrateLeft(self.objPoints, self.imgPoints)
			else:
				calibrateRight(self.objPoints, self.imgPoints)
			
			self.searchingToggle.SetValue(False)
			self.__UpdateCalibrationButtonBackground()
			self.stepsLabel.SetLabel("Captured Corners: " + str(step) + " Calibration saved")
	
	def CancelCalibration(self, event):
		
		evt = self.CalibrationEnded()
		self.GetEventHandler().ProcessEvent(evt)
		
		self.cancelCalibrationButton.Show(False)
		self.searchingToggle.Show(False)
		self.searchingToggle.SetValue(False)
		self.stepsLabel.Show(False)
		self.Show(False)
		try:
			self.Destroy()
		except:
			pass
	
	def __UpdateCalibrationButtonBackground(self):
		if(self.searchingToggle.GetValue()):
			self.searchingToggle.SetBackgroundColour("Red")
		else:
			self.searchingToggle.SetBackgroundColour(wx.NullColour)
