# game.py - Sistema de recorte mejorado para Gals Panic

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
    """Gestiona las áreas cortadas y la reducción del área de juego"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Grid que representa el área de juego (True = área válida, False = cortada/bloqueada)
        self.playable_area = [[True for _ in range(width)] for _ in range(height)]
        self.total_pixels = width * height
        self.cut_pixels = 0
        
        # Superficie visual para mostrar el estado del área
        self.area_surface = pygame.Surface((width, height))
        self.area_surface.fill(WHITE)  # Blanco = área de juego
        
        # Marcar bordes como límites (no cortables pero válidos para caminar)
        self.border_thickness = 2
        for y in range(self.height):
            for x in range(self.width):
                if (x < self.border_thickness or x >= self.width - self.border_thickness or 
                    y < self.border_thickness or y >= self.height - self.border_thickness):
                    pass  # Los bordes siguen siendo válidos para caminar
        
    def is_point_inside_polygon(self, x, y, polygon_points):
        """Determina si un punto está dentro de un polígono usando ray casting mejorado"""
        if len(polygon_points) < 3:
            return False
        
        # Agregar pequeña perturbación para evitar casos edge
        x += 0.001
        y += 0.001
        
        inside = False
        j = len(polygon_points) - 1
        
        for i in range(len(polygon_points)):
            xi, yi = polygon_points[i]
            xj, yj = polygon_points[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        
        return inside
    
    def flood_fill_area(self, start_x, start_y, area_grid):
        """Encuentra el área conectada usando flood fill iterativo optimizado"""
        if (not (0 <= start_x < self.width and 0 <= start_y < self.height) or
            not area_grid[start_y][start_x]):
            return []
        
        area_pixels = []
        visited = set()
        stack = [(start_x, start_y)]
        
        while stack:
            x, y = stack.pop()
            
            if (x, y) in visited or x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue
                
            if not area_grid[y][x]:
                continue
                
            visited.add((x, y))
            area_pixels.append((x, y))
            
            # Añadir píxeles adyacentes (4-conectividad)
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited:
                    stack.append((nx, ny))
        
        return area_pixels
    
    def find_all_connected_areas(self, area_grid):
        """Encuentra todas las áreas conectadas separadas"""
        visited = set()
        areas = []
        
        for y in range(self.height):
            for x in range(self.width):
                if area_grid[y][x] and (x, y) not in visited:
                    area_pixels = self.flood_fill_area(x, y, area_grid)
                    if area_pixels:
                        areas.append(area_pixels)
                        visited.update(area_pixels)
        
        return areas
    
    def area_contains_border(self, area_pixels):
        """Verifica si un área toca cualquier borde del área de juego"""
        border_margin = 3  # Margen más amplio para detectar bordes
        
        for x, y in area_pixels:
            if (x <= border_margin or x >= self.width - border_margin - 1 or 
                y <= border_margin or y >= self.height - border_margin - 1):
                return True
        return False
    
    def area_contains_enemies(self, area_pixels, enemies):
        """Verifica si un área contiene enemigos"""
        area_set = set(area_pixels)
        
        for enemy in enemies:
            enemy_area_x, enemy_area_y = enemy.get_area_position()
            
            # Verificar un área 3x3 alrededor del enemigo para mayor precisión
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    check_x = enemy_area_x + dx
                    check_y = enemy_area_y + dy
                    
                    if (check_x, check_y) in area_set:
                        return True
        
        return False
    
    def get_polygon_bounding_box(self, polygon_points):
        """Obtiene la caja delimitadora de un polígono con márgenes"""
        if not polygon_points:
            return 0, 0, self.width, self.height
        
        min_x = max(0, min(p[0] for p in polygon_points) - 1)
        max_x = min(self.width - 1, max(p[0] for p in polygon_points) + 1)
        min_y = max(0, min(p[1] for p in polygon_points) - 1)
        max_y = min(self.height - 1, max(p[1] for p in polygon_points) + 1)
        
        return int(min_x), int(min_y), int(max_x), int(max_y)
    
    def cut_area_with_trail(self, trail_points, enemies):
        """Corta el área usando el trail del jugador - Versión mejorada"""
        if len(trail_points) < 4:  # Necesitamos al menos 4 puntos para un polígono válido
            print("Trail muy corto para formar un polígono válido")
            return 0
        
        print(f"Iniciando corte con {len(trail_points)} puntos del trail")
        
        # Limpiar y validar el trail
        valid_trail = []
        for point in trail_points:
            x, y = int(point[0]), int(point[1])
            if 0 <= x < self.width and 0 <= y < self.height:
                valid_trail.append((x, y))
        
        if len(valid_trail) < 4:
            print("No hay suficientes puntos válidos en el trail")
            return 0
        
        # Cerrar el polígono si es necesario
        if valid_trail[0] != valid_trail[-1]:
            # Encontrar el punto de borde más cercano al último punto
            last_point = valid_trail[-1]
            closest_border = self._find_closest_border_point(last_point)
            if closest_border:
                valid_trail.append(closest_border)
        
        print(f"Trail válido con {len(valid_trail)} puntos")
        
        # Crear copia del área actual
        temp_area = [row[:] for row in self.playable_area]
        
        # Obtener bounding box para optimizar el procesamiento
        min_x, min_y, max_x, max_y = self.get_polygon_bounding_box(valid_trail)
        
        # Marcar píxeles dentro del polígono
        enclosed_pixels = []
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if temp_area[y][x] and self.is_point_inside_polygon(x, y, valid_trail):
                    enclosed_pixels.append((x, y))
                    temp_area[y][x] = False  # Marcar como cortado temporalmente
        
        print(f"Píxeles encerrados: {len(enclosed_pixels)}")
        
        if len(enclosed_pixels) < 10:  # Área mínima para ser válida
            print("Área encerrada demasiado pequeña")
            return 0
        
        # Encontrar todas las áreas conectadas después del corte simulado
        connected_areas = self.find_all_connected_areas(temp_area)
        print(f"Áreas conectadas después del corte: {len(connected_areas)}")
        
        # Determinar qué área eliminar según la lógica del Gals Panic
        area_to_remove = None
        
        # Verificar si el área encerrada contiene enemigos
        enclosed_has_enemies = self.area_contains_enemies(enclosed_pixels, enemies)
        print(f"Área encerrada contiene enemigos: {enclosed_has_enemies}")
        
        if not enclosed_has_enemies:
            # El área encerrada no contiene enemigos -> eliminarla
            area_to_remove = enclosed_pixels
            print("Eliminando área encerrada (sin enemigos)")
        else:
            # El área encerrada contiene enemigos -> eliminar otra área
            # Buscar la menor área que no toque bordes y no contenga enemigos
            best_area = None
            best_size = float('inf')
            
            for area in connected_areas:
                if (not self.area_contains_border(area) and 
                    not self.area_contains_enemies(area, enemies) and
                    len(area) < best_size and
                    len(area) >= 10):  # Tamaño mínimo
                    best_area = area
                    best_size = len(area)
            
            if best_area:
                area_to_remove = best_area
                print(f"Eliminando área sin enemigos ni bordes ({len(best_area)} píxeles)")
            else:
                print("No se encontró área válida para eliminar")
                return 0
        
        # Aplicar el corte real
        if area_to_remove:
            pixels_removed = self._apply_cut(area_to_remove)
            print(f"¡Área cortada! {pixels_removed} píxeles eliminados")
            return pixels_removed
        
        return 0
    
    def _apply_cut(self, pixels_to_remove):
        """Aplica el corte eliminando los píxeles especificados"""
        pixels_removed = 0
        
        for x, y in pixels_to_remove:
            if (0 <= x < self.width and 0 <= y < self.height and 
                self.playable_area[y][x]):
                self.playable_area[y][x] = False
                self.area_surface.set_at((x, y), LIGHT_BLUE)
                pixels_removed += 1
        
        self.cut_pixels += pixels_removed
        return pixels_removed
    
    def _find_closest_border_point(self, point):
        """Encuentra el punto de borde más cercano"""
        x, y = point
        
        # Distancias a cada borde
        dist_left = x
        dist_right = self.width - 1 - x
        dist_top = y
        dist_bottom = self.height - 1 - y
        
        min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
        
        if min_dist == dist_left:
            return (0, y)
        elif min_dist == dist_right:
            return (self.width - 1, y)
        elif min_dist == dist_top:
            return (x, 0)
        else:
            return (x, self.height - 1)
    
    def is_position_valid(self, x, y):
        """Verifica si una posición está en el área de juego válida"""
        x, y = int(x), int(y)
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.playable_area[y][x]
    
    def get_safe_spawn_position(self, margin=50):
        """Obtiene una posición segura para spawn de objetos"""
        # Buscar área válida en el centro
        center_x, center_y = self.width // 2, self.height // 2
        
        for radius in range(0, min(self.width, self.height) // 2, 10):
            for angle in range(0, 360, 30):
                x = int(center_x + radius * math.cos(math.radians(angle)))
                y = int(center_y + radius * math.sin(math.radians(angle)))
                
                if (margin <= x < self.width - margin and 
                    margin <= y < self.height - margin and
                    self.is_position_valid(x, y)):
                    return x, y
        
        # Fallback: centro del área si no se encuentra otra posición
        if self.is_position_valid(center_x, center_y):
            return center_x, center_y
        
        # Último recurso: buscar cualquier posición válida
        for y in range(margin, self.height - margin):
            for x in range(margin, self.width - margin):
                if self.is_position_valid(x, y):
                    return x, y
        
        return self.width // 2, self.height // 2  # Posición por defecto
    
    def get_cut_percentage(self):
        """Devuelve el porcentaje de área cortada"""
        return (self.cut_pixels / self.total_pixels) * 100
    
    def draw(self, screen, offset_x=0, offset_y=0):
        """Dibuja el área de juego"""
        screen.blit(self.area_surface, (offset_x, offset_y))

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
        self.invulnerable_time = 0
        self.min_trail_distance = 3  # Distancia mínima entre puntos del trail
        
        # Para convertir coordenadas
        self.area_offset_x = 0
        self.area_offset_y = 0
        
    def set_area_offset(self, offset_x, offset_y):
        """Establece el offset para convertir coordenadas"""
        self.area_offset_x = offset_x
        self.area_offset_y = offset_y
        
    def update(self, keys, game_area, area_manager):
        # Actualizar tiempo de invulnerabilidad
        if self.invulnerable_time > 0:
            self.invulnerable_time -= 1
        
        old_x, old_y = self.x, self.y
        new_x, new_y = self.x, self.y
        
        # Calcular nueva posición
        if keys[pygame.K_LEFT]:
            new_x -= self.speed
        if keys[pygame.K_RIGHT]:
            new_x += self.speed
        if keys[pygame.K_UP]:
            new_y -= self.speed
        if keys[pygame.K_DOWN]:
            new_y += self.speed
        
        # Verificar límites del área de pantalla
        new_x = max(game_area['x'], min(new_x, game_area['x'] + game_area['width'] - self.size))
        new_y = max(game_area['y'], min(new_y, game_area['y'] + game_area['height'] - self.size))
        
        # Convertir a coordenadas del área manager
        area_x = int(new_x + self.size // 2 - self.area_offset_x)
        area_y = int(new_y + self.size // 2 - self.area_offset_y)
        
        # Solo moverse si la nueva posición es válida
        if area_manager.is_position_valid(area_x, area_y):
            self.x, self.y = new_x, new_y
        else:
            # Si no puede moverse, cancelar el corte actual
            if self.cutting:
                print("Posición inválida durante corte - cancelando")
                self.reset_cut()
        
        # Verificar movimiento
        moving = old_x != self.x or old_y != self.y
        
        if moving:
            center_x = self.x + self.size // 2
            center_y = self.y + self.size // 2
            area_center_x = int(center_x - self.area_offset_x)
            area_center_y = int(center_y - self.area_offset_y)
            
            on_border_now = self.is_on_border(area_center_x, area_center_y, area_manager)
            
            # Lógica de corte mejorada
            if self.on_border and not on_border_now:
                # Empezar corte desde el borde
                self.cutting = True
                self.start_cut_pos = (area_center_x, area_center_y)
                self.trail = [(area_center_x, area_center_y)]
                self.last_trail_update = pygame.time.get_ticks()
                print(f"Iniciando corte desde ({area_center_x}, {area_center_y})")
                
            elif self.cutting:
                # Continuar corte
                current_time = pygame.time.get_ticks()
                
                # Añadir punto al trail si ha pasado suficiente tiempo y distancia
                if current_time - self.last_trail_update > 20:  # 20ms entre puntos
                    trail_x, trail_y = int(area_center_x), int(area_center_y)
                    
                    # Verificar distancia mínima desde el último punto
                    if (not self.trail or 
                        math.sqrt((trail_x - self.trail[-1][0])**2 + 
                                 (trail_y - self.trail[-1][1])**2) >= self.min_trail_distance):
                        self.trail.append((trail_x, trail_y))
                        self.last_trail_update = current_time
                
                # Completar corte si regresa al borde
                if on_border_now and len(self.trail) >= 4:
                    print(f"Completando corte con {len(self.trail)} puntos")
                    completed_trail = self.complete_cut()
                    if completed_trail:
                        self.on_border = on_border_now
                        return completed_trail
            
            self.on_border = on_border_now
            
        return None
    
    def is_on_border(self, x, y, area_manager):
        """Verifica si el jugador está en el borde del área válida"""
        x, y = int(x), int(y)
        border_threshold = 8  # Umbral más amplio para facilitar el juego
        
        # Verificar bordes del área de juego
        if (x <= border_threshold or x >= area_manager.width - border_threshold - 1 or 
            y <= border_threshold or y >= area_manager.height - border_threshold - 1):
            return True
        
        # Verificar proximidad a áreas cortadas
        for dx in range(-border_threshold, border_threshold + 1):
            for dy in range(-border_threshold, border_threshold + 1):
                check_x = x + dx
                check_y = y + dy
                
                if (0 <= check_x < area_manager.width and 
                    0 <= check_y < area_manager.height):
                    if not area_manager.is_position_valid(check_x, check_y):
                        return True
        
        return False
    
    def complete_cut(self):
        """Completa un corte y devuelve los puntos del trail"""
        if len(self.trail) < 4:
            print(f"Trail muy corto: {len(self.trail)} puntos")
            self.reset_cut()
            return None
        
        # Crear una copia del trail para el corte
        trail_copy = self.trail.copy()
        
        # Asegurar que el polígono esté cerrado conectando al borde más cercano
        last_point = trail_copy[-1]
        border_point = self._find_closest_border_point(last_point)
        
        if border_point and border_point != last_point:
            trail_copy.append(border_point)
        
        print(f"Trail completado con {len(trail_copy)} puntos")
        self.reset_cut()
        return trail_copy
    
    def _find_closest_border_point(self, point):
        """Encuentra el punto de borde más cercano"""
        x, y = point
        
        # Usar las dimensiones del área manager desde el offset
        width = 1180  # game_area width
        height = 570  # game_area height
        
        distances = {
            'left': x,
            'right': width - 1 - x,
            'top': y,
            'bottom': height - 1 - y
        }
        
        closest_border = min(distances, key=distances.get)
        
        if closest_border == 'left':
            return (0, y)
        elif closest_border == 'right':
            return (width - 1, y)
        elif closest_border == 'top':
            return (x, 0)
        elif closest_border == 'bottom':
            return (x, height - 1)
        
        return point
    
    def reset_cut(self):
        """Reinicia el corte actual"""
        self.cutting = False
        self.trail.clear()
        self.start_cut_pos = None
    
    def hit(self):
        """Maneja cuando el jugador es golpeado"""
        self.invulnerable_time = 120  # 2 segundos a 60 FPS
        self.reset_cut()
    
    def is_invulnerable(self):
        """Verifica si el jugador está en período de invulnerabilidad"""
        return self.invulnerable_time > 0
    
    def draw(self, screen):
        # Dibujar el trail de corte
        if len(self.trail) > 1 and self.cutting:
            screen_trail = [(x + self.area_offset_x, y + self.area_offset_y) for x, y in self.trail]
            if len(screen_trail) > 1:
                pygame.draw.lines(screen, YELLOW, False, screen_trail, 3)
                
                # Línea desde el último punto hasta el jugador
                if screen_trail:
                    last_pos = screen_trail[-1]
                    current_pos = (self.x + self.size // 2, self.y + self.size // 2)
                    pygame.draw.line(screen, ORANGE, last_pos, current_pos, 2)
        
        # Dibujar el jugador
        color = GREEN if self.on_border else BLUE
        
        # Parpadear si está invulnerable
        if self.is_invulnerable() and (self.invulnerable_time // 5) % 2 == 0:
            color = (color[0] // 2, color[1] // 2, color[2] // 2)
        
        pygame.draw.rect(screen, color, (self.x, self.y, self.size, self.size))
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.size, self.size), 2)
        
        # Indicador de corte
        if self.cutting:
            if (pygame.time.get_ticks() // 200) % 2 == 0:
                pygame.draw.circle(screen, YELLOW, 
                                 (self.x + self.size//2, self.y - 10), 3)

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
        self.stuck_counter = 0  # Contador para detectar si está atascado
        self.last_position = (x, y)
        
        # Offsets del área de juego
        self.game_area_offset_x = 50
        self.game_area_offset_y = 100
        
        if enemy_type == "hunter":
            self.color = PURPLE
            self.speed *= 0.8
            self.trail_hunter = True
        elif enemy_type == "fast":
            self.color = ORANGE
            self.speed *= 1.5
    
    def get_area_position(self):
        """Devuelve la posición del enemigo en coordenadas del área manager"""
        area_x = int(self.x + self.size // 2 - self.game_area_offset_x)
        area_y = int(self.y + self.size // 2 - self.game_area_offset_y)
        return area_x, area_y
        
    def update(self, game_area, area_manager, player=None):
        # Verificar si está atascado
        current_pos = (self.x, self.y)
        if abs(current_pos[0] - self.last_position[0]) < 1 and abs(current_pos[1] - self.last_position[1]) < 1:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        
        # Si está atascado, reubicarlo
        if self.stuck_counter > 60:  # 1 segundo a 60 FPS
            self._relocate_if_stuck(game_area, area_manager)
            self.stuck_counter = 0
        
        self.last_position = current_pos
        
        if self.type == "bouncer":
            self._bouncer_behavior(game_area, area_manager)
        elif self.type == "hunter" and player:
            self._hunter_behavior(game_area, area_manager, player)
        elif self.type == "fast":
            self._bouncer_behavior(game_area, area_manager)
    
    def _relocate_if_stuck(self, game_area, area_manager):
        """Reubica el enemigo si está atascado"""
        area_x, area_y = area_manager.get_safe_spawn_position()
        self.x = area_x + self.game_area_offset_x - self.size // 2
        self.y = area_y + self.game_area_offset_y - self.size // 2
        
        # Cambiar dirección aleatoriamente
        self.direction_x = random.choice([-1, 1])
        self.direction_y = random.choice([-1, 1])
        print(f"Enemigo reubicado a ({self.x}, {self.y})")
    
    def _bouncer_behavior(self, game_area, area_manager):
        """Comportamiento básico de rebote mejorado"""
        # Calcular nueva posición
        new_x = self.x + self.speed * self.direction_x
        new_y = self.y + self.speed * self.direction_y
        
        # Verificar límites de pantalla primero
        hit_wall_x = False
        hit_wall_y = False
        
        if (new_x <= game_area['x'] or 
            new_x >= game_area['x'] + game_area['width'] - self.size):
            hit_wall_x = True
        
        if (new_y <= game_area['y'] or 
            new_y >= game_area['y'] + game_area['height'] - self.size):
            hit_wall_y = True
        
        # Verificar áreas cortadas
        if not hit_wall_x and not hit_wall_y:
            # Verificar múltiples puntos del enemigo
            test_positions = [
                (new_x + 2, new_y + 2),  # esquina superior izquierda
                (new_x + self.size - 2, new_y + 2),  # esquina superior derecha
                (new_x + 2, new_y + self.size - 2),  # esquina inferior izquierda
                (new_x + self.size - 2, new_y + self.size - 2),  # esquina inferior derecha
                (new_x + self.size // 2, new_y + self.size // 2)  # centro
            ]
            
            for test_x, test_y in test_positions:
                area_x = int(test_x - self.game_area_offset_x)
                area_y = int(test_y - self.game_area_offset_y)
                
                if (0 <= area_x < area_manager.width and 0 <= area_y < area_manager.height):
                    if not area_manager.is_position_valid(area_x, area_y):
                        # Determinar qué dirección bloquear basándose en la posición del obstáculo
                        if abs(test_x - (self.x + self.size // 2)) > abs(test_y - (self.y + self.size // 2)):
                            hit_wall_x = True
                        else:
                            hit_wall_y = True
                        break
        
        # Aplicar movimiento y rebotes
        if hit_wall_x:
            self.direction_x *= -1
            # Añadir pequeña variación aleatoria para evitar patrones repetitivos
            self.direction_x += random.uniform(-0.1, 0.1)
        else:
            self.x = new_x
            
        if hit_wall_y:
            self.direction_y *= -1
            # Añadir pequeña variación aleatoria
            self.direction_y += random.uniform(-0.1, 0.1)
        else:
            self.y = new_y
        
        # Normalizar direcciones para mantener velocidad constante
        direction_magnitude = math.sqrt(self.direction_x**2 + self.direction_y**2)
        if direction_magnitude > 0:
            self.direction_x /= direction_magnitude
            self.direction_y /= direction_magnitude
        
        # Mantener dentro de los límites
        self.x = max(game_area['x'], min(self.x, game_area['x'] + game_area['width'] - self.size))
        self.y = max(game_area['y'], min(self.y, game_area['y'] + game_area['height'] - self.size))
    
    def _hunter_behavior(self, game_area, area_manager, player):
        """Comportamiento de caza hacia el jugador mejorado"""
        target_x, target_y = player.x, player.y
        
        # Si el jugador está cortando, perseguir su trail
        if player.cutting and player.trail and len(player.trail) > 3:
            min_dist = float('inf')
            for trail_point in player.trail[-5:]:  # Últimos 5 puntos
                trail_screen_x = trail_point[0] + player.area_offset_x
                trail_screen_y = trail_point[1] + player.area_offset_y
                dist = math.sqrt((self.x - trail_screen_x)**2 + (self.y - trail_screen_y)**2)
                if dist < min_dist:
                    min_dist = dist
                    target_x, target_y = trail_screen_x - self.size//2, trail_screen_y - self.size//2
        
        # Calcular dirección hacia el objetivo
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 5:  # Solo moverse si no está muy cerca
            # Normalizar dirección
            if dist > 0:
                dx /= dist
                dy /= dist
            
            # Calcular nueva posición
            new_x = self.x + dx * self.speed
            new_y = self.y + dy * self.speed
            
            # Verificar si la nueva posición es válida
            valid_move = True
            test_positions = [
                (new_x + self.size // 2, new_y + self.size // 2),  # centro
                (new_x + 2, new_y + 2),  # esquinas
                (new_x + self.size - 2, new_y + self.size - 2)
            ]
            
            for test_x, test_y in test_positions:
                if (test_x < game_area['x'] or test_x >= game_area['x'] + game_area['width'] or
                    test_y < game_area['y'] or test_y >= game_area['y'] + game_area['height']):
                    valid_move = False
                    break
                
                area_x = int(test_x - self.game_area_offset_x)
                area_y = int(test_y - self.game_area_offset_y)
                
                if (0 <= area_x < area_manager.width and 
                    0 <= area_y < area_manager.height):
                    if not area_manager.is_position_valid(area_x, area_y):
                        valid_move = False
                        break
            
            if valid_move:
                self.x = new_x
                self.y = new_y
            else:
                # Si no puede moverse directamente, intentar movimiento alternativo
                # Probar movimiento solo en X o solo en Y
                alt_x = self.x + dx * self.speed
                alt_y = self.y
                
                area_x = int(alt_x + self.size // 2 - self.game_area_offset_x)
                area_y = int(alt_y + self.size // 2 - self.game_area_offset_y)
                
                if (game_area['x'] <= alt_x <= game_area['x'] + game_area['width'] - self.size and
                    0 <= area_x < area_manager.width and 0 <= area_y < area_manager.height and
                    area_manager.is_position_valid(area_x, area_y)):
                    self.x = alt_x
                else:
                    # Probar solo movimiento en Y
                    alt_x = self.x
                    alt_y = self.y + dy * self.speed
                    
                    area_x = int(alt_x + self.size // 2 - self.game_area_offset_x)
                    area_y = int(alt_y + self.size // 2 - self.game_area_offset_y)
                    
                    if (game_area['y'] <= alt_y <= game_area['y'] + game_area['height'] - self.size and
                        0 <= area_x < area_manager.width and 0 <= area_y < area_manager.height and
                        area_manager.is_position_valid(area_x, area_y)):
                        self.y = alt_y
        
        # Mantener dentro de los límites
        self.x = max(game_area['x'], min(self.x, game_area['x'] + game_area['width'] - self.size))
        self.y = max(game_area['y'], min(self.y, game_area['y'] + game_area['height'] - self.size))
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)
    
    def draw(self, screen):
        center_x = int(self.x + self.size // 2)
        center_y = int(self.y + self.size // 2)
        pygame.draw.circle(screen, self.color, (center_x, center_y), self.size // 2)
        pygame.draw.circle(screen, WHITE, (center_x, center_y), self.size // 2, 2)
        
        # Indicador visual para enemigos atascados
        if self.stuck_counter > 30:
            pygame.draw.circle(screen, YELLOW, (center_x, center_y - 15), 3)

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
        
        # Inicializar sistema de áreas
        self.area_manager = AreaManager(self.game_area['width'], self.game_area['height'])
        
        # Inicializar jugador en el borde
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
        
        # Variables de debug
        self.debug_mode = False
    
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
            # Usar el sistema de spawn seguro del área manager
            area_x, area_y = self.area_manager.get_safe_spawn_position()
            
            # Convertir a coordenadas de pantalla
            screen_x = area_x + self.game_area['x'] - ENEMY_SIZE // 2
            screen_y = area_y + self.game_area['y'] - ENEMY_SIZE // 2
            
            enemy_type = types[i % len(types)]
            enemy = Enemy(screen_x, screen_y, enemy_type)
            enemies.append(enemy)
            
            print(f"Enemigo {enemy_type} creado en ({screen_x}, {screen_y})")
        
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
            elif event.key == pygame.K_F1:  # Toggle debug mode
                self.debug_mode = not self.debug_mode
                print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")
        
        return None
    
    def update(self):
        if self.state != GameState.PLAYING:
            return
        
        keys = pygame.key.get_pressed()
        
        # Actualizar jugador y obtener trail si completa corte
        completed_trail = self.player.update(keys, self.game_area, self.area_manager)
        if completed_trail:
            print(f"Trail completado con {len(completed_trail)} puntos")
            
            if self.debug_mode:
                print("Posiciones de enemigos:")
                for i, enemy in enumerate(self.enemies):
                    area_x, area_y = enemy.get_area_position()
                    print(f"  Enemigo {i}: pantalla({enemy.x:.1f}, {enemy.y:.1f}) -> área({area_x}, {area_y})")
            
            # Procesar el corte
            pixels_cut = self.area_manager.cut_area_with_trail(completed_trail, self.enemies)
            if pixels_cut > 0:
                points_earned = pixels_cut * POINTS_PER_AREA
                self.score += points_earned
                print(f"¡Área cortada! +{points_earned} puntos ({pixels_cut} píxeles)")
                
                # Crear partículas de éxito
                for _ in range(15):
                    self.particles.append({
                        'x': self.player.x + random.randint(-20, 20),
                        'y': self.player.y + random.randint(-20, 20),
                        'vx': random.uniform(-3, 3),
                        'vy': random.uniform(-3, 3),
                        'life': 60,
                        'color': YELLOW
                    })
            else:
                print("No se cortó ningún área")
        
        # Actualizar enemigos
        for enemy in self.enemies:
            enemy.update(self.game_area, self.area_manager, self.player)
        
        # Verificar colisiones solo si el jugador no está invulnerable
        if not self.player.is_invulnerable():
            self._check_collisions()
        
        # Actualizar partículas
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.1  # Gravedad
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.particles.remove(particle)
        
        # Verificar condiciones de victoria/derrota
        area_cut = self.area_manager.get_cut_percentage()
        if area_cut >= self.target_area:
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
        if self.player.cutting and len(self.player.trail) > 10:
            for enemy in self.enemies:
                enemy_center = (enemy.x + enemy.size//2, enemy.y + enemy.size//2)
                
                # Verificar colisión con los primeros puntos del trail (excluyendo los últimos)
                trail_to_check = self.player.trail[:-8]  # Excluir últimos 8 puntos
                
                for trail_point in trail_to_check:
                    trail_screen_x = trail_point[0] + self.player.area_offset_x
                    trail_screen_y = trail_point[1] + self.player.area_offset_y
                    
                    dist = math.sqrt(
                        (enemy_center[0] - trail_screen_x)**2 + 
                        (enemy_center[1] - trail_screen_y)**2
                    )
                    if dist < (enemy.size // 2 + 5):  # Radio de colisión
                        self._player_hit()
                        return
    
    def _player_hit(self):
        """Maneja cuando el jugador es golpeado"""
        self.lives -= 1
        self.player.hit()
        
        # Mover jugador a una posición segura en el borde
        safe_positions = [
            (self.game_area['x'], self.game_area['y'] + self.game_area['height'] // 2),
            (self.game_area['x'] + self.game_area['width'] - self.player.size, 
             self.game_area['y'] + self.game_area['height'] // 2),
            (self.game_area['x'] + self.game_area['width'] // 2, self.game_area['y']),
            (self.game_area['x'] + self.game_area['width'] // 2, 
             self.game_area['y'] + self.game_area['height'] - self.player.size)
        ]
        
        # Elegir la posición más alejada de los enemigos
        best_pos = safe_positions[0]
        max_min_distance = 0
        
        for pos in safe_positions:
            min_distance_to_enemies = float('inf')
            for enemy in self.enemies:
                dist = math.sqrt((pos[0] - enemy.x)**2 + (pos[1] - enemy.y)**2)
                min_distance_to_enemies = min(min_distance_to_enemies, dist)
            
            if min_distance_to_enemies > max_min_distance:
                max_min_distance = min_distance_to_enemies
                best_pos = pos
        
        self.player.x, self.player.y = best_pos
        self.player.on_border = True
        
        # Crear efecto de partículas
        for _ in range(20):
            self.particles.append({
                'x': self.player.x + self.player.size // 2,
                'y': self.player.y + self.player.size // 2,
                'vx': random.uniform(-8, 8),
                'vy': random.uniform(-8, 8),
                'life': 45,
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
        self.player.invulnerable_time = 0
        
        # Incrementar dificultad
        self.enemies = self._create_enemies()
        for enemy in self.enemies:
            enemy.speed *= (1 + self.level * 0.08)  # Incremento más gradual
        
        # Añadir un enemigo extra cada 3 niveles
        if self.level % 3 == 0 and len(self.enemies) < 8:  # Límite máximo de enemigos
            area_x, area_y = self.area_manager.get_safe_spawn_position()
            new_enemy_x = area_x + self.game_area['x'] - ENEMY_SIZE // 2
            new_enemy_y = area_y + self.game_area['y'] - ENEMY_SIZE // 2
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
        self.player.invulnerable_time = 0
        
        # Recrear enemigos
        self.enemies = self._create_enemies()
        self.particles.clear()
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Dibujar área de juego base
        pygame.draw.rect(self.screen, DARK_GRAY, 
                        (self.game_area['x'], self.game_area['y'], 
                         self.game_area['width'], self.game_area['height']))
        
        # Dibujar el área de juego válida encima
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
        for particle in self.particles:
            size = max(1, particle['life'] // 10)  # Tamaño variable
            pygame.draw.circle(self.screen, particle['color'],
                             (int(particle['x']), int(particle['y'])), size)
        
        # Dibujar UI
        self._draw_ui()
        
        # Información de debug
        if self.debug_mode:
            self._draw_debug_info()
        
        # Dibujar overlays según el estado
        if self.state == GameState.PAUSED:
            self._draw_pause_overlay()
        elif self.state == GameState.GAME_OVER:
            self._draw_game_over_overlay()
        elif self.state == GameState.LEVEL_COMPLETE:
            self._draw_level_complete_overlay()
    
    def _draw_debug_info(self):
        """Dibuja información de debug"""
        debug_y = 100
        
        # Información del jugador
        player_area_pos = (
            int(self.player.x + self.player.size // 2 - self.player.area_offset_x),
            int(self.player.y + self.player.size // 2 - self.player.area_offset_y)
        )
        
        debug_texts = [
            f"Player pos: ({self.player.x:.1f}, {self.player.y:.1f})",
            f"Player area pos: {player_area_pos}",
            f"On border: {self.player.on_border}",
            f"Cutting: {self.player.cutting}",
            f"Trail points: {len(self.player.trail)}",
            f"Invulnerable: {self.player.invulnerable_time}",
            f"Enemies: {len(self.enemies)}"
        ]
        
        for i, text in enumerate(debug_texts):
            debug_surface = self.small_font.render(text, True, YELLOW)
            self.screen.blit(debug_surface, (WINDOW_WIDTH - 300, debug_y + i * 20))
    
    def _draw_ui(self):
        """Dibuja la interfaz de usuario"""
        # Fondo de la UI
        pygame.draw.rect(self.screen, BLACK, (0, 0, WINDOW_WIDTH, 80))
        pygame.draw.line(self.screen, WHITE, (0, 80), (WINDOW_WIDTH, 80), 2)
        
        # Información del juego
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        
        # Obtener porcentaje actual de área cortada
        current_area = self.area_manager.get_cut_percentage()
        area_text = self.font.render(f"Cut: {current_area:.1f}%", True, WHITE)
        
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
        
        progress_fill = min(progress_width, int(progress_width * current_area / self.target_area))
        if progress_fill > 0:
            color = GREEN if current_area < self.target_area * 0.8 else YELLOW
            pygame.draw.rect(self.screen, color,
                            (progress_x, progress_y, progress_fill, 30))
        
        pygame.draw.rect(self.screen, WHITE,
                        (progress_x, progress_y, progress_width, 30), 2)
        
        # Texto de objetivo
        target_text = self.small_font.render(f"Target: {self.target_area}%", True, WHITE)
        self.screen.blit(target_text, (progress_x, progress_y + 35))
        
        # Mostrar estado de invulnerabilidad
        if self.player.is_invulnerable():
            invul_time = self.player.invulnerable_time / 60.0
            invul_text = self.small_font.render(f"INVULNERABLE ({invul_time:.1f}s)", True, YELLOW)
            self.screen.blit(invul_text, (20, 50))
        
        # Mostrar controles de debug
        if self.debug_mode:
            debug_text = self.small_font.render("DEBUG MODE (F1 to toggle)", True, YELLOW)
            self.screen.blit(debug_text, (WINDOW_WIDTH - 250, 10))
    
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