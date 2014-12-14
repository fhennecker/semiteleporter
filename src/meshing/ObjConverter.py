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
	oc = ObjConverter("bonjour")
	oc.write([[0,0,0],[1,1,1],[2,2,2], [0,0,1], [0,1,0], [1, 0,0]])
	oc2 = ObjConverter("reducted_phone")
	oc2.writeFromJson("reducted_phone.json")

