from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

WIN_W = 980
WIN_H = 800

# field settings
GRID_SIZE   = 480     # half length of the game field
TILE_SIZE   = 60      # size of each tile
WALL_H      = 115     
EDGE_PAD    = 54      #boundary limit for player
FOV_Y       = 97.0   

# Player settings
PLAYER_SCALE   = 0.37
GUN_LENGTH     = 60
MOVE_STEP      = 18.0
ROTATE_STEP    = 6.0

# Bullet settings
BULLET_SPEED   = 10.0
BULLET_SIZE    = 7
MAX_MISSES     = 10

# Enemy settings
NUM_ENEMIES    = 5
ENEMY_SPEED    = 0.18
ENEMY_Z_POS    = 26
ENEMY_BIG_R    = 25
ENEMY_SMALL_R  = 12
BULLET_HIT_R   = 42   # radius to count bullet hitting enemy
PLAYER_HIT_R   = 37   # radius to count enemy hitting player

# Cheat mode settings
CHEAT_BULLET_SPEED  = 15.0
CHEAT_FIRE_INTERVAL = 0.25
CHEAT_AIM_TOLERANCE = 15.0
CHEAT_SCAN_RANGE    = 900.0
CHEAT_MAX_BULLETS   = 10
CHEAT_ROTATE_SPEED  = 240.0

# Camera rotate (3rd person)
CAM_ROTATE_DEG   = 180.0
CAM_ROTATE_DIST  = 720.0
CAM_Z           = 301.0
CAM_LOOK_OFFSET = 168.0

#Game state variables
playerLife  = 5
score       = 0
missCount = 0

isGameOver  = False
playerDown  = False

# Player position and aim
playerX  = 0.0
playerY  = 0.0
gunAngle = 0.0   # degrees

# Bullet and enemy lists
bullets = []
enemies = []

# Cheat mode flags
cheatMode    = False
cheatVision  = False
cheatCooldown = 0.0

# Camera state
firstPerson      = False
lockedAngleFP    = 0.0
orbitAngle       = CAM_ROTATE_DEG
orbitDist        = CAM_ROTATE_DIST
camHeight        = CAM_Z

# Frame timing
lastTime = 0.0

# For terminal feedback
prevLife   = None
prevMisses = None

# Math helpers

def toRadians(degrees):
    return degrees * math.pi / 180.0

def getDirection(angleDeg):
    # Returns (dx, dy) unit vector for the gun angle
    r = toRadians(angleDeg)
    return -math.sin(r), math.cos(r)

def clampValue(val, minVal, maxVal):
    if val < minVal:
        return minVal
    if val > maxVal:
        return maxVal
    return val

def dist2D(ax, ay, bx, by):
    return math.sqrt((bx - ax) ** 2 + (by - ay) ** 2)

def randomSpawnPos():
    low  = -GRID_SIZE + EDGE_PAD
    high =  GRID_SIZE - EDGE_PAD
    x = random.uniform(low, high)
    y = random.uniform(low, high)
    return x, y

def isInsideBounds(x, y):
    low  = -GRID_SIZE + EDGE_PAD
    high =  GRID_SIZE - EDGE_PAD
    xOk = (x >= low) and (x <= high)
    yOk = (y >= low) and (y <= high)
    return xOk and yOk

# feedback

def printBulletFired():
    print("Player Bullet Fired!")

def printLifeUpdate():
    global prevLife
    if prevLife is None or playerLife != prevLife:
        print("Remaining Player Life:", playerLife)
        prevLife = playerLife

def printMissUpdate():
    global prevMisses
    if prevMisses is None or missCount != prevMisses:
        print(f"Bullet MISSED: {missCount}")
        prevMisses = missCount

# Game reset nd over

def startGameOver():
    global isGameOver, playerDown
    isGameOver = True
    playerDown = True

def resetGame():
    global playerLife, score, missCount, isGameOver, playerDown
    global playerX, playerY, gunAngle, bullets, enemies
    global cheatMode, cheatVision, cheatCooldown
    global firstPerson, lockedAngleFP, orbitAngle, orbitDist, camHeight
    global lastTime, prevLife, prevMisses

    playerLife  = 5
    score       = 0
    missCount = 0
    isGameOver  = False
    playerDown  = False

    playerX  = 0.0
    playerY  = 0.0
    gunAngle = 0.0
    bullets  = []

    cheatMode     = False
    cheatVision   = False
    cheatCooldown = 0.0
    lockedAngleFP = 0.0

    firstPerson = False
    orbitAngle  = CAM_ROTATE_DEG
    orbitDist   = CAM_ROTATE_DIST
    camHeight   = CAM_Z

    lastTime = time.time()

    # spawn enemies
    enemies = []
    for i in range(NUM_ENEMIES):
        ex, ey = randomSpawnPos()
        ph = random.uniform(0, 2 * math.pi)
        enemies.append({"x": ex, "y": ey, "phase": ph})

    prevLife   = None
    prevMisses = None
    printLifeUpdate()

