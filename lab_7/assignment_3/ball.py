import pygame
pygame.init()

RED_COLOR = (255, 0, 0)
HEIGHT = 600
WIDTH = 600
BLACK_COLOR = (0, 0, 0)
WHITE_COLOR = (255, 255, 255)
BLUE_COLOR = (0, 0, 255)
GREEN_COLOR = (0, 255, 0)
FPS = 60
SPEED = 5
RADIUS = 25
y = HEIGHT//2
x = WIDTH//2
SIZE = (WIDTH, HEIGHT)

screen = pygame.display.set_mode(SIZE)
pygame.display.set_caption("Moving Ball")
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()

    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT] and x-RADIUS-SPEED>=0:
        x -= SPEED
    if keys[pygame.K_RIGHT] and x+RADIUS-SPEED<=WIDTH:
        x += SPEED
    if keys[pygame.K_UP] and y-RADIUS-SPEED>=0:
        y -= SPEED
    if keys[pygame.K_DOWN] and y+RADIUS+SPEED<=WIDTH:
        y += SPEED
    
    screen.fill(WHITE_COLOR)
    circle = pygame.draw.circle(screen, RED_COLOR, (x, y), RADIUS)
    pygame.display.update()
    clock.tick(FPS)
