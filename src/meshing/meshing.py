#!/usr/bin/env python
# -*- coding: utf-8 -*-

from VoxelSpace import VoxelSpace, flatten, Point, norm3D
from math import sqrt
import Queue
import numpy as np
import traceback
from sys import stdout

class ObjParser:
	def __init__(self, filename):
		with open(filename, 'r') as obj:
			self.points = []
			for line in obj.readlines():
				if line[0:2] == "v ":
					self.points.append(map(float, line[1:].split()))


class Mesher:
	def __init__(self, voxelSpace, debug=False):
		self.points = voxelSpace
		self.activeEdges = Queue.Queue()
		self.existingEdges = {}
		self.faces = set()
		self.debug = debug
		self.findSeedTriangle()
		self.lastFace = (-1, -1, -1)
		try:
			self.growRegion()
		except:
			traceback.print_exc()
		self.writeToObj("test.obj")

	def info(self, *msg):
		msg = ('[%4d faces]' % (len(self.faces)),) + msg
		line = '\r' + ' '.join(map(str, msg))
		stdout.write(line.ljust(80))
		stdout.flush()

	def hasFace(self, p1, p2, p3):
		return (p1, p2, p3) in self.faces or\
		       (p2, p3, p1) in self.faces or\
		       (p3, p1, p2) in self.faces or\
		       (p3, p2, p1) in self.faces or\
		       (p2, p1, p3) in self.faces or\
		       (p1, p3, p2) in self.faces

	def hasEdge(self, fromPoint, toPoint):
		"""Return true if there is an edge between fromPoint and toPoint"""
		return fromPoint in self.existingEdges and toPoint in self.existingEdges[fromPoint]

	def setEdge(self, point, *otherPoints):
		existing = self.existingEdges.get(point, set())
		self.existingEdges[point] = existing.union(set(otherPoints))
		for otherPoint in otherPoints:
			existing = self.existingEdges.get(otherPoint, set())
			self.existingEdges[otherPoint] = existing.union(set((point,)))

	def writeToObj(self, filename):
		with open(filename, 'w') as obj:
			for point in self.points.getSortedPoints():
				obj.write("v "+str(point.x)+" "+str(point.y)+" "+str(point.z))
				# if point in self.lastFace:
				# 	obj.write(" 1 0 1")
				obj.write("\n")
			for face in self.faces:
				obj.write("f "+str(face[0].index)+" "+str(face[1].index)+" "+str(face[2].index)+"\n")

	def findSeedTriangle(self):
		""" Builds the first triangle PQR in order to start region growing """
		# the highest point is by convention part of the seed triangle
		P = self.points.getHighestPoint()
		# its closest point too
		Q = self.points.closestPointTo(P, requiresDifferent=True)
		# we now have to find R which minimizes distance(R, P)+distance(Q, P)
		R = self.points.closestPointToEdge(P,Q)

		self.faces.add((P, Q, R))

		# enqueing the seed triangle's edges
		self.activeEdges.put((P, Q))
		self.activeEdges.put((P, R))
		self.activeEdges.put((Q, R))
		self.setEdge(P, Q, R)
		self.setEdge(Q, R)

	def longestEdgeLength(self, point):
		""" Returns the length of the longest edge adjacent to a point """
		res = max(map(point.distance, self.existingEdges[point]))
		return res

	def shortestEdgeLength(self, point):
		""" Returns the length of the shortest edge adjacent to a point """
		res = min(map(point.distance, self.existingEdges[point]))
		return res

	def samplingUniformityDegree(self, point):
		""" Returns the sampling uniformity degree of a point already part of a face.
			The SUD of a point is the ratio between its longest and shortest adjacent edges. """
		res = self.longestEdgeLength(point)/self.shortestEdgeLength(point)
		return res

	def minEdgeAverage(self, a, b):
		""" Computes the average length of point a and b's shorter adjacent edges """
		res = float(self.shortestEdgeLength(a)+self.shortestEdgeLength(b))/2
		return res

	def influenceRegion(self, aPoint, bPoint):
		""" Returns a list of the corners of the influence region """
		# helper : see CADreconstruction.pdf - H.-W. Lin et al. for notations
		s = max(self.samplingUniformityDegree(aPoint), self.samplingUniformityDegree(bPoint))
		s *= self.minEdgeAverage(aPoint, bPoint)

		a, b = aPoint.toNPArray(), bPoint.toNPArray()

		# midpoint of (a,b)
		# Pm = (a+b)/2
		# third point of the triangle adjacent to a, b
		PkPoint = [x for x in self.existingEdges[aPoint] if x in self.existingEdges[bPoint]][0]
		Pk = PkPoint.toNPArray()
		# barycenter of the triangle
		P = (a+b+Pk)/3

		# compute normal for triangle (a, b, Pk)”
		ka = a-Pk # k->a vector positioned at origin
		kb = b-Pk # k->b vector positioned at origin
		N = np.cross(ka, kb)
		# N /= norm3D(N) # normalize

		# find edge side direction
		n5 = np.cross(kb-ka, N)
		norm = norm3D(n5)
		if norm == 0:
			return None
		n5 /= norm # normalize

		aa = a + s*n5
		bb = b + s*n5
		
		# aa, bb is the the (a, b) transposed on the parallel plane which delimits
		# the influence region. It helps us compute the two other corners of the region
		l, m, q = np.linalg.solve(np.array([bb-aa, b-P, N]).transpose(), P-aa)
		bbb = aa + l*(bb-aa)
		l, m, q = np.linalg.solve(np.array([aa-bb, a-P, N]).transpose(), P-bb)
		aaa = bb + l*(aa-bb)

		res = [P+N, P-N, aaa+N, aaa-N, bbb+N, bbb-N]
		# we now have to add/subtract N to these points to get the real corners
		return res

	def isInRegion(self, regionBox, point):
		"""
		Return true if the point is effectively in the influence region box
		(voxels sampling might return points near the region, but outside)
		"""
		a, b, c, unused, d, unused2 = regionBox
		matrix = np.array([b-a, c-a, d-a]).transpose()
		l, m, g = np.linalg.solve(matrix, point.toNPArray()-a)
		return 0 < l <= 1 and 0 < m and 0 < g and m + g <= 1

	def isInnerEdge(self, a, b):
		"""Return True if edge a,b belongs to 2 triangles"""
		inter = self.existingEdges.get(a, set()) & self.existingEdges.get(b, set())
		if len(inter) != 2:
			return False
		for point in inter:
			if not self.hasFace(a, b, point):
				return False
		return True

	def growRegion(self):
		while not self.activeEdges.empty():
			# Get next active edge
			a, b = self.activeEdges.get()

			# Already inner edge; skip
			if self.isInnerEdge(a, b):
				continue
			self.info("Find triangle from edge", repr(a), repr(b))

			# Find influence region bounding (extruded triangle)
			regionPoints = self.influenceRegion(a,b)

			# The region is malformed; skip
			if regionPoints is None:
				continue

			# Triangle bounding box
			minCoords = Point(*[min(map(lambda x:x[i], regionPoints)) for i in range(3)])
			maxCoords = Point(*[max(map(lambda x:x[i], regionPoints)) for i in range(3)])

			# Voxels bounding box
			minVoxel = self.points.voxelIndexForPoint(minCoords)
			maxVoxel = self.points.voxelIndexForPoint(maxCoords)
			voxelsToLookup = self.points.voxelsInRegion(minVoxel, maxVoxel)

			# Get all points around influence region sorted by distance to active edge
			distanceToEdge = lambda p: norm3D(p-a) + norm3D(p-b)
			eligiblePoints = sorted(self.points.pointsInVoxels(voxelsToLookup), key=distanceToEdge)

			for newPoint in eligiblePoints:
				# Ignore edge vertices
				if newPoint == a or newPoint == b:
					continue

				# Already has a face with this point
				if self.hasFace(newPoint, a, b):
					continue

				# Point not in influence region (voxel sampling)
				if not self.isInRegion(regionPoints, newPoint):
					continue

				self.info("Add face", repr(a), repr(b), repr(newPoint))
				if not self.hasEdge(newPoint, a):
					self.activeEdges.put((newPoint, a))
				else: 
					self.info("Already has edge", repr(newPoint), repr(a))
				if not self.hasEdge(newPoint, b):
					self.activeEdges.put((b, newPoint))
				else:
					self.info("Already has edge", repr(newPoint), repr(b))
				self.setEdge(newPoint, a, b)
				self.lastFace = (newPoint, a, b)
				self.faces.add(self.lastFace)
				break

			if self.debug:
				self.writeToObj("test.obj")
				nPoints = self.points.numberOfPoints()
				with open("test.obj", 'a') as lalala:
					for bonjour in regionPoints:
						print>> lalala, "v %f %f %f 0 1 1" % tuple(bonjour)
					print>> lalala, "f %d %d %d" % (2+nPoints, 1+nPoints, 3+nPoints,)
					print>> lalala, "f %d %d %d" % (4+nPoints, 2+nPoints, 3+nPoints,)
					print>> lalala, "f %d %d %d" % (2+nPoints, 1+nPoints, 5+nPoints,)
					print>> lalala, "f %d %d %d" % (2+nPoints, 5+nPoints, 6+nPoints,)
		self.info("Finished")

		print

if __name__ == "__main__":
	from sys import argv

	op = ObjParser(argv[1] if len(argv) > 1 else "icoSphere.obj")
	vs = VoxelSpace(int(argv[2]) if len(argv) > 2 else 1)
	vs.addPoints(op.points)
	print vs
	mesher = Mesher(vs, debug=(len(argv) > 3))