# text drawing

def drawText(screenX, screenY, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glRasterPos2f(screenX, screenY)
    i = 0
    while i < len(text):
        glutBitmapCharacter(font, ord(text[i]))
        i += 1

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# Bullet fire

def fireBullet(angle=None, speed=None):
    global bullets
    if isGameOver:
        return

    shootAngle = gunAngle if angle is None else angle
    shootSpeed = BULLET_SPEED if speed is None else speed

    
    bodyDepth  = 30
    bodyHeight = 72
    legLen     = 54
    baseZ      = legLen + 2

    handZ   = bodyHeight * 0.85 + 6
    handY   = bodyDepth  * 0.20
    gunZ    = handZ + 6.0
    gunY    = handY + 4.0

    tipLocalY = gunY + GUN_LENGTH
    tipLocalZ = gunZ

    tipWorldY = tipLocalY * PLAYER_SCALE
    tipWorldZ = tipLocalZ * PLAYER_SCALE

    dx, dy = getDirection(shootAngle)

    bx = playerX + dx * tipWorldY
    by = playerY + dy * tipWorldY
    bz = baseZ   + tipWorldZ-10

    bullets.append({
        "x": bx, "y": by, "z": bz,
        "angle": shootAngle,
        "speed": shootSpeed
    })
    printBulletFired()

# Scene drawing functions

def drawFloor():
    startPos = -GRID_SIZE
    endPos   =  GRID_SIZE

    glBegin(GL_QUADS)

    rowNum = 0
    y = startPos
    while y < endPos:
        colNum = 0
        x = startPos
        while x < endPos:
            if (rowNum + colNum) % 2 == 0:
                glColor3f(1.0, 1.0, 1.0)
            else:
                glColor3f(0.7, 0.5, 0.94)

            glVertex3f(x,            y,            0)
            glVertex3f(x + TILE_SIZE, y,            0)
            glVertex3f(x + TILE_SIZE, y + TILE_SIZE, 0)
            glVertex3f(x,            y + TILE_SIZE, 0)

            colNum += 1
            x += TILE_SIZE
        rowNum += 1
        y += TILE_SIZE

    glEnd()


def drawBoundaryWalls():
    G = GRID_SIZE
    H = WALL_H

    glBegin(GL_QUADS)

    # Left wall blue
    glColor3f(0, 0, 1)
    glVertex3f(-G, -G, 0)
    glVertex3f(-G,  G, 0)
    glVertex3f(-G,  G, H)
    glVertex3f(-G, -G, H)

    # Right wall green
    glColor3f(0, 1, 0)
    glVertex3f(G, -G, 0)
    glVertex3f(G,  G, 0)
    glVertex3f(G,  G, H)
    glVertex3f(G, -G, H)

    # Far wall cyan
    glColor3f(0, 1, 1)
    glVertex3f(-G, G, 0)
    glVertex3f( G, G, 0)
    glVertex3f( G, G, H)
    glVertex3f(-G, G, H)

    # Near wall white
    glColor3f(1, 1, 1)
    glVertex3f(-G, -G, 0)
    glVertex3f( G, -G, 0)
    glVertex3f( G, -G, H)
    glVertex3f(-G, -G, H)

    glEnd()


def drawPlayer():
    q = gluNewQuadric()

    bodyW  = 64
    bodyD  = 30
    bodyH  = 72
    colW   = 64
    colD   = 30
    colH   = 28
    headR  = 18
    legLen = 54
    legR0  = 10
    legR1  = 6
    legOffX = 14

    handR0  = 13.0
    handR1  = 6.0
    handLen = 48.0
    gunR0   = 13.0
    gunR1   = 2.4

    baseZ = legLen + 2

    glPushMatrix()
    glTranslatef(playerX, playerY, baseZ)
    glScalef(PLAYER_SCALE, PLAYER_SCALE, PLAYER_SCALE)

    if playerDown:
        glRotatef(90, 1, 0, 0)

    glRotatef(gunAngle, 0, 0, 1)

    # legs
    glColor3f(0.0, 0.0, 1.0)
    legPositions = [-legOffX, legOffX]
    idx = 0
    while idx < len(legPositions):
        glPushMatrix()
        glTranslatef(legPositions[idx], 0, 0)
        glRotatef(180, 1, 0, 0)
        gluCylinder(q, legR0, legR1, legLen, 18, 18)
        glPopMatrix()
        idx += 1
    # body
    glPushMatrix()
    glColor3f(0.35, 0.45, 0.25)
    glTranslatef(0, 0, bodyH / 2.0 + 6)
    glScalef(bodyW / 50.0, bodyD / 50.0, bodyH / 50.0)
    glutSolidCube(50)
    glPopMatrix()
    
    # upper chest
    glPushMatrix()
    glColor3f(0.35, 0.45, 0.25)
    glTranslatef(0, 0, bodyH - colH / 2.0 + 6)
    glScalef(colW / 50.0, colD / 50.0, colH / 50.0)
    glutSolidCube(50)
    glPopMatrix()
    
    # Hands and gun 
    handZ  = bodyH * 0.85 + 6
    handY0 = bodyD * 0.20
    handX  = bodyW * 0.29

    glColor3f(0.95, 0.88, 0.77)

    # Left hand
    glPushMatrix()
    glTranslatef(-handX, handY0, handZ)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, handR0, handR1, handLen, 16, 16)
    glPopMatrix()

    # Right hand
    glPushMatrix()
    glTranslatef(handX, handY0, handZ)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, handR0, handR1, handLen, 16, 16)
    glPopMatrix()
    

    # Gun 
    gunZ  = handZ +2
    gunY0 = handY0 

    glPushMatrix()
    glColor3f(0.8, 0.8, 0.8)
    glTranslatef(0, gunY0, gunZ)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, gunR0, gunR1, GUN_LENGTH, 20, 20)
    glPopMatrix()
    
    # head
    glPushMatrix()
    glColor3f(0.0, 0.0, 0.0)
    glTranslatef(0, 0, bodyH + headR)
    gluSphere(q, headR, 18, 18)
    glPopMatrix()
    
    glPopMatrix()


