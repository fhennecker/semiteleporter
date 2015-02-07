from math import floor, sqrt

class VoxelSpace:
	""" VoxelSpace holds points within voxels. It makes it easier to find
		points that are close to each other for example"""
	def __init__(self, voxelSize=10):
		self.voxelSize = voxelSize
		self.voxels = {}

	def numberOfVoxels(self):
		return len(self.voxels);

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

	def pointsInCube(self, vx, vy, vz, neighbours=0):
		""" vx, vy and vz define the index of a VOXEL
			Returns a list of all points within the cube :
			[vx-neighbours, vx+neighbours]x[vy-neighbours, vy+neighbours]x[vz-neighbours, vz+neighbours] """

		def rangeBuilder(vc):
			return range(vc-neighbours, vc+neighbours+1)

		res = []
		for x in rangeBuilder(vx):
			for y in rangeBuilder(vy):
				for z in rangeBuilder(vz):
					key = (x, y, z)
					if key in self.voxels:
						res += self.voxels[key]
		return res

	def voxelsInLayer(self, vx, vy, vz, innerLayer=1, outerLayer=1):
		""" Returns a list of all voxels containing points within a hollow voxel cube. """

		def layerRangeBuilder(vc):
			return range(int(vc-outerLayer), int(vc+outerLayer+1))

		def shouldBeIgnored(x, y, z): # returns all voxels within emtpy cube core
			return  ((x, y, z) not in self.voxels) \
					or ((x > vx-innerLayer and x < vx+innerLayer) \
					and (y > vy-innerLayer and y < vy+innerLayer) \
					and (z > vz-innerLayer and z < vz+innerLayer))

		res = []
		for x in layerRangeBuilder(vx):
			for y in layerRangeBuilder(vy):
				for z in layerRangeBuilder(vz):
					if not shouldBeIgnored(x, y, z):
						res.append((x, y, z))
		return res

	def pointsInVoxels(self, voxels):
		res = []
		for voxel in voxels:
			if voxel in self.voxels:
				res += self.voxels[voxel]
		return res



	def closestPointTo(self, x, y, z, distanceLimit=10):
		""" Finds and returns the closest point to (x, y z) 
			we'll only look in voxels within distanceLimit (distance in voxels)"""
		
		def distance(a, b): # distance between two 3D points
			return sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)

		res = None
		# we're going to look through the closest layer first, and go one layer
		# further while we don't find any point
		currentLayer = 0 
		numberOfVoxelsChecked = 0
		currentDistance = float('inf')
		cx, cy, cz = self.voxelIndexForPoint(x, y, z)

		checking = False # if we find a point, we'll need to check if there's no closer one in the next layer

		while (res == None or checking) and numberOfVoxelsChecked < self.numberOfVoxels() and currentLayer < distanceLimit:
			voxelsToCheck = self.voxelsInLayer(cx, cy, cz, currentLayer, currentLayer)
			for point in self.pointsInVoxels(voxelsToCheck):
				if distance((x, y, z), point) < currentDistance:
					currentDistance = distance((x, y, z), point)
					res = point
					checking = not checking # if checking is false, we found the first candidate
											# if it is true, we were checking and we need to get out of the while
			currentLayer+=1
			numberOfVoxelsChecked += len(voxelsToCheck)
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
	print "Points in layer :"
	print space.pointsInVoxels(space.voxelsInLayer(1, 0, 0))

	# testing closestPointTo
	points = VoxelSpace(10)
	points.addPoints([(0, 0, 9), (0, 0, 11), (0, 0, 0)])
	print "Closest point to 0,0,0"
	print points.closestPointTo(0,0,0)
	print "Closest point to 0,0,9"
	print points.closestPointTo(0,0,9)
	print "Closest point to 0,0,10"
	print points.closestPointTo(0,0,10)
	print "Closest point to 0,0,9.99"
	print points.closestPointTo(0,0,9.99)
	print "Closest point to 1000,1000,1000"
	print points.closestPointTo(1000,1000,1000)
