from VoxelSpace import VoxelSpace, flatten
from math import sqrt

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
		self.findSeedTriangle()
		for line in self.points.getSortedPoints():
			print line

	def findSeedTriangle(self):
		""" Builds the first triangle PQR in order to start region growing """
		# the highest point is by convention part of the seed triangle
		P = self.points.getHighestPoint()
		# its closest point too
		Q = self.points.closestPointTo(P, requiresDifferent=True)
		
		# we now have to find R which minimizes distance(R, P)+distance(Q, P)
		pVoxel = self.points.voxelIndexForPoint(P)
		qVoxel = self.points.voxelIndexForPoint(Q)

		print P, Q





op = ObjParser("teapot.obj")
vs = VoxelSpace(20)
vs.addPoints(op.points)
print vs
mesher = Mesher(vs)