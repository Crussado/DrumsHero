import pygame
import sys
import random

from config import WIDTH, HEIGHT, CANT_BUTTONS, FPS, DIST, FINISHLOAD
from music import Music
from scenes import TitleScene

class GameState():
    def __init__(self):
        # Player state
        self.score = 0
        self.combo = 0

        # Music file
        self.file = './test2.mp3'

        # Generate note config
        self.eps_time = 0.1
        self.eps_mel = 1
        self.cant_buttons = CANT_BUTTONS
        self.width = WIDTH
        self.height = HEIGHT
        self.combo_limit = 5
        self.fps = FPS

        self.screen = pygame.display.set_mode((self.width, self.height))

    def music_analizer(self):
        self.music_controller = Music(self.file)
        self.music_controller.mix_song()
        self.velocity = self.music_controller.get_vel()/100
        time = (DIST/self.velocity)/self.fps
        self.times, self.croma = self.music_controller.get_cromagrama()
        random.Random(1).shuffle(self.croma)
        self.event_times = self.music_controller.get_events()
        self.times -= time
        # TODO
        self.times = list(filter(lambda x: x >= 0, self.times))
        pygame.event.post(pygame.event.Event(FINISHLOAD))

    def font(self, size):
        return pygame.font.Font('Lobster-Regular.ttf', size)

    def reset_combo(self):
        self.combo = 0

    def render_combo(self):
        return 2**int(self.combo)
    
    def increase_combo(self):
        if self.combo < self.combo_limit:
            self.combo += 1/8

    def change_file(self, file):
        self.file = file

class Game():
    def __init__(self, file):
        # Pygame init
        pygame.init()
        pygame.mixer.init()
        self.game_state = GameState()

    def play(self):
        pygame.init()
        pygame.display.set_caption("Drums Hero")
        clock = pygame.time.Clock()

        active_scene = TitleScene(self.game_state)

        while active_scene != None:
            # Event filtering
            filtered_events = []
            for event in pygame.event.get():
                quit_attempt = False
                if event.type == pygame.QUIT:
                    quit_attempt = True
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    quit_attempt = True
                if quit_attempt:
                    active_scene.terminate()
                else:
                    filtered_events.append(event)

            active_scene.check_event(filtered_events)
            active_scene.update()
            active_scene.draw(self.game_state.screen)

            active_scene = active_scene.next

            pygame.display.flip()
            clock.tick(self.game_state.fps)

        pygame.quit()

def main():
    game = Game('./test2.mp3')
    game.play()
    sys.exit()

main()
