import pygame
import sys
import math
from enum import Enum

# Inicializar Pygame
pygame.init()

# Constantes del juego
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
LIGHT_BLUE = (173, 216, 230)

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 8
        self.speed = 3
        self.trail = []  # Para el rastro mientras corta
        self.cutting = False
        
    def update(self, keys):
        # Movimiento básico
        if keys[pygame.K_LEFT] and self.x > 0:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x < WINDOW_WIDTH - self.size:
            self.x += self.speed
        if keys[pygame.K_UP] and self.y > 0:
            self.y -= self.speed
        if keys[pygame.K_DOWN] and self.y < WINDOW_HEIGHT - self.size:
            self.y += self.speed
            
        # Añadir posición al rastro si se está moviendo
        if any([keys[pygame.K_LEFT], keys[pygame.K_RIGHT], 
                keys[pygame.K_UP], keys[pygame.K_DOWN]]):
            self.trail.append((self.x + self.size//2, self.y + self.size//2))
            # Limitar el tamaño del rastro
            if len(self.trail) > 100:
                self.trail.pop(0)
    
    def draw(self, screen):
        # Dibujar el rastro
        if len(self.trail) > 1:
            pygame.draw.lines(screen, YELLOW, False, self.trail, 2)
        
        # Dibujar el jugador
        pygame.draw.rect(screen, BLUE, (self.x, self.y, self.size, self.size))

class Enemy:
    def __init__(self, x, y, speed=2):
        self.x = x
        self.y = y
        self.size = 10
        self.speed = speed
        self.direction_x = 1
        self.direction_y = 1
        
    def update(self):
        # Movimiento básico - rebota en los bordes
        self.x += self.speed * self.direction_x
        self.y += self.speed * self.direction_y
        
        if self.x <= 0 or self.x >= WINDOW_WIDTH - self.size:
            self.direction_x *= -1
        if self.y <= 0 or self.y >= WINDOW_HEIGHT - self.size:
            self.direction_y *= -1
    
    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x + self.size//2), int(self.y + self.size//2)), self.size//2)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Gals Panic Remake")
        self.clock = pygame.time.Clock()
        self.state = GameState.PLAYING
        
        # Inicializar objetos del juego
        self.player = Player(50, 50)
        self.enemies = [
            Enemy(200, 200, 2),
            Enemy(400, 300, 1.5),
            Enemy(600, 100, 2.5)
        ]
        
        self.score = 0
        self.lives = 3
        self.area_revealed = 0
        self.target_area = 75  # Porcentaje a descubrir para ganar
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                    
        return True
    
    def update(self):
        if self.state == GameState.PLAYING:
            keys = pygame.key.get_pressed()
            self.player.update(keys)
            
            for enemy in self.enemies:
                enemy.update()
                
            # Verificar colisiones (básico por ahora)
            player_rect = pygame.Rect(self.player.x, self.player.y, self.player.size, self.player.size)
            for enemy in self.enemies:
                enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.size, enemy.size)
                if player_rect.colliderect(enemy_rect):
                    self.lives -= 1
                    self.player.x, self.player.y = 50, 50  # Resetear posición
                    self.player.trail.clear()
                    if self.lives <= 0:
                        self.state = GameState.GAME_OVER
    
    def draw(self):
        self.screen.fill(BLACK)
        
        if self.state == GameState.PLAYING:
            # Dibujar área de juego
            pygame.draw.rect(self.screen, GRAY, (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT), 2)
            
            # Dibujar enemigos
            for enemy in self.enemies:
                enemy.draw(self.screen)
            
            # Dibujar jugador
            self.player.draw(self.screen)
            
            # Dibujar UI
            font = pygame.font.Font(None, 36)
            score_text = font.render(f"Score: {self.score}", True, WHITE)
            lives_text = font.render(f"Lives: {self.lives}", True, WHITE)
            area_text = font.render(f"Area: {self.area_revealed:.1f}%", True, WHITE)
            
            self.screen.blit(score_text, (10, 10))
            self.screen.blit(lives_text, (10, 50))
            self.screen.blit(area_text, (10, 90))
            
        elif self.state == GameState.GAME_OVER:
            font = pygame.font.Font(None, 72)
            game_over_text = font.render("GAME OVER", True, RED)
            restart_text = pygame.font.Font(None, 36).render("Press R to restart or ESC to quit", True, WHITE)
            
            self.screen.blit(game_over_text, (WINDOW_WIDTH//2 - game_over_text.get_width()//2, WINDOW_HEIGHT//2 - 50))
            self.screen.blit(restart_text, (WINDOW_WIDTH//2 - restart_text.get_width()//2, WINDOW_HEIGHT//2 + 50))
            
        pygame.display.flip()
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
