# scripts/menu.py - Sistema de menús del juego

import pygame
import sys
import random
from .config import *

class Button:
    def __init__(self, x, y, width, height, text, font_size=MENU_FONT_SIZE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        self.is_hovered = False
        self.is_clicked = False
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.is_clicked = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.is_clicked and self.rect.collidepoint(event.pos):
                    self.is_clicked = False
                    return True
                self.is_clicked = False
        return False
    
    def draw(self, screen):
        # Color del botón según el estado
        if self.is_clicked:
            color = DARK_GRAY
            text_color = YELLOW
        elif self.is_hovered:
            color = GRAY
            text_color = WHITE
        else:
            color = BLACK
            text_color = LIGHT_BLUE
            
        # Dibujar botón
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        # Dibujar texto centrado
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font_title = pygame.font.Font(None, MENU_TITLE_SIZE)
        self.font_menu = pygame.font.Font(None, MENU_FONT_SIZE)
        
        # Calcular posiciones centradas
        center_x = WINDOW_WIDTH // 2
        start_y = WINDOW_HEIGHT // 2 - 50
        
        # Crear botones
        self.buttons = {
            'new_game': Button(
                center_x - MENU_BUTTON_WIDTH // 2,
                start_y,
                MENU_BUTTON_WIDTH,
                MENU_BUTTON_HEIGHT,
                "Nuevo Juego"
            ),
            'options': Button(
                center_x - MENU_BUTTON_WIDTH // 2,
                start_y + MENU_BUTTON_HEIGHT + MENU_SPACING,
                MENU_BUTTON_WIDTH,
                MENU_BUTTON_HEIGHT,
                "Opciones"
            ),
            'quit': Button(
                center_x - MENU_BUTTON_WIDTH // 2,
                start_y + (MENU_BUTTON_HEIGHT + MENU_SPACING) * 2,
                MENU_BUTTON_WIDTH,
                MENU_BUTTON_HEIGHT,
                "Salir"
            )
        }
        
        # Partículas de fondo (efecto visual)
        self.particles = []
        for i in range(50):
            self.particles.append({
                'x': random.randint(0, WINDOW_WIDTH),
                'y': random.randint(0, WINDOW_HEIGHT),
                'speed': random.uniform(0.5, 2),
                'size': random.randint(1, 3)
            })
    
    def handle_events(self, event):
        result = None
        
        for name, button in self.buttons.items():
            if button.handle_event(event):
                if name == 'new_game':
                    result = 'start_game'
                elif name == 'options':
                    result = 'options'
                elif name == 'quit':
                    result = 'quit'
        
        return result
    
    def update(self):
        # Actualizar partículas de fondo
        for particle in self.particles:
            particle['y'] += particle['speed']
            if particle['y'] > WINDOW_HEIGHT:
                particle['y'] = -10
                particle['x'] = random.randint(0, WINDOW_WIDTH)
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Dibujar partículas de fondo
        for particle in self.particles:
            pygame.draw.circle(self.screen, DARK_GRAY, 
                             (int(particle['x']), int(particle['y'])), 
                             particle['size'])
        
        # Título del juego
        title_text = self.font_title.render("GALS PANIC", True, YELLOW)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(title_text, title_rect)
        
        # Subtítulo
        subtitle_text = self.font_menu.render("Remake", True, WHITE)
        subtitle_rect = subtitle_text.get_rect(center=(WINDOW_WIDTH // 2, 200))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Dibujar botones
        for button in self.buttons.values():
            button.draw(self.screen)
        
        # Instrucciones en la parte inferior
        info_text = pygame.font.Font(None, 24).render(
            "Usa las flechas para moverte - Corta áreas para revelar la imagen", 
            True, GRAY
        )
        info_rect = info_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
        self.screen.blit(info_text, info_rect)

class OptionsMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font_title = pygame.font.Font(None, MENU_TITLE_SIZE)
        self.font_menu = pygame.font.Font(None, MENU_FONT_SIZE)
        
        center_x = WINDOW_WIDTH // 2
        start_y = WINDOW_HEIGHT // 2 - 100
        
        self.buttons = {
            'volume': Button(
                center_x - MENU_BUTTON_WIDTH // 2,
                start_y,
                MENU_BUTTON_WIDTH,
                MENU_BUTTON_HEIGHT,
                "Volumen: 100%"
            ),
            'difficulty': Button(
                center_x - MENU_BUTTON_WIDTH // 2,
                start_y + MENU_BUTTON_HEIGHT + MENU_SPACING,
                MENU_BUTTON_WIDTH,
                MENU_BUTTON_HEIGHT,
                "Dificultad: Normal"
            ),
            'back': Button(
                center_x - MENU_BUTTON_WIDTH // 2,
                start_y + (MENU_BUTTON_HEIGHT + MENU_SPACING) * 3,
                MENU_BUTTON_WIDTH,
                MENU_BUTTON_HEIGHT,
                "Volver"
            )
        }
        
        self.volume = 100
        self.difficulty = "Normal"
    
    def handle_events(self, event):
        result = None
        
        for name, button in self.buttons.items():
            if button.handle_event(event):
                if name == 'volume':
                    self.volume = (self.volume + 25) % 125
                    if self.volume == 0:
                        self.volume = 25
                    self.buttons['volume'].text = f"Volumen: {self.volume}%"
                elif name == 'difficulty':
                    difficulties = ["Fácil", "Normal", "Difícil", "Extremo"]
                    current_index = difficulties.index(self.difficulty)
                    self.difficulty = difficulties[(current_index + 1) % len(difficulties)]
                    self.buttons['difficulty'].text = f"Dificultad: {self.difficulty}"
                elif name == 'back':
                    result = 'back'
        
        return result
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Título
        title_text = self.font_title.render("OPCIONES", True, YELLOW)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(title_text, title_rect)
        
        # Dibujar botones
        for button in self.buttons.values():
            button.draw(self.screen)

class MenuManager:
    def __init__(self, screen):
        self.screen = screen
        self.current_menu = 'main'
        self.main_menu = MainMenu(screen)
        self.options_menu = OptionsMenu(screen)
    
    def handle_events(self, event):
        if self.current_menu == 'main':
            result = self.main_menu.handle_events(event)
            if result == 'options':
                self.current_menu = 'options'
            elif result in ['start_game', 'quit']:
                return result
                
        elif self.current_menu == 'options':
            result = self.options_menu.handle_events(event)
            if result == 'back':
                self.current_menu = 'main'
        
        return None
    
    def update(self):
        if self.current_menu == 'main':
            self.main_menu.update()
    
    def draw(self):
        if self.current_menu == 'main':
            self.main_menu.draw()
        elif self.current_menu == 'options':
            self.options_menu.draw()
    
    def get_settings(self):
        return {
            'volume': self.options_menu.volume,
            'difficulty': self.options_menu.difficulty
        }