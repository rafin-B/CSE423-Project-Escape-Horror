from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

WIN_W        = 1024
WIN_H        = 768

GRID_SIZE    = 480      # Half-length of the square arena
TILE_SIZE    = 60       # Floor tile size
WALL_H       = 120      # Boundary wall height
EDGE_PAD     = 50       # Player boundary padding

#  PLAYER CONSTANTS

PLAYER_SCALE  = 0.37    # Global scale applied to the drawn player model
MOVE_STEP     = 14.0    # Units moved per key press
ROTATE_STEP   = 5.0     # Degrees rotated per key press

PLAYER_HIT_R  = 42.0    # Distance at which ghost catches player (game over)

#  GHOST (ENEMY) CONSTANTS

GHOST_BASE_SPEED   = 0.30   # Starting (slow) ghost speed
GHOST_MAX_SPEED    = 0.50   # Maximum ghost speed (easy)
GHOST_MAX_SPEED_NORMAL= 0.80
GHOST_MAX_SPEED_HARD = 1 # Maximum ghost speed (hard mode)
GHOST_ACCEL_TIME   = 90.0   # Seconds over which ghost reaches max speed
GHOST_Z_POS        = 30     # Ghost float height
GHOST_BODY_R       = 28     # Ghost body sphere radius
GHOST_HEAD_R       = 18     # Ghost head sphere radius
GHOST_WARN_DIST    = 200.0  # Distance at which "warning" flicker starts

#  CAMERA CONSTANTS

CAM_TOPDOWN_NORMAL = 420.0
CAM_TOPDOWN_ZOOM   = 680.0

FOV_TOPDOWN   = 75.0
FOV_FIRSTPERSON = 90.0

CAM_ORBIT_DEG   = 180.0
CAM_LOOK_OFFSET = 150.0

#  GAME MODE SETTINGS

# Mode indices
MODE_EASY   = 0
MODE_NORMAL = 1
MODE_HARD   = 2

MODE_SETTINGS = {
    MODE_EASY:   {"label": "EASY",   "time": 180.0, "cells": 2, "switches": 2, "ghost_max": GHOST_MAX_SPEED,      "color": (0.20, 0.95, 0.20)},
    MODE_NORMAL: {"label": "NORMAL", "time": 150.0, "cells": 3, "switches": 2, "ghost_max": GHOST_MAX_SPEED_NORMAL,      "color": (0.95, 0.85, 0.20)},
    MODE_HARD:   {"label": "HARD",   "time": 120.0, "cells": 4, "switches": 2, "ghost_max": GHOST_MAX_SPEED_HARD, "color": (0.95, 0.20, 0.20)},
}

# Current selected game mode (default: Normal)
currentMode = MODE_NORMAL


#  OBJECTIVE / ITEM COUNTS  

NUM_POWER_CELLS  = 3
NUM_SWITCHES     = 2
GAME_TIME_LIMIT  = 150.0

# Interaction radius
INTERACT_RADIUS  = 90.0


# WALL DEFINITIONS


INNER_WALLS = [
    # Horizontal walls
    (-300,  -80,  -80,  -80),
    (  80,  -80,  300,  -80),
    (-200,  120,    -40,  120),
    (   40,  120,  200,  120),
    (-300, -250, -150, -250),
    ( 150, -250,  300, -250),
    (-100,  280,  100,  280),
    (-300,  300, -180,  300),
    ( 180,  300,  300,  300),

    # Vertical walls
    (  -80, -300,  -80,  -80),
    (  -80,   80,  -80,  300),
    (   80, -300,   80,  -80),
    (   80,   80,   80,  300),
    ( -200, -300, -200, -160),
    (  200, -300,  200, -160),
    ( -200,  160, -200,  300),
    (  200,  160,  200,  300),
    ( -350, -100, -350,  100),
    (  350, -100,  350,  100),
]

WALL_THICKNESS = 14.0

SWITCH_POSITIONS = [
    ( 280.0,  180.0),
    (-280.0,  -50.0),
]

# Exit position (fixed at north boundary)
EXIT_X =   0.0
EXIT_Y = 425.0

SAFE_POSITION = (320.0, 320.0)

#  RANDOM SPAWN HELPERS

def toRadians(degrees):
    return degrees * math.pi / 180.0

def getDirection(angleDeg):
    r = toRadians(angleDeg)
    return -math.sin(r), math.cos(r)

def dist2D(ax, ay, bx, by):
    return math.sqrt((bx - ax) ** 2 + (by - ay) ** 2)

def clampValue(val, minVal, maxVal):
    if val < minVal: return minVal
    if val > maxVal: return maxVal
    return val

def isInsideBounds(x, y):
    lo = -GRID_SIZE + EDGE_PAD
    hi =  GRID_SIZE - EDGE_PAD
    return (lo <= x <= hi) and (lo <= y <= hi)

def segmentAABBCollide(wx1, wy1, wx2, wy2, px, py, radius):
    half = WALL_THICKNESS / 2.0 + radius
    minX = min(wx1, wx2) - half
    maxX = max(wx1, wx2) + half
    minY = min(wy1, wy2) - half
    maxY = max(wy1, wy2) + half
    return (minX <= px <= maxX) and (minY <= py <= maxY)

def isBlockedByWall(nx, ny, radius=18.0):
    for (wx1, wy1, wx2, wy2) in INNER_WALLS:
        if segmentAABBCollide(wx1, wy1, wx2, wy2, nx, ny, radius):
            return True
    return False

def randomSpawnFar(px, py, minDist=300.0):
    """Spawn a random position at least minDist from (px,py)."""
    lo = -GRID_SIZE + EDGE_PAD
    hi =  GRID_SIZE - EDGE_PAD
    for _ in range(200):
        x = random.uniform(lo, hi)
        y = random.uniform(lo, hi)
        if dist2D(px, py, x, y) >= minDist:
            return x, y
    return lo + 40, lo + 40

def randomOpenPosition(excludeList=None, minDistFromEach=80.0,
                       minDistFromPlayer=150.0, clearRadius=35.0):
    
    if excludeList is None:
        excludeList = []

    lo = -GRID_SIZE + EDGE_PAD + 30
    hi =  GRID_SIZE - EDGE_PAD - 30

    for _ in range(500):
        x = random.uniform(lo, hi)
        y = random.uniform(lo, hi)

        # Must be in bounds
        if not isInsideBounds(x, y):
            continue

        # Must not be inside a wall
        if isBlockedByWall(x, y, radius=clearRadius):
            continue

        # Must not be too close to player start
        if dist2D(0.0, 0.0, x, y) < minDistFromPlayer:
            continue

        # Must not be too close to existing items
        tooClose = False
        for (ex, ey) in excludeList:
            if dist2D(x, y, ex, ey) < minDistFromEach:
                tooClose = True
                break
        if tooClose:
            continue

        # Also keep away from exit and safe
        if dist2D(x, y, EXIT_X, EXIT_Y) < 80.0:
            continue
        sx, sy = SAFE_POSITION
        if dist2D(x, y, sx, sy) < 80.0:
            continue

        return x, y

    # Fallback: safe known open positions
    fallbacks = [
        (-350.0,  350.0),
        ( 350.0, -350.0),
        (-250.0, -200.0),
        ( 250.0,  250.0),
        (-300.0,  200.0),
        ( 300.0, -200.0),
        (-150.0, -350.0),
        ( 150.0,  350.0),
    ]
    random.shuffle(fallbacks)
    for (fx, fy) in fallbacks:
        skip = False
        for (ex, ey) in excludeList:
            if dist2D(fx, fy, ex, ey) < minDistFromEach:
                skip = True
                break
        if not skip:
            return fx, fy

    return -350.0, 350.0   # last resort

