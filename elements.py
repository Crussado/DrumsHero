import pygame
import random
from config import OFF_COLORS, TOKEN_SIZE, BORDER_COLOR, ROWS, BASE, ON_COLORS, YELLOW_ON,\
    GOLDEN, WHITE, BLUE_OFF, BLUE_ON

class Particle():
    def __init__(self, cant, x, y):
        self.cant = cant
        self.x = x
        self.y = y
        self.radius = 4
        self.reduse = 0.3
        self.again = True
        self.particles = []
        self.add_particles(self.cant)

    # Moves an draws particles
    def emit(self, screen):
        self.delete_particles()
        if self.particles:
            for particle in self.particles:
                pygame.draw.circle(
                    screen,
                    YELLOW_ON,
                    (particle['x'], particle['y']),
                    particle['radius'])
                particle['x'] += particle['x_dir']
                particle['y'] += particle['y_dir']
                particle['radius'] -= self.reduse

            if self.particles[0]['radius'] < self.radius/2 and self.again:
                self.again = False
                self.add_particles(self.cant//2)


    def add_particles(self, cant):
        self.particles += [{
            'x': self.x + random.randint(-10, 10),
            'y': self.y + random.randint(-10, 10),
            'radius': self.radius,
            'x_dir': random.randint(-4, 4),
            'y_dir': random.randint(-4, 4),
        } for i in range(cant)]

    def delete_particles(self):
        self.particles = list(filter(lambda p: p['radius'] > 0, self.particles))

class Diamond(pygame.sprite.Sprite):
    def __init__(self, note):
        super().__init__()
        self.note = note
        self.color = OFF_COLORS[note]
        self.image = pygame.Surface((TOKEN_SIZE, TOKEN_SIZE), pygame.SRCALPHA)
        self.vertices = [(TOKEN_SIZE // 2, 0), (TOKEN_SIZE, TOKEN_SIZE // 2), (TOKEN_SIZE // 2, TOKEN_SIZE), (0, TOKEN_SIZE // 2)]
        self.draw_diamond()
        self.draw_border()

    def draw_diamond(self):
        pygame.draw.polygon(self.image, self.color, self.vertices)

    def draw_border(self):
        pygame.draw.polygon(self.image, BORDER_COLOR, self.vertices, 3)

class Token(Diamond):
    def __init__(self, note):
        super().__init__(note)
        self.rect = self.image.get_rect(center=(int(ROWS[note+1]), 0))
        self.rect_spawn = self.image.get_rect(center=(int(ROWS[note+1]), 0))
        
        collider_ratio = 0.4
        self.rect.width = TOKEN_SIZE * collider_ratio
        self.rect.height = TOKEN_SIZE * collider_ratio

        collider_ratio = 1.15
        self.rect_spawn.width = TOKEN_SIZE * collider_ratio
        self.rect_spawn.height = TOKEN_SIZE * collider_ratio

        self.velocity = 1

    def update(self):
        self.rect.y += self.velocity
        self.rect_spawn.y += self.velocity

    def collidepoint(self, point):
        return self.rect_spawn.collidepoint(point)

    def destroy(self, height):
        return self.rect.y > height

class Button(Diamond):
    def __init__(self, note):
        super().__init__(note)
        self.draw_diamond()
        self.draw_border()
        self.x = int(ROWS[note+1])
        self.y = BASE
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def key_down(self):
        self.color = ON_COLORS[self.note]
        self.draw_diamond()

    def key_up(self):
        self.color = OFF_COLORS[self.note]
        self.draw_diamond()
        self.draw_border()

class StandardButton(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, normal_color, border_color, text, font):
        super().__init__()

        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.vertices = (0, 0, width, height)
        self.normal_color = normal_color
        self.border_color = border_color
        pygame.draw.rect(self.image, normal_color, self.vertices)
        pygame.draw.rect(self.image, self.border_color, self.vertices, 3)

        self.rect = self.image.get_rect(center=(x, y))

        self.text = text
        self.color_text = GOLDEN
        self.font = font

        text_renderizado = self.font.render(self.text, True, self.color_text)
        rect_text = text_renderizado.get_rect(center=(self.rect.width//2, self.rect.height//2))
        self.image.blit(text_renderizado, rect_text)

        self.pressed = False

    def update(self, event):
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                pass
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        if event.type == pygame.MOUSEBUTTONUP:
            self.pressed = False

    def consume_action(self):
        if self.pressed:
            self.pressed = False
            return True
        return False
        
class LoadingAnimation():
    def __init__(self, game_state) -> None:
        self.actual_diamond = 0
        self.steps = 2
        self.actual_step = 0
        self.dist = 50
        self.margin_bottom = TOKEN_SIZE + 30
        self.initial_pos = game_state.height - self.margin_bottom
        self.size = 30
        self.margin = 20
        self.final_pos = game_state.height - self.margin_bottom - self.dist
        self.diamonds_q = []
        self.vertices = [(TOKEN_SIZE // 2, 0), (TOKEN_SIZE, TOKEN_SIZE // 2), (TOKEN_SIZE // 2, TOKEN_SIZE), (0, TOKEN_SIZE // 2)]
        for i in range(3):
            image = pygame.Surface((TOKEN_SIZE, TOKEN_SIZE), pygame.SRCALPHA)
            pygame.draw.polygon(image, (255,255,255), self.vertices, 3)
            rect = image.get_rect(center=((game_state.width - TOKEN_SIZE*2) - (i*(TOKEN_SIZE + self.margin)), (self.final_pos + TOKEN_SIZE//2) if i == 2 else (self.initial_pos + TOKEN_SIZE//2)))
            self.diamonds_q.insert(0, (image, rect))

    def draw(self, screen):
        for diamond in self.diamonds_q:
            screen.blit(diamond[0], diamond[1])

    def update(self):
        if self.actual_step == self.steps:
            self.actual_diamond = (self.actual_diamond + 1) % len(self.diamonds_q)
            self.actual_step = 0
            image, rect = self.diamonds_q[self.actual_diamond]
            rect.y = self.final_pos
            self.diamonds_q[self.actual_diamond] = (image, rect)
        else:
            image, rect = self.diamonds_q[self.actual_diamond]
            rect.y += (self.dist / self.steps)
            self.actual_step += 1
            self.diamonds_q[self.actual_diamond] = (image, rect)
        pass

class RichText():
    def __init__(self, size, font='Lobster-Regular.ttf') -> None:
        self.font = pygame.font.Font(font, size)
        self.size = size
        self.surfaces = []
        self.rects = []

    def render(self, text, color):
        self.surfaces = [self.font.render(line, True, color) for line in text.split('\n')]
    
    def get_rect(self, x, y):
        self.rects = [surface.get_rect(center=(x, y+i*self.size)) for i, surface in enumerate(self.surfaces)]
    
    def blit(self, background):
        for surface, rect in zip(self.surfaces, self.rects):
            background.blit(surface, rect)

class TextInput():
    def __init__(self, x, y, width, height, font) -> None:
        self.focused = False
        self.text = ''
        
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(x, y))
        # pygame.draw.polygon(image, (255,255,255), self.vertices, 3)
        self.x = x
        self.y = y
        self.font = font(height - height//3)

    def focus(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.focused = True
            else:
                self.focused = False
    
    def get_key(self, event_key):
        if self.focused:
            if event_key.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event_key.unicode
    
    def draw(self, screen):
        if self.focused:
            border_color = BLUE_ON
        else:
            border_color = BLUE_OFF

        render_text = self.font.render(self.text, True, 'black')
        rect_text = render_text.get_rect(topleft=(10,-3))
        self.image.fill(WHITE)
        self.image.blit(render_text, rect_text)
        screen.blit(self.image, self.rect)
        pygame.draw.rect(screen, border_color, self.rect, 3)

    def get_value(self):
        return self.text