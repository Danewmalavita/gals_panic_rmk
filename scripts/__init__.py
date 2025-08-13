# scripts/__init__.py - Inicialización del paquete scripts

"""
Paquete de scripts del juego Gals Panic Remake
Contiene toda la lógica del juego, configuración y sistema de menús
"""

__version__ = "1.0.0"
__author__ = "Danew Malavita"

# Importaciones principales del paquete
from .config import *
from .menu import MenuManager
from .game import Game

__all__ = [
    'MenuManager',
    'Game',
    # Constantes de configuración más importantes
    'WINDOW_WIDTH',
    'WINDOW_HEIGHT',
    'FPS',
    'BLACK',
    'WHITE',
    'BLUE',
    'RED',
    'GREEN',
    'YELLOW',
]