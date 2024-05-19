import numpy as np
import random
import math
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import time

# Constants
DISPLAY_WIDTH = 1000
DISPLAY_HEIGHT = 720
GRAVITY = np.array([0, -1], dtype=np.float64)  # Increased gravity for faster descent
TRAIL_COLORS = [(45 / 255, 45 / 255, 45 / 255), (60 / 255, 60 / 255, 60 / 255), (75 / 255, 75 / 255, 75 / 255),
                (125 / 255, 125 / 255, 125 / 255), (150 / 255, 150 / 255, 150 / 255)]
DYNAMIC_OFFSET = 2
STATIC_OFFSET = 5

TEXT_COLOR = (0, 0, 0)
TEXT_SIZE = 45
TEXT_POSITION = (100 , DISPLAY_HEIGHT -100)

class Firework:
    def __init__(self):
        self.color = [random.random(), random.random(), random.random()]
        self.colors = [
            [random.random(), random.random(), random.random()],
            [random.random(), random.random(), random.random()],
            [random.random(), random.random(), random.random()]
        ]
        self.firework = Particle(random.randint(0, DISPLAY_WIDTH), 0, True, self.color)
        self.exploded = False
        self.particles = []
        self.min_max_particles = [200, 600]

    def update(self):
        if not self.exploded:
            self.firework.apply_force(GRAVITY)
            self.firework.move()
            self.show(self.firework)

            if self.firework.vel[1] <= 0:  # Firework should go up and slow down before exploding
                self.exploded = True
                self.explode()
        else:
            for particle in self.particles:
                particle.apply_force(
                    GRAVITY + np.array([random.uniform(-0.05, 0.05), random.uniform(-0.04, 0.08)], dtype=np.float64))
                particle.move()
                self.show(particle)

            # Remove particles that have decayed
            self.particles = [p for p in self.particles if not p.remove]

    def explode(self):
        amount = random.randint(self.min_max_particles[0], self.min_max_particles[1])
        for _ in range(amount):
            self.particles.append(Particle(self.firework.pos[0], self.firework.pos[1], False, self.colors))

    def show(self, particle):
        glColor3f(*particle.color)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(particle.pos[0], particle.pos[1])
        for angle in range(0, 361, 10):
            glVertex2f(
                particle.pos[0] + math.sin(math.radians(angle)) * particle.size,
                particle.pos[1] + math.cos(math.radians(angle)) * particle.size
            )
        glEnd()

class Particle:
    def __init__(self, x, y, firework, color):
        self.firework = firework
        self.pos = np.array([x, y], dtype=np.float64)
        self.origin = np.array([x, y], dtype=np.float64)
        self.remove = False
        self.explosion_radius = random.randint(5, 40)
        self.life = 0
        self.acc = np.array([0, 0], dtype=np.float64)
        self.trails = []
        self.prev_posx = [-10] * 10
        self.prev_posy = [-10] * 10

        if self.firework:
            self.vel = np.array([0, random.uniform(30, 35)], dtype=np.float64)  # Increased speed
            self.size = 5
            self.color = color
            for i in range(5):
                self.trails.append(Trail(i, self.size, True))
        else:
            self.vel = np.array([random.uniform(-2, 2), random.uniform(-2, 2)], dtype=np.float64)  # Increased speed
            self.vel *= random.randint(10, self.explosion_radius + 5)  # Increased speed
            self.size = random.randint(2, 4)
            self.color = random.choice(color)
            for i in range(5):
                self.trails.append(Trail(i, self.size, False))

    def apply_force(self, force):
        self.acc += force

    def move(self):
        if not self.firework:
            self.vel *= 0.85  # Reduced drag to keep speed higher

        # Update velocity and position
        self.vel += self.acc
        self.pos += self.vel
        self.acc *= 0

        # Boundary checks
        if self.pos[0] < 0 or self.pos[0] > DISPLAY_WIDTH or self.pos[1] < 0 or self.pos[1] > DISPLAY_HEIGHT:
            self.remove = True

        # Distance check for explosion particles
        if self.life == 0 and not self.firework:
            distance = np.linalg.norm(self.pos - self.origin)
            if distance > self.explosion_radius:
                self.remove = True

        self.decay()
        self.trail_update()
        self.life += 1

    def decay(self):
        if 30 > self.life > 5:  # Faster decay for particles
            if random.randint(0, 15) == 0:  # Increased chance of removal
                self.remove = True
        elif self.life > 30:
            if random.randint(0, 2) == 0:  # Further increased chance of removal
                self.remove = True

    def trail_update(self):
        self.prev_posx.pop()
        self.prev_posx.insert(0, int(self.pos[0]))
        self.prev_posy.pop()
        self.prev_posy.insert(0, int(self.pos[1]))

        for n, t in enumerate(self.trails):
            if t.dynamic:
                t.get_pos(self.prev_posx[n + DYNAMIC_OFFSET], self.prev_posy[n + DYNAMIC_OFFSET])
            else:
                t.get_pos(self.prev_posx[n + STATIC_OFFSET], self.prev_posy[n + STATIC_OFFSET])

