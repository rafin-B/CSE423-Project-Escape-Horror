from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random,time

W,H, dtop = 540,780,700



dmx,dmy = 250,dtop
dsize = 30
dspeed = 130
acc = 4
dcol = (1,1,1)


ctx,cty = 270,60
cw,ch = 110,20
cspeed = 14

score = 0
running = True
paused = False
cheat = False
last = time.time()


btns = {
 "r":(60,740,(0,1,1)),
 "t":(270,740,(1,0.6,0)),
 "x":(480,740,(1,0,0))
}


def point(x,y):
 glBegin(GL_POINTS)
 glVertex2f(float(x),float(y))
 glEnd()

def findZone(x0,y0,x1,y1):
 dx,dy=x1-x0,y1-y0
 if abs(dx)>abs(dy):
  if dx>=0 and dy>=0:return 0
  if dx<0 and dy>=0:return 3
  if dx<0:return 4
  return 7
 else:
  if dx>=0 and dy>=0:return 1
  if dx<0 and dy>=0:return 2
  if dx<0:return 5
  return 6

def toZone0(z,x,y):
 if z==0:return x,y
 if z==1:return y,x
 if z==2:return y,-x
 if z==3:return -x,y
 if z==4:return -x,-y
 if z==5:return -y,-x
 if z==6:return -y,x
 if z==7:return x,-y

def fromZone0(z,x,y):
 if z==0:return x,y
 if z==1:return y,x
 if z==2:return -y,x
 if z==3:return -x,y
 if z==4:return -x,-y
 if z==5:return -y,-x
 if z==6:return y,-x
 if z==7:return x,-y

def drawLine(x0,y0,x1,y1):
 z=findZone(x0,y0,x1,y1)

 x0,y0=toZone0(z,x0,y0)
 x1,y1=toZone0(z,x1,y1)

 dx=x1-x0
 dy=y1-y0
 d=2*dy-dx
 x,y=x0,y0

 while x<=x1:
  X,Y=fromZone0(z,x,y)
  point(X,Y)

  if d>0:
   y+=1
   d+=2*(dy-dx)
  else:
   d+=2*dy
  x+=1


def diamond(cx,cy,s,col):
 glColor3f(*col)

 top=(cx,cy+s//2)
 right=(cx+s//2,cy)
 bottom=(cx,cy-s//2)
 left=(cx-s//2,cy)

 drawLine(*top,*right)
 drawLine(*right,*bottom)
 drawLine(*bottom,*left)
 drawLine(*left,*top)

def catcher(cx,cy,w,h,col):
 glColor3f(*col)
 drawLine(cx-w//2,cy,cx-w//4,cy-h)
 drawLine(cx-w//4,cy-h,cx+w//4,cy-h)
 drawLine(cx+w//4,cy-h,cx+w//2,cy)
 drawLine(cx-w//2,cy,cx+w//2,cy)


def newDiamond():
 global dmx,dmy,dcol
 dmy=dtop
 dmx=random.randint(dsize,W-dsize)

 r,g,b=random.random(),random.random(),random.random()
 if max(r,g,b)<0.4:
  r,g,b=1,0.85,0.4
 dcol=(r,g,b)

def collision():
 return (dmx+dsize/2>ctx-cw/2 and
         dmx-dsize/2<ctx+cw/2 and
         dmy-dsize/2<cty+ch/2 and
         dmy+dsize/2>cty-ch/2)

def restart():
 global score,dspeed,running,paused,cheat,ctx,last
 score=0
 dspeed=130
 running=True
 paused=False
 cheat=False
 ctx=W//2
 last=time.time()
 newDiamond()
 print("Starting Over")

def gameOver():
 global running
 running=False
 print("Game Over | Score:",score)

def autoCatch(dt):
 global ctx
 diff=dmx-ctx
 step=220*dt

 if abs(diff)<step:
  ctx=dmx
 else:
  ctx+=step if diff>0 else -step

 ctx=max(cw//2,min(W-cw//2,ctx))


def update():
 global dmy,dspeed,last,score

 if running and not paused:
  now=time.time()
  dt=now-last
  last=now

  dmy-=dspeed*dt
  dspeed+=acc*dt

  if cheat:
   autoCatch(dt)

  if collision():
   score+=1
   print("Score:",score)
   newDiamond()
  elif dmy<0:
   gameOver()

 glutPostRedisplay()


def keyboard(k,x,y):
 global paused,cheat,last,dspeed,cspeed
 if k==b' ':
  paused=not paused
  if not paused:last=time.time()
 elif k==b'c':
  cheat=not cheat
  print("Cheat Mode:",cheat)
 elif k == b'w':
  dspeed += 20
  print("Diamond speed increased:", dspeed)

 elif k == b's':
  dspeed = max(20, dspeed - 20)
  print("Diamond speed decreased:", dspeed)

 elif k == b'd':
  cspeed += 2
  print("Catcher speed increased:", cspeed)

 elif k == b'a':
  cspeed = max(2, cspeed - 2)
  print("Catcher speed decreased:", cspeed) 

def arrows(k,x,y):
 global ctx
 if not running or paused or cheat:return

 if k==GLUT_KEY_LEFT: ctx-=cspeed
 if k==GLUT_KEY_RIGHT: ctx+=cspeed

 ctx=max(cw//2,min(W-cw//2,ctx))

def mouse(btn,state,x,y):
 if btn!=GLUT_LEFT_BUTTON or state!=GLUT_DOWN:return
 y=H-y

 for k,(bx,by,col) in btns.items():
  if bx-25<x<bx+25 and by-25<y<by+25:
   click(k)

def click(k):
 global paused,last
 if k=="r": restart()
 elif k=="t":
  paused=not paused
  if not paused:last=time.time()
 elif k=="x":
  print("Goodbye | Score:",score)
  glutLeaveMainLoop()


def drawButtons():
 for k,(x,y,col) in btns.items():
  glColor3f(*col)
  s=18

  if k=="r":
   drawLine(x+s,y+s,x-s,y)
   drawLine(x+s,y-s,x-s,y)
   drawLine(x+s,y,x-s,y)

  elif k=="t":
   if paused:
    drawLine(x-s,y-s,x+s,y)
    drawLine(x+s,y,x-s,y+s)
    drawLine(x-s,y+s,x-s,y-s)
   else:
    drawLine(x-6,y-s,x-6,y+s)
    drawLine(x+6,y-s,x+6,y+s)

  elif k=="x":
   drawLine(x-s,y-s,x+s,y+s)
   drawLine(x-s,y+s,x+s,y-s)


def display():
 glClear(GL_COLOR_BUFFER_BIT)

 col=(1,0,0) if not running else (1,1,1)
 catcher(ctx,cty,cw,ch,col)

 if running:
  diamond(dmx,dmy,dsize,dcol)

 drawButtons()
 glutSwapBuffers()


def init():
 glClearColor(0,0,0,0)
 glPointSize(2)
 glMatrixMode(GL_PROJECTION)
 glLoadIdentity()
 gluOrtho2D(0,W,0,H)
 newDiamond()


glutInit()
glutInitDisplayMode(GLUT_DOUBLE|GLUT_RGB)
glutInitWindowSize(W,H)
glutInitWindowPosition(320,140)
glutCreateWindow(b"24301553_Assignment02")

init()

glutDisplayFunc(display)
glutKeyboardFunc(keyboard)
glutSpecialFunc(arrows)
glutMouseFunc(mouse)

glutIdleFunc(update)

glutMainLoop()