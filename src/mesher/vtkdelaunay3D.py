#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import optparse
import vtk
import tempfile


""" Readme :
install (ubuntu) : sudo apt-get install python-vtk
exec example : python vtkdelaunay3D.py icoSphere.obj icoSphere.vtk
  (input file : icoSphere.obj)
  (output files : icoSphere.vtk and icoSphere.vtk.obj)
important parameter alpha (default = 10) :
  python vtkdelaunay3D.py -a 10 teapot_up.obj: gives some teapot with holes
  python vtkdelaunay3D.py -a 20 teapot_up.obj: gives some lovely ship
"""
def delaunay3D(points ,file_out=None,render=True,sizeX=800,sizeY=800,alpha=10.0,tolerance=0.001,offset=2.5):
    """
    Reads a file of vertices in VTK or OBJ format (ignoring any other info)
    Calls vtk Delaunay triangulation
    If file_out specified, writes the result in VTK and OBJ format
    As option, renders the result and displays it using OpenGL
    Optional parameters:
    - alpha (or distance) value to control output shape. VALUE=0.0 => convex hull
    - tolerance to control discarding of closely spaced points
    - offset to control the size of the initial, bounding Delaunay triangulation
    """

    vtkFile = tempfile.NamedTemporaryFile()

    # writes a copy compliant to VTK format
    # as the number of vertices musts be stated in the beginning
    # writing of the file must wait the input is totaly read
    vtkFile.write("# vtk DataFile Version 2.0\n"+vtkFile.name+'\n')
    vtkFile.write("ASCII\nDATASET UNSTRUCTURED_GRID\n")
    vtkFile.write("POINTS "+str(len(points))+" float\n")
    for p in points:
        vtkFile.write("%f %f %f\n" % tuple(p.xyz))
    vtkFile.flush()

    # read VTK input data
    reader = vtk.vtkUnstructuredGridReader()
    reader.SetFileName(vtkFile.name)
    reader.Update()

    # delaunay3D
    delaunay = vtk.vtkDelaunay3D()
    delaunay.SetInputConnection(reader.GetOutputPort())
    delaunay.SetAlpha(alpha)
    delaunay.SetTolerance(tolerance)
    delaunay.SetOffset(offset)

    # extract geometry
    geometry = vtk.vtkGeometryFilter()
    geometry.SetInputConnection(delaunay.GetOutputPort())

    # triangulate
    triangle = vtk.vtkTriangleFilter()
    triangle.PassVertsOff()
    triangle.PassLinesOff()
    triangle.SetInputConnection(geometry.GetOutputPort())

    # write output data VTK
    if (file_out):
        writer = vtk.vtkPolyDataWriter()
        writer.SetFileName(file_out)
        writer.SetInputConnection(triangle.GetOutputPort())
        writer.Update()
    # write output data OBJ
    # as VTK format allows writing multiple points coordinates
    # on a single line, all the coordinates are read before writing
        pointsSection=False
        polygonsSection=False
        vtkFile=open(file_out,'r')
        objFile=open(file_out+'.obj','w')
        for line in vtkFile:
            liste=line.strip().split()
            if len(liste)>2 and liste[0]!='#':
                if polygonsSection:
                    if liste[0]=='3':
        # this polygon is a triangle
        # the indices of the vertices start from 0
        # in OBJ format, they start from 1
                        objFile.write('f')
                        for j in range(1,4):
                            objFile.write(' '+str(int(liste[j])+1))
                        objFile.write('\n')
                elif pointsSection:
                    if liste[0]=="POLYGONS":
                        pointsSection=False
                        polygonsSection=True
                        nTriangles=int(liste[1])
                        assert len(coord)==3*nPoints
                        for i in range(nPoints):
                            objFile.write('v')
                            for j in range(3):
                                objFile.write(' '+coord[3*i+j])
                            objFile.write('\n')	
                    else:
                        for c in liste:
                            coord.append(c)
                elif liste[0]=="POINTS":
                    pointsSection=True
                    nPoints=int(liste[1])
                    coord=[]
        vtkFile.close()
        objFile.close()

    # if not render:
    # 	return

    # # mapper process object
    # mapper = vtk.vtkDataSetMapper()
    # mapper.SetInput(triangle.GetOutput())

    # # actor
    # actor = vtk.vtkActor()
    # actor.SetMapper(mapper)

    # # create render
    # ren = vtk.vtkRenderer()
    # ren.AddActor(actor)
    # ren.SetBackground(.5, .5, .5)

    # # render window
    # renWin = vtk.vtkRenderWindow()
    # renWin.AddRenderer(ren)
    # renWin.SetSize(sizeX,sizeY)

    # # watches for events
    # iren = vtk.vtkRenderWindowInteractor()
    # iren.SetRenderWindow(renWin)

    # # trackball camera
    # style = vtk.vtkInteractorStyleTrackballCamera()
    # iren.SetInteractorStyle(style)

    # # start render
    # renWin.Render()

    # # initialize and start the event loop
    # iren.Initialize()
    # iren.Start()

if __name__ == "__main__":
    opt = optparse.OptionParser(usage = 'usage: %prog [options] input.vtk [output.vtk]')
    opt.add_option('-a', '--alpha',
                   type = 'float',
                   default = 10.0,
                   metavar = 'VALUE',
                   dest = 'alpha',
                   action = 'store',
                   help = 'Specify alpha (or distance) value to control output shape. VALUE=0.0 convex hull [default: %default]')
    opt.add_option('-t', '--tolerance',
                   type = 'float',
                   default = 0.001,
                   metavar = 'VALUE',
                   dest = 'tolerance',
                   action = 'store',
                   help = 'Specify a tolerance to control discarding of closely spaced points [default: %default]')
    opt.add_option('-s', '--offset',
                   type = 'float',
                   default = 2.5,
                   metavar = 'VALUE',
                   dest = 'offset',
                   action = 'store',
                   help = 'Specify a multiplier to control the size of the initial, bounding Delaunay triangulation [default: %default]')

    # command line
    (options, args) = opt.parse_args()
    l = len(args)
    if (l != 1 and l != 2):
       opt.error("incorrect number of arguments")
    file_in  = args[0]
    if (l == 2):
       file_out = args[1]
    else:
       file_out = None

    delaunay3D(file_in,file_out,render=True,sizeX=800,sizeY=800,alpha=10.0,tolerance=0.001,offset=2.5)
