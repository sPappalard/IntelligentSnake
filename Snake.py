import pygame
import random
import time
import json
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple

# Inizializzazione Pygame
pygame.init()

# Costanti
WINDOW_SIZE = 600
GRID_SIZE = 20
GRID_COUNT = WINDOW_SIZE // GRID_SIZE
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GAME_TIME = 180  # 3 minuti in secondi

# Classi di enumerazione
class Difficulty(Enum):
    EASY = 0.15
    MEDIUM = 0.1
    HARD = 0.05

class GameMode(Enum):
    POINTS = "POINTS"
    TIME = "TIME"

class Barrier(Enum):
    NONE = "NONE"
    BORDER = "BORDER"
    RANDOM = "RANDOM"

@dataclass
class GameStats:
    player_name: str
    score: int
    mode: GameMode
    difficulty: Difficulty
    duration: float

class Button:
    def __init__(self, x, y, width, height, text, color=(100, 100, 100)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.font = pygame.font.Font(None, 32)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE), pygame.RESIZABLE)
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.barriers = []
        self.reset_game()
        self.load_stats()
        self.game_quit = False

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
        self.barriers = []
        self.food = self.spawn_food()
        self.food_color = self.random_color()
        self.snake_color = (0, 255, 0)
        self.score = 0
        self.start_time = time.time()
        self.game_quit = False

    def random_color(self):
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def spawn_food(self):
        while True:
            pos = (random.randint(0, GRID_COUNT-1), random.randint(0, GRID_COUNT-1))
            if pos not in self.snake and pos not in self.barriers:
                return pos

    def create_random_barriers(self):
        self.barriers = []
        # Definisci l'area di sicurezza intorno al serpente
        safe_zone = set()
        center = (GRID_COUNT//2, GRID_COUNT//2)
        for x in range(center[0]-2, center[0]+3):
            for y in range(center[1]-2, center[1]+3):
                safe_zone.add((x, y))

        # Crea linee di barriere casuali orizzontali e verticali
        for _ in range(5):  # Numero di linee
            # Linea orizzontale
            y = random.randint(1, GRID_COUNT-2)
            length = random.randint(3, 8)  # Lunghezza casuale della linea
            start_x = random.randint(0, GRID_COUNT-length)
            barrier_line = [(x, y) for x in range(start_x, start_x+length)]
            # Aggiungi solo se non interseca la zona di sicurezza
            if not any(pos in safe_zone for pos in barrier_line):
                self.barriers.extend(barrier_line)

            # Linea verticale
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

    def main_menu(self):
        difficulty = Difficulty.EASY
        game_mode = GameMode.POINTS
        barrier_type = Barrier.NONE
        color_change = False
        
        buttons = {
            'difficulty': Button(50, 100, 200, 50, f"Difficulty: {difficulty.name}", (0, 128, 0)),
            'mode': Button(50, 170, 200, 50, f"Mode: {game_mode.name}", (0, 128, 0)),
            'barrier': Button(50, 240, 200, 50, f"Barrier: {barrier_type.name}", (0, 128, 0)),
            'color': Button(50, 310, 200, 50, f"Color Change: {color_change}", (0, 128, 0)),
            'start': Button(50, 380, 200, 50, "Start Game", (0, 128, 0)),
            'stats': Button(50, 450, 200, 50, "View Stats", (0, 128, 0))
        }

        while True:
            self.screen.fill((0, 0, 0))
            
            # Disegno sfondo stile anni '80
            self.screen.fill((0, 0, 0))
            for i in range(0, WINDOW_SIZE, 20):
                pygame.draw.line(self.screen, (0, 255, 0), (i, 0), (i, WINDOW_SIZE), 1)
                pygame.draw.line(self.screen, (0, 255, 0), (0, i), (WINDOW_SIZE, i), 1)

            for button in buttons.values():
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

    def get_player_name(self):
        input_box = pygame.Rect(WINDOW_SIZE//4, WINDOW_SIZE//2, WINDOW_SIZE//2, 50)
        font = pygame.font.Font(None, 32)
        text = ""
        active = True

        while active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return text
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

            self.screen.fill(BLACK)
            txt_surface = font.render("INSERIRE NOME UTENTE: " + text, True, WHITE)
            self.screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
            pygame.draw.rect(self.screen, WHITE, input_box, 2)
            
            pygame.display.flip()
            self.clock.tick(60)

    def show_stats(self):
        font = pygame.font.Font(None, 32)
        mode_filter = GameMode.POINTS
        
        while True:
            self.screen.fill(BLACK)
            
            # Bottone per cambiare il filtro
            filter_button = Button(50, 50, 200, 50, f"Filter: {mode_filter.name}", (0, 128, 0))
            filter_button.draw(self.screen)
            
            # Bottone per resettare le statistiche
            reset_button = Button(50, 120, 200, 50, "Reset Stats", (128, 0, 0))
            reset_button.draw(self.screen)
            
            # Mostra statistiche filtrate
            y_offset = 200
            filtered_stats = [stat for stat in self.stats if stat['mode'] == mode_filter.name]
            
            for stat in filtered_stats:
                text = f"{stat['player_name']}: {stat['score']} points"
                if mode_filter == GameMode.TIME:
                    text += f" in {stat['duration']:.1f}s"
                text_surface = font.render(text, True, WHITE)
                self.screen.blit(text_surface, (50, y_offset))
                y_offset += 40

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if filter_button.is_clicked(pygame.mouse.get_pos()):
                        mode_filter = GameMode.TIME if mode_filter == GameMode.POINTS else GameMode.POINTS
                    elif reset_button.is_clicked(pygame.mouse.get_pos()):
                        self.reset_stats()

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
            
            while not game_over:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.game_quit = True
                            game_over = True
                        elif event.key == pygame.K_UP and self.direction != (0, 1):
                            self.direction = (0, -1)
                        elif event.key == pygame.K_DOWN and self.direction != (0, -1):
                            self.direction = (0, 1)
                        elif event.key == pygame.K_LEFT and self.direction != (1, 0):
                            self.direction = (-1, 0)
                        elif event.key == pygame.K_RIGHT and self.direction != (-1, 0):
                            self.direction = (1, 0)

                # Movimento serpente
                head = self.snake[0]
                new_head = (head[0] + self.direction[0], head[1] + self.direction[1])

                if settings['barrier'] == Barrier.NONE:
                    # Modalità senza barriere: il serpente attraversa i bordi
                    new_head = self.wrap_position(new_head)
                    if new_head in self.snake:
                        game_over = True
                        continue
                elif settings['barrier'] == Barrier.RANDOM:
                    # Modalità con barriere casuali: il serpente muore solo se colpisce le barriere
                    if new_head in self.barriers:
                        game_over = True
                        continue
                    new_head = self.wrap_position(new_head)
                else:
                    # Modalità con barriere: il serpente muore se colpisce i bordi o le barriere
                    if (new_head in self.snake or 
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
                    self.food_color = self.random_color()
                else:
                    self.snake.pop()

                # Controllo vittoria/tempo
                current_time = time.time() - start_time
                remaining_time = GAME_TIME - current_time
                
                if settings['mode'] == GameMode.POINTS and self.score >= 100:
                    game_over = True
                elif settings['mode'] == GameMode.TIME and remaining_time <= 0:
                    game_over = True

                # Disegno
                self.screen.fill(BLACK)
                
                # Disegno barriere
                for barrier in self.barriers:
                    pygame.draw.rect(self.screen, RED,
                                  (barrier[0] * GRID_SIZE, barrier[1] * GRID_SIZE,
                                   GRID_SIZE, GRID_SIZE))

                # Disegno serpente
                for segment in self.snake:
                    pygame.draw.rect(self.screen, self.snake_color,
                                  (segment[0] * GRID_SIZE, segment[1] * GRID_SIZE,
                                   GRID_SIZE, GRID_SIZE))

                # Disegno cibo
                pygame.draw.rect(self.screen, self.food_color,
                              (self.food[0] * GRID_SIZE, self.food[1] * GRID_SIZE,
                               GRID_SIZE, GRID_SIZE))

                # Disegno punteggio
                font = pygame.font.Font(None, 36)
                score_text = font.render(f"Score: {self.score}", True, WHITE)
                self.screen.blit(score_text, (10, 10))

                if settings['mode'] == GameMode.TIME:
                    # Mostra il tempo rimanente in minuti e secondi
                    minutes = int(remaining_time // 60)
                    seconds = int(remaining_time % 60)
                    time_text = font.render(f"Time: {minutes}:{seconds:02d}", True, WHITE)
                    self.screen.blit(time_text, (10, 50))

                pygame.display.flip()
                self.clock.tick(1/settings['difficulty'].value)

            # Salva statistiche solo se il gioco non è stato abbandonato
            if game_over and self.score > 0 and not self.game_quit:
                self.stats.append({
                    'player_name': settings['player_name'],
                    'score': self.score,
                    'mode': settings['mode'].name,
                    'difficulty': settings['difficulty'].name,
                    'duration': time.time() - start_time
                })
                self.save_stats()

if __name__ == "__main__":
    game = Game()
    game.run()