def drawEnemy(en):
    q = gluNewQuadric()

    glPushMatrix()
    glTranslatef(en["x"], en["y"], ENEMY_Z_POS)

    # Pulsing effect
    pulseAmt = 0.18 * math.sin(en["phase"])
    s = 1.0 + pulseAmt
    glScalef(s, s, s)

    # Outer red sphere
    glColor3f(1.0, 0.0, 0.0)
    gluSphere(q, ENEMY_BIG_R, 25, 25)

    # Inner black sphere (head)
    innerR = ENEMY_BIG_R * 0.55
    glPushMatrix()
    glTranslatef(0, 0, ENEMY_BIG_R * 0.85)
    glColor3f(0.0, 0.0, 0.0)
    gluSphere(q, innerR, 25, 25)
    glPopMatrix()

    glPopMatrix()


def drawBullet(b):
    glPushMatrix()
    glTranslatef(b["x"], b["y"], b["z"])
    glColor3f(1.0, 0.0, 0.0)
    glutSolidCube(BULLET_SIZE)
    glPopMatrix()

# Camera 

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = WIN_W / float(WIN_H)
    gluPerspective(FOV_Y, aspect, 0.5, 2500)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if not firstPerson:
        # 3rd person orbit camera
        theta = toRadians(orbitAngle)
        eyeX  = orbitDist * math.sin(theta)
        eyeY  = orbitDist * math.cos(theta) + CAM_LOOK_OFFSET
        eyeZ  = camHeight
        gluLookAt(eyeX, eyeY, eyeZ,   0, 250, 0,   0, 0, 1)
        return

    # First person 
    global lockedAngleFP

    legLen    = 54
    bodyH     = 72
    baseZ     = legLen + 2
    headTopZ  = baseZ + (bodyH + 18) * PLAYER_SCALE

    fdx, fdy = getDirection(gunAngle)

    # Cheat on V off (locked direction)
    if cheatMode and not cheatVision:
        vdx, vdy = getDirection(lockedAngleFP)

        pullBack = 18.0
        liftUp   = 10.0
        lookDist = 650

        cx = playerX - vdx * pullBack
        cy = playerY - vdy * pullBack
        cz = headTopZ + liftUp

        gluLookAt(cx, cy, cz,
                  cx + vdx * lookDist,
                  cy + vdy * lookDist,
                  cz - 2.0,
                  0, 0, 1)
        return

    # Normal FP or cheat + V on
    bodyD  = 32
    handZ  = bodyH * 0.85 + 4
    handY0 = bodyD * 0.20
    gunZ   = handZ + 6.0
    gunY0  = handY0 + 4.0

    tipY = gunY0 + GUN_LENGTH
    tipZ = gunZ

    gTipX = playerX + fdx * (tipY * PLAYER_SCALE)
    gTipY = playerY + fdy * (tipY * PLAYER_SCALE)
    gTipZ = baseZ + tipZ * PLAYER_SCALE

    if cheatMode and cheatVision:
        pullBack = 12.0
        dropAmt  = -4.0
    else:
        pullBack = 18.0
        dropAmt  = -8.0

    cx = gTipX - fdx * pullBack
    cy = gTipY - fdy * pullBack
    cz = gTipZ +5

    lookDist = 520
    gluLookAt(cx, cy, cz,
              gTipX + fdx * lookDist,
              gTipY + fdy * lookDist,
              gTipZ - 10.0,
              0, 0, 1)

