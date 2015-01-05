import cv2
import numpy as np
import wx
import wx.lib.newevent
import abc
from helper_functions import getFrames, getFrame, sideBySide, redGreen, returnValidImage

class VideoFeed(wx.Panel):
	
	__metaclass__ = abc.ABCMeta
	
	def __init__(self, parent, cams, fps=30):
		wx.Panel.__init__(self, parent)

		self.parent = parent
		self.Cams = cams
		image = self.GetImage()

		height, width = image.shape[:2]
		self.SetSize((width, height))
		self.parent.FitInside()
		
		image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
		self.image = wx.ImageFromData(width, height, image)

		self.timer = wx.Timer(self)
		self.timer.Start(1000./fps)

		self.SetDoubleBuffered(True)
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_TIMER, self.NextFrame)


	def OnPaint(self, evt):
		dc = wx.BufferedPaintDC(self)
		if(dc.IsOk() and dc.CanDrawBitmap()):
			dc.DrawBitmap(self.image.ConvertToBitmap(), 0, 0)

	def NextFrame(self, event):
		image = self.GetImage()
		
		height, width = image.shape[:2]
		self.SetSize((width, height))
		
		image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
		self.image = wx.ImageFromData(width, height, image)
		self.Refresh()
	
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
	
	def GetImage(self):
		return redGreen(self.distance, getFrames(self.Cams))

class Calibration(VideoFeed):
	CornerFound, EVT_CORNER_FOUND = wx.lib.newevent.NewEvent()
	
	def __init__(self, parent, cams, pool, fps=30, tolerance=3):
		
		self.fps = fps
		# tolerance is how long the calibration should wait for cv2.findChessboardCorners
		# Larger tolerance means for more laggy video stream but easier to find corners.
		self.tolerance = tolerance
		self.steps = 0
		self.Searching = False
		
		# termination criteria
		self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
		self.patternSize = (7,6)

		# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
		self.objp = np.zeros((6*7,3), np.float32)
		self.objp[:,:2] = np.mgrid[0:7,0:6].T.reshape(-1,2)

		# Arrays to store object points and image points from all the images.
		self.objPoints = [] # 3d point in real world space
		self.imgPoints = [] # 2d points in image plane.
		
		self.pool = pool
		
		super(Calibration, self).__init__(parent, cams, fps)
	
	def GetImage(self):
		image = returnValidImage(getFrame(self.Cams))
		
		if(self.Searching):
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
				
				evt = self.CornerFound(step=self.steps)
				wx.PostEvent(self, evt)
				
				self.objPoints.append(self.objp)

				cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), self.criteria)
				self.imgPoints.append(corners)

				# Draw and display the corners
				cv2.drawChessboardCorners(image, self.patternSize, corners, ret)
		
		return image