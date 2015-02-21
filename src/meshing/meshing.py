from VoxelSpace import VoxelSpace, flatten, Point
from math import sqrt
import Queue
import numpy as np

class ObjParser:
	def __init__(self, filename):
		with open(filename, 'r') as obj:
			self.points = []
			for line in obj.readlines():
				if line[0:2] == "v ":
					self.points.append(map(float, line[1:].split()))


class Mesher:
	def __init__(self, voxelSpace):
		self.points = voxelSpace
		self.activeEdges = Queue()
		self.existingEdges = {}
		self.faces = []
		self.findSeedTriangle()
		self.growRegion()
		self.writeToObj("test.obj")


	def writeToObj(self, filename):
		with open(filename, 'w') as obj:
			for point in self.points.getSortedPoints():
				obj.write("v "+str(point.x)+" "+str(point.y)+" "+str(point.z)+"\n")
			obj.write("f "+str(self.P.index)+" "+str(self.Q.index)+" "+str(self.R.index)+"\n")


	def findSeedTriangle(self):
		""" Builds the first triangle PQR in order to start region growing """
		# the highest point is by convention part of the seed triangle
		P = self.points.getHighestPoint()
		# its closest point too
		Q = self.points.closestPointTo(P, requiresDifferent=True)
		# we now have to find R which minimizes distance(R, P)+distance(Q, P)
		R = self.points.closestPointToEdge(P,Q)

		self.faces.append((P.index, Q.index, R.index))

		# enqueing the seed triangle's edges
		self.activeEdges.put((P.index, Q.index), (P.index, R.index), (Q.index, R.index))
		self.existingEdges[P] = [Q, R]
		self.existingEdges[Q] = [P, R]
		self.existingEdges[R] = [Q, P]

	def longestEdgeLength(self, point):
		""" Returns the length of the longest edge adjacent to a point """
		res = 0
		if point in self.existingEdges:
			res = max(map(lambda x:point.distance(x)), self.existingEdges[point])
		return res

	def shortestEdgeLength(self, point):
		""" Returns the length of the shortest edge adjacent to a point """
		res = float("inf")
		if point in self.existingEdges:
			res = min(map(lambda x:point.distance(x)), self.existingEdges[point])
		return res

	def samplingUniformityDegree(self, point):
		""" Returns the sampling uniformity degree of a point already part of a face.
			The SUD of a point is the ratio between its longest and shortest adjacent edges. """
		res = None
		if point in self.existingEdges :
			res = self.longestEdgeLength(point)/self.shortestEdgeLength(point)
		return res

	def minEdgeAverage(self, a, b):
		""" Computes the average length of point a and b's shorter adjacent edges """
		res = None
		if point in self.existingEdges:
			res = float(self.shortestEdgeLength(a)+self.shortestEdgeLength(b))/2
		return res

	def influenceRegion(self, a, b):
		""" Computes the influence region of the edge a, b """
		# helper : see CADreconstruction.pdf - H.-W. Lin et al. for notations
		s = max(self.samplingUniformityDegree(a), self.samplingUniformityDegree(b))
		s *= self.minEdgeAverage(a, b)

		# midpoint of (a,b)
		Pm = Point((a.x+b.x)/2, (a.y+b.y)/2, (a.z+b.z)/2)
		# third point of the triangle adjacent to a, b
		Pk = [x for x in self.existingEdges[a] if x in self.existingEdges[b]][0]
		# barycenter of the triangle
		P = Point((a.x+b.x+Pk.x)/3, (a.y+b.y+Pk.y)/3, (a.z+b.z+Pk.z)/3)

		# compute normal for a, b, Pk
		ka = a-Pk # k->a vector positioned at origin
		kb = b-Pk # k->b vector positioned at origin
		N = np.cross(ka.toNPArray(), kb.toNPArray())

		# build influence region
		# TODO

	def growRegion(self):
		while not self.activeEdges.empty():
			a, b = self.activeEdges.get()
			


op = ObjParser("icoSphere.obj")
vs = VoxelSpace(1)
vs.addPoints(op.points)
print vs
mesher = Mesher(vs)