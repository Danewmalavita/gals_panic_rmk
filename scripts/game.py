# scripts/game.py - Lógica principal del juego Gals Panic

import pygame
import math
import random
from enum import Enum
from config import *

class GameState(Enum):
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    LEVEL_COMPLETE = 4

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = PLAYER_SIZE
        self.speed = PLAYER_SPEED
        self.trail = []
        self.cutting = False
        self.start_cut_pos = None
        self.on_border = True  # Si está en el borde del área segura
        
    def update(self, keys, game_area):
        old_x, old_y = self.x, self.y
        
        # Movimiento del jugador
        if keys[pygame.K_LEFT] and self.x > game_area['x']:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x < game_area['x'] + game_area['width'] - self.size:
            self.x += self.speed
        if keys[pygame.K_UP] and self.y > game_area['y']:
            self.y -= self.speed
        if keys[pygame.K_DOWN] and self.y < game_area['y'] + game_area['height'] - self.size:
            self.y += self.speed
        
        # Verificar si se está moviendo
        moving = old_x != self.x or old_y != self.y
        
        if moving:
            center_x = self.x + self.size // 2
            center_y = self.y + self.size // 2
            
            # Verificar si está en el borde
            on_border_now = (
                center_x <= game_area['x'] + 5 or 
                center_x >= game_area['x'] + game_area['width'] - 5 or
                center_y <= game_area['y'] + 5 or 
                center_y >= game_area['y'] + game_area['height'] - 5
            )
            
            # Lógica de corte
            if self.on_border and not on_border_now:
                # Empezar corte
                self.cutting = True
                self.start_cut_pos = (center_x, center_y)
                self.trail = [(center_x, center_y)]
            elif self.cutting:
                # Continuar corte
                self.trail.append((center_x, center_y))
                
                # Si regresa al borde, completar corte
                if on_border_now:
                    self.complete_cut()
            
            self.on_border = on_border_now
            
            # Limitar tamaño del trail
            if len(self.trail) > TRAIL_MAX_LENGTH:
                self.trail.pop(0)
    
    def complete_cut(self):
        """Completa un corte y calcula el área cortada"""
        if len(self.trail) > 3:
            # Aquí iría la lógica para calcular el área cortada
            # Por ahora, simulamos que se cortó un área
            self.cutting = False
            cut_area = len(self.trail) * 2  # Simulación simple
            self.trail.clear()
            return cut_area
        else:
            self.cutting = False
            self.trail.clear()
            return 0
    
    def reset_cut(self):
        """Reinicia el corte actual"""
        self.cutting = False
        self.trail.clear()
        self.start_cut_pos = None
    
    def draw(self, screen):
        # Dibujar el trail de corte
        if len(self.trail) > 1 and self.cutting:
            pygame.draw.lines(screen, YELLOW, False, self.trail, 3)
            # Línea punteada desde el último punto hasta el jugador
            if self.trail:
                last_pos = self.trail[-1]
                current_pos = (self.x + self.size // 2, self.y + self.size // 2)
                pygame.draw.line(screen, ORANGE, last_pos, current_pos, 2)
        
        # Dibujar el jugador
        color = GREEN if self.on_border else BLUE
        pygame.draw.rect(screen, color, (self.x, self.y, self.size, self.size))
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.size, self.size), 2)