# --- Player ---
playerX      = 0.0
playerY      = 0.0
gunAngle     = 0.0
playerAlive  = True

# --- Ghost ---
ghostX       = -400.0
ghostY       = -400.0
ghostPhase   = 0.0

# --- Camera ---
orbitAngle   = 0.0
orbitDist    = CAM_TOPDOWN_NORMAL
camHeight    = CAM_TOPDOWN_NORMAL
firstPerson  = False
lockedFP     = 0.0
zoomedOut    = False

# --- Objective Tracking ---
powerCellsCollected  = 0
switchesActivated    = [False, False]
hasKey               = False
safeopened           = False
exitUnlocked         = False
playerWon            = False

powerCellAlive       = [True, True, True]
switchState          = [False, False]

# Random spawn positions (filled at reset)
POWER_CELL_POSITIONS = []
KEY_POSITION         = (0.0, -350.0)

#Timing
lastTime       = 0.0
elapsedTime    = 0.0
flickerTimer   = 0.0

#Cheat Mode
cheatMode = False   # C key toggles this

# Overall game state
isGameOver   = False
gameStarted  = False    # False = mode-select / start screen
gameMsg      = ""

# Mode select state
startPhase   = 0        # 0 = choose mode, 1 = press enter to play

def resetGame():
    global playerX, playerY, gunAngle, playerAlive
    global ghostX, ghostY, ghostPhase
    global camHeight, firstPerson, lockedFP, zoomedOut
    global orbitAngle, orbitDist
    global powerCellsCollected, switchesActivated, hasKey, safeopened
    global exitUnlocked, playerWon, powerCellAlive, switchState
    global lastTime, elapsedTime, flickerTimer
    global isGameOver, gameMsg
    global NUM_POWER_CELLS, GAME_TIME_LIMIT
    global POWER_CELL_POSITIONS, KEY_POSITION
    global cheatMode

    settings = MODE_SETTINGS[currentMode]
    NUM_POWER_CELLS  = settings["cells"]
    GAME_TIME_LIMIT  = settings["time"]

    #Player
    playerX     = 0.0
    playerY     = 0.0
    gunAngle    = 0.0
    playerAlive = True

    #Ghost spawns far away
    ghostX, ghostY = randomSpawnFar(0.0, 0.0, minDist=350.0)
    ghostPhase  = 0.0

    #Camera
    firstPerson = True
    lockedFP    = 0.0
    zoomedOut   = False
    camHeight   = CAM_TOPDOWN_NORMAL
    orbitAngle  = 0.0
    orbitDist   = CAM_TOPDOWN_NORMAL

    #Objectives
    powerCellsCollected = 0
    powerCellAlive      = [True] * NUM_POWER_CELLS
    switchesActivated   = [False] * NUM_SWITCHES
    switchState         = [False] * NUM_SWITCHES
    hasKey              = False
    safeopened          = False
    exitUnlocked        = False
    playerWon           = False

    #Random spawn positions for power cells and key
    spawnedPositions = []
    # Also keep away from fixed switches and safe
    for sx, sy in SWITCH_POSITIONS:
        spawnedPositions.append((sx, sy))
    spawnedPositions.append(SAFE_POSITION)

    POWER_CELL_POSITIONS = []
    for i in range(NUM_POWER_CELLS):
        pos = randomOpenPosition(
            excludeList=spawnedPositions,
            minDistFromEach=100.0,
            minDistFromPlayer=160.0,
            clearRadius=35.0
        )
        POWER_CELL_POSITIONS.append(pos)
        spawnedPositions.append(pos)

    # Key spawn (away from cells and switches)
    KEY_POSITION = randomOpenPosition(
        excludeList=spawnedPositions,
        minDistFromEach=100.0,
        minDistFromPlayer=180.0,
        clearRadius=35.0
    )

    #Timing 
    lastTime     = time.time()
    elapsedTime  = 0.0
    flickerTimer = 0.0

    # Cheat mode resets off
    cheatMode = False

    # Game state 
    isGameOver = False
    gameMsg    = ""

    mode_label = MODE_SETTINGS[currentMode]["label"]
    print(f"=== ESCAPE HORROR: Game Reset [{mode_label} MODE] ===")
    print(f"  Time: {int(GAME_TIME_LIMIT)}s | Power Cells: {NUM_POWER_CELLS}")
    print(f"  Power cell positions: {POWER_CELL_POSITIONS}")
    print(f"  Key position: {KEY_POSITION}")

#  GAME OVER / WIN TRIGGERS

def triggerGameOver(reason):
    global isGameOver, playerAlive, gameMsg
    isGameOver  = True
    playerAlive = False
    gameMsg     = reason
    print("GAME OVER:", reason)

def triggerWin():
    global isGameOver, playerWon, gameMsg
    isGameOver = True
    playerWon  = True
    gameMsg    = "YOU ESCAPED! Congratulations!"
    print("PLAYER WINS:", gameMsg)
    
#  TEXT DRAWING

