# scripts/config.py - Configuración global del juego

# Configuración de pantalla
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_BLUE = (173, 216, 230)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# Configuración del menú
MENU_FONT_SIZE = 48
MENU_TITLE_SIZE = 72
MENU_BUTTON_HEIGHT = 60
MENU_BUTTON_WIDTH = 300
MENU_SPACING = 20

# Configuración del jugador
PLAYER_SIZE = 12
PLAYER_SPEED = 4
TRAIL_MAX_LENGTH = 200

# Configuración de enemigos
ENEMY_SIZE = 15
ENEMY_SPEED_MIN = 1.5
ENEMY_SPEED_MAX = 3.5
ENEMY_COUNT = 3

# Configuración del juego
INITIAL_LIVES = 3
TARGET_AREA_PERCENTAGE = 75
POINTS_PER_AREA = 10

# Rutas de archivos
SCRIPTS_PATH = "scripts/"
ASSETS_PATH = "assets/"
IMAGES_PATH = ASSETS_PATH + "images/"
SOUNDS_PATH = ASSETS_PATH + "sounds/"