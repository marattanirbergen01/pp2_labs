import pygame
import random

pygame.init()

WIDTH = 800
HEIGHT = 600
FPS = 60
clock = pygame.time.Clock()
points = []
last_pos = (0, 0)
w = 3

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Paint")

#Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
color_mode = BLUE
screen.fill(WHITE)

#Font, Icons and Buttons
welcome_font = pygame.font.SysFont('Arial', 50)
font = pygame.font.SysFont('Arial', 30)
rect_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_3/icons/rec.png")
rect_img = pygame.transform.scale(rect_img, (50, 50))
but1_rect = rect_img.get_rect(center = (50, 50))
circle_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_3/icons/circle.jpeg")
circle_img = pygame.transform.scale(circle_img, (50, 50))
but2_rect = circle_img.get_rect(center = (150, 50))
eraser_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_3/icons/eraser.png")
eraser_img = pygame.transform.scale(eraser_img, (50, 50))
but3_rect = eraser_img.get_rect(center = (350, 50))
red_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_3/icons/red.png")
red_img = pygame.transform.scale(red_img, (50, 50))
but_r_rect = red_img.get_rect(center = (450, 50))
green_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_3/icons/green.png")
green_img = pygame.transform.scale(green_img, (50, 50))
but_g_rect = green_img.get_rect(center = (550, 50))
blue_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_3/icons/blue.png")
blue_img = pygame.transform.scale(blue_img, (50, 50))
but_b_rect = blue_img.get_rect(center = (650, 50))
pencil_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_3/icons/pencil.png")
pencil_img = pygame.transform.scale(pencil_img, (50, 50))
but_line_rect = pencil_img.get_rect(center = (250, 50))
saver_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_3/icons/saver.png")
saver_img = pygame.transform.scale(saver_img, (90, 60))
but_saver_rect = pencil_img.get_rect(center = (730, 50))

#Boolean variables
line = False
circle = False
rectangle = False
eraser = False
draw = False
erasing = False

def drawLine(screen, start, end, width, color_mode):
    
    x1 = start[0]
    y1 = start[1]
    x2 = end[0]
    y2 = end[1]

    dx = abs(x1-x2)
    dy = abs(y1-y2)
    A = y2 - y1
    B = x1 - x2
    C = x2 * y1 - x1 * y2

    if dx > dy:
        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1

        for x in range(x1, x2):
            y = (-C - A * x) / B
            pygame.draw.circle(screen, color_mode, (x, y), width)
    else:   
        if y1 > y2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
        for y in range(y1, y2):
            x = (-C - B * y) / A
            pygame.draw.circle(screen, color_mode, (x, y), width)

def drawCircle(screen, start, end, size, color):
    x1 = start[0]
    y1 = start[1]
    x2 = end[0]
    y2 = end[1]

    width = abs(x1-x2)
    height = abs(y1-y2)

    if x1 <= x2:
        if y1 < y2:
            pygame.draw.ellipse(screen, color, (x1, y1, width, height), size)
        else:
            pygame.draw.ellipse(screen, color, (x1, y2, width, height), size)
    else:
        if y1 < y2:
            pygame.draw.ellipse(screen, color, (x2, y1, width, height), size)
        else:
            pygame.draw.ellipse(screen, color, (x2, y2, width, height), size)

def drawRect(screen, start, end, size, color):
    x1 = start[0]
    y1 = start[1]
    x2 = end[0]
    y2 = end[1]

    width = abs(x1-x2)
    height = abs(y1-y2)

    if x1 <= x2:
        if y1 < y2:
            pygame.draw.rect(screen, color, (x1, y1, width, height), size)
        else:
            pygame.draw.rect(screen, color, (x1, y2, width, height), size)
    else:
        if y1< y2:
            pygame.draw.rect(screen, color, (x2, y1, width, height), size)
        else:
            pygame.draw.rect(screen, color, (x2, y2, width, height), size)