# Update functions

def moveEnemies(dt):
    global playerLife
    frameScale = dt * 60.0

    for en in enemies:
        en["phase"] += 0.14 * frameScale

        toX = playerX - en["x"]
        toY = playerY - en["y"]
        d   = math.sqrt(toX * toX + toY * toY) + 1e-6

        stepX = (toX / d) * ENEMY_SPEED * frameScale
        stepY = (toY / d) * ENEMY_SPEED * frameScale

        newX = en["x"] + stepX
        newY = en["y"] + stepY

        lo = -GRID_SIZE + EDGE_PAD
        hi =  GRID_SIZE - EDGE_PAD

        en["x"] = clampValue(newX, lo, hi)
        en["y"] = clampValue(newY, lo, hi)

        # Check if enemy reached player
        if d < PLAYER_HIT_R:
            playerLife -= 1
            printLifeUpdate()
            en["x"], en["y"] = randomSpawnPos()
            if playerLife <= 0:
                startGameOver()


def moveBullets(dt):
    global bullets, missCount
    frameScale = dt * 60.0

    i = 0
    while i < len(bullets):
        b = bullets[i]
        dx, dy = getDirection(b["angle"])
        b["x"] += dx * b["speed"] * frameScale
        b["y"] += dy * b["speed"] * frameScale

        if not isInsideBounds(b["x"], b["y"]):
            missCount += 1
            printMissUpdate()
            bullets.pop(i)
            if missCount >= MAX_MISSES:
                startGameOver()
        else:
            i += 1


def handleHits():
    global score

    hitBullets = set()

    i = 0
    while i < len(enemies):
        en = enemies[i]
        j  = 0
        while j < len(bullets):
            if j in hitBullets:
                j += 1
                continue
            b = bullets[j]
            separation = dist2D(en["x"], en["y"], b["x"], b["y"])
            if separation < BULLET_HIT_R:
                score += 1
                en["x"], en["y"] = randomSpawnPos()
                hitBullets.add(j)
                break
            j += 1
        i += 1

    # Remove bullets that hit something (in reverse order to keep indices valid)
    for idx in sorted(hitBullets, reverse=True):
        bullets.pop(idx)


def runCheatAutoFire(dt):
    global cheatCooldown

    cheatCooldown -= dt
    if cheatCooldown > 0:
        return
    if len(bullets) >= CHEAT_MAX_BULLETS:
        return

    fdx, fdy = getDirection(gunAngle)

    bestIdx  = -1
    bestDist = 1e18

    for i in range(len(enemies)):
        en = enemies[i]
        toX = en["x"] - playerX
        toY = en["y"] - playerY

        # Project onto gun direction
        along = toX * fdx + toY * fdy
        if not (0 < along <= CHEAT_SCAN_RANGE):
            continue

        # Perpendicular distance from gun line
        perpX = toX - along * fdx
        perpY = toY - along * fdy
        perp  = math.sqrt(perpX * perpX + perpY * perpY)

        if perp <= CHEAT_AIM_TOLERANCE:
            if along < bestDist:
                bestDist = along
                bestIdx  = i

    if bestIdx == -1:
        return

    target = enemies[bestIdx]
    dx = target["x"] - playerX
    dy = target["y"] - playerY
    shootAngle = math.degrees(math.atan2(-dx, dy))

    fireBullet(angle=shootAngle, speed=CHEAT_BULLET_SPEED)
    cheatCooldown = CHEAT_FIRE_INTERVAL

