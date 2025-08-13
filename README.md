# Gals Panic Remake

Un remake moderno del clásico juego arcade Gals Panic desarrollado en Python con Pygame.

## Estructura del Proyecto

```
gals_panic_remake/
├── main.py                 # Archivo principal - ejecutar desde aquí
├── scripts/
│   ├── __init__.py        # Inicialización del paquete
│   ├── config.py          # Configuraciones globales del juego
│   ├── menu.py            # Sistema de menús (Principal y Opciones)
│   └── game.py            # Lógica principal del juego
├── assets/                # Recursos del juego (opcional)
│   ├── images/           # Imágenes y sprites
│   ├── sounds/           # Efectos de sonido y música
│   └── fonts/            # Fuentes personalizadas
├── screenshots/          # Capturas de pantalla automáticas
├── README.md             # Este archivo
└── requirements.txt      # Dependencias del proyecto
```

## Características

### **Sistema de Menús**
- **Menú Principal**: Nuevo Juego, Opciones, Salir
- **Menú de Opciones**: Configuración de volumen y dificultad
- **Interfaz visual**: Botones interactivos con efectos hover
- **Partículas de fondo**: Efectos visuales animados

### **Gameplay**
- **Mecánica de corte**: Corta áreas del campo de juego para revelar la imagen
- **Múltiples enemigos**: Diferentes tipos con comportamientos únicos
- **Sistema de vidas**: 3 vidas iniciales
- **Niveles de dificultad**: Fácil, Normal, Difícil, Extremo
- **Sistema de puntuación**: Puntos por áreas reveladas

### **Tipos de Enemigos**
- **Bouncer**: Rebota en las paredes
- **Hunter**: Te persigue y ataca tu línea de corte
- **Fast**: Enemigo rápido y agresivo

## Instalación y Ejecución

### **Requisitos**
- Python 3.7 o superior
- Pygame 2.0+

### **Instalación**

1. **Clonar o descargar el proyecto**
```bash
git clone [url-del-repositorio]
cd gals_panic_remake
```

2. **Instalar dependencias**
```bash
pip install pygame
```

O usando requirements.txt:
```bash
pip install -r requirements.txt
```

3. **Ejecutar el juego**
```bash
python main.py
```

## Controles

### **Menús**
- **Mouse**: Navegación por botones
- **Clic izquierdo**: Seleccionar opción

### **Juego**
- **Flechas del teclado**: Movimiento del jugador
- **P**: Pausar/Reanudar juego
- **ESC**: Volver al menú principal
- **R**: Reiniciar partida (en game over)

### **Controles Globales**
- **F11**: Alternar pantalla completa
- **F12**: Tomar captura de pantalla

## Mecánicas del Juego

### **Objetivo**
Corta áreas del campo de juego para revelar la imagen oculta. Necesitas revelar el 75% del área para completar el nivel.

### **Cómo Jugar**
1. Muévete desde el borde del área de juego hacia el interior
2. Tu línea de corte aparecerá en amarillo
3. Regresa al borde para completar el corte
4. Evita que los enemigos te toquen a ti o a tu línea de corte
5. Revela el 75% del área para ganar el nivel

### **Estados del Jugador**
- **Verde**: En el borde (seguro)
- **Azul**: Cortando (vulnerable)

## ⚙️ Configuración

### **Resolución**
- **Pantalla**: 1280x720 (16:9)
- **FPS**: 60

### **Niveles de Dificultad**
- **Fácil**: 2 enemigos básicos
- **Normal**: 3 enemigos (1 rápido)
- **Difícil**: 4 enemigos (incluye hunter)
- **Extremo**: 5 enemigos (múltiples hunters)

## Personalización

### **Modificar Configuración**
Edita `scripts/config.py` para cambiar:
- Resolución de pantalla
- Velocidades de juego
- Colores
- Tamaños de elementos

### **Añadir Assets**
- **Imágenes**: Coloca en `assets/images/`
- **Sonidos**: Coloca en `assets/sounds/`
- **Fuentes**: Coloca en `assets/fonts/`

## Resolución de Problemas

### **Error de importación pygame**
```bash
pip install --upgrade pygame
```

### **Pantalla en blanco**
Verifica que no tengas aplicaciones que interfieran con la aceleración gráfica.

### **Rendimiento bajo**
- Cierra otras aplicaciones
- Reduce la resolución en `config.py`
- Verifica drivers gráficos actualizados

## Próximas Características

- [ ] Sistema de corte real con flood fill
- [ ] Imágenes de fondo para revelar
- [ ] Efectos de sonido y música
- [ ] Power-ups y elementos especiales
- [ ] Múltiples niveles
- [ ] Sistema de puntuaciones altas
- [ ] Mejores gráficos y animaciones

## Desarrollo

### **Arquitectura del Código**
- **main.py**: GameManager principal y bucle de juego
- **scripts/config.py**: Constantes y configuración
- **scripts/menu.py**: Sistema completo de menús
- **scripts/game.py**: Lógica del juego y clases principales

### **Contribuir**
1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit cambios (`git commit -am 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crear Pull Request

## Licencia

Este proyecto es un remake educativo del clásico Gals Panic para fines de aprendizaje y demostración de programación con Python y Pygame.

---

**¡Disfruta del juego!** 
