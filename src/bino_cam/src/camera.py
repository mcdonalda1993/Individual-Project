import cv2
from helper_functions import *
import wx
import wx.lib.scrolledpanel

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
		
		self.videoFeed = ShowCapture(self.panel, self.Cams)
		
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		mainSizer.Add(self.combo)
		mainSizer.Add(self.sld)
		mainSizer.Add(self.videoFeed)
		
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
		# print "You selected: " + self.combo.GetStringSelection()
		self.sld.Show(self.combo.GetCurrentSelection()==1)
		self.videoFeed.mode = self.combo.GetStringSelection()
		self.panel.Layout()
	
	def OnSliderChanged(self, event):
		# print "Slider value: " + str(self.sld.GetValue())
		self.videoFeed.distance = self.sld.GetValue()
		

class ShowCapture(wx.Panel):
	def __init__(self, parent, cams, fps=30):
		wx.Panel.__init__(self, parent)

		self.parent = parent
		self.Cams = cams
		self.mode = displayOptions[0]
		self.distance = 0
		image = sideBySide(getFrames(cams))

		height, width = image.shape[:2]
		self.parent.SetVirtualSize((width, height))
		self.SetSize((width, height))
		
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
		if(self.mode == displayOptions[0]):
			image = sideBySide(getFrames(self.Cams))
		elif(self.mode == displayOptions[1]):
			image = redGreen(self.distance, getFrames(self.Cams))
		
		height, width = image.shape[:2]
		self.SetSize((width, height))
		
		image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
		self.image = wx.ImageFromData(width, height, image)
		self.Refresh()

app = wx.App(False)
frame = MainWindow(None, "Binocular Algorithm Example")
app.MainLoop()
