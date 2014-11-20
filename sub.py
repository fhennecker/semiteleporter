import cv2
import numpy as np

def subtract(a, b, threshold):
	res = np.empty_like(a)
	if (a.shape == b.shape):
		res[:] = a
		for x in range(len(a)):
			for y in range(len(a[0])):
				for z in range(len(a[0][0])):
					if (z == 2):
						aval = b[x][y][z]
						bval = a[x][y][z]
						if (aval > bval):
							res[x][y][z] = aval-bval
						elif (aval < bval):
							res[x][y][z] = bval-aval
						else:
							res[x][y][z] = 0
						if res[x][y][z] > threshold:
							res[x][y][z] = 255
						else:
							res[x][y][z] = 0
					else:
						res[x][y][z] = 0
	return res

if __name__ == "__main__":

	vase = cv2.imread("demo/vase.jpg")
	vaselaser = cv2.imread("demo/vasefakelaser.jpg")

	cv2.imshow('Vase', subtract(vase, vaselaser, 100))
	cv2.waitKey(0)
	cv2.destroyAllWindows()
