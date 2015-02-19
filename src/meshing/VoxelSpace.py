from math import floor, sqrt
import numpy as np

def flatten(list_of_lists):
	"""[[a, b], [c, d]] -> [a, b, c, d]"""
	return reduce(list.__add__, list_of_lists, [])

def combine(head, *tail):
	"""
	Generate all possible combinations of a set of list
	[[a, b], [c, d]] -> [(a,c), (a,d), (b,c), (b,d)]
	(works on higher dimensions)
	"""
	if not tail:
		return [(h,) for h in head]
	return [(h,) + t for h in head for t in combine(tail[0], *tail[1:])]

class Point:
	def __init__(self, x=0, y=0, z=0, index=None):
		self.x = x
		self.y = y
		self.z = z
		self.index = index

	def __str__(self):
		return "Point<"+str(self.x)+", "+str(self.y)+", "+str(self.z)+", #"+str(self.index)+">"

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

	def distance(self, other):
		return sqrt((self.x-other.x)**2 + (self.y-other.y)**2 + (self.z-other.z)**2)

class VoxelSpace:
	""" VoxelSpace holds points within voxels. It makes it easier to find
		points that are close to each other for example"""
	def __init__(self, voxelSize=10):
		self.voxelSize = voxelSize
		self.voxels = {}
		self.highestPoint = None
		self.highestPointIndex = 1 # .obj files start counting vertices at 1, not 0

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
		if isinstance(point, tuple) or isinstance(point, list):
			point = Point(point[0], point[1], point[2])

		# computing in which voxel the point should be
		key = self.voxelIndexForPoint(point)

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
		x, y = range(vx-outer+1, vx+outer), range(vy-outer+1, vy+outer)
		voxels = combine(x, y, range(vz-outer+1, vz-inner+1))
		voxels += combine(x, y, range(vz+inner, vz+outer))

		# Left and right planes
		y, z = range(vy-outer+1, vy+outer), range(vz-inner+1, vz+inner)
		voxels += combine(range(vx-outer+1, vx-inner+1), y, z)
		voxels += combine(range(vx+inner, vx+outer), y, z)

		# Front and back planes
		x, z = range(vx-inner+1, vx+inner), range(vz-inner+1, vz+inner)
		voxels += combine(x, range(vy-outer+1, vy-inner+1), z)
		voxels += combine(x, range(vy+inner, vy+outer), z)

		# Return only non-empty
		return list(set(filter(self.voxels.get, voxels)))

	def voxelsInCube(self, cornerA, cornerB):
		""" Returns all voxels within the cube defined by the two corners in argument"""
		def rangeBuilder(a, b):
			if a < b :
				return range(a, b+1)
			else:
				return range(b, a+1)
		voxels = combine(rangeBuilder(cornerA[0], cornerB[0]), \
						rangeBuilder(cornerA[1], cornerB[1]), \
						rangeBuilder(cornerA[2], cornerB[2]))
		return filter(self.voxels.get, voxels)

	def pointsInVoxels(self, voxels):
		get = lambda xyz: self.voxels.get(xyz, [])
		return flatten(map(get, voxels))

	def closestPointTo(self, point, distanceLimit=10, requiresDifferent=False):
		""" Finds and returns the closest point to (x, y z) 
			we'll only look in voxels within distanceLimit (distance in voxels)"""
		
		distance = lambda p: point.distance(p)
		cx, cy, cz = self.voxelIndexForPoint(point)

		for i in range(distanceLimit):
			points = self.pointsInVoxels(self.voxelsInLayer(cx, cy, cz, i, i+1))
			# Invariant: if we find points in a layer, the nearest one is in
			#            this list (we examine layers incrementally)
			if points:
				resList = sorted(points, key=distance)
				if not requiresDifferent or (requiresDifferent and resList[0] != point):
					return resList[0]
				elif len(resList)>1:
					return resList[1]
				else:
					return None

	def getHighestPoint(self):
		return self.highestPoint

def test_flatten():
	assert flatten([[1, 2], [3, 4]]) == [1, 2, 3, 4]

def test_combine():
	assert combine(range(2)) == [(0,), (1,)]
	assert set(combine(range(2), range(2))) == set([(0,0), (0,1), (1,0), (1,1)])
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

def test_voxelsInCube():
	points = VoxelSpace(10)
	points.addPoints([(0, 0, 0), (10, 0, 0), (0, 10, 0), (10, 10, 10)])
	voxels = points.voxelsInCube((1, 1, 1), (0,0,0))
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
	test_voxelsInCube()
