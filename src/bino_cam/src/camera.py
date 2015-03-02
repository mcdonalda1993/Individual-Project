#!/usr/bin/env python

import cv2
import wx
import wx.lib.scrolledpanel
from multiprocessing import Pool
from helper_functions import setCameraResolutions16x9, openSavedCalibration
from gui_video import *
import rospy

displayOptions = ["Side by side", "Red-Green", "Corrected Side By Side", "Depth Map", "Point Cloud"]

class MainWindow(wx.Frame):
	def __init__(self, parent, title, processPool):
				
		self.pool = processPool
		
		self.Cams = (cv2.VideoCapture(0), cv2.VideoCapture(1))
		setCameraResolutions16x9(self.Cams, 720)
		
		wx.Frame.__init__(self, parent, title=title)
		
		self.panel = wx.lib.scrolledpanel.ScrolledPanel(self, wx.ID_ANY)
		self.panel.SetupScrolling()
		
		# Setup all the controls. Non default ones are hidden.
		self.combo = wx.ComboBox(self.panel,
							  value=displayOptions[0], 
							  size=wx.DefaultSize,
							  choices=displayOptions,
							  style=wx.CB_READONLY)
		self.combo.Bind(wx.EVT_COMBOBOX, self.OnSelect)
		
		
		# Setup views. Non default ones are hidden.
		self.sideBySide = SideBySide(self.panel, self.Cams)
		
		self.redGreen = RedGreen(self.panel, self.Cams)
		self.redGreen.Show(False)
		self.correctedSideBySide = CorrectedSideBySide(self.panel, self.Cams)
		self.correctedSideBySide.Show(False)
		
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		mainSizer.Add(self.combo)
		mainSizer.Add(self.sideBySide)
		mainSizer.Add(self.redGreen)
		mainSizer.Add(self.correctedSideBySide)
		
		self.panel.SetAutoLayout(True)
		self.panel.SetSizer(mainSizer)
		self.panel.Layout()		
		
		# Setting up the menu.
		filemenu = wx.Menu()
		# wx.ID_ABOUT and wx.ID_EXIT are standard ids provided by wxWidgets.
		menuAbout = filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
		menuExit = filemenu.Append(wx.ID_EXIT,"&Exit"," Terminate the program")
		
		calibrationMenu = wx.Menu()
		
		calibration = wx.Menu()
		calibrate0 = calibration.Append(1, "Calibrate left camera (&0) ")
		calibrate1 = calibration.Append(2, "Calibrate right camera (&1) ")
		calibrationMenu.AppendSubMenu(calibration, "Calibrate cameras")
		
		openCalibrationMenu = wx.Menu()
		openCalibrate0 = openCalibrationMenu.Append(3, "Open calibration for left camera (&0) ")
		openCalibrate1 = openCalibrationMenu.Append(4, "Open calibration for right camera (&1) ")
		calibrationMenu.AppendSubMenu(openCalibrationMenu, "&Open saved calibration")
		
		# Creating the menubar.
		menuBar = wx.MenuBar()
		menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
		menuBar.Append(calibrationMenu, "&Calibration")
		self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

		# Set events.
		self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
		self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
		self.Bind(wx.EVT_MENU, self.StartCalibration, calibrate0)
		self.Bind(wx.EVT_MENU, self.StartCalibration, calibrate1)
		self.Bind(wx.EVT_MENU, self.OpenCalibration, openCalibrate0)
		self.Bind(wx.EVT_MENU, self.OpenCalibration, openCalibrate1)
		
		self.Show(True)
		
	def OnSelect(self, event):
		
		self.sideBySide.Show(self.combo.GetCurrentSelection() == 0)
		
		self.redGreen.Show(self.combo.GetCurrentSelection() == 1)
		# Slider control is only shown for RedGreen feed
		
		self.correctedSideBySide.Show(self.combo.GetCurrentSelection() == 2)
		if(hasattr(self, "depthMap")):
			self.depthMap.Show(self.combo.GetCurrentSelection()==3)
		elif(self.combo.GetCurrentSelection()==3):
			self.depthMap = DepthMap(self.panel, self.Cams)
			mainSizer = self.panel.GetSizer()
			mainSizer.Add(self.depthMap)
			self.panel.SetSizer(mainSizer)
			
		if(hasattr(self, "pointCloud")):
			self.pointCloud.Show(self.combo.GetCurrentSelection()==4)
		elif(self.combo.GetCurrentSelection()==4):
			self.pointCloud = PointCloud(self.panel, self.Cams)
			mainSizer = self.panel.GetSizer()
			mainSizer.Add(self.pointCloud)
			self.panel.SetSizer(mainSizer)
		
		self.panel.FitInside()
		self.panel.Layout()
		self.Refresh()
	
	def OnAbout(self, event):
		# A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
		dlg = wx.MessageDialog( self, "TO DO", "About Binocular Algorithm Example", wx.OK)
		dlg.ShowModal() # Show it
		dlg.Destroy() # finally destroy it when finished.

	def OnExit(self, event):
		self.sideBySide.Show(False)
		self.redGreen.Show(False)
		self.correctedSideBySide.Show(False)
		if(hasattr(self, "calibrationFeed")):
			self.calibrationFeed.Show(False)
		if(hasattr(self, "depthMap")):
			self.depthMap.Destroy()
		if(hasattr(self, "pointCloud")):
			self.pointCloud.Destroy()
		self.Cams[0].release()
		self.Cams[1].release()
		self.Close(True)  # Close the frame.
		wx.GetApp().ExitMainLoop()
	
	def StartCalibration(self, event):
		self.combo.Show(False)
		self.sideBySide.Show(False)
		self.redGreen.Show(False)
		self.correctedSideBySide.Show(False)
		
		self.calibrationFeed = Calibration(self.panel, self.Cams[event.Id-1], self.pool, event.Id-1)
		self.calibrationFeed.Bind(Calibration.EVT_CALIBRATION_ENDED, self.EndCalibration)
		
		mainSizer = self.panel.GetSizer()
		mainSizer.Add(self.calibrationFeed)
		self.panel.SetSizer(mainSizer)
		self.panel.FitInside()
		self.panel.Layout()
		self.Refresh()
	
	def EndCalibration(self, event):
		self.combo.Show(True)
		self.combo.SetValue(displayOptions[0])
		self.sideBySide.Show(True)
	
	def OpenCalibration(self, event):
		openFileDialog = wx.FileDialog(self, "Open saved calibration", "", "","Calibration files (*.txt)|*.txt|Calibration files (*.ini)|*.ini", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		
		if openFileDialog.ShowModal() == wx.ID_CANCEL:
			return	# the user changed idea...
		
		openSavedCalibration(openFileDialog.GetPath(), event.Id-3)
		self.panel.FitInside()
		self.panel.Layout()
		self.Refresh()

if __name__ == '__main__':
	rospy.init_node("camera_gui", anonymous=True)
	processPool = Pool()
	app = wx.App(False)
	frame = MainWindow(None, "Binocular Algorithm Example", processPool)
	app.MainLoop()
