import wx
import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor

class VtkPointCloud(wx.Panel):
	def __init__(self, parent, size=3, zMin=-10.0, zMax=10.0, maxNumPoints=1e6):
		wx.Panel.__init__(self, parent)
		 
		#to interact with the scene using the mouse use an instance of vtkRenderWindowInteractor. 
		self.widget = wxVTKRenderWindowInteractor(self, -1)
		self.widget.Enable(1)
		self.widget.AddObserver("ExitEvent", lambda o,e,f=self: f.Close())
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.Add(self.widget, 1, wx.EXPAND)
		self.SetSizer(self.sizer)
		self.Layout()
		
		self.maxNumPoints = maxNumPoints
		self.vtkPolyData = vtk.vtkPolyData()
		self.clearPoints()
		mapper = vtk.vtkPolyDataMapper()
		mapper.SetInputData(self.vtkPolyData)
		mapper.SetColorModeToDefault()
		mapper.SetScalarRange(zMin, zMax)
		mapper.SetScalarVisibility(1)
		self.vtkActor = vtk.vtkActor()
		self.vtkActor.GetProperty().SetPointSize(size);
		self.vtkActor.SetMapper(mapper)
		
		# Renderer
		renderer = vtk.vtkRenderer()
		renderer.AddActor(self.vtkActor)
		renderer.SetBackground(0.0, 0.0, 0.0)
		renderer.ResetCamera()

		self.widget.GetRenderWindow().AddRenderer(renderer)
		
		axes = vtk.vtkAxesActor()
		self.marker = vtk.vtkOrientationMarkerWidget()
		self.marker.SetInteractor( self.widget._Iren )
		self.marker.SetOrientationMarker( axes )
		self.marker.SetViewport(0.75,0,1,0.25)
		self.marker.SetEnabled(1)
		
		renderer.ResetCamera()
		renderer.ResetCameraClippingRange()
		cam = renderer.GetActiveCamera()

		cam.Azimuth(180)
 
	def addPoint(self, point):
		if self.vtkPoints.GetNumberOfPoints() < self.maxNumPoints:
			pointId = self.vtkPoints.InsertNextPoint(point[:])
			print self.vtkPoints.GetNumberOfPoints()
			self.vtkDepth.InsertNextValue(point[2])
			self.vtkCells.InsertNextCell(1)
			self.vtkCells.InsertCellPoint(pointId)
		else:
			r = random.randint(0, self.maxNumPoints)
			self.vtkPoints.SetPoint(r, point[:])
		
		self.vtkCells.Modified()
		self.vtkPoints.Modified()
		self.vtkDepth.Modified()
 
	def clearPoints(self):
		self.vtkPoints = vtk.vtkPoints()
		self.vtkCells = vtk.vtkCellArray()
		self.vtkDepth = vtk.vtkDoubleArray()
		self.vtkDepth.SetName('DepthArray')
		self.vtkPolyData.SetPoints(self.vtkPoints)
		self.vtkPolyData.SetVerts(self.vtkCells)
		self.vtkPolyData.GetPointData().SetScalars(self.vtkDepth)
		self.vtkPolyData.GetPointData().SetActiveScalars('DepthArray')
 
class TestFrame(wx.Frame):
	def __init__(self,parent,title):
		wx.Frame.__init__(self,parent,title=title,size=(650,600), style=wx.MINIMIZE_BOX|wx.SYSTEM_MENU|
						  wx.CAPTION|wx.CLOSE_BOX|wx.CLIP_CHILDREN)
		self.sp = wx.SplitterWindow(self)
		self.VtkPointCloud = VtkPointCloud(self.sp)
		self.p2 = wx.Panel(self.sp,style=wx.SUNKEN_BORDER)
		 
		self.sp.SplitHorizontally(self.VtkPointCloud,self.p2,470)
 
		self.statusbar = self.CreateStatusBar()
		self.statusbar.SetStatusText("Click on the Plot Button")
		 
		self.plotbut = wx.Button(self.p2,-1,"plot", size=(40,20),pos=(10,10))
		self.plotbut.Bind(wx.EVT_BUTTON,self.plot)
		
		self.count = 0
		 
 
	def plot(self,event):
		self.VtkPointCloud.addPoint((self.count, self.count, self.count, 255, 255, 255))
		self.count += 1
		self.statusbar.SetStatusText("Use your mouse to interact with the model")
 
if __name__ == '__main__':	 
	app = wx.App(redirect=False)
	frame = TestFrame(None,"Lights, Cameras, Action")
	frame.Show()
	app.MainLoop()