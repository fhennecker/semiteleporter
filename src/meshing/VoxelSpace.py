from math import floor, sqrt
import numpy as np

def flatten(list_of_lists):
	"""[[a, b], [c, d]] -> [a, b, c, d]"""
	for lst in list_of_lists:
		for elem in lst:
			yield elem

def combine(Xrange, Yrange, Zrange):
	"""
	Generate all possible combinations of x,y,z
	"""
	for x in Xrange:
		for y in Yrange:
			for z in Zrange:
				yield (x, y, z)

class Point:
	def __init__(self, x=0, y=0, z=0, index=None):
		self.xyz = np.array((x, y, z))
		self.index = index

	@property
	def x(self): return self.xyz[0]

	@property
	def y(self): return self.xyz[1]
	
	@property
	def z(self): return self.xyz[2]

	def __str__(self):
		return "Point<"+str(self.x)+", "+str(self.y)+", "+str(self.z)+", #"+str(self.index)+">"

	def __repr__(self):
		return "#" + str(self.index)

	def __eq__(self, other):
		res = False
		if isinstance(other, tuple) or isinstance(other, list) and len(other) == 3:
			if self.x == other[0] and self.y == other[1] and self.z == other[2]:
				res = True
		elif isinstance(other, Point):
			if self.x == other.x and self.y == other.y and self.z == other.z:
				res = True
		return res

	def __ne__(self, other):
		return not (self == other)

	def __hash__(self):
		return hash((self.x, self.y, self.z, self.index))

	def __add__(self, other):
		if isinstance(other, Point):
			return self.xyz + other.xyz
		return self.xyz + other

	def __sub__(self, other):
		if isinstance(other, Point):
			return self.xyz - other.xyz
		return self.xyz - other

	def toNPArray(self):
		return self.xyz

	def distance(self, other):
		return np.linalg.norm(self - other)

