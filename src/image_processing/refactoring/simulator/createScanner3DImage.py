import numpy as np
import cv2

# Object to scan, flat in XZ plane
# Square
#scanObject = np.array([ (-50,-50), (50,-50), (50,50), (-50,50) ], dtype=float)
# Cross
scanObject = np.array([(-50,-100),(50,-100),(50,-50),(100,-50),(100,50),(50,50),(50,100),(-50,100),(-50,50),(-100,50),(-100,-50),(-50,-50) ], dtype=float)
scanObjectHeight = 100

# Laser angle and position
laserRightPos = [150.0, 295.0, 0.0]
laserLeftPos  = [-150.0, 295.0, 0.0]
cameraPos     = [0.0, 295.0, 0.0]
cameraDir     = [0.0, 178.0-295.0, 350.0]
cameraSize    = [1920.0, 1080.0]
cameraAngle   = np.radians(120.0)
turnTablePos  = [0.0,178.0,350.0]
turnTableDiam = 500.0
nSteps        = 32

# ----------------------------------------------------------------------------------------

class c2DSegment:
    # ax+by+c=0
    def __init__(self, p0, p1):
        self.points = np.array([p0, p1], dtype=float)
        self.a = self.points[1][1]-self.points[0][1]
        self.b = -(self.points[1][0]-self.points[0][0])
        self.c = -(self.a * self.points[0][0] + self.b * self.points[0][1])

    def intersect(self, line):
        rv=None
        mat=np.matrix([[self.a, self.b],[line.a, line.b]])
        if np.linalg.det(mat) != 0:
            crossPt = (mat.I * np.matrix([-self.c,-line.c]).T).A1
            if (crossPt - self.points[0]).dot(crossPt - self.points[1]) < 0:
                rv = crossPt
                
        return rv

class c3DLine:
    # (x-xp)/a=(y-yp)/b=(z-zp)/c, dir = (a,b,c)
    def __init__(self, p, dir):
        self.dir=np.array(dir)
        self.p=np.array(p)
        
class c3DPlane:
    # ax+by+cz+d=0, dir=(a,b,c)
    def __init__(self, p, dir, size):
        self.dir=np.array(dir)
        self.origin=np.array(p)
        self.offset=np.array(size)/2
        
        self.d=-self.dir.dot(self.origin)
        self.Xaxis = np.cross(np.array([0,1, 0], dtype=float), self.dir)
        self.Xaxis /= np.linalg.norm(self.Xaxis)
        self.Yaxis = np.cross(self.dir, self.Xaxis)
        self.Yaxis /= np.linalg.norm(self.Yaxis)
        
    def intersect(self,line):
        l = -(self.dir.dot(line.p)+self.d)/self.dir.dot(line.dir)
        return line.p+l*line.dir

    def get2DCoord(self, p):
        return tuple(map(int,map(round,[self.Xaxis.dot(p-self.origin), -self.Yaxis.dot(p-self.origin)]+self.offset)))
    
# Laser line in XZ plane (extend 2x beyond center)
class myLaser:
    def __init__(self, p, target, name):
        self.p    = p
        self.dir  = np.array([-p[0], target[2]])
        self.line = c2DSegment([p[0], 0], [-p[0], 2*target[2]])
        self.name = name

# ----------------------------------------------------------------------------------------
        