# Input handlers

def keyHandler(key, mx, my):
    global gunAngle, playerX, playerY
    global cheatMode, cheatVision, lockedAngleFP

    if key == b'r' or key == b'R':
        resetGame()
        return

    if isGameOver:
        return

    if key == b'c' or key == b'C':
        cheatMode = not cheatMode
        if not cheatMode:
            cheatVision = False
        status = "ON" if cheatMode else "OFF"
        print("Cheat Mode:", status)
        return

    if key == b'v' or key == b'V':
        if cheatMode:
            cheatVision = not cheatVision
            status = "ON" if cheatVision else "OFF"
            print("Cheat (V):", status)
            if not cheatVision and firstPerson:
                lockedAngleFP = gunAngle
        return

    dx, dy = getDirection(gunAngle)

    if key == b'w' or key == b'W':
        nx = playerX + dx * MOVE_STEP
        ny = playerY + dy * MOVE_STEP
        if isInsideBounds(nx, ny):
            playerX = nx
            playerY = ny

    elif key == b's' or key == b'S':
        nx = playerX - dx * MOVE_STEP
        ny = playerY - dy * MOVE_STEP
        if isInsideBounds(nx, ny):
            playerX = nx
            playerY = ny

    elif key == b'a' or key == b'A':
        if not cheatMode:
            gunAngle = (gunAngle + ROTATE_STEP) % 360.0

    elif key == b'd' or key == b'D':
        if not cheatMode:
            gunAngle = (gunAngle - ROTATE_STEP) % 360.0


def arrowKeyHandler(key, mx, my):
    global orbitAngle, camHeight

    if firstPerson:
        return

    if key == GLUT_KEY_LEFT:
        orbitAngle = (orbitAngle - 2.0) % 360.0

    elif key == GLUT_KEY_RIGHT:
        orbitAngle = (orbitAngle + 2.0) % 360.0

    elif key == GLUT_KEY_UP:
        camHeight = clampValue(camHeight + 20.0, 450, 700)

    elif key == GLUT_KEY_DOWN:
        camHeight = clampValue(camHeight - 20.0, 450, 700)


def mouseHandler(btn, state, mx, my):
    global firstPerson, lockedAngleFP

    if state != GLUT_DOWN:
        return

    if btn == GLUT_LEFT_BUTTON:
        fireBullet()

    elif btn == GLUT_RIGHT_BUTTON:
        firstPerson = not firstPerson
        if firstPerson and not cheatVision:
            lockedAngleFP = gunAngle
        mode = "FIRST PERSON" if firstPerson else "THIRD PERSON"
        print("Camera:", mode)

# Main loop call

def idle():
    global gunAngle, lastTime

    nowTime = time.time()
    dt = nowTime - lastTime
    lastTime = nowTime

    if dt < 0:
        dt = 0.0
    elif dt > 0.05:
        dt = 0.05

    if not isGameOver:
        if cheatMode:
            gunAngle = (gunAngle + CHEAT_ROTATE_SPEED * dt) % 360.0
            runCheatAutoFire(dt)
            
        moveEnemies(dt)
        moveBullets(dt)
        handleHits()

    glutPostRedisplay()


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, WIN_W, WIN_H)

    setupCamera()

    drawFloor()
    drawBoundaryWalls()

    for en in enemies:
        drawEnemy(en)

    drawPlayer()

    for b in bullets:
        drawBullet(b)

    if not isGameOver:
        drawText(10, 770, f"Player Life Remaining: {playerLife}")
        drawText(10, 750, f"Game Score: {score}")
        drawText(10, 730, f"Player Bullet Missed: {missCount}")
    else:
        drawText(10, 770, f"Game is Over. Your Score is {score}.")
        drawText(10, 750, "Press \"R\" to RESTART the Game.")

    glutSwapBuffers()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(500, 100)
    glutCreateWindow(b"24301553 LAB: 03")
    resetGame() #Prepares the world before rendering starts
    glutDisplayFunc(display)
    glutKeyboardFunc(keyHandler)
    glutSpecialFunc(arrowKeyHandler)
    glutMouseFunc(mouseHandler)
    glutIdleFunc(idle)

    glutMainLoop()


if __name__ == "__main__":
    main()