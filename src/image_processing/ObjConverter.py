from json import loads

class ObjConverter:
	def __init__(self, filename):
		self.filename = filename
		self.f = open(filename+".obj", 'a')

	def write(self, values):
		""" Converts a list of [X, Y, Z] lists to file """
		self.f.close()
		self.f = open(self.filename+".obj", 'w')
		for value in values:
			toWrite = "v " # vertex keyword in .obj
			toWrite += "%f %f %f\n" % (value[0], value[1], value[2])
			self.f.write(toWrite)
		self.f.close()
		self.f = open(self.filename+".obj", 'a')

	def append(self, x, y, z):
		""" Appends point x, y, z to file """
		self.f.write("v %f %f %f\n" % (x, y, z))

	def writeFromJson(self, filename):
		self.write(loads(open(filename, 'r').read()))

if __name__ == "__main__":
	from sys import argv
	for filename in argv[1:]:
		name = filename.replace('.json', '')
		oc2 = ObjConverter(name)
		oc2.writeFromJson(filename)
		print "Converted", name

