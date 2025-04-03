import pygame 
import random
pygame.init()

W, H = 1200, 800
FPS = 60

screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
clock = pygame.time.Clock()
done = False
bg = (0, 0, 0)

#paddle
paddleW = 150
paddleH = 25
paddleSpeed = 20
paddle = pygame.Rect(W // 2 - paddleW // 2, H - paddleH - 30, paddleW, paddleH)


#Ball
ballRadius = 20
ballSpeed = 6
ball_rect = int(ballRadius * 2 ** 0.5)
ball = pygame.Rect(random.randrange(ball_rect, W - ball_rect), H // 2, ball_rect, ball_rect)
dx, dy = 1, -1

#Game score
game_score = 0
game_score_fonts = pygame.font.SysFont('comicsansms', 40)
game_score_text = game_score_fonts.render(f'Your game score is: {game_score}', True, (0, 0, 0))
game_score_rect = game_score_text.get_rect()
game_score_rect.center = (210, 20)

#Catching sound
collision_sound = pygame.mixer.Sound('/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/2_task/catch.mp3')

#Function that detect collision
def detect_collision(dx, dy, ball, rect):
    if dx > 0:
        delta_x = ball.right - rect.left
    else:
        delta_x = rect.right - ball.left
    if dy > 0:
        delta_y = ball.bottom - rect.top
    else:
        delta_y = rect.bottom - ball.top

    if abs(delta_x - delta_y) < 10:
        dx, dy = -dx, -dy
    if delta_x > delta_y:
        dy = -dy
    elif delta_y > delta_x:
        dx = -dx
    return dx, dy

block_list = []
color_list = []
rows = 4
columns = 10
shrink_rate = 3
initial_paddle = paddleW
last_time = pygame.time.get_ticks()

#block settings
for i in range(rows):
    for j in range(columns):
        if j%4 == 3:
            block = pygame.Rect(10 + 120*j, 50 + 70 * i, 100, 50)
            color = (128, 128, 128)
        else:
            block = pygame.Rect(10 + 120 * j, 50 + 70 * i, 100, 50)
            color = (random.randrange(0, 255), random.randrange(0, 255), random.randrange(0, 255))
            if ((j > random.randrange(0, 11) and j < random.randrange(0, 11)) and i > random.randrange(0, 4)) or ((j > random.randrange(0, 4) and j < random.randrange(0, 11)) and i > random.randrange(0, 7)):
                color = (255, 255, 0)
        block_list.append(block)
        color_list.append(color)


#Game over Screen
losefont = pygame.font.SysFont('comicsansms', 40)
losetext = losefont.render('Game Over', True, (255, 255, 255))
losetextRect = losetext.get_rect()
losetextRect.center = (W // 2, H // 2 - 100)

#restart screen
restarttext = losefont.render('Press R to restart a game', True, (255, 255, 255))
restartRect = restarttext.get_rect()
restartRect.center = (W // 2, H // 2)

#Win Screen
winfont = pygame.font.SysFont('comicsansms', 40)
wintext = losefont.render('You win yay', True, (255, 255, 255))
wintextRect = wintext.get_rect()
wintextRect.center = (W // 2, H // 2 - 100)

#Pause Screen
pausefont = pygame.font.SysFont('comiscansms', 40)
pausetext = pausefont.render("Settings", True, (0, 0, 0))
pauseRect = pausetext.get_rect()
pauseRect.center = (W//2, H//2)
#for pause screen
restarttext2 = losefont.render('Press R to restart a game', True, bg)
restartRect2 = restarttext2.get_rect()
restartRect2.center = (W // 2, H // 2 - 200)

#Boolean variable for pause screen
paused = False

#Buttons
font = pygame.font.SysFont('Arial', 30)
plus_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/2_task/icons/plus.png")
plus_img = pygame.transform.scale(plus_img, (40, 40))
but1_rect = plus_img.get_rect(center = (700, 400))
but3_rect = plus_img.get_rect(center = (700, 600))
minus_img = pygame.image.load("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_9/2_task/icons/minus.png")
minus_img = pygame.transform.scale(minus_img, (40, 40))
but2_rect = minus_img.get_rect(center = (500, 400))
but4_rect = minus_img.get_rect(center = (500, 600))

#Boolean variables for buttons
pressed1 = False
pressed2 = False
pressed3 = False
pressed4 = False

#Function that draw buttons
def drawing_buttons():
    pygame.draw.rect(screen, (0, 0, 0), but1_rect)
    screen.blit(plus_img, but1_rect.topleft)
    pygame.draw.rect(screen, (0, 0, 0), but3_rect)
    screen.blit(plus_img, but3_rect.topleft)
    pygame.draw.rect(screen, (0, 0, 0), but2_rect)
    screen.blit(minus_img, but2_rect.topleft)
    pygame.draw.rect(screen, (0, 0, 0), but4_rect)
    screen.blit(minus_img, but4_rect.topleft)

#Function that restart a game
def restart_game():
    global game_score, paddleW, block_list, color_list, ballSpeed, paddle, lose, win
    game_score = 0
    paddleW = 150  # Set paddle width back to initial value
    lose = False
    win = False
    # Reinitialize block positions and colors
    block_list = []
    color_list = []
    for i in range(rows):
        for j in range(columns):
            if j % 4 == 3:
                block = pygame.Rect(10 + 120 * j, 50 + 70 * i, 100, 50)
                color = (128, 128, 128)
            else:
                block = pygame.Rect(10 + 120 * j, 50 + 70 * i, 100, 50)
                color = (random.randrange(0, 255), random.randrange(0, 255), random.randrange(0, 255))
                if ((j > random.randrange(0, 11) and j < random.randrange(0, 11)) and i > random.randrange(0, 4)) or ((j > random.randrange(0, 4) and j < random.randrange(0, 11)) and i > random.randrange(0, 7)):
                    color = (255, 255, 0)
            block_list.append(block)
            color_list.append(color)
    # Reset ball speed
    ballSpeed = 6
    # Reset paddle position
    paddle = pygame.Rect(W // 2 - paddleW // 2, H - paddleH - 30, paddleW, paddleH)
    #Reset ball position
    ball = pygame.Rect(random.randrange(ball_rect, W - ball_rect), H // 2, ball_rect, ball_rect)
    # Reset ball movement direction
    global dx, dy
    dx, dy = 1, -1

#main loop
while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                paused = True
            if event.key == pygame.K_r:
                restart_game()

    while paused:
        for event in pygame.event.get():
            pos = pygame.mouse.get_pos()
            if event.type == pygame.QUIT:
                exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = False

                if event.key == pygame.K_r:
                    restart_game()
                    paused = False

            #Check if buttons are pressed
            if event.type==pygame.MOUSEBUTTONDOWN:
                if but1_rect.collidepoint(event.pos):
                    pressed1 = True
                if but2_rect.collidepoint(event.pos):
                    pressed2 = True
                if but3_rect.collidepoint(event.pos):
                    pressed3 = True
                if but4_rect.collidepoint(event.pos):
                    pressed4 = True

            if event.type == pygame.MOUSEBUTTONUP:
                if pressed1 == True:
                    pressed1 = False
                if pressed2 == True:
                    pressed2 = False
                if pressed3 == True:
                    pressed3 = False
                if pressed4 == True:
                    pressed4 = False

            if pressed1:
                ballSpeed += 1

            if pressed2:
                if ballSpeed>1:
                    ballSpeed -= 1

            if pressed3:
                ballRadius += 1

            if pressed4:
                if ballRadius > 1:
                    ballRadius -= 1

        screen.fill((255, 255, 255))
        font = pygame.font.SysFont('Arial', 30)
        speed_text = font.render(f"Speed: {int(ballSpeed)}", True, (bg))
        radius_text = font.render(f"Radius: {int(ballRadius)}", True, (bg))
        screen.blit(pausetext, (W // 2 - pausetext.get_width() // 2, 100))
        screen.blit(speed_text, (W//2 - speed_text.get_width() // 2, 300))
        screen.blit(radius_text, (W // 2 - radius_text.get_width() // 2, 500))
        screen.blit(restarttext2, restartRect2)
        drawing_buttons()
        pygame.display.update()

    screen.fill(bg)

    #Convert milliseconds to seconds by dividing by 1000
    current_time = pygame.time.get_ticks()
    elapsed_time = (current_time - last_time) / 1000
    last_time = current_time

    # Increase ball speed over time
    ballSpeed += elapsed_time * 0.1
    
    # Shrink paddle over time
    paddleW -= elapsed_time * shrink_rate
    paddleW = max(paddleW, ballRadius * 4) 
    
    #Drawing blocks
    for color, block in enumerate(block_list):
        pygame.draw.rect(screen, color_list[color], block)
        if color_list[color] == (255, 255, 0):
            pygame.draw.circle(screen, (0, 0, 0), block.center, 20)

    #drawing the paddle
    pygame.draw.rect(screen, pygame.Color(255, 255, 255), paddle)
    #drawing the ball
    pygame.draw.circle(screen, pygame.Color(255, 0, 0), ball.center, ballRadius)

    #Ball movement
    ball.x += ballSpeed * dx
    ball.y += ballSpeed * dy

    #Collision left 
    if ball.centerx < ballRadius or ball.centerx > W - ballRadius:
        dx = -dx
    #Collision top
    if ball.centery < ballRadius + 50: 
        dy = -dy
    #Collision with paddle
    if ball.colliderect(paddle) and dy > 0:
        dx, dy = detect_collision(dx, dy, ball, paddle)

    #Collision blocks
    hitIndex = ball.collidelist(block_list)

    if hitIndex != -1:
        hit_block = block_list[hitIndex]
        hit_color = color_list[hitIndex]
        if hit_color != (128, 128, 128):
            hit_block = block_list.pop(hitIndex)
            hit_color = color_list.pop(hitIndex)
            dx, dy = detect_collision(dx, dy, ball, hit_block)
            game_score += 1
            collision_sound.play()
            if hit_color == (255, 255, 0):
                paddleW += 40
                paddle.width = int(paddleW)
        else:
            dx, dy = detect_collision(dx, dy, ball, hit_block)
        
    #Game score
    game_score_text = game_score_fonts.render(f'Your game score is: {game_score}', True, (255, 255, 255))
    screen.blit(game_score_text, game_score_rect)
    
    #Win/lose screens
    if ball.bottom > H:
        for event in pygame.event.get():
            if event.key == pygame.K_r:
                restart_game()
        screen.fill((0, 0, 0))
        screen.blit(losetext, losetextRect)
        screen.blit(restarttext, restartRect)
        pygame.display.update()

    if not len(block_list):
        for event in pygame.event.get():
            if event.key == pygame.K_r:
                restart_game()
        screen.fill((0, 0, 0))
        screen.blit(wintext, wintextRect)
        screen.blit(restarttext, restartRect)
        pygame.display.update()

    #Paddle Control
    key = pygame.key.get_pressed()
    if key[pygame.K_LEFT] and paddle.left > 0:
        paddle.left -= paddleSpeed
    if key[pygame.K_RIGHT] and paddle.right < W:
        paddle.right += paddleSpeed

    pygame.display.flip()
    clock.tick(FPS)
