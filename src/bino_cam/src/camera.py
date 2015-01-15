import cv2
import wx
import wx.lib.scrolledpanel
from multiprocessing import Pool
from helper_functions import getWidth, setCameraResolutions16x9, calibrateLeft, calibrateRight
from gui_video import *

displayOptions = ["Side by side", "Red-Green", "Corrected Side By Side"]

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
		
		self.sld = wx.Slider(self.panel, size=(getWidth(), -1), minValue=0, maxValue=getWidth())
		self.sld.Bind(wx.EVT_SCROLL, self.OnSliderChanged)
		self.sld.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSliderRelease)
		
		self.cancelCalibrationButton = wx.Button(self.panel, label="Cancel Calibration")
		self.cancelCalibrationButton.Bind(wx.EVT_BUTTON, self.CancelCalibration)
		self.searchingToggle = wx.ToggleButton(self.panel, label="Enable Calibration")
		self.searchingToggle.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleChanged)
		
		calibrationSizer = wx.BoxSizer(wx.HORIZONTAL)
		calibrationSizer.Add(self.cancelCalibrationButton)
		calibrationSizer.Add(self.searchingToggle)
		
		font = wx.Font(20, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		self.steps = wx.StaticText(self.panel)
		self.steps.SetLabel("Captured Corners: 0")
		self.steps.SetFont(font)
		
		self.sld.Show(False)
		self.cancelCalibrationButton.Show(False)
		self.searchingToggle.Show(False)
		self.steps.Show(False)
		
		# Setup views. Non default ones are hidden.
		self.sideBySide = SideBySide(self.panel, self.Cams)
		self.redGreen = RedGreen(self.panel, self.Cams)
		self.redGreen.Show(False)
		self.correctedSideBySide = CorrectedSideBySide(self.panel, self.Cams)
		self.correctedSideBySide.Show(False)
		
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		mainSizer.Add(self.combo)
		mainSizer.Add(self.sld)
		mainSizer.Add(calibrationSizer)
		mainSizer.Add(self.steps)
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
		
		calibration = wx.Menu()
		calibrate0 = calibration.Append(1, "Calibrate left camera (&0) ")
		calibrate1 = calibration.Append(2, "Calibrate right camera (&1) ")
		
		# Creating the menubar.
		menuBar = wx.MenuBar()
		menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
		menuBar.Append(calibration, "&Calibration")
		self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

		# Set events.
		self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
		self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
		self.Bind(wx.EVT_MENU, self.StartCalibration, calibrate0)
		self.Bind(wx.EVT_MENU, self.StartCalibration, calibrate1)
		
		self.Show(True)
		
	def OnSelect(self, event):
		
		self.sideBySide.Show(self.combo.GetCurrentSelection() == 0)
		
		self.redGreen.Show(self.combo.GetCurrentSelection() == 1)
		# Slider control is only shown for RedGreen feed
		self.sld.Show(self.combo.GetCurrentSelection() == 1)
		
		self.correctedSideBySide.Show(self.combo.GetCurrentSelection() == 2)
		
		self.panel.FitInside()
		self.panel.Layout()
		self.Refresh()
	
	def OnSliderChanged(self, event):
		self.redGreen.distance = self.sld.GetValue()
	
	def OnSliderRelease(self, event):
		## TODO Fix scroll virtual size not updating with change in distance slider		
		self.panel.FitInside()
		self.panel.Layout()
		self.Refresh()
	
	def OnAbout(self, event):
		# A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
		dlg = wx.MessageDialog( self, "TO DO", "About Binocular Algorithm Example", wx.OK)
		dlg.ShowModal() # Show it
		dlg.Destroy() # finally destroy it when finished.

	def OnExit(self, event):
		self.CancelCalibration(None)
		self.Cams[0].release()
		self.Cams[1].release()
		self.Close(True)  # Close the frame.
	
	def StartCalibration(self, event):
		self.combo.Show(False)
		self.sld.Show(False)
		self.sideBySide.Show(False)
		self.redGreen.Show(False)
		self.correctedSideBySide.Show(False)
		
		self.cancelCalibrationButton.Show(True)
		self.searchingToggle.Show(True)
		self.steps.Show(True)
		
		self.calibrationFeed = Calibration(self.panel, self.Cams[event.Id-1], self.pool, event.Id-1)
		self.calibrationFeed.Bind(Calibration.EVT_CORNER_FOUND, self.UpdateLabel)
		
		self.searchingToggle.SetValue(False)
		self.steps.SetLabel("Captured Corners: 0")
		
		mainSizer = self.panel.GetSizer()
		mainSizer.Add(self.calibrationFeed)
		self.panel.SetSizer(mainSizer)
		self.panel.FitInside()
		self.panel.Layout()
		self.Refresh()
		
	def ToggleChanged(self, event):
		self.calibrationFeed.Searching = self.searchingToggle.GetValue()
	
	def UpdateLabel(self, event):

		step = event.step

		self.steps.SetLabel("Captured Corners: " + str(step))
		if(step > 10):
			self.calibrationFeed.Searching = False
			if(self.calibrationFeed.Left):
				calibrateLeft(self.calibrationFeed.objPoints, self.calibrationFeed.imgPoints)
			else:
				calibrateRight(self.calibrationFeed.objPoints, self.calibrationFeed.imgPoints)
			# self.CancelCalibration(None)
			self.steps.SetLabel("Captured Corners: " + str(step) + " Calibration saved")
	
	def CancelCalibration(self, event):
		self.combo.Show(True)
		self.combo.SetValue(displayOptions[0])
		self.sideBySide.Show(True)

		self.cancelCalibrationButton.Show(False)
		self.searchingToggle.Show(False)
		self.steps.Show(False)
		try:
			self.calibrationFeed.Show(False)
			self.calibrationFeed.Destroy()
		except:
			pass

if __name__ == '__main__':
	processPool = Pool()
	app = wx.App(False)
	frame = MainWindow(None, "Binocular Algorithm Example", processPool)
	app.MainLoop()
