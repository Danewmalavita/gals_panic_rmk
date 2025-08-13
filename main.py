# main.py - Archivo principal del juego Gals Panic

import pygame
import sys
import os
from scripts.config import *
from scripts.menu import MenuManager
from scripts.game import Game

class GameManager:
    def __init__(self):
        # Inicializar Pygame
        pygame.init()
        
        # Crear ventana
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Gals Panic Remake")
        
        # Intentar cargar un icono si existe
        try:
            icon = pygame.image.load("assets/images/icon.png")
            pygame.display.set_icon(icon)
        except:
            pass  # Si no hay icono, continuar sin él
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Estados del juego
        self.current_state = 'menu'  # 'menu' o 'game'
        
        # Inicializar sistemas
        self.menu_manager = MenuManager(self.screen)
        self.game = None
        self.settings = {'volume': 100, 'difficulty': 'Normal'}
    
    def handle_events(self):
        """Maneja los eventos globales del juego"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                # Teclas globales
                if event.key == pygame.K_F11:
                    self._toggle_fullscreen()
                elif event.key == pygame.K_F12:
                    self._take_screenshot()
            
            # Delegar eventos según el estado actual
            if self.current_state == 'menu':
                result = self.menu_manager.handle_events(event)
                if result == 'start_game':
                    self._start_game()
                elif result == 'quit':
                    self.running = False
            
            elif self.current_state == 'game' and self.game:
                result = self.game.handle_events(event)
                if result == 'menu':
                    self._return_to_menu()
    
    def update(self):
        """Actualiza la lógica del juego según el estado actual"""
        if self.current_state == 'menu':
            self.menu_manager.update()
        elif self.current_state == 'game' and self.game:
            self.game.update()
            
            # Verificar si el juego ha terminado
            if not self.game.is_running():
                # El juego maneja sus propios estados de game over y level complete
                pass
    
    def draw(self):
        """Dibuja la pantalla según el estado actual"""
        if self.current_state == 'menu':
            self.menu_manager.draw()
        elif self.current_state == 'game' and self.game:
            self.game.draw()
        
        # Actualizar pantalla
        pygame.display.flip()
    
    def run(self):
        """Bucle principal del juego"""
        print("Iniciando Gals Panic Remake...")
        print(f"Resolución: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        print("Controles:")
        print("- Flechas: Movimiento")
        print("- P: Pausa")
        print("- ESC: Menú")
        print("- F11: Pantalla completa")
        print("- F12: Captura de pantalla")
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        self._cleanup()
    
    def _start_game(self):
        """Inicia una nueva partida"""
        self.settings = self.menu_manager.get_settings()
        self.game = Game(self.screen, self.settings)
        self.current_state = 'game'
        print(f"Nuevo juego iniciado - Dificultad: {self.settings['difficulty']}")
    
    def _return_to_menu(self):
        """Vuelve al menú principal"""
        self.current_state = 'menu'
        self.game = None
        print("Regresando al menú principal...")
    
    def _toggle_fullscreen(self):
        """Alterna entre pantalla completa y ventana"""
        current_flags = self.screen.get_flags()
        if current_flags & pygame.FULLSCREEN:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        else:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
        
        # Actualizar referencias de pantalla
        self.menu_manager.screen = self.screen
        if self.game:
            self.game.screen = self.screen
    
    def _take_screenshot(self):
        """Toma una captura de pantalla"""
        try:
            if not os.path.exists("screenshots"):
                os.makedirs("screenshots")
            
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshots/gals_panic_{timestamp}.png"
            
            pygame.image.save(self.screen, filename)
            print(f"Captura guardada: {filename}")
        except Exception as e:
            print(f"Error al guardar captura: {e}")
    
    def _cleanup(self):
        """Limpia recursos antes de cerrar"""
        print("Cerrando juego...")
        pygame.quit()
        sys.exit()

def main():
    """Función principal"""
    try:
        game_manager = GameManager()
        game_manager.run()
    except Exception as e:
        print(f"Error crítico: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)

if __name__ == "__main__":
    main()