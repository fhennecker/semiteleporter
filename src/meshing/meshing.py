#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
		self.activeEdges = Queue.Queue()
		self.existingEdges = {}
		self.faces = []
		self.findSeedTriangle()
		try:
			self.growRegion()
		except:
			pass
		self.writeToObj("test.obj")


	def writeToObj(self, filename):
		with open(filename, 'w') as obj:
			for point in self.points.getSortedPoints():
				obj.write("v "+str(point.x)+" "+str(point.y)+" "+str(point.z)+"\n")
			for face in self.faces :
				obj.write("f "+str(face[0].index)+" "+str(face[1].index)+" "+str(face[2].index)+"\n")


	def findSeedTriangle(self):
		""" Builds the first triangle PQR in order to start region growing """
		# the highest point is by convention part of the seed triangle
		P = self.points.getHighestPoint()
		# its closest point too
		Q = self.points.closestPointTo(P, requiresDifferent=True)
		# we now have to find R which minimizes distance(R, P)+distance(Q, P)
		R = self.points.closestPointToEdge(P,Q)

		self.faces.append((P, Q, R))

		# enqueing the seed triangle's edges
		self.activeEdges.put((P, Q), (P, R), (Q, R))
		self.existingEdges[P] = [Q, R]
		self.existingEdges[Q] = [P, R]
		self.existingEdges[R] = [Q, P]

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
		Pm = (a+b)/2
		# third point of the triangle adjacent to a, b
		PkPoint = [x for x in self.existingEdges[aPoint] if x in self.existingEdges[bPoint]][0]
		Pk = PkPoint.toNPArray()
		# barycenter of the triangle
		P = (a+b+Pk)/3

		# compute normal for triangle (a, b, Pk)”
		ka = a-Pk # k->a vector positioned at origin
		kb = b-Pk # k->b vector positioned at origin
		N = np.cross(ka, kb)

		# build influence region
		n5 = np.cross(kb-ka, N)
		# TODO check direction of n5 when Mr. Procrastination and Ms. Too Late are gone
		aa = a+n5
		bb = b+n5
		# aa, bb is the the (a, b) transposed on the parallel plane which delimits
		# the influence region. It helps us compute the two other corners of the region
		l, m, q = np.linalg.solve(np.array([bb-aa, b-P, N]).transpose(), P-aa)
		bbb = aa + l*(bb-aa)
		l, m, q = np.linalg.solve(np.array([aa-bb, a-P, N]).transpose(), P-bb)
		aaa = bb + l*(aa-bb)

		res = [P+N, P-N, aaa+N, aaa-N, bbb+N, bbb-N]
		print aaa, bbb
		with open("degueu.obj", 'w') as lalala:
			for hello in [a, b, Pk]:
				print>> lalala, "v %f %f %f 1 0 0" % tuple(hello)
			for bonjour in res:
				print>> lalala, "v %f %f %f 0 1 1" % tuple(bonjour)
			print>> lalala, "f 1 2 3"
			print>> lalala, "f 5 4 6"
			print>> lalala, "f 7 5 6"
			print>> lalala, "f 5 4 8"
			print>> lalala, "f 9 8 5"

		# we now have to add/subtract N to these points to get the real corners
		return [P+N, P-N, aaa+N, aaa-N, bbb+N, bbb-N]

	def growRegion(self):
		while not self.activeEdges.empty():
			a, b = self.activeEdges.get()
			print a, b
			regionPoints = self.influenceRegion(a,b)
			minCoords = Point(*[min(map(lambda x:x[i], regionPoints)) for i in range(3)])
			maxCoords = Point(*[max(map(lambda x:x[i], regionPoints)) for i in range(3)])
			minVoxel = self.points.voxelIndexForPoint(minCoords)
			maxVoxel = self.points.voxelIndexForPoint(maxCoords)
			voxelsToLookup = self.points.voxelsInRegion(minVoxel, maxVoxel)
			eligiblePoints = self.points.pointsInVoxels(voxelsToLookup)


			distanceToEdge = lambda ep: np.linalg.norm((ep-a).toNPArray()) + np.linalg.norm((ep-b).toNPArray())
			eps = sorted(filter(lambda ep: ep not in [a, b], eligiblePoints), key=distanceToEdge)
			if len(eps) > 0 :
				newPoint = eps[0]

				self.faces.append((a, b, newPoint))
				self.activeEdges.put((newPoint, a))
				self.activeEdges.put((newPoint, b))
				self.existingEdges[a].append(newPoint)
				self.existingEdges[b].append(newPoint)
				self.existingEdges[newPoint] = [a, b]

op = ObjParser("icoSphere.obj")
vs = VoxelSpace(1)
vs.addPoints(op.points)
print vs
mesher = Mesher(vs)