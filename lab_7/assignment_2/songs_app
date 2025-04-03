import pygame
pygame.init()

HEIGHT = 300
WIDTH = 300
SIZE = (HEIGHT, WIDTH)

SONG_END = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(SONG_END)
songs = ['/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_7/assigment_2/songs/s_1.mp3',
           '/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_7/assigment_2/songs/s_2.mp3',
           '/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_7/assigment_2/songs/s_3.mp3', 
           '/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_7/assigment_2/songs/s_4.mp3']
next_song = 0
clock = pygame.time.Clock()
pause = False
screen = pygame.display.set_mode(SIZE)
pygame.display.set_caption("Music Player")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                next_song -= 1
                if next_song == -1:
                    next_song = len(songs) - 1
                pygame.mixer.music.load(songs[next_song])
                pygame.mixer.music.play()

            elif event.key == pygame.K_RIGHT:
                next_song += 1
                if next_song == len(songs):
                    next_song = 0
                pygame.mixer.music.load(songs[next_song])
                pygame.mixer.music.play()

            elif event.key == pygame.K_SPACE and pause == False:
                pause = True
                pygame.mixer.music.pause()

            elif event.key == pygame.K_SPACE and pause == True:
                pause = False
                pygame.mixer.music.unpause()


    pygame.display.flip()
    clock.tick(60)