while True:
    clock.tick(FPS)
        
    pygame.draw.rect(screen, (128, 128, 128), but1_rect)
    screen.blit(rect_img, but1_rect.topleft)
    pygame.draw.rect(screen, (128, 128, 128), but2_rect)
    screen.blit(circle_img, but2_rect.topleft)
    pygame.draw.rect(screen, (128, 128, 128), but3_rect)
    screen.blit(eraser_img, but3_rect.topleft)
    pygame.draw.rect(screen, (128, 128, 128), but_r_rect)
    screen.blit(red_img, but_r_rect.topleft)
    pygame.draw.rect(screen, (128, 128, 128), but_g_rect)
    screen.blit(green_img, but_g_rect.topleft)
    pygame.draw.rect(screen, (128, 128, 128), but_b_rect)
    screen.blit(blue_img, but_b_rect.topleft)
    pygame.draw.rect(screen, (128, 128, 128), but_line_rect)
    screen.blit(pencil_img, but_line_rect.topleft)
    pygame.draw.rect(screen, (128, 128, 128), but_saver_rect)
    screen.blit(saver_img, but_saver_rect.topleft)
    pygame.display.flip()

    pressed_keys = pygame.key.get_pressed()
    if pressed_keys[pygame.K_r]:
        color_mode = RED
    elif pressed_keys[pygame.K_g]:
        color_mode = GREEN
    elif pressed_keys[pygame.K_b]:
        color_mode = BLUE
        
    for event in pygame.event.get():
        pos = pygame.mouse.get_pos()
        if event.type == pygame.QUIT:
            exit()
                

        if event.type==pygame.MOUSEBUTTONDOWN and event.button == 1:
            if but1_rect.collidepoint(event.pos):
                line = False
                rectangle = True
                circle = False
                eraser = False
            if but2_rect.collidepoint(event.pos):
                line = False
                rectangle = False
                circle = True
                eraser = False
            if but3_rect.collidepoint(event.pos):
                line = False
                rectangle = False
                circle = False
                eraser = True
            if but_line_rect.collidepoint(event.pos):
                line = True
                rectangle = False
                circle = False
                eraser = False
            if but_b_rect.collidepoint(event.pos):
                color_mode = BLUE
            if but_g_rect.collidepoint(event.pos):
                color_mode = GREEN
            if but_r_rect.collidepoint(event.pos):
                color_mode = RED
            if but_saver_rect.collidepoint(event.pos):
                pygame.image.save(screen, 'paint.png')
 
        if line:
            if event.type == pygame.MOUSEBUTTONDOWN:
                draw = True
                last_pos = pos
                pygame.draw.circle(screen, color_mode, pos, w)
            
            if event.type == pygame.MOUSEBUTTONUP:
                draw = False
            
            if event.type == pygame.MOUSEMOTION:
                if draw:
                    drawLine(screen, last_pos, pos, w, color_mode)
                last_pos = pos

        if rectangle:
            if event.type == pygame.MOUSEBUTTONDOWN:
                last_pos = pos
            if event.type == pygame.MOUSEBUTTONUP:
                drawRect(screen, last_pos, pos, w, color_mode)

        if circle:
            if event.type == pygame.MOUSEBUTTONDOWN:
                last_pos = pos
            if event.type == pygame.MOUSEBUTTONUP:
                drawCircle(screen, last_pos, pos, w, color_mode)

        if eraser:
            if event.type == pygame.MOUSEBUTTONDOWN:
                (x, y) = pos
                erasing = True
                pygame.draw.rect(screen, WHITE, (x, y, 50, 50))
            if event.type == pygame.MOUSEMOTION:
                if erasing:
                    pygame.draw.rect(screen, WHITE, (pos[0], pos[1], 50, 50))
            if event.type == pygame.MOUSEBUTTONUP:
                erasing = False

    pygame.display.update()
    pygame.display.flip()
