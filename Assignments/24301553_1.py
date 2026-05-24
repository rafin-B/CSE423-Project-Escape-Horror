from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

angle = 0
mode = "day"

rain_drops = []

for i in range(200):
    x = random.uniform(0, 1000)
    y = random.uniform(0, 1000)
    rain_drops.append([x, y])


def draw_background():
    if mode == "day":
        glColor3f(0.4, 0.7, 1.0)
    else:
        glColor3f(0.0, 0.0, 0.0)

    glBegin(GL_TRIANGLES)

    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glVertex2f(0, 1000)

    glVertex2f(1000, 0)
    glVertex2f(1000, 1000)
    glVertex2f(0, 1000)

    glEnd()


def house():
    glColor3f(0, 0, 1)
    glBegin(GL_TRIANGLES)
    glVertex2f(200, 600)
    glVertex2f(500, 800)
    glVertex2f(800, 600)
    glEnd()

    glColor3f(0.75, 0.75, 0.75)
    glBegin(GL_TRIANGLES)
    glVertex2f(300, 400)
    glVertex2f(700, 400)
    glVertex2f(300, 600)

    glVertex2f(300, 600)
    glVertex2f(700, 600)
    glVertex2f(700, 400)
    glEnd()

    glColor3f(0, 0, 0)
    glBegin(GL_LINES)
    glVertex2f(450, 400)
    glVertex2f(450, 500)
    glVertex2f(450, 500)
    glVertex2f(550, 500)
    glVertex2f(550, 500)
    glVertex2f(550, 400)
    glEnd()


def rain():
    glColor3f(1, 1, 1)
    glLineWidth(2)
    glBegin(GL_LINES)
    for drop in rain_drops:
        x, y = drop
        glVertex2f(x, y)
        glVertex2f(x + angle*5, y - 15)
    glEnd()


def update_rain():
    for i in range(len(rain_drops)):
        x, y = rain_drops[i]

        x += angle
        y-=5

        if y < 0 or x < 0 or x > 1000:
            x = random.uniform(0, 1000)
            y = random.uniform(0, 1000)

        rain_drops[i] = [x, y]


def special_keys(key, x, y):
    global angle

    if key == GLUT_KEY_LEFT:
        angle -= .3

    elif key == GLUT_KEY_RIGHT:
        angle+= .3

    glutPostRedisplay()


def keyboard(key, x, y):
    global mode

    if key == b'd':
        mode = "day"

    elif key == b'n':
        mode = "night"

    glutPostRedisplay()


def animate():
    update_rain()
    glutPostRedisplay()


def setup_projection():
    glViewport(0, 0, 1000, 1000)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 1000, 0.0, 1000, 0.0, 1.0)
    glMatrixMode(GL_MODELVIEW)


def display():
    glLoadIdentity()
    setup_projection()
    draw_background()
    house()
    rain()

    glutSwapBuffers()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_RGBA)
    glutInitWindowSize(1000, 1000)
    glutCreateWindow(b"24301553 Task 01")

    glutDisplayFunc(display)
    glutIdleFunc(animate)
    glutSpecialFunc(special_keys)
    glutKeyboardFunc(keyboard)

    glutMainLoop()


if __name__ == "__main__":
    main()
  
    
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

points = []
speed = 2.0
blink = False
freeze = False
blink_counter = 0

def mouse(button, state, x, y):
    global points, blink

    if freeze:
        return

    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        dx = random.choice([-1, 1])
        dy = random.choice([-1, 1])
        color = (random.random(), random.random(), random.random())
        points.append([x, 1000 - y, dx, dy, color])

    elif button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        blink = not blink


def draw_points():
    global points, blink_counter

    glPointSize(6)
    glBegin(GL_POINTS)

    for i in range(len(points)):
        x, y, dx, dy, color = points[i]

        if blink and (blink_counter // 15) % 2 == 0:
            glColor3f(0, 0, 0)
        else:
            glColor3f(*color)

        glVertex2f(x, y)

        if not freeze:
            x += dx * speed
            y += dy * speed

            if x <= 0 or x >= 1000:
                dx = -dx
            if y <= 0 or y >= 1000:
                dy = -dy

            points[i] = [x, y, dx, dy, color]

    glEnd()

def animate():
    global blink_counter

    if blink and not freeze:
        blink_counter += 1

    glutPostRedisplay()

def special_keys(key, x, y):
    global speed

    if freeze:
        return

    if key == GLUT_KEY_UP:
        speed *= 1.5
    elif key == GLUT_KEY_DOWN:
        speed /= 1.5

def keyboard(key, x, y):
    global freeze

    if key == b' ':
        freeze = not freeze

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setup_projection()
    draw_points()
    glutSwapBuffers()
    
def setup_projection():
    glViewport(0, 0, 1000, 1000)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 1000, 0.0, 1000, 0.0, 1.0)
    glMatrixMode(GL_MODELVIEW)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(1000, 1000)
    glutCreateWindow(b"24301553 Task 02")

    glutDisplayFunc(display)
    glutMouseFunc(mouse)
    glutSpecialFunc(special_keys)
    glutKeyboardFunc(keyboard)
    glutIdleFunc(animate)

    glutMainLoop()

if __name__ == "__main__":
    main()