import cv2
import wx
import wx.lib.scrolledpanel
from multiprocessing import Pool
from helper_functions import getWidth, setCameraResolutions16x9
from gui_video import *

displayOptions = ["Side by side", "Red-Green"]

class MainWindow(wx.Frame):
	def __init__(self, parent, title, pool):
				
		self.pool = pool
		
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
		
		font = wx.Font(20, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		self.steps = wx.StaticText(self.panel)
		self.steps.SetLabel("Captured Corners: 0")
		self.steps.SetFont(font)
		
		self.sld.Show(False)
		self.cancelCalibrationButton.Show(False)
		self.steps.Show(False)
		
		# Setup views. Non default ones are hidden.
		self.sideBySide = SideBySide(self.panel, self.Cams)
		self.redGreen = RedGreen(self.panel, self.Cams)
		self.redGreen.Show(False)
		
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		mainSizer.Add(self.combo)
		mainSizer.Add(self.sld)
		mainSizer.Add(self.cancelCalibrationButton)
		mainSizer.Add(self.steps)
		mainSizer.Add(self.sideBySide)
		mainSizer.Add(self.redGreen)
		
		self.panel.SetAutoLayout(True)
		self.panel.SetSizer(mainSizer)
		self.panel.Layout()		
		
		# Setting up the menu.
		filemenu = wx.Menu()
		# wx.ID_ABOUT and wx.ID_EXIT are standard ids provided by wxWidgets.
		menuAbout = filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
		menuExit = filemenu.Append(wx.ID_EXIT,"&Exit"," Terminate the program")
		
		calibration = wx.Menu()
		calibrate0 = calibration.Append(0, "Calibrate left camera (&0) ")
		calibrate1 = calibration.Append(1, "Calibrate right camera (&1) ")
		
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
		self.Cams[0].release()
		self.Cams[1].release()
		self.Close(True)  # Close the frame.
	
	def StartCalibration(self, event):
		self.combo.Show(False)
		self.sld.Show(False)
		self.sideBySide.Show(False)
		self.redGreen.Show(False)
		
		self.cancelCalibrationButton.Show(True)
		self.steps.Show(True)
		
		self.calibrationFeed = Calibration(self.panel, self.Cams[event.Id], self.pool)
		self.calibrationFeed.Bind(Calibration.EVT_CORNER_FOUND, self.UpdateLabel)
		
		mainSizer = self.panel.GetSizer()
		mainSizer.Add(self.calibrationFeed)
		self.panel.SetSizer(mainSizer)
		self.panel.FitInside()
		self.panel.Layout()
		self.Refresh()
	
	def UpdateLabel(self, event):
		## TODO determine when to stop calibration and save results
		step = event.step
		# print "Update: " + str(step)
		self.steps.SetLabel("Captured Corners: " + str(step))
	
	def CancelCalibration(self, event):
		self.combo.Show(True)
		self.combo.SetValue(displayOptions[0])
		self.sideBySide.Show(True)

		self.cancelCalibrationButton.Show(False)
		self.steps.Show(False)
		self.calibrationFeed.Show(False)
		self.calibrationFeed.Destroy()

if __name__ == '__main__':
	pool = Pool()
	app = wx.App(False)
	frame = MainWindow(None, "Binocular Algorithm Example", pool)
	app.MainLoop()