class Trail:
    def __init__(self, n, size, dynamic):
        self.pos_in_line = n
        self.pos = np.array([-10, -10], dtype=np.float64)
        self.dynamic = dynamic

        if self.dynamic:
            self.color = TRAIL_COLORS[n]
            self.size = int(size - n / 2)
        else:
            self.color = [255 / 255.0, 255 / 255.0, 200 / 255.0]
            self.size = size - 2
            if self.size < 0:
                self.size = 0

    def get_pos(self, x, y):
        self.pos = np.array([x, y], dtype=np.float64)

    def show(self):
        glColor3f(*self.color)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(self.pos[0], self.pos[1])
        for angle in range(0, 361, 10):
            glVertex2f(
                self.pos[0] + math.sin(math.radians(angle)) * self.size,
                self.pos[1] + math.cos(math.radians(angle)) * self.size
            )
        glEnd()

# Function to draw text with size
def draw_text(text, position, size, color):
    glColor3f(*color)
    glPushMatrix()
    glTranslatef(position[0], position[1], 0.0)
    glScalef(size / 100.0, size / 100.0, 1.0)
    for character in text:
        glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(character))
    glPopMatrix()

# Function to update the position of the text
def update_text_position(time_elapsed):
    frequency = 0.5  # Adjust frequency to change speed of animation
    amplitude = 50   # Adjust amplitude to change height of animation
    vertical_offset = amplitude * math.sin(2 * math.pi * frequency * time_elapsed)
    return (TEXT_POSITION[0], TEXT_POSITION[1] + vertical_offset)

def update():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    current_time = time.time()
    text_position = update_text_position(current_time)

    draw_text("Happy 21st Birthday Sweaty :)" , text_position, TEXT_SIZE, TEXT_COLOR)

    global fireworks
    for fw in fireworks:
        fw.update()
        if fw.exploded and all(p.remove for p in fw.particles):
            fireworks.remove(fw)
    while len(fireworks) < 6 :  # Ensure continuous generation of new fireworks
        fireworks.append(Firework())
    glutSwapBuffers()

def timer(value):
    update()
    glutPostRedisplay()
    glutTimerFunc(10, timer, 0)  # Reduced interval for faster updates

def main():
    global fireworks
    fireworks = [Firework() for _ in range(4)]

    glutInit()
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(DISPLAY_WIDTH, DISPLAY_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Fireworks")
    glClearColor(1.0, 0.75, 0.8, 1.0)
    gluOrtho2D(0, DISPLAY_WIDTH, 0, DISPLAY_HEIGHT)

    glutDisplayFunc(update)
    glutTimerFunc(0, timer, 0)
    glutMainLoop()

if __name__ == "__main__":
    main()
