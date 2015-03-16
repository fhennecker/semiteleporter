import tempfile
from subprocess import check_output

def meshBPA(points, outFile, radius=[10, 20, 50, 80]):
    pointsFile = tempfile.NamedTemporaryFile()
    for p in points:
        x, y, z = p.xyz
        u, v, w = p.normal
        pointsFile.write(("%f "*6 + "\n")%(x, y, z, u, v, w))
    pointsFile.flush()

    radius_opts = reduce(lambda acc,x: acc + ["-r", str(x)], radius, [])

    print check_output([
        "./ballpivoting", 
        "-i", pointsFile.name, "-o", outFile, #Input/Output
        "-p" # Parallel computation
    ] + radius_opts)

