import pygame
import random
import time
import json
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple

# Inizializzazione Pygame
pygame.init()


# Costanti
WINDOW_SIZE = 600
GRID_SIZE = 25
GRID_COUNT = WINDOW_SIZE // GRID_SIZE
DARK_GRAY = (40, 40, 40)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 99, 71)
NEON_GREEN = (57, 255, 20)
GAME_TIME = 180  # 3 minuti in secondi

# Font personalizzati
FONT_LARGE = pygame.font.Font(None, 48)
FONT_MEDIUM = pygame.font.Font(None, 36)
FONT_SMALL = pygame.font.Font(None, 24)

# Classi di enumerazione
class Difficulty(Enum):
    EASY = 0.14
    MEDIUM = 0.1
    HARD = 0.08

class GameMode(Enum):
    POINTS = "POINTS"
    TIME = "TIME"

class Barrier(Enum):
    NONE = "NONE"
    BORDER = "BORDER"
    RANDOM = "RANDOM"

class Button:
    def __init__(self, x, y, width, height, text, color=(100, 100, 100), hover_color=(150, 150, 150)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=10)
        
        text_surface = FONT_MEDIUM.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption("The Snake")
        self.clock = pygame.time.Clock()
        self.last_direction_change = time.time()
        self.direction_change_cooldown = 0.1
        self.barriers = []
        self.reset_game()
        self.load_stats()
        self.game_quit = False

    def spawn_food(self):
        attempts = 0
        max_attempts = 100  # Limite di sicurezza
        
        while attempts < max_attempts:
            pos = (random.randint(0, GRID_COUNT-1), random.randint(0, GRID_COUNT-1))
            # Verifica esplicita per modalità BORDER
            if pos[0] == 0 or pos[0] == GRID_COUNT-1 or pos[1] == 0 or pos[1] == GRID_COUNT-1:
                # Posizione sul bordo, non valida
                attempts += 1
                continue
            
            if pos not in self.snake and pos not in self.barriers:
                return pos
            
            attempts += 1
        
        # Fallback: trova qualsiasi posizione libera non sul bordo
        for x in range(1, GRID_COUNT-1):
            for y in range(1, GRID_COUNT-1):
                pos = (x, y)
                if pos not in self.snake and pos not in self.barriers:
                    return pos
        
        # Ultima risorsa se tutto il resto fallisce
        return (GRID_COUNT//2, GRID_COUNT//2)

    def create_random_barriers(self):
        self.barriers = []
        safe_zone = set()
        center = (GRID_COUNT//2, GRID_COUNT//2)
        for x in range(center[0]-2, center[0]+3):
            for y in range(center[1]-2, center[1]+3):
                if 0 <= x < GRID_COUNT and 0 <= y < GRID_COUNT:
                    safe_zone.add((x, y))

        for _ in range(5):
            y = random.randint(1, GRID_COUNT-2)
            length = random.randint(3, 8)
            start_x = random.randint(0, GRID_COUNT-length)
            barrier_line = [(x, y) for x in range(start_x, start_x+length)]
            if not any(pos in safe_zone for pos in barrier_line):
                self.barriers.extend(barrier_line)

            x = random.randint(1, GRID_COUNT-2)
            length = random.randint(3, 8)
            start_y = random.randint(0, GRID_COUNT-length)
            barrier_line = [(x, y) for y in range(start_y, start_y+length)]
            if not any(pos in safe_zone for pos in barrier_line):
                self.barriers.extend(barrier_line)

    def create_border_barriers(self):
        self.barriers = [(x, 0) for x in range(GRID_COUNT)]
        self.barriers.extend([(x, GRID_COUNT-1) for x in range(GRID_COUNT)])
        self.barriers.extend([(0, y) for y in range(GRID_COUNT)])
        self.barriers.extend([(GRID_COUNT-1, y) for y in range(GRID_COUNT)])

    def wrap_position(self, pos):
        x, y = pos
        return (x % GRID_COUNT, y % GRID_COUNT)

    def load_stats(self):
        try:
            with open('snake_stats.json', 'r') as f:
                self.stats = json.load(f)
        except FileNotFoundError:
            self.stats = []

    def save_stats(self):
        with open('snake_stats.json', 'w') as f:
            json.dump(self.stats, f)

    def reset_stats(self):
        self.stats = []
        self.save_stats()

    def reset_game(self):
        self.snake = [(GRID_COUNT//2, GRID_COUNT//2)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.barriers = []
        self.food = self.spawn_food()
        self.food_color = self.pulse_color()
        self.snake_color = NEON_GREEN
        self.score = 0
        self.start_time = time.time()
        self.game_quit = False
        self.particle_effects = []

    def pulse_color(self):
        t = time.time() * 2
        r = int(255 * (0.5 + 0.5 * math.sin(t)))
        g = int(100 * (0.5 + 0.5 * math.sin(t + 2)))
        b = int(100 * (0.5 + 0.5 * math.sin(t + 4)))
        return (r, g, b)

    def get_player_name(self):
        input_box = pygame.Rect(WINDOW_SIZE//4, WINDOW_SIZE//2 - 50, WINDOW_SIZE//2, 60)
        text = ""
        active = True
        cursor_visible = True
        cursor_timer = 0

        while active:
            current_time = time.time()
            
            # Aggiorna il cursore ogni 0.5 secondi
            if current_time - cursor_timer >= 0.5:
                cursor_visible = not cursor_visible
                cursor_timer = current_time

            self.screen.fill(DARK_GRAY)
            
            # Disegna il titolo
            title = FONT_LARGE.render("INSERISCI IL TUO NOME", True, WHITE)
            title_rect = title.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 - 150))
            self.screen.blit(title, title_rect)

            # Disegna il box di input
            pygame.draw.rect(self.screen, BLACK, input_box, border_radius=10)
            pygame.draw.rect(self.screen, WHITE, input_box, 2, border_radius=10)

            # Disegna il testo inserito
            txt_surface = FONT_MEDIUM.render(text + ("|" if cursor_visible else ""), True, WHITE)
            text_rect = txt_surface.get_rect(center=input_box.center)
            self.screen.blit(txt_surface, text_rect)

            # Disegna il testo di aiuto
            help_text = FONT_SMALL.render("Premi ENTER per confermare", True, WHITE)
            help_rect = help_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 + 50))
            self.screen.blit(help_text, help_rect)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and text:
                        return text
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    elif len(text) < 20 and event.unicode.isalnum():  # Limite di 20 caratteri
                        text += event.unicode

            pygame.display.flip()
            self.clock.tick(60)

    def main_menu(self):
        difficulty = Difficulty.EASY
        game_mode = GameMode.POINTS
        barrier_type = Barrier.NONE
        color_change = False
        
        # Centra i pulsanti e usa dimensioni consistenti
        button_width = 300
        button_height = 60
        button_spacing = 20
        start_y = WINDOW_SIZE//2 - (5 * (button_height + button_spacing))//2

        buttons = {
            'difficulty': Button(WINDOW_SIZE//2 - button_width//2, start_y, 
                               button_width, button_height, 
                               f"Difficulty: {difficulty.name}", (0, 128, 128)),
            'mode': Button(WINDOW_SIZE//2 - button_width//2, start_y + button_height + button_spacing, 
                          button_width, button_height, 
                          f"Mode: {game_mode.name}", (0, 128, 128)),
            'barrier': Button(WINDOW_SIZE//2 - button_width//2, start_y + 2 * (button_height + button_spacing), 
                            button_width, button_height, 
                            f"Barrier: {barrier_type.name}", (0, 128, 128)),
            'color': Button(WINDOW_SIZE//2 - button_width//2, start_y + 3 * (button_height + button_spacing), 
                          button_width, button_height, 
                          f"Color Change: {color_change}", (0, 128, 128)),
            'start': Button(WINDOW_SIZE//2 - button_width//2, start_y + 4 * (button_height + button_spacing), 
                          button_width, button_height, 
                          "Start Game", (0, 180, 0)),
            'stats': Button(WINDOW_SIZE//2 - button_width//2, start_y + 5 * (button_height + button_spacing), 
                          button_width, button_height, 
                          "View Stats", (128, 0, 128))
        }

        while True:
            mouse_pos = pygame.mouse.get_pos()
            
            # Sfondo animato
            self.screen.fill(DARK_GRAY)
            current_time = time.time()
            for x in range(0, WINDOW_SIZE, 40):
                for y in range(0, WINDOW_SIZE, 40):
                    color_value = int(128 + 127 * math.sin(current_time + x * 0.01 + y * 0.01))
                    pygame.draw.rect(self.screen, (0, color_value//4, color_value//4), 
                                   (x, y, 2, 2))

            # Titolo animato
            title = FONT_LARGE.render("MODERN SNAKE", True, WHITE)
            title_pos = (WINDOW_SIZE//2, start_y - 80)
            title_rect = title.get_rect(center=title_pos)
            self.screen.blit(title, title_rect)

            # Aggiorna e disegna i pulsanti
            for button in buttons.values():
                button.update(mouse_pos)
                button.draw(self.screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    
                    if buttons['difficulty'].is_clicked(pos):
                        difficulties = list(Difficulty)
                        current_idx = difficulties.index(difficulty)
                        difficulty = difficulties[(current_idx + 1) % len(difficulties)]
                        buttons['difficulty'].text = f"Difficulty: {difficulty.name}"
                    
                    elif buttons['mode'].is_clicked(pos):
                        modes = list(GameMode)
                        current_idx = modes.index(game_mode)
                        game_mode = modes[(current_idx + 1) % len(modes)]
                        buttons['mode'].text = f"Mode: {game_mode.name}"
                    
                    elif buttons['barrier'].is_clicked(pos):
                        barriers = list(Barrier)
                        current_idx = barriers.index(barrier_type)
                        barrier_type = barriers[(current_idx + 1) % len(barriers)]
                        buttons['barrier'].text = f"Barrier: {barrier_type.name}"
                    
                    elif buttons['color'].is_clicked(pos):
                        color_change = not color_change
                        buttons['color'].text = f"Color Change: {color_change}"
                    
                    elif buttons['start'].is_clicked(pos):
                        player_name = self.get_player_name()
                        if player_name:
                            return {
                                'difficulty': difficulty,
                                'mode': game_mode,
                                'barrier': barrier_type,
                                'color_change': color_change,
                                'player_name': player_name
                            }
                    
                    elif buttons['stats'].is_clicked(pos):
                        self.show_stats()

            pygame.display.flip()
            self.clock.tick(60)

    def run(self):
        while True:
            settings = self.main_menu()
            if settings is None:
                break
                
            self.reset_game()
            
            if settings['barrier'] == Barrier.BORDER:
                self.create_border_barriers()
            elif settings['barrier'] == Barrier.RANDOM:
                self.create_random_barriers()

            game_over = False
            start_time = time.time()
            last_move_time = time.time()
            move_delay = settings['difficulty'].value
            
            while not game_over:
                current_time = time.time()
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.game_quit = True
                            game_over = True
                        elif current_time - self.last_direction_change >= self.direction_change_cooldown:
                            if event.key == pygame.K_UP and self.direction != (0, 1):
                                self.next_direction = (0, -1)
                                self.last_direction_change = current_time
                            elif event.key == pygame.K_DOWN and self.direction != (0, -1):
                                self.next_direction = (0, 1)
                                self.last_direction_change = current_time
                            elif event.key == pygame.K_LEFT and self.direction != (1, 0):
                                self.next_direction = (-1, 0)
                                self.last_direction_change = current_time
                            elif event.key == pygame.K_RIGHT and self.direction != (-1, 0):
                                self.next_direction = (1, 0)
                                self.last_direction_change = current_time

                if current_time - last_move_time >= move_delay:
                    self.direction = self.next_direction
                    last_move_time = current_time
                    
                    # Movimento serpente
                    head = self.snake[0]
                    new_head = (head[0] + self.direction[0], head[1] + self.direction[1])

                    if settings['barrier'] == Barrier.NONE:
                        new_head = self.wrap_position(new_head)
                        if new_head in self.snake[1:]:  # Controlla collisione solo con il corpo
                            game_over = True
                            continue
                    elif settings['barrier'] == Barrier.RANDOM:
                        if new_head in self.barriers:
                            game_over = True
                            continue
                        new_head = self.wrap_position(new_head)
                        if new_head in self.snake[1:]:
                            game_over = True
                            continue
                    else:
                        if (new_head in self.snake[1:] or 
                            new_head in self.barriers or 
                            new_head[0] < 0 or new_head[0] >= GRID_COUNT or 
                            new_head[1] < 0 or new_head[1] >= GRID_COUNT):
                            game_over = True
                            continue

                    self.snake.insert(0, new_head)
                    
                    # Controllo cibo
                    if new_head == self.food:
                        self.score += 10
                        if settings['color_change']:
                            self.snake_color = self.food_color
                        self.food = self.spawn_food()
                        self.food_color = self.pulse_color()
                        
                        # Aggiungi particelle per effetto speciale
                        for _ in range(10):
                            self.particle_effects.append({
                                'pos': (new_head[0] * GRID_SIZE + GRID_SIZE//2, 
                                      new_head[1] * GRID_SIZE + GRID_SIZE//2),
                                'vel': (random.uniform(-2, 2), random.uniform(-2, 2)),
                                'ttl': 1.0,  # Time to live
                                'color': self.food_color
                            })
                    else:
                        self.snake.pop()

                    # Aggiorna particelle
                    for particle in self.particle_effects[:]:
                        particle['ttl'] -= move_delay
                        if particle['ttl'] <= 0:
                            self.particle_effects.remove(particle)
                        else:
                            particle['pos'] = (particle['pos'][0] + particle['vel'][0],
                                             particle['pos'][1] + particle['vel'][1])

                # Controllo vittoria/tempo
                current_time = time.time() - start_time
                remaining_time = GAME_TIME - current_time
                
                if settings['mode'] == GameMode.POINTS and self.score >= 1000000:
                    game_over = True
                elif settings['mode'] == GameMode.TIME and remaining_time <= 0:
                    game_over = True

                # Disegno
                self.screen.fill(DARK_GRAY)
                
                # Disegna griglia sottile
                for x in range(0, WINDOW_SIZE, GRID_SIZE):
                    pygame.draw.line(self.screen, (60, 60, 60), (x, 0), (x, WINDOW_SIZE))
                for y in range(0, WINDOW_SIZE, GRID_SIZE):
                    pygame.draw.line(self.screen, (60, 60, 60), (0, y), (WINDOW_SIZE, y))
                
                # Disegno barriere con effetto gradiente
                for barrier in self.barriers:
                    pygame.draw.rect(self.screen, RED,
                                  (barrier[0] * GRID_SIZE, barrier[1] * GRID_SIZE,
                                   GRID_SIZE, GRID_SIZE))
                    pygame.draw.rect(self.screen, (200, 0, 0),
                                  (barrier[0] * GRID_SIZE + 2, barrier[1] * GRID_SIZE + 2,
                                   GRID_SIZE - 4, GRID_SIZE - 4))

                # Disegno serpente con effetto gradiente
                for i, segment in enumerate(self.snake):
                    color = self.snake_color
                    if i == 0:  # Testa del serpente
                        pygame.draw.rect(self.screen, color,
                                      (segment[0] * GRID_SIZE, segment[1] * GRID_SIZE,
                                       GRID_SIZE, GRID_SIZE))
                        # Occhi del serpente
                        eye_color = (255, 255, 255)
                        eye_size = GRID_SIZE // 4
                        eye_offset = GRID_SIZE // 4
                        if self.direction[0] == 1:  # Destra
                            left_eye = (segment[0] * GRID_SIZE + GRID_SIZE - eye_offset, 
                                      segment[1] * GRID_SIZE + eye_offset)
                            right_eye = (segment[0] * GRID_SIZE + GRID_SIZE - eye_offset, 
                                       segment[1] * GRID_SIZE + GRID_SIZE - eye_offset - eye_size)
                        elif self.direction[0] == -1:  # Sinistra
                            left_eye = (segment[0] * GRID_SIZE + eye_offset - eye_size, 
                                      segment[1] * GRID_SIZE + eye_offset)
                            right_eye = (segment[0] * GRID_SIZE + eye_offset - eye_size, 
                                       segment[1] * GRID_SIZE + GRID_SIZE - eye_offset - eye_size)
                        elif self.direction[1] == -1:  # Su
                            left_eye = (segment[0] * GRID_SIZE + eye_offset, 
                                      segment[1] * GRID_SIZE + eye_offset - eye_size)
                            right_eye = (segment[0] * GRID_SIZE + GRID_SIZE - eye_offset - eye_size, 
                                       segment[1] * GRID_SIZE + eye_offset - eye_size)
                        else:  # Giù
                            left_eye = (segment[0] * GRID_SIZE + eye_offset, 
                                      segment[1] * GRID_SIZE + GRID_SIZE - eye_offset)
                            right_eye = (segment[0] * GRID_SIZE + GRID_SIZE - eye_offset - eye_size, 
                                       segment[1] * GRID_SIZE + GRID_SIZE - eye_offset)
                        pygame.draw.rect(self.screen, eye_color, (*left_eye, eye_size, eye_size))
                        pygame.draw.rect(self.screen, eye_color, (*right_eye, eye_size, eye_size))
                    else:
                        # Effetto gradiente per il corpo
                        alpha = max(0.3, 1 - i / len(self.snake))
                        segment_color = (int(color[0] * alpha), 
                                       int(color[1] * alpha), 
                                       int(color[2] * alpha))
                        pygame.draw.rect(self.screen, segment_color,
                                      (segment[0] * GRID_SIZE + 1, segment[1] * GRID_SIZE + 1,
                                       GRID_SIZE - 2, GRID_SIZE - 2))

                # Disegno cibo con effetto pulsante
                self.food_color = self.pulse_color()
                pygame.draw.rect(self.screen, self.food_color,
                              (self.food[0] * GRID_SIZE, self.food[1] * GRID_SIZE,
                               GRID_SIZE, GRID_SIZE))
                
                # Disegno particelle
                for particle in self.particle_effects:
                    alpha = int(255 * (particle['ttl']))
                    color = (*particle['color'][:3], alpha)
                    pygame.draw.circle(self.screen, color, 
                                     (int(particle['pos'][0]), int(particle['pos'][1])), 
                                     3)

                # Disegno punteggio con effetto ombra
                score_text = FONT_LARGE.render(f"Score: {self.score}", True, WHITE)
                score_shadow = FONT_LARGE.render(f"Score: {self.score}", True, (40, 40, 40))
                score_rect = score_text.get_rect(topleft=(20, 20))
                self.screen.blit(score_shadow, (score_rect.x + 2, score_rect.y + 2))
                self.screen.blit(score_text, score_rect)

                if settings['mode'] == GameMode.TIME:
                    # Mostra il tempo rimanente con effetto ombra
                    minutes = int(remaining_time // 60)
                    seconds = int(remaining_time % 60)
                    time_text = FONT_LARGE.render(f"Time: {minutes}:{seconds:02d}", True, WHITE)
                    time_shadow = FONT_LARGE.render(f"Time: {minutes}:{seconds:02d}", True, (40, 40, 40))
                    time_rect = time_text.get_rect(topleft=(20, 70))
                    self.screen.blit(time_shadow, (time_rect.x + 2, time_rect.y + 2))
                    self.screen.blit(time_text, time_rect)

                pygame.display.flip()
                self.clock.tick(60)  # Mantiene 60 FPS costanti

            # Game Over screen
            if game_over and not self.game_quit:
                self.show_game_over(settings['player_name'], self.score)
                
                # Salva statistiche
                if self.score > 0:
                    self.stats.append({
                        'player_name': settings['player_name'],
                        'score': self.score,
                        'mode': settings['mode'].name,
                        'difficulty': settings['difficulty'].name,
                        'duration': time.time() - start_time
                    })
                    self.save_stats()

    def show_game_over(self, player_name, score):
        alpha = 0
        fade_speed = 5
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
        overlay.fill(BLACK)
        
        while alpha < 128:
            overlay.set_alpha(alpha)
            self.screen.blit(overlay, (0, 0))
            alpha += fade_speed
            pygame.display.flip()
            self.clock.tick(60)
            
        game_over_text = FONT_LARGE.render("GAME OVER", True, WHITE)
        score_text = FONT_MEDIUM.render(f"Final Score: {score}", True, WHITE)
        player_text = FONT_MEDIUM.render(f"Player: {player_name}", True, WHITE)
        continue_text = FONT_SMALL.render("Press any key to continue", True, WHITE)
        
        game_over_rect = game_over_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 - 60))
        score_rect = score_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2))
        player_rect = player_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 + 40))
        continue_rect = continue_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 + 100))
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    waiting = False
                    
            overlay.set_alpha(128)
            self.screen.blit(overlay, (0, 0))
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(score_text, score_rect)
            self.screen.blit(player_text, player_rect)
            self.screen.blit(continue_text, continue_rect)
            pygame.display.flip()
            self.clock.tick(60)

    def show_stats(self):
        # Constants for pagination
        STATS_PER_PAGE = 10
        current_page = 0

        button_width = 300
        button_height = 40
        button_spacing = 20

        # Create buttons for navigation
        back_button = Button(20, WINDOW_SIZE - 60, 150, 40, "Back", (128, 0, 0))
        prev_button = Button(WINDOW_SIZE//2 - 160, WINDOW_SIZE - 60, 150, 40, "Previous", (0, 128, 128))
        next_button = Button(WINDOW_SIZE//2 + 10, WINDOW_SIZE - 60, 150, 40, "Next", (0, 128, 128))
        reset_button = Button(WINDOW_SIZE - 170, WINDOW_SIZE - 60, 150, 40, "Reset", (128, 0, 0))

        showing_stats = True
        while showing_stats:
            mouse_pos = pygame.mouse.get_pos()
            self.screen.fill(DARK_GRAY)

            # Update button hover states
            back_button.update(mouse_pos)
            prev_button.update(mouse_pos)
            next_button.update(mouse_pos)
            reset_button.update(mouse_pos)

            # Calculate total pages
            total_pages = max(1, (len(self.stats) + STATS_PER_PAGE - 1) // STATS_PER_PAGE)

            # Draw title
            title = FONT_LARGE.render("HIGH SCORES", True, WHITE)
            title_rect = title.get_rect(center=(WINDOW_SIZE//2, 50))
            self.screen.blit(title, title_rect)

            # Draw stats
            if self.stats:
                start_idx = current_page * STATS_PER_PAGE
                end_idx = min(start_idx + STATS_PER_PAGE, len(self.stats))
                y_pos = 100  # Start position for stats

                # Headers
                headers = ["Player", "Score", "Mode", "Difficulty", "Duration"]
                x_positions = [50, 200, 350, 500, 650]
                for header, x in zip(headers, x_positions):
                    text = FONT_SMALL.render(header, True, (200, 200, 200))
                    self.screen.blit(text, (x, y_pos))

                y_pos += 40  # Space between headers and stats

                # Stats entries
                for i in range(start_idx, end_idx):
                    stat = self.stats[i]
                    color = WHITE if i % 2 == 0 else (200, 200, 200)

                    # Player name
                    text = FONT_SMALL.render(str(stat['player_name'])[:15], True, color)
                    self.screen.blit(text, (50, y_pos))

                    # Score
                    text = FONT_SMALL.render(str(stat['score']), True, color)
                    self.screen.blit(text, (200, y_pos))

                    # Mode
                    text = FONT_SMALL.render(str(stat['mode']), True, color)
                    self.screen.blit(text, (350, y_pos))

                    # Difficulty
                    text = FONT_SMALL.render(str(stat['difficulty']), True, color)
                    self.screen.blit(text, (500, y_pos))

                    # Duration
                    duration = f"{stat['duration']:.1f}s"
                    text = FONT_SMALL.render(duration, True, color)
                    self.screen.blit(text, (650, y_pos))

                    y_pos += 30  # Space between rows

                # Page indicator
                page_text = FONT_SMALL.render(f"Page {current_page + 1} of {total_pages}", True, WHITE)
                page_rect = page_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE - 100))
                self.screen.blit(page_text, page_rect)
            else:
                # No stats message
                no_stats = FONT_MEDIUM.render("No statistics available", True, WHITE)
                no_stats_rect = no_stats.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2))
                self.screen.blit(no_stats, no_stats_rect)

            # Draw buttons
            back_button.draw(self.screen)
            if total_pages > 1:
                if current_page > 0:
                    prev_button.draw(self.screen)
                if current_page < total_pages - 1:
                    next_button.draw(self.screen)
            reset_button.draw(self.screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_button.is_clicked(event.pos):
                        showing_stats = False
                    elif prev_button.is_clicked(event.pos) and current_page > 0:
                        current_page -= 1
                    elif next_button.is_clicked(event.pos) and current_page < total_pages - 1:
                        current_page += 1
                    elif reset_button.is_clicked(event.pos):
                        self.reset_stats()
                        showing_stats = False

            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    game = Game()
    game.run()