class VoxelSpace:
	""" VoxelSpace holds points within voxels. It makes it easier to find
		points that are close to each other for example"""
	def __init__(self, voxelSize=10):
		self.voxelSize = voxelSize
		self.voxels = {}
		self.highestPoint = None
		self.highestPointIndex = 1 # .obj files start counting vertices at 1, not 0
		self.boundingBox = [[0,0], [0,0], [0,0]]

	def range3D(self, xmin, xmax, ymin, ymax, zmin, zmax):
		return combine(
			xrange(max(xmin, self.boundingBox[0][0]), min(xmax, self.boundingBox[0][1]+1)),
			xrange(max(ymin, self.boundingBox[1][0]), min(ymax, self.boundingBox[1][1]+1)),
			xrange(max(zmin, self.boundingBox[2][0]), min(zmax, self.boundingBox[2][1]+1))
		)

	def __str__(self):
		return 	"VoxelSpace<voxelSize="+str(self.voxelSize)+\
				", #voxels="+str(self.numberOfVoxels())+\
				", #points="+str(self.numberOfPoints())+\
				", avg(points/voxel)="+str(self.averagePointsPerVoxel())+">"

	def numberOfVoxels(self):
		return len(self.voxels)

	def numberOfPoints(self):
		return self.highestPointIndex-1

	def averagePointsPerVoxel(self):
		return float(self.numberOfPoints())/self.numberOfVoxels()

	def voxelIndexForPoint(self, point):
		""" Returns the index of the voxel the point x, y, z belongs to """
		fl = lambda x: int(floor(x))
		xVoxel = fl(point.x/self.voxelSize)
		yVoxel = fl(point.y/self.voxelSize)
		zVoxel = fl(point.z/self.voxelSize)
		return (xVoxel, yVoxel, zVoxel)

	def addPoint(self, point):
		if not isinstance(point, Point):
			point = Point(point[0], point[1], point[2])

		# computing in which voxel the point should be
		key = self.voxelIndexForPoint(point)

		for i in xrange(3):
			self.boundingBox[i][0] = min(key[i], self.boundingBox[i][0])
			self.boundingBox[i][1] = max(key[i], self.boundingBox[i][1])

		# creating a new voxel if necessary
		if key not in self.voxels:
			self.voxels[key] = []

		# all points need to be sorted in a final .obj
		point.index = self.highestPointIndex
		self.highestPointIndex += 1
		self.voxels[key].append(point)

		if self.highestPoint == None or point.z > self.highestPoint.z:
			self.highestPoint = point

	def addPoints(self, pointsList):
		""" Adds a list of points in this format (lists can be changed to tuples):
			[[x1, y1, z1], [x2, y2, z2], ...] """
		for point in pointsList:
			self.addPoint(point)

	def allPoints(self):
		""" Returns a list of all points contained in the VoxelSpace """
		res = []
		for voxel in self.voxels: 
			res += self.voxels[voxel]
		return res

	def pointsInCube(self, vx, vy, vz, neighbours=0):
		"""
		Returns a list of all points within a cube centered on vx,vy,vz
		extended to neighbours
		"""
		return self.pointsInVoxels(self.voxelsInLayer(vx, vy, vz, 0, neighbours))

	def voxelsInLayer(self, vx, vy, vz, inner=1, outer=2):
		"""
		Returns a list of all voxels containing points within a hollow voxel cube.
		"""
		# Top and bottom planes
		xmin, xmax, ymin, ymax = vx-outer+1, vx+outer, vy-outer+1, vy+outer
		voxels = list(self.range3D(xmin, xmax, ymin, ymax, vz-outer+1, vz-inner+1))
		voxels += list(self.range3D(xmin, xmax, ymin, ymax, vz+inner, vz+outer))

		# Left and right planes
		ymin, ymax, zmin, zmax = vy-outer+1, vy+outer, vz-inner+1, vz+inner
		voxels += list(self.range3D(vx-outer+1, vx-inner+1, ymin, ymax, zmin, zmax))
		voxels += list(self.range3D(vx+inner, vx+outer, ymin, ymax, zmin, zmax))

		# Front and back planes
		xmin, xmax, zmin, zmax = vx-inner+1, vx+inner, vz-inner+1, vz+inner
		voxels += list(self.range3D(xmin, xmax, vy-outer+1, vy-inner+1, zmin, zmax))
		voxels += list(self.range3D(xmin, xmax, vy+inner, vy+outer, zmin, zmax))

		# Return only non-empty
		return list(set(filter(self.voxels.get, voxels)))

	def voxelsAroundRegion(self, cornerA, cornerB, inner=1, outer=1):
		if outer < inner:
			outer = inner

		def rangeBuilder(a, b, extension):
			if a < b :
				return (a-extension, b+extension+1)
			else:
				return (b-extension, a+extension+1)

		# removing center
		args = rangeBuilder(cornerA[0], cornerB[0], inner-1) + \
		       rangeBuilder(cornerA[1], cornerB[1], inner-1) + \
		       rangeBuilder(cornerA[2], cornerB[2], inner-1)
		toRemove = set(self.range3D(*args))

		args = rangeBuilder(cornerA[0], cornerB[0], outer) + \
		       rangeBuilder(cornerA[1], cornerB[1], outer) + \
		       rangeBuilder(cornerA[2], cornerB[2], outer)
		voxels = set(self.range3D(*args))

		return filter(self.voxels.get, voxels^toRemove)

	def voxelsInRegion(self, cornerA, cornerB):
		""" Returns all voxels within the parallelepipedic 
			region defined by the two corners in argument """
		def rangeBuilder(a, b):
			if a < b :
				return (a, b+1)
			else:
				return (b, a+1)
		args = rangeBuilder(cornerA[0], cornerB[0]) + \
		       rangeBuilder(cornerA[1], cornerB[1]) + \
		       rangeBuilder(cornerA[2], cornerB[2])
		return filter(self.voxels.get, self.range3D(*args))

	def pointsInVoxels(self, voxels):
		# get = lambda xyz: self.voxels.get(xyz, [])
		# return flatten(map(get, voxels))
		for vox in voxels:
			for point in self.voxels.get(vox, []):
				yield point

	def closestPointTo(self, point, distanceLimit=10, requiresDifferent=False):
		""" Finds and returns the closest point to (x, y z) 
			we'll only look in voxels within distanceLimit (distance in voxels)"""
		
		cx, cy, cz = self.voxelIndexForPoint(point)

		for i in xrange(distanceLimit):
			points = self.pointsInVoxels(self.voxelsInLayer(cx, cy, cz, i, i+1))
			# Invariant: if we find points in a layer, the nearest one is in
			#            this list (we examine layers incrementally)
			if points:
				resList = sorted(points, key=point.distance)
				if not requiresDifferent or (requiresDifferent and resList[0] != point):
					return resList[0]
				elif len(resList)>1:
					return resList[1]
				else:
					return None

	def closestPointToEdge(self, a, b, distanceLimit=10):
		""" Finds the point p which minimizes distance(a,p)+distance(b,p) """
		aVoxel = self.voxelIndexForPoint(a)
		bVoxel = self.voxelIndexForPoint(b)
		res = None
		bestDistance = float("inf")

		for point in self.pointsInVoxels(self.voxelsInRegion(aVoxel, bVoxel)):
			# print "checking for", point
			if point != a and point != b:
				distance = point.distance(a)+point.distance(b)
				if distance < bestDistance:
					bestDistance = distance
					res = point

		# didn't find any point, start looking in layers around region
		if not res:
			layer = 1
			while layer<distanceLimit and not res:
				for point in self.pointsInVoxels(self.voxelsAroundRegion(aVoxel, bVoxel, layer)):
					distance = point.distance(a)+point.distance(b)
					if distance < bestDistance:
						bestDistance = distance
						res = point
				layer += 1

		return res

	def getHighestPoint(self):
		return self.highestPoint

	def getSortedPoints(self):
		return sorted(self.allPoints(), key=lambda x: x.index)
		

