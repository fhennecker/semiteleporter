def toObjFile(values, filename):
	""" Converts a list of [X, Y, Z] lists to filename.obj """
	f = open(filename+".obj", 'w')
	for value in values:
		toWrite = "v " # vertex keyword in .obj
		toWrite += "%f %f %f" % (value[0], value[1], value[2])
		f.write(toWrite+"\n")
	f.close()


toObjFile([[1.111, 2.222, 3.333], [4.444, 5.555, 6.666], [7.777, 8.888, 9.999]], "bonjour")