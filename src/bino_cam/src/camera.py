import cv2
import wx
import wx.lib.scrolledpanel
from helper_functions import getWidth, setCameraResolutions16x9
from gui_video import *

displayOptions = ["Side by side", "Red-Green"]

class MainWindow(wx.Frame):
	def __init__(self, parent, title):
		self.Cams = (cv2.VideoCapture(0), cv2.VideoCapture(1))
		setCameraResolutions16x9(self.Cams, 720)
		
		wx.Frame.__init__(self, parent, title=title)
		
		self.panel = wx.lib.scrolledpanel.ScrolledPanel(self, wx.ID_ANY)
		self.panel.SetupScrolling()
		
		self.combo = wx.ComboBox(self.panel,
							  value=displayOptions[0], 
							  size=wx.DefaultSize,
							  choices=displayOptions,
							  style=wx.CB_READONLY)
		self.combo.Bind(wx.EVT_COMBOBOX, self.OnSelect)
		
		self.sld = wx.Slider(self.panel, size=(getWidth(), -1), minValue=0, maxValue=getWidth())
		self.sld.Bind(wx.EVT_SCROLL, self.OnSliderChanged)
		self.sld.Show(False)
		
		self.sideBySide = SideBySide(self.panel, self.Cams)
		self.redGreen = RedGreen(self.panel, self.Cams)
		self.redGreen.Show(False)
		
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		mainSizer.Add(self.combo)
		mainSizer.Add(self.sld)
		mainSizer.Add(self.sideBySide)
		mainSizer.Add(self.redGreen)
		
		self.panel.SetAutoLayout(True)
		self.panel.SetSizer(mainSizer)
		self.panel.Layout()		
		
		# Setting up the menu.
		filemenu= wx.Menu()
		
		# wx.ID_ABOUT and wx.ID_EXIT are standard ids provided by wxWidgets.
		menuAbout = filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
		menuExit = filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")

		# Creating the menubar.
		menuBar = wx.MenuBar()
		menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
		self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

		# Set events.
		self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
		self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
		
		self.Show(True)
		

	def OnAbout(self,e):
		# A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
		dlg = wx.MessageDialog( self, "TO DO", "About Binocular Algorithm Example", wx.OK)
		dlg.ShowModal() # Show it
		dlg.Destroy() # finally destroy it when finished.

	def OnExit(self,e):
		self.Cams[0].release()
		self.Cams[1].release()
		self.Close(True)  # Close the frame.
	
	def OnSelect(self, event):
		
		self.sideBySide.Show(self.combo.GetCurrentSelection() == 0)
		
		self.redGreen.Show(self.combo.GetCurrentSelection() == 1)
		# Shows the additional slider control for RedGreen feed if it is selected
		self.sld.Show(self.combo.GetCurrentSelection() == 1)

		self.panel.Layout()
		self.Refresh()
	
	def OnSliderChanged(self, event):
		# print "Slider value: " + str(self.sld.GetValue())
		self.redGreen.distance = self.sld.GetValue()

app = wx.App(False)
frame = MainWindow(None, "Binocular Algorithm Example")
app.MainLoop()
