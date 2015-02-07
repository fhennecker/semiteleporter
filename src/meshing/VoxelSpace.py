from math import floor

class VoxelSpace:
	""" VoxelSpace holds points within voxels. It makes it easier to find
		points that are close to each other for example"""
	def __init__(self, voxelSize=10):
		self.voxelSize = voxelSize
		self.voxels = {}

	def voxelIndexForPoint(self, x, y, z):
		""" Returns the index of the voxel the point x, y, z belongs to """
		xVoxel = floor(x/self.voxelSize)
		yVoxel = floor(y/self.voxelSize)
		zVoxel = floor(z/self.voxelSize)
		return (xVoxel, yVoxel, zVoxel)

	def addPoint(self, x, y, z):
		# computing in which voxel the point should be
		key = self.voxelIndexForPoint(x, y, z)

		# creating a new voxel if necessary
		if not key in self.voxels:
			self.voxels[key] = []

		self.voxels[key].append((x, y, z))

	def addPoints(self, pointsList):
		""" Adds a list of points in this format (lists can be changed to tuples):
			[[x1, y1, z1], [x2, y2, z2], ...] """
		for point in pointsList:
			self.addPoint(point[0], point[1], point[2])

	def allPoints(self):
		""" Returns a list of all points contained in the VoxelSpace """
		res = []
		for voxel in self.voxels: 
			res += self.voxels[voxel]
		return res

	def pointsInCube(self, xCenter, yCenter, zCenter, neighbours=0):
		""" xCenter, yCenter and zCenter define the index of a VOXEL
			Returns a list of all points within the cube :
			[xCenter-neighbours, xCenter+neighbours]
			[yCenter-neighbours, yCenter+neighbours]
			[zCenter-neighbours, zCenter+neighbours] """
		res = []
		for x in range(xCenter-neighbours, xCenter+neighbours+1):
			for y in range(yCenter-neighbours, yCenter+neighbours+1):
				for z in range(zCenter-neighbours, zCenter+neighbours+1):
					key = (x, y, z)
					if key in self.voxels:
						res += self.voxels[key]
		return res

if __name__ == "__main__":
	# test suite
	space = VoxelSpace(5)
	space.addPoint(0, 0, 0)
	space.addPoint(1.1, 2.2, 3.3)
	space.addPoints([(-1, -1, -1), (5, 3, 2), (6, 6, 6)])
	print "All points : "
	print space.allPoints()
	print "All voxels : "
	print space.voxels
	print "Points in cube :"
	print space.pointsInCube(1, 0, 0, 0)
