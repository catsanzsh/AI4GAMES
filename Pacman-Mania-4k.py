import pygame
import sys
import math
import random
import time  # Import the time module

# --- Constants --- (Same as before, plus audio-related constants)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 480
PACMAN_SIZE = 20
PACMAN_SPEED = 3
PELLET_SIZE = 5
GHOST_SIZE = 20
GHOST_SPEED = 2

MAZE_WALLS = [
    (50, 50, 500, 10),
    (50, 420, 500, 10),
    (50, 50, 10, 370),
    (540, 50, 10, 370),
    (150, 150, 10, 100),
    (250, 250, 100, 10),
    (350, 100, 10, 100),
]

# --- Audio Constants ---
SAMPLE_RATE = 44100  # Standard audio sample rate
BIT_DEPTH = -16     # Signed 16-bit audio

# --- Classes ---

class Pacman:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, PACMAN_SIZE, PACMAN_SIZE)
        self.direction = "right"
        self.mouth_open = True
        self.mouth_timer = 0
        self.mouth_timer_max = 10
        self.last_chomp_time = 0  # Track time since last chomp sound

    def move(self, dx, dy):
        new_x = self.x + dx
        new_y = self.y + dy
        new_rect = pygame.Rect(new_x, new_y, PACMAN_SIZE, PACMAN_SIZE)
        collision = False
        for wall in MAZE_WALLS:
            if new_rect.colliderect(pygame.Rect(wall)):
                collision = True
                break
        if not collision:
            self.x = new_x
            self.y = new_y
            self.rect = new_rect

    def draw(self, screen):
        self.mouth_timer = (self.mouth_timer + 1) % self.mouth_timer_max
        self.mouth_open = self.mouth_timer < self.mouth_timer_max // 2
        pygame.draw.circle(screen, YELLOW, (self.x + PACMAN_SIZE // 2, self.y + PACMAN_SIZE // 2), PACMAN_SIZE // 2)

    def play_chomp_sound(self):
        current_time = time.time()
        if current_time - self.last_chomp_time > 0.1:  # At least 0.1 seconds between chomps
            generate_beep(440, 0.05)  # Short, higher-pitched beep for chomp
            self.last_chomp_time = current_time


class Pellet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, PELLET_SIZE, PELLET_SIZE)
        self.eaten = False

    def draw(self, screen):
        if not self.eaten:
            pygame.draw.circle(screen, WHITE, (self.x + PELLET_SIZE // 2, self.y + PELLET_SIZE // 2), PELLET_SIZE // 2)


class Ghost:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, GHOST_SIZE, GHOST_SIZE)
        self.dx = random.choice([-1, 1]) * GHOST_SPEED
        self.dy = random.choice([-1, 1]) * GHOST_SPEED

    def move(self):
        new_x = self.x + self.dx
        new_y = self.y + self.dy
        new_rect = pygame.Rect(new_x, new_y, GHOST_SIZE, GHOST_SIZE)
        for wall in MAZE_WALLS:
            wall_rect = pygame.Rect(wall)
            if new_rect.colliderect(wall_rect):
                if new_rect.centerx < wall_rect.centerx:
                    self.dx = -abs(self.dx)
                elif new_rect.centerx > wall_rect.centerx:
                    self.dx = abs(self.dx)
                if new_rect.centery < wall_rect.centery:
                    self.dy = -abs(self.dy)
                elif new_rect.centery > wall_rect.centery:
                    self.dy = abs(self.dy)
        self.x = new_x
        self.y = new_y
        self.rect = new_rect

    def draw(self, screen):
        pygame.draw.rect(screen, RED, self.rect)


# --- Sound Generation Functions ---

def generate_beep(frequency, duration):
    """Generates a square wave beep sound and plays it."""
    num_samples = int(duration * SAMPLE_RATE)
    sound_wave = []
    for i in range(num_samples):
        sample_time = i / SAMPLE_RATE
        # Square wave: value is 1 or -1
        value = 1 if (sample_time * frequency) % 1 < 0.5 else -1
        sound_wave.append(value)
    sound_array = pygame.mixer.Sound(buffer=convert_to_signed16(sound_wave))
    sound_array.play()


def convert_to_signed16(data):
    """Converts a list of floats in range [-1, 1] to a signed 16-bit buffer."""
    int_data = [int(sample * 32767) for sample in data]
    return bytearray(b''.join(sample.to_bytes(2, byteorder='little', signed=True) for sample in int_data))


# --- Functions ---

def generate_pellets(maze_walls):
    pellets = []
    spacing = 30
    for x in range(spacing, SCREEN_WIDTH - spacing, spacing):
        for y in range(spacing, SCREEN_HEIGHT - spacing, spacing):
            pellet_rect = pygame.Rect(x, y, PELLET_SIZE, PELLET_SIZE)
            valid_position = True
            for wall in maze_walls:
                if pellet_rect.colliderect(pygame.Rect(wall)):
                    valid_position = False
                    break
            if abs(x - 100) < PACMAN_SIZE + spacing and abs(y - 100) < PACMAN_SIZE + spacing:
                valid_position = False
            if valid_position:
                pellets.append(Pellet(x, y))
    return pellets

def draw_maze(screen, maze_walls):
    for wall in maze_walls:
        pygame.draw.rect(screen, BLUE, wall)


# --- Initialization ---

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pacman Mania 1.0R Beta")
clock = pygame.time.Clock()

# Initialize Pygame's mixer *after* pygame.init()
pygame.mixer.init(frequency=SAMPLE_RATE, size=BIT_DEPTH, channels=1)  # Mono audio

pacman = Pacman(100, 100)
pellets = generate_pellets(MAZE_WALLS)
ghosts = [Ghost(300, 200), Ghost(400, 300)]
score = 0
font = pygame.font.Font(None, 36)
game_over = False

# --- Game Loop ---

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over:
                pacman = Pacman(100, 100)
                pellets = generate_pellets(MAZE_WALLS)
                ghosts = [Ghost(300, 200), Ghost(400, 300)]
                score = 0
                game_over = False

    if not game_over:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            pacman.move(-PACMAN_SPEED, 0)
            pacman.direction = "left"
            pacman.play_chomp_sound()
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            pacman.move(PACMAN_SPEED, 0)
            pacman.direction = "right"
            pacman.play_chomp_sound()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            pacman.move(0, -PACMAN_SPEED)
            pacman.direction = "up"
            pacman.play_chomp_sound()
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            pacman.move(0, PACMAN_SPEED)
            pacman.direction = "down"
            pacman.play_chomp_sound()

        for ghost in ghosts:
            ghost.move()

        for pellet in pellets:
            if pacman.rect.colliderect(pellet.rect) and not pellet.eaten:
                pellet.eaten = True
                score += 10
                generate_beep(880, 0.1)  # Higher-pitched beep for pellet collection

        for ghost in ghosts:
            if pacman.rect.colliderect(ghost.rect):
                generate_beep(220, 0.5)  # Low-pitched beep for game over
                game_over = True

    screen.fill(BLACK)
    draw_maze(screen, MAZE_WALLS)
    for pellet in pellets:
        pellet.draw(screen)
    pacman.draw(screen)
    for ghost in ghosts:
        ghost.draw(screen)

    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    if game_over:
        game_over_text = font.render("Game Over! Press R to restart", True, WHITE)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(game_over_text, text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
