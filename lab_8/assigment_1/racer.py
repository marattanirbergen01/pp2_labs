import pygame, random
from pygame.locals import *

pygame.init()

#COLORS
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

#SIZE
WIDTH = 400
HEIGHT = 600

#IMAGES
player_img = pygame.image.load('/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_1/player.png')
enemy_img = pygame.image.load('/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_1/enemy.png')
coin_img = pygame.image.load('/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_1/coin.png')
background = pygame.image.load('/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_1/street.png')

#Sounds
accident_sound = pygame.mixer.Sound("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_1/sounds/accident.wav")
coin_sound = pygame.mixer.Sound("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_1/sounds/coin.wav")
music = pygame.mixer.Sound("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_8/assigment_1/sounds/music.ogg")
music.play(-1)

#DISPLAY
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racer Game")
clock = pygame.time.Clock()

#FPS 
FPS = 60

#FONTS
font = pygame.font.SysFont("Verdana", 20)

#CLASS PLAYER
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.image = pygame.transform.scale(self.image, (30, 75))
        self.rect = self.image.get_rect()
        self.rect.center = (220, 550)
        self.dx = 1.5
        self.dy = 1.5

    def update(self):
        pressed_keys = pygame.key.get_pressed()
        if self.rect.left > 20 and pressed_keys[K_LEFT]:
            self.rect.move_ip(-self.dx, 0)
        if self.rect.right < 380 and pressed_keys[K_RIGHT]:
            self.rect.move_ip(self.dx, 0)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

#CLASS ENEMY
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = enemy_img
        self.rect = self.image.get_rect()
        self.rect.center = (random.randint(30, 380), 0)
        self.dx = 1.5
        self.dy = 1.5

    def move(self):
        global SCORE 
        self.rect.move_ip(0, self.dy)
        if self.rect.bottom > 600:
            SCORE += 1
            self.rect.top = 0
            self.rect.center = (random.randint(30, 380), 0)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

#CLASS COIN
class Coin(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = coin_img
        self.rect = self.image.get_rect()
        self.rect.center = (random.randint(30, 380), 0)
        self.dx = 1.5
        self.dy = 1.5

    def move(self):
        self.rect.move_ip(0, self.dy)
        if self.rect.bottom > 600:
            self.rect.top = 0
            self.rect.center = (random.randint(30, 380), 0)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

restart = True

#main loop
while restart:
    #Variables
    SCORE = 0
    COINS = 0
    running = True
    lose = False
    #Creating objects
    P1 = Player()
    E1 = Enemy()
    C1 = Coin()

    #Groupping objects
    enemies = pygame.sprite.Group()
    enemies.add(E1)
    coins = pygame.sprite.Group()
    coins.add(C1)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                restart = not restart
                running = not running
            
        P1.update()
        E1.move()
        C1.move()

        #Collisions
        if pygame.sprite.spritecollideany(P1, enemies):
            lose = True
            accident_sound.play()
            music.stop()
        if pygame.sprite.spritecollideany(P1, coins):
            COINS += 1
            SCORE += 2
            C1.rect.top = 0
            C1.rect.center = (random.randint(30, 380), 0)
            coin_sound.play()

        #When player lose, he/she can see statistics
        while lose:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    restart = False
                    running = not running
                    lose = False
                
                #If u press "r", u can restart
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        running = not running
                        lose = False
                        music.play(-1)

            game_over = font.render("Game Over", True, BLACK)
            restarting = font.render("Press R to restart", True, BLACK)
            total_score = font.render(f"Your score: {SCORE}", True, BLACK)
            coins_text = font.render(f"Your coins: {COINS}", True, BLACK)
            pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 200, HEIGHT // 2 - 200, 400, 400))
            screen.blit(game_over, game_over.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))
            screen.blit(restarting, restarting.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            screen.blit(total_score, total_score.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 75)))
            screen.blit(coins_text, coins_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 25)))
            pygame.display.flip()
        
        #Displaying statistics
        screen.blit(background, (0, 0))
        coins_text = font.render(f"COINS", True, BLACK)
        score = font.render(f"{SCORE}", True, BLACK)
        coins_cnt = font.render(f"{COINS}", False, False)

        screen.blit(font.render(f"SCORE", True, BLACK), (470, 10))
        screen.blit(coins_text, (470, 130))
        screen.blit(score, score.get_rect(center=(505, 50)))
        screen.blit(coins_cnt, coins_cnt.get_rect(center=(505, 170)))

        #drawing objects
        P1.draw(screen)
        E1.draw(screen)
        C1.draw(screen)

        pygame.display.update()
    pygame.display.update()
    clock.tick(FPS)
pygame.quit()  
