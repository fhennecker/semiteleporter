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

class VoxelSpace:
	""" VoxelSpace holds points within voxels. It makes it easier to find
		points that are close to each other for example"""
	def __init__(self, voxelSize=10):
		self.voxelSize = voxelSize
		self.voxels = {}
		self.highestPoint = None

	def __str__(self):
		return 	"VoxelSpace<voxelSize="+str(self.voxelSize)+\
				", #voxels="+str(self.numberOfVoxels())+\
				", #points="+str(self.numberOfPoints())+\
				", avg(points/voxel)="+str(self.averagePointsPerVoxel())+">"

	def numberOfVoxels(self):
		return len(self.voxels)

	def numberOfPoints(self):
		return sum(len(self.voxels[voxel]) for voxel in self.voxels)

	def averagePointsPerVoxel(self):
		return float(self.numberOfPoints())/self.numberOfVoxels()

	def voxelIndexForPoint(self, x, y, z):
		""" Returns the index of the voxel the point x, y, z belongs to """
		fl = lambda x: int(floor(x))
		xVoxel = fl(x/self.voxelSize)
		yVoxel = fl(y/self.voxelSize)
		zVoxel = fl(z/self.voxelSize)
		return (xVoxel, yVoxel, zVoxel)

	def addPoint(self, x, y, z):
		# computing in which voxel the point should be
		key = self.voxelIndexForPoint(x, y, z)

		# creating a new voxel if necessary
		if key not in self.voxels:
			self.voxels[key] = []

		self.voxels[key].append((x, y, z))

		if self.highestPoint == None or z > self.highestPoint[2]:
			self.highestPoint = (x, y, z)

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
		y, z = range(vy-outer, vy+outer), range(vz-inner+1, vz+inner)
		voxels += combine(range(vx-outer+1, vx-inner+1), y, z)
		voxels += combine(range(vx+inner, vx+outer), y, z)

		# Front and back planes
		x, z = range(vx-inner+1, vx+inner), range(vz-inner+1, vz+inner)
		voxels += combine(x, range(vy-outer+1, vy-inner+1), z)
		voxels += combine(x, range(vy+inner, vy+outer), z)

		# Return only non-empty
		return filter(self.voxels.get, voxels)

	def pointsInVoxels(self, voxels):
		get = lambda xyz: self.voxels.get(xyz, [])
		return flatten(map(get, voxels))

	def closestPointTo(self, x, y, z, distanceLimit=10):
		""" Finds and returns the closest point to (x, y z) 
			we'll only look in voxels within distanceLimit (distance in voxels)"""
		
		p0 = np.array([x, y, z])
		distance = lambda p: np.linalg.norm(np.array(p) - p0)
		cx, cy, cz = self.voxelIndexForPoint(x, y, z)

		for i in range(distanceLimit):
			points = self.pointsInVoxels(self.voxelsInLayer(cx, cy, cz, i, i+1))
			# Invariant: if we find points in a layer, the nearest one is in
			#            this list (we examine layers incrementally)
			if points:
				return sorted(points, key=distance)[0]

	def highestPoint(self):
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

	space.addPoint(*POINTS[0])
	space.addPoint(*POINTS[1])
	space.addPoints(POINTS[2:])
	assert set(space.allPoints()) == set(POINTS) # Order may vary
	assert space.voxels == {
		(0,0,0): [(0,0,0), (1.1,2.2,3.3)], 
		(1,0,0): [(5,3,2)],
		(1,1,1): [(6,6,6)],
		(-1,-1,-1): [(-1,-1,-1)]
	}
	assert set(space.pointsInCube(0, 0, 0, 2)) == set(POINTS)
	voxels = set(space.voxelsInLayer(0, 0, 0, 1, 2))
	assert voxels == set([(1,0,0), (1,1,1), (-1,-1,-1)])
	got = set(space.pointsInVoxels(voxels))
	expected = set(flatten(space.voxels.values())) ^ set(space.voxels[(0,0,0)])
	assert got == expected

def test_closestPointTo():
	points = VoxelSpace(10)
	points.addPoints([(0, 0, 9), (0, 0, 11), (0, 0, 0)])
	assert points.closestPointTo(0, 0, 0) == (0, 0, 0)
	assert points.closestPointTo(1, 0, 0) == (0, 0, 0)
	assert points.closestPointTo(0, 0, 9.99) == (0, 0, 9)
	assert points.closestPointTo(0, 0, 10.01) == (0, 0, 11)
	assert points.closestPointTo(0, 0, 10) in [(0, 0, 9), (0, 0, 11)]
	assert points.closestPointTo(1000,1000,1000) is None, "Point too far"

if __name__ == "__main__":
	test_flatten()
	test_combine()
	test_partition()
	test_closestPointTo()