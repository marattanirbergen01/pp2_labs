import pygame
import random
from math import cos, sin, pi

pygame.init()

#Size and other variable
WIDTH = 800
HEIGHT = 600
FPS = 60
clock = pygame.time.Clock()
points = []
last_pos = (0, 0)
w = 3

#Setting up Display
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
rect_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/3_task/icons/rec.png")
rect_img = pygame.transform.scale(rect_img, (30, 30))
but1_rect = rect_img.get_rect(center = (40, 30))
circle_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/3_task/icons/circle.jpeg")
circle_img = pygame.transform.scale(circle_img, (30, 30))
but2_rect = circle_img.get_rect(center = (100, 30))
pencil_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/3_task/icons/pencil.png")
pencil_img = pygame.transform.scale(pencil_img, (30, 30))
but_line_rect = pencil_img.get_rect(center = (160, 30))
eraser_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/3_task/icons/eraser.png")
eraser_img = pygame.transform.scale(eraser_img, (30, 30))
but3_rect = eraser_img.get_rect(center = (220, 30))
square_img = pygame.image.load('/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/3_task/icons/square.png')
square_img = pygame.transform.scale(square_img, (30, 30))
but4_rect = square_img.get_rect(center = (280, 30))
rtriangle_img = pygame.image.load('/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/3_task/icons/righttriangle.png')
rtriangle_img = pygame.transform.scale(rtriangle_img, (30, 30))
but5_rect = rtriangle_img.get_rect(center = (340, 30))
etriangle_img = pygame.image.load('/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/3_task/icons/eqtriangle.png')
etriangle_img = pygame.transform.scale(etriangle_img, (30, 30))
but6_rect = etriangle_img.get_rect(center = (400, 30))
rhombus_img = pygame.image.load('/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/3_task/icons/rhombus.png')
rhombus_img = pygame.transform.scale(rhombus_img, (30, 30))
but7_rect = rhombus_img.get_rect(center = (460, 30))
red_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/3_task/icons/red.png")
red_img = pygame.transform.scale(red_img, (30, 30))
but_r_rect = red_img.get_rect(center = (520, 30))
green_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/3_task/icons/green.png")
green_img = pygame.transform.scale(green_img, (30, 30))
but_g_rect = green_img.get_rect(center = (580, 30))
blue_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/3_task/icons/blue.png")
blue_img = pygame.transform.scale(blue_img, (30, 30))
but_b_rect = blue_img.get_rect(center = (640, 30))
saver_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/3_task/icons/saver.png")
saver_img = pygame.transform.scale(saver_img, (60, 45))
but_saver_rect = pencil_img.get_rect(center = (700, 30))

#Boolean variables
line = False
circle = False
rectangle = False
eraser = False
draw = False
erasing = False
square = False
rtriagnle = False
etriangle = False
rhombus = False

#Function for drawing line
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

#Function for drawing circle
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

#Function for drawing rectangle
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

#Function for drawing square
def drawSquare(screen, start, end, size, color):
    x1 = start[0]
    y1 = start[1]
    x2 = end[0]
    y2 = end[1]

    a = abs(x1-x2)
    if x1 <= x2:
        if y1 < y2:
            pygame.draw.rect(screen, color, (x1, y1, a, a), size)
        else:
            pygame.draw.rect(screen, color, (x1, y2, a, a), size)
    else:
        if y1 < y2:
            pygame.draw.rect(screen, color, (x2, y1, a, a), size)
        else:
            pygame.draw.rect(screen, color, (x2, y2, a, a), size)

#Function for drawing right triangle
def drawrtriangle(screen, start, end, size, color):
    x1, y1, x2, y2 = start[0], start[1], end[0], end[1] 
    difx = abs(x1-x2) 
    dify = abs(y1-y2) 
    if x1 <= x2: 
        if y1 < y2: 
            pygame.draw.polygon(screen, color, [(x1, y1), (x1, y1 + dify), (x2, y2)], size)    
        else: 
            pygame.draw.polygon(screen, color, [(x1, y1), (x1, y1 - dify), (x2, y2)], size)    
             
    else: 
        if y1 < y2: 
            pygame.draw.polygon(screen, color, [(x1, y1), (x1, y1 + dify), (x2, y2)], size)    
        else: 
            pygame.draw.polygon(screen, color, [(x1, y1), (x1, y1 - dify), (x2, y2)], size)    

#Function for drawing equilateral triangle
def drawetriangle(pos, color):
    pygame.draw.polygon(screen, color, pos, 3)

