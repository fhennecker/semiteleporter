#!/usr/bin/env python
# -*- coding: utf-8 -*-

from VoxelSpace import VoxelSpace, flatten, Point
from math import sqrt
import Queue
import numpy as np
import traceback

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
		self.faces = set()
		self.findSeedTriangle()
		try:
			self.growRegion()
		except:
			traceback.print_exc()
		self.writeToObj("test.obj")

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
		# N /= np.linalg.norm(N) # normalize

		# find edge side direction
		n5 = np.cross(kb-ka, N)
		n5 /= np.linalg.norm(n5) # normalize

		# TODO check direction of n5 when Mr. Procrastination and Ms. Too Late are gone
		aa = a + s*n5
		bb = b + s*n5
		
		# aa, bb is the the (a, b) transposed on the parallel plane which delimits
		# the influence region. It helps us compute the two other corners of the region
		l, m, q = np.linalg.solve(np.array([bb-aa, b-P, N]).transpose(), P-aa)
		bbb = aa + l*(bb-aa)
		l, m, q = np.linalg.solve(np.array([aa-bb, a-P, N]).transpose(), P-bb)
		aaa = bb + l*(aa-bb)

		res = [P+N, P-N, aaa+N, aaa-N, bbb+N, bbb-N]
		with open("degueu.obj", 'w') as lalala:
			for hello in [a, b, Pk]:
				print>> lalala, "v %f %f %f 1 0 0" % tuple(hello)
			for bonjour in res:
				print>> lalala, "v %f %f %f 0 1 1" % tuple(bonjour)
			print>> lalala, "f 1 2 3"
			print>> lalala, "f 5 4 6"
			print>> lalala, "f 7 5 6"
			print>> lalala, "f 5 4 8"
			print>> lalala, "f 5 8 9"

		# we now have to add/subtract N to these points to get the real corners
		return res

	def growRegion(self):
		while not self.activeEdges.empty():
			a, b = self.activeEdges.get()
			print "Find triangle from edge", repr(a), repr(b)
			regionPoints = self.influenceRegion(a,b)
			minCoords = Point(*[min(map(lambda x:x[i], regionPoints)) for i in range(3)])
			maxCoords = Point(*[max(map(lambda x:x[i], regionPoints)) for i in range(3)])
			minVoxel = self.points.voxelIndexForPoint(minCoords)
			maxVoxel = self.points.voxelIndexForPoint(maxCoords)
			voxelsToLookup = self.points.voxelsInRegion(minVoxel, maxVoxel)

			elligible = lambda p: p not in (a, b)
			eligiblePoints = filter(elligible, self.points.pointsInVoxels(voxelsToLookup))

			distanceToEdge = lambda p: np.linalg.norm((p-a).toNPArray()) + np.linalg.norm((p-b).toNPArray())
			eps = sorted(eligiblePoints, key=distanceToEdge)

			for newPoint in eps:
				if self.hasFace(newPoint, a, b):
					continue
				print "Add face", repr(a), repr(b), repr(newPoint)
				if not self.hasEdge(newPoint, a):
					self.activeEdges.put((newPoint, a))
				else: 
					print "Already has edge", repr(newPoint), repr(a)
				if not self.hasEdge(newPoint, b):
					self.activeEdges.put((b, newPoint))
				else:
					print "Already has edge", repr(newPoint), repr(b)
				self.setEdge(newPoint, a, b)
				self.faces.add((newPoint, a, b))
				break
			print "--------------------------------"
		print "\033[1mHave %d faces\033[0m" % (len(self.faces))
		print self.existingEdges

if __name__ == "__main__":
	from sys import argv

	op = ObjParser(argv[1] if len(argv) > 1 else "icoSphere.obj")
	vs = VoxelSpace(int(argv[2]) if len(argv) > 2 else 1)
	vs.addPoints(op.points)
	print vs
	mesher = Mesher(vs)
