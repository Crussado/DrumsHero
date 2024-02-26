import pygame
from abc import ABC, abstractmethod
import threading

from elements import Button, Token, StandardButton, Particle, LoadingAnimation, RichText, TextInput
from config import GOLDEN, KEYS, ROWS, GREY, BASE, SCORE, UPDATEANIMATION, FINISHLOAD, TOKEN_SIZE, PADDING

class Scene(ABC):
    @abstractmethod
    def __init__(self, game_state) -> None:
        self.game_state = game_state
        self.next = self
        super().__init__()

    @abstractmethod
    def check_event(self, events):
        pass

    @abstractmethod
    def update(self):
        pass
    
    @abstractmethod
    def draw(self, screen):
        pass

    def switch_to(self, next_scene):
        self.next = next_scene

    def terminate(self):
        self.switch_to(None)

class TitleScene(Scene):
    def __init__(self, game_state) -> None:
        super().__init__(game_state)
        sector_screen_sizes = self.game_state.height // 6
        self.padding = PADDING
        call_analizer = lambda: threading.Thread(target=self.game_state.music_analizer).start()
        self.buttons_config = {
            'x': self.game_state.width // 2,
            'y': sector_screen_sizes,
            'width': self.game_state.width // 3,
            'height': sector_screen_sizes - self.padding,
            'color': 'purple', # change to ocre
            'type': {
                'BORING': lambda: (call_analizer(), self.switch_to(LoadingScene(self.game_state))),
                'LIVE': lambda: self.switch_to(LoadingScene(self.game_state)),
                'CONFIG': lambda: self.switch_to(ConfigScene(self.game_state)),
                'EXIT': lambda: self.terminate(),
            },
            'font_size': 30,
        }

        self.buttons = pygame.sprite.Group()
        for i, tipo in enumerate(self.buttons_config['type']):
            button = StandardButton(
                self.buttons_config['x'],
                self.buttons_config['y'] + (i+1) * (self.buttons_config['height'] + self.padding),
                self.buttons_config['width'],
                self.buttons_config['height'],
                (190, 66, 234),
                (134, 92, 150),
                tipo,
                self.game_state.font(self.buttons_config['font_size']),
            )

            self.buttons.add(button)

    def check_event(self, events):
        super().check_event(events)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP:
                self.buttons.update(event)
    
    def update(self):
        super().update()
        for button in self.buttons:
            if button.consume_action():
                self.buttons_config['type'][button.text]()

    def draw(self, screen):
        super().draw(screen)
        screen.fill((155, 235, 200))
        text_renderizado = self.game_state.font(70).render('Drums Hero', True, GOLDEN)
        rect_text = text_renderizado.get_rect(center=(self.game_state.width//2, self.padding*2))
        screen.blit(text_renderizado, rect_text)

        self.buttons.draw(screen)

class GameScene(Scene):
    def __init__(self, game_state) -> None:
        super().__init__(game_state)
        # Groups
        self.all_sprites = pygame.sprite.Group()
        self.buttons = pygame.sprite.Group()
        self.tokens = pygame.sprite.Group()
        self.last_tokens = []
        self.particles = []

        self.fail = pygame.mixer.Sound('./sounds/fail.mp3')

        # self.draw_screen(screen)
        self.create_buttons()

        # Music config
        self.croma = self.game_state.croma.copy()
        self.times = self.game_state.times.copy()
        self.event_times = self.game_state.event_times.copy()

        self.initial_time = pygame.time.get_ticks()
        self.game_state.music_controller.play()

    def draw(self, screen):
        super().draw(screen)
        # Draw screen
        self.draw_screen(screen)
        for p in self.particles:
            p.emit(screen)
        self.particles = list(filter(lambda p: len(p.particles) > 0, self.particles))
        self.tokens.draw(screen)
        self.buttons.draw(screen)

        rich_text = RichText(20)
        rich_text.render(text=f'Score:\n{self.game_state.score}\nX{2**int(self.game_state.combo)}', color=GOLDEN)
        rich_text.get_rect(ROWS[0]//2, BASE//2)
        rich_text.blit(screen)

    def create_buttons(self):
        for note in range(self.game_state.cant_buttons):
            button = Button(note)
            self.all_sprites.add(button)
            self.buttons.add(button)

    def get_button_by_key(self, key):
        for button in self.buttons.sprites():
            if key == KEYS[button.note]:
                return button

    def draw_screen(self, screen):
        screen.fill('purple')
        for row in ROWS:
            pygame.draw.line(screen, GREY, (row, 0), (row, self.game_state.height), 2)
        pygame.draw.line(screen, GREY, (ROWS[0], BASE), (self.game_state.width, BASE), 2)

    def check_event(self, events):
        super().check_event(events)
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in KEYS:
                button = self.get_button_by_key(event.key)
                button.key_down()
                collisions = pygame.sprite.spritecollide(button, self.tokens, False)
                if collisions:
                    self.particles += [Particle(6 + self.game_state.render_combo() * SCORE, button.x, button.y)]
                    self.all_sprites.remove(collisions[0])
                    self.tokens.remove(collisions[0])
                    self.game_state.score += self.game_state.render_combo() * SCORE
                    self.game_state.increase_combo()
                else:
                    self.fail.play()
            elif event.type == pygame.KEYUP and event.key in KEYS:
                button = self.get_button_by_key(event.key)
                button.key_up()

    def synchronize(self, actual_time):
        if ((len(self.event_times) > 0 and(actual_time - self.event_times[0]) > self.game_state.eps_time)) or\
            (len(self.times) > 0 and((actual_time - self.times[0]) > self.game_state.eps_time)):
            # print('discard')
            self.event_times = self.event_times[1:]
            self.times = self.times[1:]
            if len(self.croma[0]) > 0:
                self.croma = list(map(lambda r: r[1:], self.croma))

    def add_token(self, index):
            token = Token(index % self.game_state.cant_buttons)
            self.all_sprites.add(token)
            self.tokens.add(token)
            self.last_tokens.append(token)
            if len(self.last_tokens) > len(ROWS):
                self.last_tokens = self.last_tokens[1:]

    def check_time_rules(self, times, actual_time):
        if len(times) == 0:
            return []
        draw = []
        if abs(actual_time - times[0]) <= self.game_state.eps_time:
            times = times[1:]
            for i, note in enumerate(self.croma):
                if len(note) > 0 and note[0] >= self.game_state.eps_mel:
                    draw.append(i)
        return draw

    def own_rules(self):
        positions = [(row,0) for row in ROWS]
        for token in self.last_tokens:
            for pos in positions:
                if token.collidepoint(pos):
                    return False
        return True

    def update(self):
        super().update()
        # Drop beat
        actual_time = (pygame.time.get_ticks() - self.initial_time) / 1000
        draw = []
        self.synchronize(actual_time)
        draw += self.check_time_rules(self.times, actual_time)
        # draw += self.check_time_rules(self.event_times, actual_time)
        if draw and self.own_rules():
            if len(self.croma[0]) > 0:
                self.croma = list(map(lambda r: r[1:], self.croma))
            for index in draw:
                self.add_token(index)

        self.all_sprites.update()
        
        for token in self.tokens:
            if token.destroy(self.game_state.height):
                self.fail.play()
                self.game_state.reset_combo()
                self.all_sprites.remove(token)
                self.tokens.remove(token)    

class LoadingScene(Scene):
    def __init__(self, game_state) -> None:
        super().__init__(game_state)
        self.animation = LoadingAnimation(game_state)
        pygame.time.set_timer(UPDATEANIMATION, 500)

    def update(self):
        super().update()

    def draw(self, screen):
        super().draw(screen)
        # Draw screen
        screen.fill((0,0,0))
        self.animation.draw(screen)
    
    def check_event(self, events):
        super().check_event(events)
        for event in events:
            if event.type == FINISHLOAD:
                pygame.time.set_timer(UPDATEANIMATION, 0)
                self.switch_to(GameScene(self.game_state))
            if event.type == pygame.MOUSEBUTTONDOWN:
                pygame.time.set_timer(UPDATEANIMATION, 0)
                self.switch_to(GameScene(self.game_state))
            if event.type == UPDATEANIMATION:
                self.animation.update()


class ConfigScene(Scene):
    def __init__(self, game_state) -> None:
        super().__init__(game_state)
        self.padding = self.game_state.width // 7
        button_height = (self.game_state.height - BASE) * 2
        self.buttons_config = {
            'x': 2*self.padding,
            'y': BASE - button_height // 2,
            'width': 2*self.padding,
            'height': button_height,
            'color': 'purple', # change to ocre
            'type': {
                'BACK': lambda: self.switch_to(TitleScene(self.game_state)),
                'SAVE': lambda: (self.game_state.change_file(self.input.get_value()), self.switch_to(TitleScene(self.game_state))),
            },
            'font_size': 30,
        }

        self.input = TextInput(self.game_state.width//2, 300, self.game_state.width//2, 70, self.game_state.font)
        self.buttons = pygame.sprite.Group()
        for i, tipo in enumerate(self.buttons_config['type']):
            button = StandardButton(
                self.buttons_config['x'] + self.padding * i * 3,
                self.buttons_config['y'],
                self.buttons_config['width'],
                self.buttons_config['height'],
                (190, 66, 234),
                (134, 92, 150),
                tipo,
                self.game_state.font(self.buttons_config['font_size']),
            )

            self.buttons.add(button)
        
    def update(self):
        super().update()
        for button in self.buttons:
            if button.consume_action():
                self.buttons_config['type'][button.text]()

    def check_event(self, events):
        super().check_event(events)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP:
                self.buttons.update(event)
                self.input.focus(event)
            if event.type == pygame.KEYDOWN:
                self.input.get_key(event)

    def draw(self, screen):
        super().draw(screen)
        screen.fill((155, 235, 200))
        self.buttons.draw(screen)
        self.input.draw(screen)
        text_renderizado = self.game_state.font(70).render('Config', True, GOLDEN)
        rect_text = text_renderizado.get_rect(center=(self.game_state.width//2, PADDING*2))
        screen.blit(text_renderizado, rect_text)
        text_renderizado = self.game_state.font(35).render('Music File:', True, GOLDEN)
        rect_text = text_renderizado.get_rect(center=(self.input.rect.left, self.input.rect.y - PADDING))
        screen.blit(text_renderizado, rect_text)