def test_flatten():
	assert flatten([[1, 2], [3, 4]]) == [1, 2, 3, 4]

def test_combine():
	c = set(combine(range(2), range(2), range(2))) 
	s = set([(0,0,0), (0,0,1), (0,1,0), (0,1,1), (1,0,0), (1,0,1), (1,1,0), (1,1,1)])
	assert c == s

def test_partition():
	space = VoxelSpace(5)
	POINTS = [(0,0,0), (1.1,2.2,3.3), (-1,-1,-1), (5,3,2), (6,6,6)]

	space.addPoint(POINTS[0])
	space.addPoint(POINTS[1])
	space.addPoints(POINTS[2:])
	assert len(space.allPoints()) == len(POINTS) # Order may vary
	assert space.voxels == {
		(0,0,0): [(0,0,0), (1.1,2.2,3.3)], 
		(1,0,0): [(5,3,2)],
		(1,1,1): [(6,6,6)],
		(-1,-1,-1): [(-1,-1,-1)]
	}
	assert len(space.pointsInCube(0, 0, 0, 2)) == len(POINTS)
	voxels = set(space.voxelsInLayer(0, 0, 0, 1, 2))
	assert voxels == set([(1,0,0), (1,1,1), (-1,-1,-1)])
	got = set(space.pointsInVoxels(voxels))
	expected = set(flatten(space.voxels.values())) ^ set(space.voxels[(0,0,0)])
	assert got == expected

	assert space.voxelsAroundRegion((0,0,0), (1,1,1)) == [(-1, -1, -1)]

def test_closestPointTo():
	points = VoxelSpace(10)
	points.addPoints([(0, 0, 9), (0, 0, 11), (0, 0, 0)])
	assert points.closestPointTo(Point(0, 0, 0)) == (0, 0, 0)
	assert points.closestPointTo(Point(0,0,0), requiresDifferent=True) == (0,0,9)
	assert points.closestPointTo(Point(1, 0, 0)) == (0, 0, 0)
	assert points.closestPointTo(Point(0, 0, 9.99)) == (0, 0, 9)
	assert points.closestPointTo(Point(0, 0, 10.01)) == (0, 0, 11)
	assert points.closestPointTo(Point(0, 0, 10)) in [(0, 0, 9), (0, 0, 11)]
	assert points.closestPointTo(Point(1000,1000,1000)) is None, "Point too far"

def test_voxelsInRegion():
	points = VoxelSpace(10)
	points.addPoints([(0, 0, 0), (10, 0, 0), (0, 10, 0), (10, 10, 10)])
	voxels = points.voxelsInRegion((1, 1, 1), (0,0,0))
	assert len(voxels) == 4
	assert (0,0,0) in voxels
	assert (1,0,0) in voxels
	assert (0,1,0) in voxels
	assert (1,1,1) in voxels

if __name__ == "__main__":
	test_flatten()
	test_combine()
	test_partition()
	test_closestPointTo()
	test_voxelsInRegion()