def drawText(screenX, screenY, text, r=1.0, g=1.0, b=1.0,
             font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(r, g, b)
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

def drawTextLarge(screenX, screenY, text, r=1.0, g=1.0, b=1.0):
    drawText(screenX, screenY, text, r, g, b, font=GLUT_BITMAP_HELVETICA_18)

#  FLOOR DRAWING

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
                glColor3f(0.75, 0.75, 0.75)
            else:
                glColor3f(0.45, 0.45, 0.45)
            glVertex3f(x, y, -2.0)
            glVertex3f(x + TILE_SIZE, y, -2.0)
            glVertex3f(x + TILE_SIZE, y + TILE_SIZE, -2.0)
            glVertex3f(x, y + TILE_SIZE, -2.0)
            colNum += 1
            x += TILE_SIZE
        rowNum += 1
        y += TILE_SIZE
    glEnd()

#  BOUNDARY WALLS


def drawBoundaryWalls():
    G = GRID_SIZE
    H = WALL_H
    glBegin(GL_QUADS)
    glColor3f(0.15, 0.15, 0.15)
    glVertex3f(-G, -G, 0);  glVertex3f(-G,  G, 0)
    glVertex3f(-G,  G, H);  glVertex3f(-G, -G, H)
    glColor3f(0.15, 0.15, 0.15)
    glVertex3f(G, -G, 0);  glVertex3f(G,  G, 0)
    glVertex3f(G,  G, H);  glVertex3f(G, -G, H)
    glColor3f(0.15, 0.15, 0.15)
    glVertex3f(-G, G, 0);  glVertex3f( G, G, 0)
    glVertex3f( G, G, H);  glVertex3f(-G, G, H)
    glColor3f(0.15, 0.15, 0.15)
    glVertex3f(-G, -G, 0);  glVertex3f( G, -G, 0)
    glVertex3f( G, -G, H);  glVertex3f(-G, -G, H)
    glEnd()


#  INNER MAZE WALLS

def drawOneInnerWall(wx1, wy1, wx2, wy2):
    H    = WALL_H + 1
    half = WALL_THICKNESS / 2.0
    dx = wx2 - wx1
    dy = wy2 - wy1
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1e-6:
        return
    dx /= length
    dy /= length
    nx = -dy
    ny =  dx
    c1x = wx1 + nx * half;  c1y = wy1 + ny * half
    c2x = wx1 - nx * half;  c2y = wy1 - ny * half
    c3x = wx2 - nx * half;  c3y = wy2 - ny * half
    c4x = wx2 + nx * half;  c4y = wy2 + ny * half
    glBegin(GL_QUADS)
    glColor3f(0.55, 0.14, 0.10)
    glVertex3f(c1x, c1y, 0);   glVertex3f(c4x, c4y, 0)
    glVertex3f(c4x, c4y, H);   glVertex3f(c1x, c1y, H)
    glColor3f(0.48, 0.12, 0.08)
    glVertex3f(c2x, c2y, 0);   glVertex3f(c3x, c3y, 0)
    glVertex3f(c3x, c3y, H);   glVertex3f(c2x, c2y, H)
    glColor3f(0.42, 0.10, 0.07)
    glVertex3f(c1x, c1y, 0);   glVertex3f(c2x, c2y, 0)
    glVertex3f(c2x, c2y, H);   glVertex3f(c1x, c1y, H)
    glColor3f(0.42, 0.10, 0.07)
    glVertex3f(c4x, c4y, 0);   glVertex3f(c3x, c3y, 0)
    glVertex3f(c3x, c3y, H);   glVertex3f(c4x, c4y, H)
    glColor3f(0.30, 0.08, 0.05)
    glVertex3f(c1x, c1y, H);   glVertex3f(c2x, c2y, H)
    glVertex3f(c3x, c3y, H);   glVertex3f(c4x, c4y, H)
    glEnd()

def drawInnerWalls():
    for wall in INNER_WALLS:
        drawOneInnerWall(*wall)


#  PLAYER DRAWING

def drawPlayer():
    q = gluNewQuadric()
    bodyW   = 64
    bodyD   = 30
    bodyH   = 72
    colW    = 64
    colD    = 30
    colH    = 28
    headR   = 18
    legLen  = 54
    legR0   = 10
    legR1   = 6
    legOffX = 14
    handR0  = 13.0
    handR1  = 6.0
    handLen = 48.0
    baseZ = legLen + 2

    glPushMatrix()
    glTranslatef(playerX, playerY, baseZ)
    glScalef(PLAYER_SCALE, PLAYER_SCALE, PLAYER_SCALE)
    glRotatef(gunAngle, 0, 0, 1)

    glColor3f(0.20, 0.30, 0.85)
    legPositions = [-legOffX, legOffX]
    idx = 0
    while idx < len(legPositions):
        glPushMatrix()
        glTranslatef(legPositions[idx], 0, 0)
        glRotatef(180, 1, 0, 0)
        gluCylinder(q, legR0, legR1, legLen, 18, 18)
        glPopMatrix()
        idx += 1

    glPushMatrix()
    glColor3f(0.50, 0.68, 0.35)
    glTranslatef(0, 0, bodyH / 2.0 + 6)
    glScalef(bodyW / 50.0, bodyD / 50.0, bodyH / 50.0)
    glutSolidCube(50)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.45, 0.60, 0.30)
    glTranslatef(0, 0, bodyH - colH / 2.0 + 6)
    glScalef(colW / 50.0, colD / 50.0, colH / 50.0)
    glutSolidCube(50)
    glPopMatrix()

    handZ  = bodyH * 0.85 + 6
    handY0 = bodyD * 0.20
    handX  = bodyW * 0.29
    glColor3f(0.85, 0.72, 0.60)

    glPushMatrix()
    glTranslatef(-handX, handY0, handZ)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, handR0, handR1, handLen, 16, 16)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(handX, handY0, handZ)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, handR0, handR1, handLen, 16, 16)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.85, 0.72, 0.60)
    glTranslatef(0, 0, bodyH + headR + 4)
    gluSphere(q, headR, 18, 18)
    glPopMatrix()

    eyeR = 4.0
    glColor3f(0.05, 0.05, 0.05)
    glPushMatrix()
    glTranslatef(-7, bodyD * 0.38, bodyH + headR * 1.5 + 4)
    gluSphere(q, eyeR, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef( 7, bodyD * 0.38, bodyH + headR * 1.5 + 4)
    gluSphere(q, eyeR, 10, 10)
    glPopMatrix()

    glPopMatrix()

#  PLAYER TOP-DOWN MARKER

def drawPlayerTopDownMarker():
    if firstPerson:
        return
    MARKER_Z   = 3.0
    RING_R     = 32.0
    RING_W     = 8.0
    SEGMENTS   = 24
    ARROW_LEN  = 50.0
    ARROW_HALF = 14.0

    fdx, fdy = getDirection(gunAngle)
    pdx = -fdy
    pdy =  fdx

    glPushMatrix()
    glTranslatef(playerX, playerY, MARKER_Z)

    glBegin(GL_QUADS)
    glColor3f(0.20, 1.00, 0.90)
    i = 0
    while i < SEGMENTS:
        a0 = toRadians(i       * 360.0 / SEGMENTS)
        a1 = toRadians((i + 1) * 360.0 / SEGMENTS)
        ix0 = math.cos(a0) * (RING_R - RING_W)
        iy0 = math.sin(a0) * (RING_R - RING_W)
        ix1 = math.cos(a1) * (RING_R - RING_W)
        iy1 = math.sin(a1) * (RING_R - RING_W)
        ox0 = math.cos(a0) * RING_R
        oy0 = math.sin(a0) * RING_R
        ox1 = math.cos(a1) * RING_R
        oy1 = math.sin(a1) * RING_R
        glVertex3f(ix0, iy0, 0)
        glVertex3f(ox0, oy0, 0)
        glVertex3f(ox1, oy1, 0)
        glVertex3f(ix1, iy1, 0)
        i += 1
    glEnd()

    bLx = pdx * (-ARROW_HALF)
    bLy = pdy * (-ARROW_HALF)
    bRx = pdx *   ARROW_HALF
    bRy = pdy *   ARROW_HALF
    tpx = fdx * ARROW_LEN
    tpy = fdy * ARROW_LEN
    midx = fdx * (RING_R - RING_W)
    midy = fdy * (RING_R - RING_W)

    glBegin(GL_QUADS)
    glColor3f(1.00, 0.95, 0.10)
    glVertex3f(0,    0,    0)
    glVertex3f(bLx,  bLy,  0)
    glVertex3f(bLx + midx, bLy + midy, 0)
    glVertex3f(midx, midy, 0)
    glVertex3f(0,    0,    0)
    glVertex3f(midx, midy, 0)
    glVertex3f(bRx + midx, bRy + midy, 0)
    glVertex3f(bRx,  bRy,  0)
    glEnd()

    glBegin(GL_QUADS)
    glColor3f(1.00, 0.70, 0.00)
    glVertex3f(bLx + midx, bLy + midy, 0)
    glVertex3f(tpx,         tpy,         0)
    glVertex3f(tpx,         tpy,         0)
    glVertex3f(bRx + midx,  bRy + midy,  0)
    glEnd()

    glPopMatrix()

#  GHOST DRAWING

def drawGhost():
    q = gluNewQuadric()
    pulseAmt = 0.15 * math.sin(ghostPhase)
    s = 1.0 + pulseAmt

    glPushMatrix()
    glTranslatef(ghostX, ghostY, GHOST_Z_POS)
    glScalef(s, s, s)

    glPushMatrix()
    glColor3f(0.88, 0.88, 0.92)
    glScalef(1.0, 1.0, 1.6)
    gluSphere(q, GHOST_BODY_R, 24, 24)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.80, 0.80, 0.86)
    glTranslatef(0, 0, -GHOST_BODY_R * 0.5)
    glRotatef(180, 1, 0, 0)
    gluCylinder(q, GHOST_BODY_R * 0.9, GHOST_BODY_R * 0.4,
                GHOST_BODY_R * 1.2, 20, 8)
    glPopMatrix()

    glColor3f(0.72, 0.72, 0.80)
    for angle in [0.0, 120.0, 240.0]:
        glPushMatrix()
        offsetX = GHOST_BODY_R * 0.45 * math.cos(toRadians(angle))
        offsetY = GHOST_BODY_R * 0.45 * math.sin(toRadians(angle))
        glTranslatef(offsetX, offsetY, -GHOST_BODY_R * 1.5)
        glRotatef(180, 1, 0, 0)
        gluCylinder(q, 5.0, 1.0, 22.0, 12, 4)
        glPopMatrix()

    glPushMatrix()
    glColor3f(0.78, 0.78, 0.84)
    glTranslatef(0, 0, GHOST_BODY_R * 1.10)
    gluSphere(q, GHOST_HEAD_R, 20, 20)
    glPopMatrix()

    eyeR = 6.0
    glColor3f(0.02, 0.00, 0.05)
    glPushMatrix()
    glTranslatef(-9.0, GHOST_HEAD_R * 0.55, GHOST_BODY_R * 1.18)
    gluSphere(q, eyeR, 12, 12)
    glPopMatrix()
    glPushMatrix()
    glTranslatef( 9.0, GHOST_HEAD_R * 0.55, GHOST_BODY_R * 1.18)
    gluSphere(q, eyeR, 12, 12)
    glPopMatrix()

    glColor3f(0.02, 0.00, 0.02)
    glPushMatrix()
    glTranslatef(0.0, GHOST_HEAD_R * 0.58, GHOST_BODY_R * 1.02)
    glScalef(1.0, 0.5, 1.0)
    gluSphere(q, 5.5, 10, 10)
    glPopMatrix()

    glPopMatrix()