#Function for drawing rhombus
def drawrhombus(pos, color):
    pygame.draw.polygon(screen, color, pos, 3)

#Main loop
while True:
    clock.tick(FPS)
        
    pygame.draw.rect(screen, (158, 158, 158), but1_rect)
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
    pygame.draw.rect(screen, (128, 128, 128), but4_rect)
    screen.blit(square_img, but4_rect.topleft)
    pygame.draw.rect(screen, (128, 128, 128), but5_rect)
    screen.blit(rtriangle_img, but5_rect.topleft)
    pygame.draw.rect(screen, (128, 128, 128), but6_rect)
    screen.blit(etriangle_img, but6_rect.topleft)
    pygame.draw.rect(screen, (128, 128, 128), but7_rect)
    screen.blit(rhombus_img, but7_rect.topleft)
    pygame.display.flip()

    #Changing color by pressing letters(r, g, b)
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
                
        #Pressing Button
        if event.type==pygame.MOUSEBUTTONDOWN and event.button == 1:
            if but1_rect.collidepoint(event.pos):
                line = False
                rectangle = True
                circle = False
                eraser = False
                square = False
                rhombus = False
                etriangle = False
                rtriagnle = False
            if but2_rect.collidepoint(event.pos):
                line = False
                rectangle = False
                circle = True
                eraser = False
                square = False
                rhombus = False
                etriangle = False
                rtriagnle = False
            if but3_rect.collidepoint(event.pos):
                line = False
                rectangle = False
                circle = False
                eraser = True
                square = False
                rhombus = False
                etriangle = False
                rtriagnle = False
            if but_line_rect.collidepoint(event.pos):
                line = True
                rectangle = False
                circle = False
                eraser = False
                square = False
                rhombus = False
                etriangle = False
                rtriagnle = False
            if but_b_rect.collidepoint(event.pos):
                color_mode = BLUE
            if but_g_rect.collidepoint(event.pos):
                color_mode = GREEN
            if but_r_rect.collidepoint(event.pos):
                color_mode = RED
            if but_saver_rect.collidepoint(event.pos):
                pygame.image.save(screen, 'paint.png')
            if but4_rect.collidepoint(event.pos):
                line = False
                rectangle = False
                circle = False
                eraser = False
                square = True
                rhombus = False
                etriangle = False
                rtriagnle = False
            if but5_rect.collidepoint(event.pos):
                line = False
                rectangle = False
                circle = False
                eraser = False
                square = False
                rhombus = False
                etriangle = False
                rtriagnle = True
            if but6_rect.collidepoint(event.pos):
                line = False
                rectangle = False
                circle = False
                eraser = False
                square = False
                rhombus = False
                etriangle = True
                rtriagnle = False
            if but7_rect.collidepoint(event.pos):
                line = False
                rectangle = False
                circle = False
                eraser = False
                square = False
                rhombus = True
                etriangle = False
                rtriagnle = False

        #Checking boolean values and drawing shapes
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

        if square:
            if event.type == pygame.MOUSEBUTTONDOWN:
                last_pos = pos
            if event.type == pygame.MOUSEBUTTONUP:
                drawSquare(screen, last_pos, pos, w, color_mode)

        if rtriagnle:
            if event.type == pygame.MOUSEBUTTONDOWN:
                last_pos = pos
            if event.type == pygame.MOUSEBUTTONUP:
                drawrtriangle(screen, last_pos, pos, w, color_mode)

        if etriangle:
            if event.type == pygame.MOUSEBUTTONDOWN:
                last_pos = pos
            if event.type == pygame.MOUSEBUTTONUP:
                drawetriangle([last_pos, pos,((pos[0] - last_pos[0])*cos(pi/3) - (pos[1] - last_pos[1])*sin(pi/3) + last_pos[0], (pos[0] - last_pos[0])*sin(pi/3) + (pos[1] - last_pos[1])*cos(pi/3) + last_pos[1])], color_mode)

        if rhombus:
            if event.type == pygame.MOUSEBUTTONDOWN:
                last_pos = pos
            if event.type == pygame.MOUSEBUTTONUP:
                d = (((last_pos[0] - pos[0]) ** 2 + (last_pos[1] - pos[1]) ** 2) ** 0.5)
                drawrhombus([last_pos, (last_pos[0] + d, last_pos[1]), (pos[0] + d, pos[1]), pos], color_mode)

    pygame.display.update()
    pygame.display.flip()
