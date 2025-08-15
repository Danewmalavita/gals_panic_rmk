import pygame
import math
import random
from enum import Enum
from .config import *

class GameState(Enum):
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    LEVEL_COMPLETE = 4

class AreaManager:
    """Gestiona las áreas cortadas y la revelación de la imagen"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Superficie para las áreas cortadas (True = cortado/revelado, False = cubierto)
        self.revealed_areas = [[False for _ in range(width)] for _ in range(height)]
        self.total_pixels = width * height
        self.revealed_pixels = 0
        
        # Superficie visual para mostrar lo cortado
        self.cut_surface = pygame.Surface((width, height))
        self.cut_surface.fill(DARK_GRAY)  # Color del área no cortada
        
    def is_point_inside_polygon(self, x, y, polygon_points):
        """Determina si un punto está dentro de un polígono usando ray casting"""
        if len(polygon_points) < 3:
            return False
            
        inside = False
        j = len(polygon_points) - 1
        
        for i in range(len(polygon_points)):
            xi, yi = polygon_points[i]
            xj, yj = polygon_points[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
            
        return inside
    
    def get_bounding_box(self, points):
        """Obtiene el rectángulo que contiene todos los puntos"""
        if not points:
            return 0, 0, 0, 0
            
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        return min_x, min_y, max_x, max_y
    
    def cut_area(self, trail_points):
        """Corta un área basada en el trail del jugador usando detección de polígono"""
        if len(trail_points) < 3:
            return 0
        
        # Simplificar el trail para evitar polígonos complejos
        simplified_trail = self.simplify_trail(trail_points)
        
        if len(simplified_trail) < 3:
            return 0
            
        # Obtener el bounding box para limitar la búsqueda
        min_x, min_y, max_x, max_y = self.get_bounding_box(simplified_trail)
        
        # Asegurar que el bounding box esté dentro de los límites
        min_x = max(0, min_x)
        min_y = max(0, min_y)
        max_x = min(self.width - 1, max_x)
        max_y = min(self.height - 1, max_y)
        
        pixels_cut = 0
        max_area = (max_x - min_x) * (max_y - min_y)
        
        # Evitar cortar áreas demasiado grandes
        if max_area > self.total_pixels * 0.5:
            return 0
        
        # Buscar píxeles dentro del polígono
        pixels_to_cut = []
        
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if (not self.revealed_areas[y][x] and 
                    self.is_point_inside_polygon(x, y, simplified_trail)):
                    pixels_to_cut.append((x, y))
        
        # Evitar cortar áreas demasiado grandes
        if len(pixels_to_cut) > self.total_pixels * 0.3:
            return 0
        
        # Cortar los píxeles
        for x, y in pixels_to_cut:
            self.revealed_areas[y][x] = True
            self.cut_surface.set_at((x, y), LIGHT_BLUE)
            pixels_cut += 1
        
        self.revealed_pixels += pixels_cut
        return pixels_cut
    
    def simplify_trail(self, points, tolerance=5):
        """Simplifica el trail eliminando puntos redundantes"""
        if len(points) <= 2:
            return points
        
        simplified = [points[0]]
        
        for i in range(1, len(points) - 1):
            # Calcular distancia al punto anterior
            prev_point = simplified[-1]
            curr_point = points[i]
            
            distance = math.sqrt(
                (curr_point[0] - prev_point[0])**2 + 
                (curr_point[1] - prev_point[1])**2
            )
            
            # Solo agregar si la distancia es mayor que la tolerancia
            if distance > tolerance:
                simplified.append(curr_point)
        
        # Siempre agregar el último punto
        simplified.append(points[-1])
        
        return simplified
    
    def get_revealed_percentage(self):
        """Devuelve el porcentaje de área revelada"""
        return (self.revealed_pixels / self.total_pixels) * 100
    
    def draw(self, screen, offset_x=0, offset_y=0):
        """Dibuja las áreas cortadas"""
        screen.blit(self.cut_surface, (offset_x, offset_y))

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = PLAYER_SIZE
        self.speed = PLAYER_SPEED
        self.trail = []
        self.cutting = False
        self.start_cut_pos = None
        self.on_border = True
        self.last_trail_update = 0
        
        # Para convertir coordenadas del área de juego a coordenadas de área
        self.area_offset_x = 0
        self.area_offset_y = 0
        
    def set_area_offset(self, offset_x, offset_y):
        """Establece el offset para convertir coordenadas"""
        self.area_offset_x = offset_x
        self.area_offset_y = offset_y
        
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
            border_threshold = 15
            on_border_now = (
                center_x <= game_area['x'] + border_threshold or 
                center_x >= game_area['x'] + game_area['width'] - border_threshold or
                center_y <= game_area['y'] + border_threshold or 
                center_y >= game_area['y'] + game_area['height'] - border_threshold
            )
            
            # Lógica de corte
            if self.on_border and not on_border_now:
                # Empezar corte
                self.cutting = True
                self.start_cut_pos = (center_x, center_y)
                self.trail = [(center_x - self.area_offset_x, center_y - self.area_offset_y)]
                self.last_trail_update = pygame.time.get_ticks()
                
            elif self.cutting:
                # Continuar corte - añadir punto convertido a coordenadas del área
                current_time = pygame.time.get_ticks()
                
                # Solo añadir puntos cada cierto tiempo para evitar trails muy densos
                if current_time - self.last_trail_update > 50:  # 50ms entre puntos
                    trail_x = center_x - self.area_offset_x
                    trail_y = center_y - self.area_offset_y
                    
                    # Verificar que el punto esté dentro del área válida
                    if (0 <= trail_x < game_area['width'] and 
                        0 <= trail_y < game_area['height']):
                        self.trail.append((trail_x, trail_y))
                        self.last_trail_update = current_time
                
                # Si regresa al borde, completar corte
                if on_border_now:
                    return self.complete_cut()
            
            self.on_border = on_border_now
            
            # Limitar tamaño del trail
            if len(self.trail) > TRAIL_MAX_LENGTH:
                self.trail = self.trail[-TRAIL_MAX_LENGTH:]
                
        return None
    
    def complete_cut(self):
        """Completa un corte y devuelve los puntos del trail"""
        if len(self.trail) > 3:  # Mínimo de puntos para hacer un corte válido
            trail_copy = self.trail.copy()
            self.cutting = False
            self.trail.clear()
            return trail_copy
        else:
            self.cutting = False
            self.trail.clear()
            return None
    
    def reset_cut(self):
        """Reinicia el corte actual"""
        self.cutting = False
        self.trail.clear()
        self.start_cut_pos = None
    
    def draw(self, screen):
        # Dibujar el trail de corte convertido de vuelta a coordenadas de pantalla
        if len(self.trail) > 1 and self.cutting:
            screen_trail = [(x + self.area_offset_x, y + self.area_offset_y) for x, y in self.trail]
            if len(screen_trail) > 1:
                pygame.draw.lines(screen, YELLOW, False, screen_trail, 3)
                
                # Línea punteada desde el último punto hasta el jugador
                if screen_trail:
                    last_pos = screen_trail[-1]
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
        self.trail_hunter = False
        
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
            self.x = max(game_area['x'], min(self.x, game_area['x'] + game_area['width'] - self.size))
        if (self.y <= game_area['y'] or 
            self.y >= game_area['y'] + game_area['height'] - self.size):
            self.direction_y *= -1
            self.y = max(game_area['y'], min(self.y, game_area['y'] + game_area['height'] - self.size))
    
    def _hunter_behavior(self, game_area, player):
        """Comportamiento de caza hacia el jugador o su trail"""
        target_x, target_y = player.x, player.y
        
        # Si el jugador está cortando, perseguir su trail
        if player.cutting and player.trail:
            min_dist = float('inf')
            for trail_point in player.trail[-10:]:  # Solo los últimos 10 puntos
                # Convertir coordenadas del trail de vuelta a coordenadas de pantalla
                trail_screen_x = trail_point[0] + player.area_offset_x
                trail_screen_y = trail_point[1] + player.area_offset_y
                dist = math.sqrt((self.x - trail_screen_x)**2 + (self.y - trail_screen_y)**2)
                if dist < min_dist:
                    min_dist = dist
                    target_x, target_y = trail_screen_x - self.size//2, trail_screen_y - self.size//2
        
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
        
        # Inicializar sistema de áreas cortadas
        self.area_manager = AreaManager(self.game_area['width'], self.game_area['height'])
        
        # Inicializar jugador en el borde izquierdo
        start_x = self.game_area['x']
        start_y = self.game_area['y'] + self.game_area['height'] // 2
        self.player = Player(start_x, start_y)
        self.player.set_area_offset(self.game_area['x'], self.game_area['y'])
        
        # Inicializar enemigos según dificultad
        self.enemies = self._create_enemies()
        
        # Variables del juego
        self.score = 0
        self.lives = INITIAL_LIVES
        self.level = 1
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
            elif event.key == pygame.K_SPACE and self.state == GameState.LEVEL_COMPLETE:
                self._next_level()
        
        return None
    
    def update(self):
        if self.state != GameState.PLAYING:
            return
        
        keys = pygame.key.get_pressed()
        
        # Actualizar jugador y obtener trail si completa corte
        completed_trail = self.player.update(keys, self.game_area)
        if completed_trail:
            # Procesar el corte
            pixels_cut = self.area_manager.cut_area(completed_trail)
            if pixels_cut > 0:
                points_earned = pixels_cut * POINTS_PER_AREA
                self.score += points_earned
                print(f"¡Área cortada! +{points_earned} puntos ({pixels_cut} píxeles)")
        
        # Actualizar enemigos
        for enemy in self.enemies:
            enemy.update(self.game_area, self.player)
        
        # Verificar colisiones
        self._check_collisions()
        
        # Verificar condiciones de victoria/derrota
        area_revealed = self.area_manager.get_revealed_percentage()
        if area_revealed >= self.target_area:
            self.state = GameState.LEVEL_COMPLETE
            self.score += self.lives * 1000  # Bonus por vidas restantes
        elif self.lives <= 0:
            self.state = GameState.GAME_OVER

    def _check_collisions(self):
        """Verifica colisiones entre jugador y enemigos"""
        player_rect = pygame.Rect(self.player.x, self.player.y, self.player.size, self.player.size)
        
        for enemy in self.enemies:
            if player_rect.colliderect(enemy.get_rect()):
                self._player_hit()
                return
        
        # Verificar colisiones con el trail si está cortando
        if self.player.cutting and len(self.player.trail) > 5:
            for enemy in self.enemies:
                enemy_center = (enemy.x + enemy.size//2, enemy.y + enemy.size//2)
                # Solo verificar contra puntos del trail que no sean muy recientes
                trail_to_check = self.player.trail[:-5]  # Excluir los últimos 5 puntos
                
                for trail_point in trail_to_check:
                    # Convertir coordenadas del trail de vuelta a coordenadas de pantalla
                    trail_screen_x = trail_point[0] + self.player.area_offset_x
                    trail_screen_y = trail_point[1] + self.player.area_offset_y
                    
                    dist = math.sqrt(
                        (enemy_center[0] - trail_screen_x)**2 + 
                        (enemy_center[1] - trail_screen_y)**2
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
        
        print(f"¡Golpeado! Vidas restantes: {self.lives}")
    
    def _next_level(self):
        """Avanza al siguiente nivel"""
        self.level += 1
        self.state = GameState.PLAYING
        
        # Reinicializar el sistema de áreas
        self.area_manager = AreaManager(self.game_area['width'], self.game_area['height'])
        
        # Resetear jugador
        self.player.x = self.game_area['x']
        self.player.y = self.game_area['y'] + self.game_area['height'] // 2
        self.player.reset_cut()
        self.player.on_border = True
        
        # Incrementar dificultad
        self.enemies = self._create_enemies()
        for enemy in self.enemies:
            enemy.speed *= (1 + self.level * 0.1)  # Incrementar velocidad
        
        # Añadir un enemigo extra cada 3 niveles
        if self.level % 3 == 0:
            new_enemy_x = random.randint(
                self.game_area['x'] + 100,
                self.game_area['x'] + self.game_area['width'] - 100
            )
            new_enemy_y = random.randint(
                self.game_area['y'] + 100,
                self.game_area['y'] + self.game_area['height'] - 100
            )
            self.enemies.append(Enemy(new_enemy_x, new_enemy_y, "hunter"))
        
        self.particles.clear()
        print(f"¡Nivel {self.level}! Dificultad incrementada.")
    
    def _restart_game(self):
        """Reinicia el juego"""
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = INITIAL_LIVES
        self.level = 1
        
        # Reinicializar el sistema de áreas
        self.area_manager = AreaManager(self.game_area['width'], self.game_area['height'])
        
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
        
        # Dibujar área de juego con fondo
        pygame.draw.rect(self.screen, WHITE, 
                        (self.game_area['x'], self.game_area['y'], 
                         self.game_area['width'], self.game_area['height']))
        
        # Dibujar las áreas cortadas encima
        self.area_manager.draw(self.screen, self.game_area['x'], self.game_area['y'])
        
        # Dibujar borde del área de juego
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
        
        # Obtener porcentaje actual de área revelada
        current_area = self.area_manager.get_revealed_percentage()
        area_text = self.font.render(f"Area: {current_area:.1f}%", True, WHITE)
        
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
                         int(progress_width * current_area / self.target_area), 30))
        pygame.draw.rect(self.screen, WHITE,
                        (progress_x, progress_y, progress_width, 30), 2)
        
        # Texto de objetivo
        target_text = self.small_font.render(f"Target: {self.target_area}%", True, WHITE)
        self.screen.blit(target_text, (progress_x, progress_y + 35))
    
    def _draw_pause_overlay(self):
        """Dibuja el overlay de pausa"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        pause_font = pygame.font.Font(None, 72)
        pause_text = pause_font.render("PAUSED", True, YELLOW)
        pause_rect = pause_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
        self.screen.blit(pause_text, pause_rect)
        
        info_text = self.font.render("Press P to continue", True, WHITE)
        info_rect = info_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 80))
        self.screen.blit(info_text, info_rect)
    
    def _draw_game_over_overlay(self):
        """Dibuja el overlay de game over"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_font = pygame.font.Font(None, 72)
        game_over_text = game_over_font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50))
        self.screen.blit(game_over_text, game_over_rect)
        
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 20))
        self.screen.blit(score_text, score_rect)
        
        restart_text = self.font.render("Press R to restart or ESC for menu", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 70))
        self.screen.blit(restart_text, restart_rect)
    
    def _draw_level_complete_overlay(self):
        """Dibuja el overlay de nivel completado"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        complete_font = pygame.font.Font(None, 72)
        complete_text = complete_font.render("LEVEL COMPLETE!", True, GREEN)
        complete_rect = complete_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50))
        self.screen.blit(complete_text, complete_rect)
        
        bonus_text = self.font.render(f"Bonus: {self.lives * 1000} points", True, YELLOW)
        bonus_rect = bonus_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 20))
        self.screen.blit(bonus_text, bonus_rect)
        
        continue_text = self.font.render("Press SPACE to continue", True, WHITE)
        continue_rect = continue_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 70))
        self.screen.blit(continue_text, continue_rect)
    
    def get_state(self):
        """Devuelve el estado actual del juego"""
        return self.state
    
    def is_running(self):
        """Verifica si el juego está corriendo"""
        return self.state in [GameState.PLAYING, GameState.PAUSED]