#  GHOST TOP-DOWN MARKER

def drawGhostTopDownMarker():
    if firstPerson:
        return
    MARKER_Z  = 2.0
    RING_R    = 36.0
    RING_W    = 9.0
    SEGMENTS  = 20

    pulse = 0.5 + 0.5 * math.sin(ghostPhase * 2.0)
    rr    = 0.80 + pulse * 0.20

    glPushMatrix()
    glTranslatef(ghostX, ghostY, MARKER_Z)
    glBegin(GL_QUADS)
    glColor3f(rr, 0.05, 0.05)
    i = 0
    while i < SEGMENTS:
        a0 = toRadians(i       * 360.0 / SEGMENTS)
        a1 = toRadians((i + 1) * 360.0 / SEGMENTS)
        ix0 = math.cos(a0) * (RING_R - RING_W)
        iy0 = math.sin(a0) * (RING_R - RING_W)
        ix1 = math.cos(a1) * (RING_R - RING_W)
        iy1 = math.sin(a1) * (RING_R - RING_W)
        ox0 = math.cos(a0) * RING_R
        oy0 = math.sin(a0) * RING_R
        ox1 = math.cos(a1) * RING_R
        oy1 = math.sin(a1) * RING_R
        glVertex3f(ix0, iy0, 0)
        glVertex3f(ox0, oy0, 0)
        glVertex3f(ox1, oy1, 0)
        glVertex3f(ix1, iy1, 0)
        i += 1
    glEnd()
    glPopMatrix()

#  POWER CELL DRAWING

def drawPowerCell(cx, cy, index):
    if not powerCellAlive[index]:
        return
    q  = gluNewQuadric()
    z  = 38.0
    rot = (elapsedTime * 80.0) % 360.0

    glPushMatrix()
    glTranslatef(cx, cy, z)

    glColor3f(0.20, 0.90, 0.20)
    gluSphere(q, 16.0, 14, 14)

    glPushMatrix()
    glRotatef(rot, 1, 1, 0)
    glColor3f(0.50, 1.00, 0.50)
    glutSolidCube(14.0)
    glPopMatrix()

    glColor3f(0.30, 1.00, 0.30)
    glPushMatrix()
    glTranslatef(0, 0, -z)
    gluCylinder(q, 2.0, 2.0, z, 8, 2)
    glPopMatrix()

    glPopMatrix()

#  SWITCH DRAWING

def drawSwitch(sx, sy, index):
    q = gluNewQuadric()
    z  = 55.0
    activated = switchState[index]

    glPushMatrix()
    glTranslatef(sx, sy, z)
    if index == 1:   
        glRotatef(180, 0, 0, 1)

    glColor3f(0.25, 0.25, 0.25)
    glPushMatrix()
    glScalef(28.0 / 50.0, 10.0 / 50.0, 36.0 / 50.0)
    glutSolidCube(50)
    glPopMatrix()

    if activated:
        glColor3f(0.10, 0.95, 0.10)
    else:
        glColor3f(0.80, 0.08, 0.08)

    glPushMatrix()
    glTranslatef(0, -8.0, 6.0 if activated else -6.0)
    gluSphere(q, 9.0, 12, 12)
    glPopMatrix()

    glPopMatrix()
    