if(__name__=="__main__"):
    laserLeft  = myLaser(laserLeftPos,turnTablePos, 'left')
    laserRight = myLaser(laserRightPos,turnTablePos, 'right')

    turnTableCenter = np.array([turnTablePos[0], turnTablePos[2]], dtype=float)
    screenDir = np.array(cameraDir, dtype=float)
    screenSize = np.array(cameraSize, dtype = float)
    screenPos = np.array(cameraPos, dtype=float) + screenDir * (screenSize[0]/2)/np.tan(cameraAngle/2)/np.linalg.norm(screenDir)
    cameraPlane = c3DPlane(screenPos , screenDir, screenSize)

    for step in range(nSteps):
        # Rotate turnTable
        currentObject=[]
        angle=2.0*np.pi*step/nSteps
        rotationMatrix = np.matrix([[np.cos(angle), -np.sin(angle)],[np.sin(angle), np.cos(angle)]])
        for point in scanObject:
            # Rotate object around itself
            newPoint = rotationMatrix * np.matrix(point).T
            # Move Object to the center of the turnTable
            currentObject.append(newPoint.A1+ turnTableCenter)

        # Take a picture for both lasers
        isBreak=False
        for laser in (laserLeft, laserRight):

            # Create black image
            img=np.zeros((screenSize[1], screenSize[0], 3), np.uint8)

            # Display object
            prevEdge=(
                cameraPlane.get2DCoord(cameraPlane.intersect(c3DLine(cameraPos, np.array([currentObject[-1][0],turnTablePos[1]                 ,currentObject[-1][1]]) - cameraPos))),
                cameraPlane.get2DCoord(cameraPlane.intersect(c3DLine(cameraPos, np.array([currentObject[-1][0],turnTablePos[1]+scanObjectHeight,currentObject[-1][1]]) - cameraPos)))
            )
            for point in currentObject:
                edge=(
                    cameraPlane.get2DCoord(cameraPlane.intersect(c3DLine(cameraPos, np.array([point[0],turnTablePos[1]               ,point[1]]) - cameraPos))),
                    cameraPlane.get2DCoord(cameraPlane.intersect(c3DLine(cameraPos, np.array([point[0],turnTablePos[1]+scanObjectHeight,point[1]]) - cameraPos)))
                )
                cv2.line(img, prevEdge[0], edge[0], (0,255,0), 1)
                cv2.line(img, prevEdge[1], edge[1], (0,255,0), 1)
                cv2.line(img, edge[0], edge[1], (0,255,0), 1)
                prevEdge=edge

        # Save image with laser off
            cv2.imwrite('%d_off.png' % (step),img)
            
            # Compute laser intersections with objects        
            l2DPoints=[]
            prevPoint= currentObject[-1]
            for point in currentObject:
                crossPt = c2DSegment(prevPoint, point).intersect(laser.line)
                if crossPt is not None:
                    l2DPoints.append(crossPt)
                prevPoint=point

            # Sort vs distance from laser
            l2DPoints.sort(key=lambda x: np.linalg.norm(x-np.array([laser.p[0],0])))

            # Create 3D lines
            currentHeight=turnTablePos[1]
            isOnTable=True

            # First point is the edge of the turnTable
            prevPoint=np.array(turnTableCenter - laser.dir/np.linalg.norm(laser.dir) * (turnTableDiam/2))
            l3DPoints=[]
            for point in l2DPoints:
                if isOnTable:
                    l3DPoints.append(np.array([prevPoint[0], turnTablePos[1], prevPoint[1]]))
                    l3DPoints.append(np.array([point[0], turnTablePos[1], point[1]]))

                else:
                    l3DPoints.append(np.array([prevPoint[0], turnTablePos[1]+scanObjectHeight, prevPoint[1]]))
                    l3DPoints.append(np.array([point[0], turnTablePos[1]+scanObjectHeight, point[1]]))

                isOnTable = not isOnTable
                prevPoint=point

            # Intersection of each point with the screen
            prevPoint=cameraPlane.get2DCoord(cameraPlane.intersect(c3DLine(cameraPos, l3DPoints[0] - cameraPos)))
            for point in l3DPoints[1:]:
                newPoint=cameraPlane.get2DCoord(cameraPlane.intersect(c3DLine(cameraPos, point - cameraPos)))
                cv2.line(img, prevPoint, newPoint, (0, 0, 255),3)
                prevPoint=newPoint

        # Save image with laser on
            cv2.imwrite('%d_%s.png' % (step, laser.name),img)

            img=cv2.resize(img, (0,0), fx=0.5, fy=0.5)
            cv2.imshow('Camera',img)
            keyEvent = cv2.waitKey(100) & 0xff
            if keyEvent == 27:
                isBreak=True
                break
            
        if isBreak:
            break
        
    cv2.destroyAllWindows()

