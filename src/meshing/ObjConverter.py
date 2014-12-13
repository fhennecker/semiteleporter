def toObjFile(values, filename):
	""" Converts a list of [X, Y, Z] lists to filename.obj """
	f = open(filename+".obj", 'w')
	for value in values:
		toWrite = "v " # vertex keyword in .obj
		toWrite += "%f %f %f\n" % (value[0], value[1], value[2])
		toWrite += "p -1\n" # point on the previous vertex defined
		f.write(toWrite)
	f.close()

toObjFile([[0,0,0],[1,1,1],[2,2,2], [0,0,1], [0,1,0], [1, 0,0]], "bonjour")