#  KEY DRAWING

def drawKey():
    if hasKey:
        return
    q   = gluNewQuadric()
    kx, ky = KEY_POSITION
    z   = 22.0
    rot = (elapsedTime * 60.0) % 360.0

    glPushMatrix()
    glTranslatef(kx, ky, z)
    glRotatef(rot, 0, 0, 1)

    glColor3f(1.00, 0.80, 0.00)
    glPushMatrix()
    glRotatef(90, 0, 1, 0)
    gluCylinder(q, 4.0, 3.0, 38.0, 12, 4)
    glPopMatrix()

    glPushMatrix()
    glColor3f(1.00, 0.85, 0.10)
    gluSphere(q, 11.0, 14, 14)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.10, 0.05, 0.00)
    glTranslatef(0, 0, 4)
    gluSphere(q, 4.5, 8, 8)
    glPopMatrix()

    glPopMatrix()


#  SAFE DRAWING

def drawSafe():
    q  = gluNewQuadric()
    sx, sy = SAFE_POSITION
    z  = 30.0

    glPushMatrix()
    glTranslatef(sx, sy, z)

    if safeopened:
        glColor3f(0.50, 0.55, 0.50)
    else:
        glColor3f(0.28, 0.28, 0.28)

    glPushMatrix()
    glScalef(50.0 / 50.0, 40.0 / 50.0, 60.0 / 50.0)
    glutSolidCube(50)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, -22.0, 8.0)
    if safeopened:
        glColor3f(0.10, 0.95, 0.10)
    else:
        glColor3f(0.90, 0.08, 0.08)
    gluSphere(q, 7.0, 12, 12)
    glPopMatrix()

    glColor3f(0.65, 0.55, 0.35)
    glPushMatrix()
    glTranslatef(0, -22.0, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(q, 4.0, 4.0, 10.0, 10, 4)
    glPopMatrix()

    glPopMatrix()

#  EXIT DOOR DRAWING

def drawExit():
    q  = gluNewQuadric()
    ex = EXIT_X
    ey = GRID_SIZE
    ez = 0.0

    glPushMatrix()
    glTranslatef(ex, ey, ez)

    glColor3f(0.40, 0.30, 0.20)
    glPushMatrix()
    glScalef(80.0 / 50.0, 10.0 / 50.0, WALL_H / 50.0)
    glutSolidCube(50)
    glPopMatrix()

    if exitUnlocked:
        glColor3f(0.08, 0.85, 0.08)
    else:
        glColor3f(0.60, 0.05, 0.05)

    glPushMatrix()
    glTranslatef(0, -4.0, 0)
    glScalef(70.0 / 50.0, 6.0 / 50.0, (WALL_H - 10.0) / 50.0)
    glutSolidCube(50)
    glPopMatrix()

    if exitUnlocked:
        glColor3f(1.00, 1.00, 0.10)
    else:
        glColor3f(0.30, 0.30, 0.30)

    glPushMatrix()
    glTranslatef(-15.0, -6.0, WALL_H * 0.55)
    glScalef(30.0 / 50.0, 4.0 / 50.0, 12.0 / 50.0)
    glutSolidCube(50)
    glPopMatrix()

    if exitUnlocked:
        glColor3f(0.15, 0.80, 0.15)
        glPushMatrix()
        glTranslatef(0, -20.0, 0)
        glRotatef(180, 1, 0, 0)
        gluCylinder(q, 30.0, 5.0, 80.0, 16, 4)
        glPopMatrix()

    glPopMatrix()

#  UI OVERLAY

def drawHUD():
    ghostDist = dist2D(playerX, playerY, ghostX, ghostY)
    timeLeft  = max(0.0, GAME_TIME_LIMIT - elapsedTime)
    minutes   = int(timeLeft) // 60
    seconds   = int(timeLeft) % 60

    # Timer colour
    if timeLeft < 30.0:
        tr, tg, tb = 1.0, 0.20, 0.20
    elif timeLeft < 60.0:
        tr, tg, tb = 1.0, 0.70, 0.00
    else:
        tr, tg, tb = 0.90, 0.90, 0.90

    # If cheat mode, show frozen time indicator
    if cheatMode:
        timeStr = f"TIME LEFT: {minutes:01d}:{seconds:02d}  [FROZEN]"
        drawText(10, WIN_H - 28, timeStr, 0.30, 0.80, 1.00)
    else:
        drawText(10, WIN_H - 28, f"TIME LEFT: {minutes:01d}:{seconds:02d}", tr, tg, tb)

    # Mode badge
    mLabel = MODE_SETTINGS[currentMode]["label"]
    mR, mG, mB = MODE_SETTINGS[currentMode]["color"]
    drawText(10, WIN_H - 50, f"MODE: {mLabel}", mR, mG, mB)

    # Power cells
    cellStr = f"Power Cells: {powerCellsCollected} / {NUM_POWER_CELLS}"
    cellR   = 0.30 if powerCellsCollected == NUM_POWER_CELLS else 0.90
    cellG   = 0.95 if powerCellsCollected == NUM_POWER_CELLS else 0.90
    cellB   = 0.30 if powerCellsCollected == NUM_POWER_CELLS else 0.10
    drawText(10, WIN_H - 74, cellStr, cellR, cellG, cellB)

    swOn  = sum(1 for s in switchState if s)
    swStr = f"Switches:    {swOn} / {NUM_SWITCHES}"
    swR   = 0.30 if swOn == NUM_SWITCHES else 0.90
    swG   = 0.95 if swOn == NUM_SWITCHES else 0.90
    swB   = 0.30 if swOn == NUM_SWITCHES else 0.10
    drawText(10, WIN_H - 98, swStr, swR, swG, swB)

    keyStr = "Key:         COLLECTED" if hasKey else "Key:         not found"
    keyR   = 1.00 if hasKey else 0.60
    keyG   = 0.85 if hasKey else 0.60
    keyB   = 0.10 if hasKey else 0.60
    drawText(10, WIN_H - 122, keyStr, keyR, keyG, keyB)

    safeStr = "Safe:        OPENED" if safeopened else "Safe:        locked"
    safeR   = 0.30 if safeopened else 0.60
    safeG   = 0.95 if safeopened else 0.60
    safeB   = 0.30 if safeopened else 0.60
    drawText(10, WIN_H - 146, safeStr, safeR, safeG, safeB)

    exitStr = "EXIT:        UNLOCKED - GO!" if exitUnlocked else "EXIT:        locked"
    exitR   = 0.10 if exitUnlocked else 0.60
    exitG   = 1.00 if exitUnlocked else 0.60
    exitB   = 0.10 if exitUnlocked else 0.60
    drawText(10, WIN_H - 170, exitStr, exitR, exitG, exitB)

    # Cheat mode badge (top center)
    if cheatMode:
        drawTextLarge(WIN_W // 2 - 90, WIN_H - 32,
                      "-- CHEAT MODE --", 0.30, 0.80, 1.00)

    # Camera mode indicator
    camModeStr = "[ FIRST PERSON ]" if firstPerson else "[ TOP-DOWN ]"
    camModeR   = 0.80 if firstPerson else 0.30
    camModeG   = 0.50 if firstPerson else 0.85
    camModeB   = 0.20 if firstPerson else 0.85
    drawText(WIN_W - 210, WIN_H - 28, camModeStr, camModeR, camModeG, camModeB)
    drawText(WIN_W - 210, WIN_H - 50, "RMB: Switch Camera", 0.50, 0.50, 0.50)

    # Controls reminder
    drawText(10, 42, "W/S: Move   A/D: Rotate   E: Interact   C: Cheat",
             0.55, 0.55, 0.55)
    drawText(10, 20, "Z: Zoom   Arrows: Camera   R: Restart",
             0.55, 0.55, 0.55)

    # Objective hint
    hint = getObjectiveHint()
    drawText(WIN_W - 520, 20, f"GOAL: {hint}", 0.90, 0.85, 0.30)

    # Ghost warning
    if ghostDist < GHOST_WARN_DIST:
        warnIntensity = 1.0 - (ghostDist / GHOST_WARN_DIST)
        flickerOn = (int(elapsedTime * 8.0) % 2) == 0
        if flickerOn:
            warnText = "!!! GHOST IS NEAR !!!"
            if cheatMode:
                warnText = "!!! GHOST IS NEAR !!! [CHEAT: SAFE]"
            drawTextLarge(WIN_W // 2 - 200, WIN_H // 2,
                          warnText, 1.0, warnIntensity * 0.20, warnIntensity * 0.20)

    # Game over / win overlay
    if isGameOver:
        if playerWon:
            drawTextLarge(WIN_W // 2 - 230, WIN_H // 2 + 60,
                          "YOU ESCAPED!", 0.10, 1.00, 0.10)
        else:
            drawTextLarge(WIN_W // 2 - 230, WIN_H // 2 + 60,
                          "GAME OVER", 1.00, 0.08, 0.08)
        drawText(WIN_W // 2 - 200, WIN_H // 2 + 20,
                 gameMsg, 1.0, 0.85, 0.30)
        drawText(WIN_W // 2 - 170, WIN_H // 2 - 20,
                 'Press  "R"  to RESTART', 0.90, 0.90, 0.90)


def getObjectiveHint():
    if powerCellsCollected < NUM_POWER_CELLS:
        left = NUM_POWER_CELLS - powerCellsCollected
        return f"Collect {left} more Power Cell(s)  [glowing green]"
    swOn = sum(1 for s in switchState if s)
    if swOn < NUM_SWITCHES:
        return "Press E near a Switch to activate it"
    if not hasKey:
        return "Find the KEY  [golden, spinning]"
    if not safeopened:
        return "Press E on the SAFE  [north-east corner]"
    if not exitUnlocked:
        return "Reach the EXIT door  [north wall]"
    return "GO! Sprint to the EXIT — north wall!"


#  CAMERA SETUP

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = WIN_W / float(WIN_H)

    if not firstPerson:
        gluPerspective(FOV_TOPDOWN, aspect, 5.0, 3000.0)
    else:
        gluPerspective(FOV_FIRSTPERSON, aspect, 1.0, 3000.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if not firstPerson:
        lookX = playerX
        lookY = playerY
        lookZ = 50
        dz = camHeight - lookZ
        dy = dz / math.tan(math.radians(50.0))
        rad = math.radians(orbitAngle)
        eyeX = playerX + math.sin(rad) * dy
        eyeY = playerY - math.cos(rad) * dy
        eyeZ = camHeight
        gluLookAt(eyeX, eyeY, eyeZ,
                  lookX, lookY, lookZ,
                  0.0,  0.0,  1.0)
        return

    legLen = 54
    bodyH  = 72
    headR  = 18
    baseZ  = legLen + 2
    eyeZ = baseZ + (bodyH + headR * 0.75) * PLAYER_SCALE
    fdx, fdy = getDirection(gunAngle)
    eyeX = playerX + fdx * 8.0
    eyeY = playerY + fdy * 8.0
    lookDist = 900.0
    gluLookAt(eyeX, eyeY, eyeZ,
              eyeX + fdx * lookDist,
              eyeY + fdy * lookDist,
              eyeZ,
              0.0, 0.0, 1.0)

#  GHOST MOVEMENT UPDATE

def updateGhost(dt):
    global ghostX, ghostY, ghostPhase

    settings = MODE_SETTINGS[currentMode]
    ghostMaxSpeed = settings["ghost_max"]

    speedFactor  = min(1.0, elapsedTime / GHOST_ACCEL_TIME)
    currentSpeed = GHOST_BASE_SPEED + (ghostMaxSpeed - GHOST_BASE_SPEED) * speedFactor

    ghostDist = dist2D(playerX, playerY, ghostX, ghostY)
    if ghostDist < 150.0:
        proximity_boost = (1.0 - ghostDist / 150.0) * 0.10
        currentSpeed += proximity_boost

    frameScale = dt * 60.0
    ghostPhase += 0.12 * frameScale

    toX = playerX - ghostX
    toY = playerY - ghostY
    d   = math.sqrt(toX * toX + toY * toY) + 1e-6

    stepX = (toX / d) * currentSpeed * frameScale
    stepY = (toY / d) * currentSpeed * frameScale

    newGX = ghostX + stepX
    newGY = ghostY + stepY

    lo = -GRID_SIZE + EDGE_PAD
    hi =  GRID_SIZE - EDGE_PAD
    ghostX = clampValue(newGX, lo, hi)
    ghostY = clampValue(newGY, lo, hi)

    # Catch check (skipped in cheat mode)
    if not cheatMode:
        if ghostDist < PLAYER_HIT_R:
            triggerGameOver("The ghost caught you!")

#  INTERACTION SYSTEM

def tryInteract():
    global powerCellsCollected, hasKey, safeopened
    global exitUnlocked, switchState, switchesActivated
    global powerCellAlive

    if isGameOver:
        return

    # Power cells
    for i in range(NUM_POWER_CELLS):
        if not powerCellAlive[i]:
            continue
        cx, cy = POWER_CELL_POSITIONS[i]
        d = dist2D(playerX, playerY, cx, cy)
        if d <= INTERACT_RADIUS:
            powerCellAlive[i] = False
            powerCellsCollected += 1
            print(f"[+] Power cell {i+1} collected! ({powerCellsCollected}/{NUM_POWER_CELLS})")
            return

    # Switches
    for i in range(NUM_SWITCHES):
        if switchState[i]:
            continue
        sx, sy = SWITCH_POSITIONS[i]
        d = dist2D(playerX, playerY, sx, sy)
        if d <= INTERACT_RADIUS:
            if powerCellsCollected < NUM_POWER_CELLS:
                print("[!] Need all power cells before activating switches!")
                return
            switchState[i]        = True
            switchesActivated[i]  = True
            print(f"[+] Switch {i+1} activated!")
            return

    # Key pickup
    if not hasKey:
        kx, ky = KEY_POSITION
        d = dist2D(playerX, playerY, kx, ky)
        if d <= INTERACT_RADIUS:
            swOn = sum(1 for s in switchState if s)
            if swOn < NUM_SWITCHES:
                print("[!] Activate all switches first to reveal the key!")
                return
            hasKey = True
            print("[+] KEY collected! Find the safe.")
            return

    # Safe
    if hasKey and not safeopened:
        sx, sy = SAFE_POSITION
        d = dist2D(playerX, playerY, sx, sy)
        if d <= INTERACT_RADIUS:
            safeopened   = True
            exitUnlocked = True
            print("[+] Safe opened! The EXIT is now UNLOCKED — go north!")
            return

    # Exit
    if exitUnlocked:
        d = dist2D(playerX, playerY, EXIT_X, EXIT_Y - 20)
        if d <= INTERACT_RADIUS + 40:
            triggerWin()
            return

    print("[i] Nothing to interact with nearby.")


#  PLAYER MOVEMENT

def movePlayer(dx, dy):
    global playerX, playerY

    nx = playerX + dx
    ny = playerY + dy

    if not isInsideBounds(nx, ny):
        return

    if isBlockedByWall(nx, ny, radius=22.0):
        if not isBlockedByWall(nx, playerY, radius=22.0) and isInsideBounds(nx, playerY):
            playerX = nx
        elif not isBlockedByWall(playerX, ny, radius=22.0) and isInsideBounds(playerX, ny):
            playerY = ny
        return

    playerX = nx
    playerY = ny


#  WIN CONDITION CHECK

def checkWinCondition():
    if not exitUnlocked:
        return
    if isGameOver:
        return
    d = dist2D(playerX, playerY, EXIT_X, GRID_SIZE - EDGE_PAD)
    if d <= 80.0:
        triggerWin()


#  INPUT HANDLERS

def keyHandler(key, mx, my):
    global gunAngle, firstPerson, lockedFP, zoomedOut, camHeight, orbitDist
    global gameStarted, currentMode, startPhase, cheatMode

    # MODE SELECT SCREEN
    if not gameStarted:
        if startPhase == 0:
            # Choose difficulty
            if key == b'1':
                currentMode = MODE_EASY
                startPhase = 1
                print("[Mode] EASY selected")
            elif key == b'2':
                currentMode = MODE_NORMAL
                startPhase = 1
                print("[Mode] NORMAL selected")
            elif key == b'3':
                currentMode = MODE_HARD
                startPhase = 1
                print("[Mode] HARD selected")
        elif startPhase == 1:
            if key == b'\r' or key == b'\n':
                resetGame()
                gameStarted = True
                print("[Game] Starting!")
            # Allow going back to mode select
            elif key == b'b' or key == b'B':
                startPhase = 0
        return

    # Restart (goes back to mode select)
    if key == b'r' or key == b'R':
        resetGame()
        gameStarted = False
        startPhase  = 0
        return

    if isGameOver:
        return

    # Cheat mode toggle
    if key == b'c' or key == b'C':
        cheatMode = not cheatMode
        state = "ON" if cheatMode else "OFF"
        print(f"[Cheat] Cheat mode {state}")
        return

    # Interact
    if key == b'e' or key == b'E':
        tryInteract()
        return

    # Camera zoom toggle
    if key == b'z' or key == b'Z':
        zoomedOut = not zoomedOut
        if zoomedOut:
            camHeight = CAM_TOPDOWN_ZOOM
            orbitDist = CAM_TOPDOWN_ZOOM
        else:
            camHeight = CAM_TOPDOWN_NORMAL
            orbitDist = CAM_TOPDOWN_NORMAL
        return

    # Movement
    fdx, fdy = getDirection(gunAngle)

    if key == b'w' or key == b'W':
        movePlayer(fdx * MOVE_STEP, fdy * MOVE_STEP)
    elif key == b's' or key == b'S':
        movePlayer(-fdx * MOVE_STEP, -fdy * MOVE_STEP)
    elif key == b'a' or key == b'A':
        gunAngle = (gunAngle + ROTATE_STEP) % 360.0
    elif key == b'd' or key == b'D':
        gunAngle = (gunAngle - ROTATE_STEP) % 360.0


def arrowKeyHandler(key, mx, my):
    global camHeight, orbitAngle

    if firstPerson:
        return

    if key == GLUT_KEY_UP:
        camHeight = clampValue(camHeight - 30.0, 300.0, 1200.0)
    elif key == GLUT_KEY_DOWN:
        camHeight = clampValue(camHeight + 30.0, 300.0, 1200.0)
    elif key == GLUT_KEY_LEFT:
        orbitAngle = (orbitAngle - 5.0) % 360.0
    elif key == GLUT_KEY_RIGHT:
        orbitAngle = (orbitAngle + 5.0) % 360.0


def mouseHandler(btn, state, mx, my):
    global firstPerson

    if state != GLUT_DOWN:
        return
    if not gameStarted:
        return
    if btn == GLUT_RIGHT_BUTTON:
        firstPerson = not firstPerson
        mode = "FIRST PERSON" if firstPerson else "TOP-DOWN"
        print(f"[Camera] Switched to {mode}")

#  IDLE / GAME LOOP UPDATE

def idle():
    global lastTime, elapsedTime, flickerTimer

    nowTime  = time.time()
    dt       = nowTime - lastTime
    lastTime = nowTime

    if dt < 0:
        dt = 0.0
    elif dt > 0.05:
        dt = 0.05

    flickerTimer += dt

    if gameStarted and not isGameOver:
        # Only advance game time if cheat mode is OFF
        if not cheatMode:
            elapsedTime += dt

            if elapsedTime >= GAME_TIME_LIMIT:
                triggerGameOver("Time is up! The ghost claimed you.")

        updateGhost(dt)
        checkWinCondition()

    glutPostRedisplay()


#  FLICKER EFFECT

def getFlickerColor():
    ghostDist = dist2D(playerX, playerY, ghostX, ghostY)
    nearFactor = max(0.0, 1.0 - ghostDist / GHOST_WARN_DIST)
    flickerSpeed = 1.5 + nearFactor * 8.0
    flicker = 0.5 + 0.5 * math.sin(flickerTimer * flickerSpeed * math.pi * 2)
    ambientR = nearFactor * 0.08 * flicker
    return ambientR


#  MODE SELECT SCREEN

def drawModeSelectScreen():
    pulse = 0.5 + 0.5 * math.sin(flickerTimer * 1.0)
    glClearColor(0.05 + pulse * 0.03, 0.00, 0.02, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    cx = WIN_W // 2

    drawTextLarge(cx - 195, WIN_H // 2 + 180,
                  "ESCAPE  HORROR",
                  0.95, 0.10, 0.10)

    drawText(cx - 130, WIN_H // 2 + 145,
             "Select  Difficulty",
             0.80, 0.75, 0.75)

    drawText(cx - 220, WIN_H // 2 + 100,
             "- - - - - - - - - - - - - - - - - - - -",
             0.40, 0.10, 0.10)

    # Easy
    drawTextLarge(cx - 140, WIN_H // 2 + 60,
                  "[1]  EASY",
                  0.20, 0.95, 0.20)
    drawText(cx - 30, WIN_H // 2 + 38,
             "3:00 min  |  2 Power Cells  |  EASY Ghost",
             0.55, 0.85, 0.55)

    # Normal
    drawTextLarge(cx - 160, WIN_H // 2 + 5,
                  "[2]  NORMAL",
                  0.95, 0.85, 0.20)
    drawText(cx - 30, WIN_H // 2 - 18,
             "2:30 min  |  3 Power Cells  |  Normal Ghost",
             0.85, 0.78, 0.55)

    # Hard
    drawTextLarge(cx - 140, WIN_H // 2 - 50,
                  "[3]  HARD",
                  0.95, 0.20, 0.20)
    drawText(cx - 30, WIN_H // 2 - 73,
             "2:00 min  |  4 Power Cells  |  FAST Ghost",
             0.85, 0.55, 0.55)

    drawText(cx - 220, WIN_H // 2 - 110,
             "- - - - - - - - - - - - - - - - - - - -",
             0.40, 0.10, 0.10)

    drawText(cx - 180, WIN_H // 2 - 145,
             "Tip: Press  C  in-game to toggle Cheat Mode",
             0.40, 0.60, 0.80)
    drawText(cx - 165, WIN_H // 2 - 168,
             "(Freezes timer, ghost cannot catch you)",
             0.35, 0.50, 0.65)

    # Credits
    drawText(cx - 200, 30,
             "Naimur Rahman Sifat  |  Rezowan Rashid Ovik  |  Junaid Islam Rafin",
             0.35, 0.30, 0.30)

    glutSwapBuffers()


def drawConfirmScreen():

    pulse = 0.5 + 0.5 * math.sin(flickerTimer * 1.2)
    glClearColor(0.06 + pulse * 0.04, 0.00, 0.00, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    cx = WIN_W // 2
    settings = MODE_SETTINGS[currentMode]
    mR, mG, mB = settings["color"]
    mLabel = settings["label"]

    drawTextLarge(cx - 195, WIN_H // 2 + 130,
                  "ESCAPE  HORROR",
                  0.95, 0.10, 0.10)

    drawTextLarge(cx - 90, WIN_H // 2 + 85,
                  f"Mode:  {mLabel}", mR, mG, mB)

    timeMin = int(settings["time"]) // 60
    timeSec = int(settings["time"]) % 60
    drawText(cx - 150, WIN_H // 2 + 58,
             f"Time: {timeMin}:{timeSec:02d}  |  Power Cells: {settings['cells']}",
             0.75, 0.75, 0.75)

    drawText(cx - 220, WIN_H // 2 + 30,
             "- - - - - - - - - - - - - - - - - - - -",
             0.40, 0.10, 0.10)

    if int(flickerTimer * 2.0) % 2 == 0:
        drawTextLarge(cx - 195, WIN_H // 2 - 10,
                      "Press  ENTER  to  Begin",
                      0.95, 0.90, 0.20)

    drawText(cx - 100, WIN_H // 2 - 50,
             "Press  B  to go back",
             0.50, 0.50, 0.50)

    drawText(cx - 200, WIN_H // 2 - 95,
             "Controls:  W/S Move   A/D Rotate   E Interact",
             0.65, 0.60, 0.60)
    drawText(cx - 200, WIN_H // 2 - 118,
             "RMB: Toggle camera   Z: Zoom   Arrows: Camera orbit",
             0.65, 0.60, 0.60)
    drawText(cx - 200, WIN_H // 2 - 141,
             "C: Cheat Mode   R: Restart / Back to menu",
             0.65, 0.60, 0.60)

    drawText(cx - 200, WIN_H // 2 - 185,
             "Objective: Collect power cells  ->  Flip switches",
             0.70, 0.85, 0.40)
    drawText(cx - 200, WIN_H // 2 - 208,
             "           Find the Key  ->  Open Safe  ->  Escape!",
             0.70, 0.85, 0.40)

    glutSwapBuffers()

#  START SCREEN 

def drawStartScreen():
    if startPhase == 0:
        drawModeSelectScreen()
    else:
        drawConfirmScreen()


#  MAIN DISPLAY FUNCTION

def display():
    glEnable(GL_DEPTH_TEST)

    if not gameStarted:
        drawStartScreen()
        return

    ambientR = getFlickerColor()
    glClearColor(0.13 + ambientR, 0.11, 0.11, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glViewport(0, 0, WIN_W, WIN_H)

    setupCamera()

    drawFloor()
    drawInnerWalls()
    drawBoundaryWalls()

    drawPlayer()
    drawPlayerTopDownMarker()

    drawGhost()
    drawGhostTopDownMarker()

    for i in range(NUM_POWER_CELLS):
        cx, cy = POWER_CELL_POSITIONS[i]
        drawPowerCell(cx, cy, i)

    for i in range(NUM_SWITCHES):
        sx, sy = SWITCH_POSITIONS[i]
        drawSwitch(sx, sy, i)

    drawKey()
    drawSafe()
    drawExit()

    drawHUD()

    glutSwapBuffers()


#  GLUT INITIALISATION AND MAIN ENTRY POINT


def main():
    global lastTime, startPhase
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(200, 80)
    glutCreateWindow(b"ESCAPE HORROR - Survive the Ghost!")

    startPhase = 0
    lastTime   = time.time()

    glutDisplayFunc(display)
    glutKeyboardFunc(keyHandler)
    glutSpecialFunc(arrowKeyHandler)
    glutMouseFunc(mouseHandler)
    glutIdleFunc(idle)

    print("=================================================================")
    print("  ESCAPE HORROR  |  Select difficulty on the start screen")
    print("  W/S   - Move forward / backward")
    print("  A/D   - Rotate left / right")
    print("  E     - Interact with objects")
    print("  C     - Toggle Cheat Mode (freeze timer + ghost can't catch you)")
    print("  Z     - Toggle zoom")
    print("  RMB   - Toggle first/third person")
    print("  Arrows- Orbit camera (3rd person)")
    print("  R     - Restart / back to mode select")
    print("=================================================================")

    glutMainLoop()


if __name__ == "__main__":
    main()