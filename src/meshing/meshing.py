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
		self.writeToObj("test.obj")

	def writeToObj(self, filename):
		with open(filename, 'w') as obj:
			for point in self.points.getSortedPoints():
				obj.write("v "+str(point.x)+" "+str(point.y)+" "+str(point.z)+"\n")
			obj.write("f "+str(self.P.index)+" "+str(self.Q.index)+" "+str(self.R.index)+"\n")


	def findSeedTriangle(self):
		""" Builds the first triangle PQR in order to start region growing """
		# the highest point is by convention part of the seed triangle
		self.P = self.points.getHighestPoint()
		# its closest point too
		self.Q = self.points.closestPointTo(self.P, requiresDifferent=True)

		# we now have to find R which minimizes distance(R, P)+distance(Q, P)
		self.R = self.points.closestPointToEdge(self.P,self.Q)





op = ObjParser("teapot.obj")
vs = VoxelSpace(20)
vs.addPoints(op.points)
print vs
mesher = Mesher(vs)