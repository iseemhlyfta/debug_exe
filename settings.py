import os

# все настройки и константы тут, чтобы не было магических чисел по коду

# пути к файлам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPRITE_DIR = os.path.join(BASE_DIR, "sprites")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SAVE_PATH = os.path.join(BASE_DIR, "save.json")
ITEMS_PATH = os.path.join(BASE_DIR, "items.json")
ROOMS_PATH = os.path.join(BASE_DIR, "rooms.json")
CHARACTERS_PATH = os.path.join(BASE_DIR, "characters.json")

# окно и шрифты (холст 4:3, тянется на реальное окно в view.present)
WIDTH = 800
HEIGHT = 600
FPS = 60
CAPTION = "Debug.exe"
CX = WIDTH // 2
CY = HEIGHT // 2

FONT_SIZE = 26
BIG_FONT_SIZE = 70
SMALL_FONT_SIZE = 18

# лого на главном экране (logo.gif в sprites/) - сидит справа, кнопки слева
LOGO_WIDTH = 360
LOGO_HEIGHT = 180  # лого 2:1, чтобы не растягивалось
LOGO_CENTER_X = WIDTH * 3 // 4
LOGO_CENTER_Y = CY
MENU_LEFT_X = 70
MENU_OPTIONS_TOP = CY - 30

# основные цвета
BG_COLOR = (13, 13, 13)
FLOOR_COLOR = (24, 24, 28)
ENEMY_COLOR = (220, 50, 50)
WALL_COLOR = (90, 90, 90)
DOOR_COLOR = (120, 100, 60)
BOSS_COLOR = (160, 60, 220)
TEXT_COLOR = (230, 230, 230)
COIN_COLOR = (255, 210, 40)
TREASURE_COL = (230, 200, 60)
SHOP_COL = (80, 200, 120)
BOSS_DOOR_COL = (200, 60, 80)

# геометрия комнаты и тайловая сетка
WALL = 36
GAP = 130
GRID = 9
COLS = 13
ROWS = 9
TILE_W = (WIDTH - 2 * WALL) / COLS
TILE_H = (HEIGHT - 2 * WALL) / ROWS

OBSTACLE_CHARS = {"#": "rock", "X": "box", "O": "pit", "B": "barrel"}
BARREL_HP = 2

# стороны света для дверей и обхода сетки
DIRS = [("N", (-1, 0)), ("S", (1, 0)), ("W", (0, -1)), ("E", (0, 1))]
OPPOSITE = {"N": "S", "S": "N", "W": "E", "E": "W"}

COLOR_CATEGORIES = {
    "stat": (120, 220, 120),
    "shot": (255, 140, 0),
    "hp": (220, 40, 60),
    "luck": (120, 220, 80),
    "special": (80, 200, 255),
}

# сложности крутят хп врагов, урон и число спавна
DIFFICULTIES = {
    "easy":   {"name": "Лёгкая",     "hp": 0.7, "dmg": 1, "spawn": -1},
    "normal": {"name": "Нормальная", "hp": 1.0, "dmg": 1, "spawn": 0},
    "hard":   {"name": "Сложная",    "hp": 1.4, "dmg": 2, "spawn": 1},
}
DIFF_KEYS = ["easy", "normal", "hard"]

# стартовые статы игрока
PLAYER_SIZE = 50
PLAYER_SPEED = 4.5
PLAYER_HALF_HEARTS = 6
PLAYER_COOLDOWN = 40
PLAYER_DAMAGE = 1.5
PLAYER_BULLET_LIFE = 38
PLAYER_BULLET_SPEED = 7
PLAYER_TEAR_SIZE = 10
INVULN_HIT = 60
INVULN_SHIELD = 45
SHIELD_RECHARGE = 360
ANIM_STEP = 0.25
ENTER_OFFSET = 70

# пули: база, перезарядка между попаданиями в одну цель, разлёт тройного/двойного
BULLET_SPEED_BASE = 9
BULLET_RADIUS = 6
BULLET_LIFE_BASE = 55
REHIT_FRAMES = 30
TRIPLE_SPREAD = 0.26
DOUBLE_OFFSET = 14

# тип врага -> характеристики и поведение (behaviour = ключ стратегии)
ENEMY_STATS = {
    "fast":     {"r": 13, "speed": 3.6, "hp": 1, "hp_floor": 1, "dmg": 1, "behaviour": "chase"},
    "tank":     {"r": 31, "speed": 1.0, "hp": 6, "hp_floor": 2, "dmg": 2, "behaviour": "chase"},
    "shooter":  {"r": 18, "speed": 1.1, "hp": 2, "hp_floor": 1, "dmg": 1, "behaviour": "ranged"},
    "splitter": {"r": 22, "speed": 1.7, "hp": 3, "hp_floor": 1, "dmg": 1, "behaviour": "chase",
                 "splits": ("small", 2)},
    "small":    {"r": 11, "speed": 2.9, "hp": 1, "hp_floor": 0, "dmg": 1, "behaviour": "chase",
                 "phases": True},
    "chaser":   {"r": 18, "speed": 2.1, "hp": 2, "hp_floor": 1, "dmg": 1, "behaviour": "chase"},
}
ENEMY_PATH_BEHAVIOUR = "chase"
SPLITTER_SPREAD = 20
SUMMON_SPREAD = 40
SUMMON_Y_OFFSET = 60
ENEMY_SPAWN_TIMER = 60
SHOOTER_RANGE = 220
SHOOTER_CD = 75
SHOOTER_BULLET_SPEED = 5
SHOOTER_BULLET_LIFE = 170