class Enemy:
    def __init__(self, x, y, enemy_type="bouncer"):
        self.x = x
        self.y = y
        self.size = ENEMY_SIZE
        self.type = enemy_type
        self.speed = random.uniform(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)
        self.direction_x = random.choice([-1, 1])
        self.direction_y = random.choice([-1, 1])
        self.color = RED
        self.trail_hunter = False  # Si persigue el trail del jugador
        
        if enemy_type == "hunter":
            self.color = PURPLE
            self.speed *= 0.8
            self.trail_hunter = True
        elif enemy_type == "fast":
            self.color = ORANGE
            self.speed *= 1.5
        
    def update(self, game_area, player=None):
        if self.type == "bouncer":
            self._bouncer_behavior(game_area)
        elif self.type == "hunter" and player:
            self._hunter_behavior(game_area, player)
        elif self.type == "fast":
            self._bouncer_behavior(game_area)
    
    def _bouncer_behavior(self, game_area):
        """Comportamiento básico de rebote"""
        self.x += self.speed * self.direction_x
        self.y += self.speed * self.direction_y
        
        # Rebotar en los bordes del área de juego
        if (self.x <= game_area['x'] or 
            self.x >= game_area['x'] + game_area['width'] - self.size):
            self.direction_x *= -1
        if (self.y <= game_area['y'] or 
            self.y >= game_area['y'] + game_area['height'] - self.size):
            self.direction_y *= -1
    
    def _hunter_behavior(self, game_area, player):
        """Comportamiento de caza hacia el jugador o su trail"""
        target_x, target_y = player.x, player.y
        
        # Si el jugador está cortando, perseguir su trail
        if player.cutting and player.trail:
            # Perseguir el punto más cercano del trail
            min_dist = float('inf')
            for trail_point in player.trail:
                dist = math.sqrt((self.x - trail_point[0])**2 + (self.y - trail_point[1])**2)
                if dist < min_dist:
                    min_dist = dist
                    target_x, target_y = trail_point[0] - self.size//2, trail_point[1] - self.size//2
        
        # Moverse hacia el objetivo
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
        
        # Mantener dentro del área de juego
        self.x = max(game_area['x'], min(self.x, game_area['x'] + game_area['width'] - self.size))
        self.y = max(game_area['y'], min(self.y, game_area['y'] + game_area['height'] - self.size))
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)
    
    def draw(self, screen):
        center_x = int(self.x + self.size // 2)
        center_y = int(self.y + self.size // 2)
        pygame.draw.circle(screen, self.color, (center_x, center_y), self.size // 2)
        pygame.draw.circle(screen, WHITE, (center_x, center_y), self.size // 2, 2)

class Game:
    def __init__(self, screen, settings=None):
        self.screen = screen
        self.settings = settings or {'volume': 100, 'difficulty': 'Normal'}
        self.state = GameState.PLAYING
        
        # Área de juego (dejando espacio para UI)
        ui_height = 100
        self.game_area = {
            'x': 50,
            'y': ui_height,
            'width': WINDOW_WIDTH - 100,
            'height': WINDOW_HEIGHT - ui_height - 50
        }
        
        # Inicializar jugador en el borde izquierdo
        start_x = self.game_area['x']
        start_y = self.game_area['y'] + self.game_area['height'] // 2
        self.player = Player(start_x, start_y)
        
        # Inicializar enemigos según dificultad
        self.enemies = self._create_enemies()
        
        # Variables del juego
        self.score = 0
        self.lives = INITIAL_LIVES
        self.level = 1
        self.area_revealed = 0
        self.target_area = TARGET_AREA_PERCENTAGE
        
        # UI
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Efectos visuales
        self.particles = []
    
    def _create_enemies(self):
        """Crea enemigos según la dificultad"""
        enemies = []
        difficulty = self.settings['difficulty']
        
        if difficulty == "Fácil":
            count = 2
            types = ["bouncer", "bouncer"]
        elif difficulty == "Normal":
            count = 3
            types = ["bouncer", "bouncer", "fast"]
        elif difficulty == "Difícil":
            count = 4
            types = ["bouncer", "fast", "hunter", "bouncer"]
        else:  # Extremo
            count = 5
            types = ["bouncer", "fast", "hunter", "hunter", "fast"]
        
        for i in range(count):
            # Posición aleatoria dentro del área de juego
            x = random.randint(
                self.game_area['x'] + 100,
                self.game_area['x'] + self.game_area['width'] - 100
            )
            y = random.randint(
                self.game_area['y'] + 100,
                self.game_area['y'] + self.game_area['height'] - 100
            )
            
            enemy_type = types[i % len(types)]
            enemies.append(Enemy(x, y, enemy_type))
        
        return enemies
    
    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'menu'
            elif event.key == pygame.K_p:
                self.state = GameState.PAUSED if self.state == GameState.PLAYING else GameState.PLAYING
            elif event.key == pygame.K_r and self.state == GameState.GAME_OVER:
                self._restart_game()
        
        return None
    
    def update(self):
        if self.state != GameState.PLAYING:
            return
        
        keys = pygame.key.get_pressed()
        
        # Actualizar jugador
        self.player.update(keys, self.game_area)
        
        # Actualizar enemigos
        for enemy in self.enemies:
            enemy.update(self.game_area, self.player)
        
        # Verificar colisiones
        self._check_collisions()
        
        # Verificar condiciones de victoria/derrota
        if self.area_revealed >= self.target_area:
            self.state = GameState.LEVEL_COMPLETE
        elif self.lives <= 0:
            self.state = GameState.GAME_OVER
    
    def _check_collisions(self):
        """Verifica colisiones entre jugador y enemigos"""
        player_rect = pygame.Rect(self.player.x, self.player.y, self.player.size, self.player.size)
        
        for enemy in self.enemies:
            if player_rect.colliderect(enemy.get_rect()):
                self._player_hit()
                break
        
        # Verificar colisiones con el trail si está cortando
        if self.player.cutting and self.player.trail:
            for enemy in self.enemies:
                enemy_center = (enemy.x + enemy.size//2, enemy.y + enemy.size//2)
                for i, trail_point in enumerate(self.player.trail[:-5]):  # No colisionar con puntos muy recientes
                    dist = math.sqrt(
                        (enemy_center[0] - trail_point[0])**2 + 
                        (enemy_center[1] - trail_point[1])**2
                    )
                    if dist < enemy.size:
                        self._player_hit()
                        return
    
    def _player_hit(self):
        """Maneja cuando el jugador es golpeado"""
        self.lives -= 1
        self.player.reset_cut()
        
        # Resetear posición del jugador al borde
        self.player.x = self.game_area['x']
        self.player.y = self.game_area['y'] + self.game_area['height'] // 2
        self.player.on_border = True
        
        # Crear efecto de partículas
        for _ in range(10):
            self.particles.append({
                'x': self.player.x,
                'y': self.player.y,
                'vx': random.uniform(-5, 5),
                'vy': random.uniform(-5, 5),
                'life': 30,
                'color': RED
            })
    
    def _restart_game(self):
        """Reinicia el juego"""
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = INITIAL_LIVES
        self.level = 1
        self.area_revealed = 0
        
        # Resetear jugador
        self.player.x = self.game_area['x']
        self.player.y = self.game_area['y'] + self.game_area['height'] // 2
        self.player.reset_cut()
        self.player.on_border = True
        
        # Recrear enemigos
        self.enemies = self._create_enemies()
        self.particles.clear()
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Dibujar área de juego
        pygame.draw.rect(self.screen, DARK_GRAY, 
                        (self.game_area['x'], self.game_area['y'], 
                         self.game_area['width'], self.game_area['height']))
        pygame.draw.rect(self.screen, WHITE,
                        (self.game_area['x'], self.game_area['y'],
                         self.game_area['width'], self.game_area['height']), 3)
        
        # Dibujar enemigos
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        # Dibujar jugador
        self.player.draw(self.screen)
        
        # Dibujar partículas
        for particle in self.particles[:]:
            pygame.draw.circle(self.screen, particle['color'],
                             (int(particle['x']), int(particle['y'])), 3)
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.particles.remove(particle)
        
        # Dibujar UI
        self._draw_ui()
        
        # Dibujar overlays según el estado
        if self.state == GameState.PAUSED:
            self._draw_pause_overlay()
        elif self.state == GameState.GAME_OVER:
            self._draw_game_over_overlay()
        elif self.state == GameState.LEVEL_COMPLETE:
            self._draw_level_complete_overlay()
    
    def _draw_ui(self):
        """Dibuja la interfaz de usuario"""
        # Fondo de la UI
        pygame.draw.rect(self.screen, BLACK, (0, 0, WINDOW_WIDTH, 80))
        pygame.draw.line(self.screen, WHITE, (0, 80), (WINDOW_WIDTH, 80), 2)
        
        # Información del juego
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        area_text = self.font.render(f"Area: {self.area_revealed:.1f}%", True, WHITE)
        
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(lives_text, (200, 20))
        self.screen.blit(level_text, (350, 20))
        self.screen.blit(area_text, (500, 20))
        
        # Barra de progreso
        progress_width = 200
        progress_x = WINDOW_WIDTH - progress_width - 20
        progress_y = 25
        
        pygame.draw.rect(self.screen, DARK_GRAY, 
                        (progress_x, progress_y, progress_width, 30))
        pygame.draw.rect(self.screen, GREEN,
                        (progress_x, progress_y, 
                         int(progress_width * self.area