# сколько врагов спавнить в комнате и где
SPAWN_BASE = 3
SPAWN_RAND = 2
SPAWN_MIN_DIST = 160
SPAWN_TRIES = 40
TIER2_FLOOR = 2

# боссы: общие параметры + свои таймеры на каждый тип
BOSS_RADIUS = 48
BOSS_START_Y = 150
BOSS_SPEED = 2.2
BOSS_HP_BASE = 35
BOSS_HP_PER_FLOOR = 22
BOSS_BOUND = 90
BOSS_BULLET_LIFE = 200
CHARGER_DASH_CD = 110
CHARGER_DASH_LEN = 40
CHARGER_DASH_SPEED = 8
CHARGER_CHASE = 1.0
CHARGER_SHOOT_CD = 90
SUMMON_SHOOT_CD = 55
SUMMON_CALL_CD = 500
SUMMON_LIMIT = 4
SUMMON_BATCH = 2
SPREAD_SHOOT_CD = 45
SPREAD_FAN = [(0, 1), (1, 0), (-1, 0), (0.7, 0.7), (-0.7, 0.7)]
BOSS_KINDS = ["spreader", "charger", "summoner"]
BOSS_NAMES = {"charger": "Вирус-Таран", "summoner": "Вирус-Призыватель", "spreader": "Вирус-Веер"}
BAR_WIDTH = 320

# шансы дропа (монеты/сердца), удача поднимает их
COIN_DROP = 0.10
COIN_DROP_LUCK = 0.03
COIN_DROP_MIN = 0.01
COIN_DROP_MAX = 0.9
BARREL_COIN = 0.05
BARREL_COIN_LUCK = 0.01
BARREL_COIN_MAX = 0.3
HEART_FULL_CHANCE = 0.03
HEART_HALF_CHANCE = 0.10
VAMPIRE_CHANCE = 0.15

# генерация этажа: сколько комнат, старт по центру, цены в магазине
ROOMS_BASE = 6
ROOMS_PER_FLOOR = 2
START_CELL = (GRID // 2, GRID // 2)
MAX_FLOOR = 3
TRAPDOOR_SIZE = 70
BRANCH_CHANCE = 0.5
MIN_DEADENDS = 3
PRICE_HEAL = 3
PRICE_ITEM = 6
PRICE_MAP = 8
PEDESTAL_OFFSET = 200

MINIMAP_CELL = 16

# настройки экрана и звука, которые можно крутить в меню настроек (все 4:3)
RESOLUTIONS = [(800, 600), (1024, 768), (1280, 960), (1600, 1200), (2048, 1536)]
DEFAULT_RES_IDX = 0
DEFAULT_FULLSCREEN = False
DEFAULT_MASTER_VOLUME = 1.0
VOLUME_STEP = 0.1
SETTINGS_ROWS = 5  # 4 настройки + строка "применить"

# разная мелочь по геймплею (поворот самонаведения, отступы спавна, реплан пути)
HOMING_TURN = 0.12
SPAWN_MARGIN = 80
SPAWN_RECT = 32
BOSS_PEDESTAL_DY = 120
PATH_REPLAN = 12
ENTITY_HALF_PEDESTAL = 20

# звук: громкость и имена файлов под события/музыку (файлы кладём в assets/)
MUSIC_VOLUME = 0.4
SFX_VOLUME = 0.6
SOUND_FILES = {
    "shot": "shot",
    "enemy_hit": "hit",
    "enemy_die": "explosion",
    "hurt": "hurt",
    "coin": "coin",
    "heart": "heal",
    "boss_die": "boss_die",
    "win": "win",
    "lose": "lose",
}
MUSIC_FILES = {
    "menu": "menu",
    "floor": "floor",
    "boss": "boss",
}

# палитра фолбэк-цветов для отрисовки без спрайтов
PALETTE = {
    "eye": (255, 255, 255),
    "shield": (80, 200, 255),
    "spawn_ring": (120, 60, 60),
    "bar_back": (60, 60, 60),
    "pit": (0, 0, 0),
    "coin_edge": (160, 120, 20),
    "trapdoor": (10, 10, 10),
    "trapdoor_edge": (120, 120, 200),
    "trapdoor_text": (180, 180, 255),
    "stat_text": (170, 175, 200),
    "menu_title": (80, 160, 255),
    "menu_sub": (150, 150, 165),
    "menu_sel": (255, 230, 120),
    "menu_foot": (120, 120, 135),
    "select_box_sel": (50, 55, 80),
    "select_box": (28, 28, 36),
    "select_border": (70, 70, 80),
    "select_desc": (165, 165, 180),
    "win": (60, 200, 80),
    "pause_title": (220, 220, 230),
    "minimap_back": (8, 8, 8),
    "minimap_start": (60, 120, 255),
    "minimap_room": (130, 130, 130),
    "minimap_unknown": (55, 55, 55),
    "minimap_near": (200, 200, 120),
    "minimap_here": (255, 255, 255),
}

SPAWN_BLINK = 5
ENTITY_OUTLINE = 28
ENEMY_SPRITE_OUTLINE = 36
BOSS_SPRITE_OUTLINE = 30
