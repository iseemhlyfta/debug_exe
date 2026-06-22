import pygame
import random
import math
import json
import os
import heapq
from abc import ABC, abstractmethod

from settings import (
    ANIM_STEP, BARREL_COIN, BARREL_COIN_LUCK, BARREL_COIN_MAX, BARREL_HP,
    BOSS_BOUND, BOSS_BULLET_LIFE, BOSS_DOOR_COL, BOSS_HP_BASE, BOSS_HP_PER_FLOOR,
    BOSS_KINDS, BOSS_PEDESTAL_DY, BOSS_RADIUS, BOSS_SPEED, BOSS_START_Y,
    BRANCH_CHANCE, BULLET_LIFE_BASE, BULLET_RADIUS, BULLET_SPEED_BASE,
    CHARACTERS_PATH, CHARGER_CHASE, CHARGER_DASH_CD, CHARGER_DASH_LEN,
    CHARGER_DASH_SPEED, CHARGER_SHOOT_CD, COIN_DROP, COIN_DROP_LUCK,
    COIN_DROP_MAX, COIN_DROP_MIN, COLOR_CATEGORIES, COLS, CX, CY,
    DEFAULT_FULLSCREEN, DEFAULT_MASTER_VOLUME, DEFAULT_RES_IDX, DIFFICULTIES,
    DIRS, DOOR_COLOR, DOUBLE_OFFSET, ENEMY_SPAWN_TIMER, ENEMY_STATS,
    ENTER_OFFSET, ENTITY_HALF_PEDESTAL, GAP, GRID, HEART_FULL_CHANCE,
    HEART_HALF_CHANCE, HEIGHT, HOMING_TURN, INVULN_HIT, INVULN_SHIELD,
    ITEMS_PATH, MAX_FLOOR, MIN_DEADENDS, OBSTACLE_CHARS, OPPOSITE, PATH_REPLAN,
    PEDESTAL_OFFSET, PLAYER_BULLET_LIFE, PLAYER_BULLET_SPEED, PLAYER_COOLDOWN,
    PLAYER_DAMAGE, PLAYER_HALF_HEARTS, PLAYER_SIZE, PLAYER_SPEED,
    PLAYER_TEAR_SIZE, PRICE_HEAL, PRICE_ITEM, PRICE_MAP, REHIT_FRAMES,
    ROOMS_BASE, ROOMS_PATH, ROOMS_PER_FLOOR, ROWS, SAVE_PATH, SHIELD_RECHARGE,
    SHOOTER_BULLET_LIFE, SHOOTER_BULLET_SPEED, SHOOTER_CD, SHOOTER_RANGE,
    SHOP_COL, SPAWN_BASE, SPAWN_MARGIN, SPAWN_MIN_DIST, SPAWN_RAND,
    SPAWN_RECT, SPAWN_TRIES, SPLITTER_SPREAD, SPREAD_FAN, SPREAD_SHOOT_CD,
    START_CELL, SUMMON_BATCH, SUMMON_CALL_CD, SUMMON_LIMIT, SUMMON_SHOOT_CD,
    SUMMON_SPREAD, SUMMON_Y_OFFSET, TIER2_FLOOR, TILE_H, TILE_W, TRAPDOOR_SIZE,
    TREASURE_COL, TRIPLE_SPREAD, VAMPIRE_CHANCE, WALL, WIDTH,
)

# вся логика игры тут, ничего не рисуем — это model


def load_items():
    # читаем предметы из json
    with open(ITEMS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    defs = {}
    for it in data["items"]:
        defs[it["id"]] = it
    return defs


def load_rooms():
    # планировки комнат, ключи с _ это комментарии в json
    with open(ROOMS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    layouts = {}
    for key, value in data.items():
        if key.startswith("_"):
            continue
        layouts[key] = value
    return layouts


def load_characters():
    # персонажи для выбора
    with open(CHARACTERS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["characters"]


# грузим данные один раз на импорте
ITEM_DEFS = load_items()
ITEM_NAMES = {k: v["name"] for k, v in ITEM_DEFS.items()}
ITEM_POOL = [k for k, v in ITEM_DEFS.items() if v.get("pool")]
BOSS_POOL = [k for k, v in ITEM_DEFS.items() if v.get("boss")]
LAYOUTS = load_rooms()
CHARACTERS = load_characters()


def load_save():
    # читаем сейв, если битый — стартуем с нуля
    data = {"difficulty": "normal", "characters": {},
            "resolution_idx": DEFAULT_RES_IDX, "fullscreen": DEFAULT_FULLSCREEN,
            "master_volume": DEFAULT_MASTER_VOLUME}
    if os.path.exists(SAVE_PATH):
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            data["difficulty"] = loaded.get("difficulty", "normal")
            data["characters"] = loaded.get("characters", {})
            data["resolution_idx"] = loaded.get("resolution_idx", DEFAULT_RES_IDX)
            data["fullscreen"] = loaded.get("fullscreen", DEFAULT_FULLSCREEN)
            data["master_volume"] = loaded.get("master_volume", DEFAULT_MASTER_VOLUME)
        except (json.JSONDecodeError, OSError, KeyError, TypeError):
            pass
    return data


def save_progress(data):
    # пишем сейв на диск
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


SAVE = load_save()
current_diff = DIFFICULTIES.get(SAVE["difficulty"], DIFFICULTIES["normal"])


def set_difficulty(dkey):
    # меняем сложность и сразу сохраняем
    global current_diff
    current_diff = DIFFICULTIES[dkey]
    SAVE["difficulty"] = dkey
    save_progress(SAVE)


def set_resolution(idx):
    # запоминаем выбранное разрешение экрана
    SAVE["resolution_idx"] = idx
    save_progress(SAVE)


def set_fullscreen(flag):
    # включаем/выключаем полноэкранный режим
    SAVE["fullscreen"] = flag
    save_progress(SAVE)


def set_master_volume(vol):
    # общая громкость, режем чтобы не вылезла за 0..1
    SAVE["master_volume"] = max(0.0, min(1.0, vol))
    save_progress(SAVE)


def item_color(kind):
    # цвет предмета по его категории
    cat = ITEM_DEFS.get(kind, {}).get("color", "stat")
    return COLOR_CATEGORIES.get(cat, (120, 220, 120))


def tile_center(col, row):
    # центр тайла в пикселях
    x = WALL + (col + 0.5) * TILE_W
    y = WALL + (row + 0.5) * TILE_H
    return x, y


def tile_rect(col, row):
    # прямоугольник тайла, чуть ужатый
    x = WALL + col * TILE_W
    y = WALL + row * TILE_H
    return pygame.Rect(int(x + 3), int(y + 3), int(TILE_W - 6), int(TILE_H - 6))


def tile_rect_full(col, row):
    # прямоугольник тайла во весь размер, без зазора (яма должна закрывать тайл целиком)
    x = WALL + col * TILE_W
    y = WALL + row * TILE_H
    return pygame.Rect(int(x), int(y), int(TILE_W) + 1, int(TILE_H) + 1)


def tile_at(x, y):
    # из пикселей в координаты тайла, с зажимом в границы
    col = int((x - WALL) / TILE_W)
    row = int((y - WALL) / TILE_H)
    col = min(max(col, 0), COLS - 1)
    row = min(max(row, 0), ROWS - 1)
    return col, row


def hits_wall(rect, walls):
    # проверка столкновения с любым из прямоугольников
    for w in walls:
        if rect.colliderect(w):
            return True
    return False


def resolve_move(entity, old_x, old_y, blockers):
    # проверяем оси отдельно, чтобы у стены не залипало, а скользило вдоль неё
    new_x, new_y = entity.x, entity.y
    entity.x, entity.y = new_x, old_y
    x_blocked = hits_wall(entity.get_rect(), blockers)
    entity.x, entity.y = old_x, new_y
    y_blocked = hits_wall(entity.get_rect(), blockers)
    entity.x = old_x if x_blocked else new_x
    entity.y = old_y if y_blocked else new_y


def filled_neighbors(grid, cell):
    # сколько соседних клеток уже заняты комнатами (для генерации)
    count = 0
    for name, d in DIRS:
        nb = (cell[0] + d[0], cell[1] + d[1])
        if nb in grid:
            count += 1
    return count


def bfs(grid, start):
    # обход в ширину по комнатам, считаем расстояния от старта
    dist = {start: 0}
    queue = [start]
    while queue:
        cell = queue.pop(0)
        for name, d in DIRS:
            nb = (cell[0] + d[0], cell[1] + d[1])
            if nb in grid and nb not in dist:
                dist[nb] = dist[cell] + 1
                queue.append(nb)
    return dist


def astar(blocked, start, goal):
    # поиск пути по тайлам, чтобы враги обходили препятствия
    if start == goal:
        return [goal]
    open_heap = [(0, start)]
    came = {start: None}
    cost = {start: 0}
    while open_heap:
        _, cur = heapq.heappop(open_heap)
        if cur == goal:
            break
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (cur[0] + dc, cur[1] + dr)
            if not (0 <= nb[0] < COLS and 0 <= nb[1] < ROWS):
                continue
            if nb in blocked and nb != goal:
                continue
            ng = cost[cur] + 1
            if nb not in cost or ng < cost[nb]:
                cost[nb] = ng
                pri = ng + abs(nb[0] - goal[0]) + abs(nb[1] - goal[1])
                heapq.heappush(open_heap, (pri, nb))
                came[nb] = cur
    if goal not in came:
        return None
    # разворачиваем путь от цели к старту
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = came[node]
    path.reverse()
    return path


def random_item():
    return random.choice(ITEM_POOL)


class Entity(ABC):
    # база для всего, что есть на сцене: координаты общие, а форма rect своя у
    # каждого типа (квадрат игрока, круг пули, прямоугольник препятствия) —
    # абстрактный get_rect не даёт забыть переопределить её в наследнике
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @abstractmethod
    def get_rect(self):
        ...


class CircleEntity(Entity):
    # всё круглое (пули, враги, монеты) считает rect из радиуса
    def __init__(self, x, y, radius):
        super().__init__(x, y)
        self.radius = radius

    def get_rect(self):
        r = self.radius
        return pygame.Rect(int(self.x - r), int(self.y - r), int(r * 2), int(r * 2))


class Player(Entity):
    # игрок: куча статов, часть переопределяется выбранным персонажем
    def __init__(self, char=None):
        super().__init__(CX, CY)
        self.size = PLAYER_SIZE
        self.speed = PLAYER_SPEED
        self.max_half = PLAYER_HALF_HEARTS
        self.half = PLAYER_HALF_HEARTS
        self.cooldown = 0
        self.cooldown_max = PLAYER_COOLDOWN
        self.damage = PLAYER_DAMAGE
        self.bullet_life = PLAYER_BULLET_LIFE
        self.bullet_speed = PLAYER_BULLET_SPEED
        self.tear_size = PLAYER_TEAR_SIZE
        self.luck = 0
        self.triple = False
        self.pierce = False
        self.double = False
        self.homing = False
        self.vampire = False
        self.max_shield = 0
        self.shield = 0
        self.shield_recharge = 0
        self.coins = 0
        self.invuln = 0
        self.moving = False
        self.facing = 1
        self.anim = 0.0
        if char:
            # перебиваем дефолты статами и флагами персонажа
            for key, val in char.get("stats", {}).items():
                setattr(self, key, val)
            for flag in char.get("flags", []):
                setattr(self, flag, True)

    @property
    def alive(self):
        return self.half > 0

    def get_rect(self):
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)


class Bullet(CircleEntity):
    # пуля, летит по направлению и живёт ограниченное число кадров
    def __init__(self, x, y, dx, dy, from_player):
        super().__init__(x, y, BULLET_RADIUS)
        self.dx = dx
        self.dy = dy
        self.speed = BULLET_SPEED_BASE
        self.from_player = from_player
        self.life = BULLET_LIFE_BASE
        self.damage = 1
        self.pierce = False
        self.homing = False
        self.hit_targets = {}  # кого уже задели и на каком кадре (для пробивающих)

    def update(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.life -= 1


class EnemyBehaviour(ABC):
    # стратегия поведения врага, чтобы добавлять типы без правки старого кода
    @abstractmethod
    def act(self, enemy, player, bullets, room):
        ...


class ChaseBehaviour(EnemyBehaviour):
    # бежим к игроку, по A* в обход препятствий (фазовые ломятся напрямик)
    def act(self, enemy, player, bullets, room):
        target_x, target_y = player.x, player.y
        if not enemy.phases and room is not None:
            enemy.path_timer -= 1
            if enemy.path_timer <= 0 or not enemy.path:
                # пересчитываем путь раз в несколько кадров
                blocked = {(o.col, o.row) for o in room.obstacles
                           if o.solid() or o.is_pit()}
                start = tile_at(enemy.x, enemy.y)
                goal = tile_at(player.x, player.y)
                enemy.path = astar(blocked, start, goal) or []
                enemy.path_timer = PATH_REPLAN
            if len(enemy.path) >= 2:
                target_x, target_y = tile_center(*enemy.path[1])  # рулим к следующей клетке пути
                blocked = {(o.col, o.row) for o in room.obstacles
                           if o.solid() or o.is_pit()}
                start = tile_at(enemy.x, enemy.y)
                goal = tile_at(player.x, player.y)
                enemy.path = astar(blocked, start, goal) or []
                enemy.path_timer = PATH_REPLAN
            if len(enemy.path) >= 2:
                target_x, target_y = tile_center(*enemy.path[1])
        dx = target_x - enemy.x
        dy = target_y - enemy.y
        dist = math.hypot(dx, dy)
        if dist != 0:
            enemy.x += (dx / dist) * enemy.speed
            enemy.y += (dy / dist) * enemy.speed


class RangedBehaviour(EnemyBehaviour):
    # держим дистанцию и постреливаем в игрока
    def act(self, enemy, player, bullets, room):
        dx = player.x - enemy.x
        dy = player.y - enemy.y
        dist = math.hypot(dx, dy)
        if dist > SHOOTER_RANGE and dist != 0:
            enemy.x += (dx / dist) * enemy.speed
            enemy.y += (dy / dist) * enemy.speed
        enemy.shoot_timer += 1
        if enemy.shoot_timer >= SHOOTER_CD:
            enemy.shoot_timer = 0
            if dist != 0:
                b = Bullet(enemy.x, enemy.y, dx / dist, dy / dist, False)
                b.speed = SHOOTER_BULLET_SPEED
                b.life = SHOOTER_BULLET_LIFE
                bullets.append(b)


# реестр стратегий: ключ из ENEMY_STATS -> объект поведения
ENEMY_BEHAVIOURS = {
    "chase": ChaseBehaviour(),
    "ranged": RangedBehaviour(),
}


class Enemy(CircleEntity):
    # враг: статы и поведение берём из таблицы по типу
    def __init__(self, kind, x, y, floor):
        if kind not in ENEMY_STATS:
            kind = "chaser"
        stats = ENEMY_STATS[kind]
        super().__init__(x, y, stats["r"])
        self.kind = kind
        self.hit_cooldown = 0
        self.spawn_timer = ENEMY_SPAWN_TIMER
        self.shoot_timer = random.randint(0, ENEMY_SPAWN_TIMER)
        self.speed = stats["speed"]
        self.hp = stats["hp"] + stats["hp_floor"] * floor
        self.damage = stats["dmg"]
        self.hp = max(1, int(round(self.hp * current_diff["hp"])))  # масштаб под сложность
        self.damage = self.damage * current_diff["dmg"]
        self.phases = stats.get("phases", False)  # проходит сквозь стены
        self.splits = stats.get("splits")  # на смерти плодит мелких
        self.behaviour = ENEMY_BEHAVIOURS[stats["behaviour"]]
        self.path = []
        self.path_timer = 0

    # hp прячем за свойство, чтобы не уходило в минус
    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        self._hp = max(0, value)

    @property
    def alive(self):
        return self._hp > 0

    def update(self, player, enemy_bullets, room=None):
        # пока спавнится — стоит на месте
        if self.spawn_timer > 0:
            self.spawn_timer -= 1
            return
        self.behaviour.act(self, player, enemy_bullets, room)
        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1


class BossBehaviour(ABC):
    # та же стратегия, что и у врагов (EnemyBehaviour), но для боссов: новый
    # тип босса с другим паттерном атаки добавляется без правок Boss/Game
    @abstractmethod
    def act(self, boss, player, bullets, room):
        ...


class ChargerBehaviour(BossBehaviour):
    # таран: копит откат и рывком летит в игрока, отскакивая от стен
    def act(self, boss, player, bullets, room):
        boss.dash_cd += 1
        if boss.dash > 0:
            boss.x += boss.vx
            boss.y += boss.vy
            boss.dash -= 1
            if boss.x < WALL + boss.radius or boss.x > WIDTH - WALL - boss.radius:
                boss.vx *= -1
            if boss.y < WALL + boss.radius or boss.y > HEIGHT - WALL - boss.radius:
                boss.vy *= -1
        else:
            dx = player.x - boss.x
            dy = player.y - boss.y
            d = math.hypot(dx, dy)
            if d != 0:
                boss.x += (dx / d) * CHARGER_CHASE
                boss.y += (dy / d) * CHARGER_CHASE
            if boss.dash_cd >= CHARGER_DASH_CD:
                boss.dash_cd = 0
                if d != 0:
                    boss.vx = (dx / d) * CHARGER_DASH_SPEED
                    boss.vy = (dy / d) * CHARGER_DASH_SPEED
                boss.dash = CHARGER_DASH_LEN
        boss.shoot_timer += 1
        if boss.shoot_timer >= CHARGER_SHOOT_CD:
            boss.shoot_timer = 0
            boss.shoot_at_player(player, bullets)


class SummonerBehaviour(BossBehaviour):
    # призыватель: ходит вбок, стреляет и подкидывает мелких врагов
    def act(self, boss, player, bullets, room):
        boss.x += boss.speed * boss.move_dir
        if boss.x < WALL + BOSS_BOUND or boss.x > WIDTH - WALL - BOSS_BOUND:
            boss.move_dir *= -1
        boss.shoot_timer += 1
        if boss.shoot_timer >= SUMMON_SHOOT_CD:
            boss.shoot_timer = 0
            boss.shoot_at_player(player, bullets)
        boss.summon_timer += 1
        if boss.summon_timer >= SUMMON_CALL_CD and len(room.enemies) < SUMMON_LIMIT:
            boss.summon_timer = 0
            for i in range(SUMMON_BATCH):  # призыв пачки
                room.enemies.append(Enemy("fast",
                                          boss.x + random.randint(-SUMMON_SPREAD, SUMMON_SPREAD),
                                          boss.y + SUMMON_Y_OFFSET, boss.floor))


class SpreaderBehaviour(BossBehaviour):
    # веер: ходит вбок и плюётся пулями во все стороны
    def act(self, boss, player, bullets, room):
        boss.x += boss.speed * boss.move_dir
        if boss.x < WALL + BOSS_BOUND or boss.x > WIDTH - WALL - BOSS_BOUND:
            boss.move_dir *= -1
        boss.shoot_timer += 1
        if boss.shoot_timer >= SPREAD_SHOOT_CD:
            boss.shoot_timer = 0
            boss.shoot_at_player(player, bullets)
            for v in SPREAD_FAN:  # веер фиксированных направлений
                b = Bullet(boss.x, boss.y, v[0], v[1], False)
                b.life = BOSS_BULLET_LIFE
                bullets.append(b)


BOSS_BEHAVIOURS = {
    "charger": ChargerBehaviour(),
    "summoner": SummonerBehaviour(),
    "spreader": SpreaderBehaviour(),
}


class Boss(CircleEntity):
    # босс: тип задаёт поведение, hp тоже спрятан за свойство
    def __init__(self, kind, hp, floor):
        super().__init__(CX, BOSS_START_Y, BOSS_RADIUS)
        if kind not in BOSS_BEHAVIOURS:
            kind = "spreader"
        self.kind = kind
        hp = max(1, int(round(hp * current_diff["hp"])))
        self.hp = hp
        self.max_hp = hp
        self.floor = floor
        self.speed = BOSS_SPEED
        self.shoot_timer = 0
        self.move_dir = 1
        self.hit_cooldown = 0
        self.dash = 0
        self.dash_cd = 0
        self.vx = 0
        self.vy = 0
        self.summon_timer = 0
        self.behaviour = BOSS_BEHAVIOURS[kind]

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        self._hp = max(0, value)

    @property
    def alive(self):
        return self._hp > 0

    def shoot_at_player(self, player, bullets, life=BOSS_BULLET_LIFE):
        # одиночный выстрел в сторону игрока, общий для всех боссов
        dx = player.x - self.x
        dy = player.y - self.y
        d = math.hypot(dx, dy)
        if d != 0:
            b = Bullet(self.x, self.y, dx / d, dy / d, False)
            b.life = life
            bullets.append(b)

    def update(self, player, bullets, room):
        # поведение по типу, потом держим босса в пределах комнаты
        self.behaviour.act(self, player, bullets, room)
        self.x = min(max(self.x, WALL + self.radius), WIDTH - WALL - self.radius)
        self.y = min(max(self.y, WALL + self.radius), HEIGHT - WALL - self.radius)
        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1


class Obstacle(Entity):
    # препятствие на тайле: камень/ящик/яма/бочка
    def __init__(self, kind, col, row):
        super().__init__(*tile_center(col, row))
        self.kind = kind
        self.col = col
        self.row = row
        self.rect = tile_rect_full(col, row) if kind == "pit" else tile_rect(col, row)
        self.hp = BARREL_HP if kind == "barrel" else 0  # бочку можно разбить

    def solid(self):
        return self.kind in ("rock", "box", "barrel")

    def is_pit(self):
        return self.kind == "pit"

    def get_rect(self):
        return self.rect


def build_obstacles(layout):
    # из текстовой планировки делаем список препятствий
    obstacles = []
    if not layout:
        return obstacles
    for row, line in enumerate(layout):
        for col, ch in enumerate(line):
            kind = OBSTACLE_CHARS.get(ch)
            if kind:
                obstacles.append(Obstacle(kind, col, row))
    return obstacles


class Coin(CircleEntity):
    # монетка-подбиралка
    def __init__(self, x, y):
        super().__init__(x, y, 9)


class Heart(CircleEntity):
    # сердце: full даёт два деления, half одно
    def __init__(self, x, y, kind):
        super().__init__(x, y, 12)
        self.kind = kind


class Pedestal(Entity):
    # тумба с предметом, price 0 значит бесплатно (награда)
    def __init__(self, x, y, kind, price):
        super().__init__(x, y)
        self.kind = kind
        self.price = price
        self.bought = False

    def get_rect(self):
        h = ENTITY_HALF_PEDESTAL
        return pygame.Rect(self.x - h, self.y - h, h * 2, h * 2)


class Room:
    # одна комната этажа: двери, враги, предметы, флаги состояния
    def __init__(self, r, c):
        self.r = r
        self.c = c
        self.kind = "normal"
        self.doors = set()
        self.cleared = False
        self.visited = False
        self.spawned = False
        self.enemies = []
        self.coins = []
        self.hearts = []
        self.pedestals = []
        self.boss = None
        self.trapdoor = False
        self.layout = None
        self.obstacles = []
        self.built = False


def door_open(room):
    # двери открываются только когда комната зачищена
    return room.cleared


def get_walls(room):
    # собираем стены комнаты, в открытых дверях оставляем проём
    walls = []
    if "N" in room.doors and door_open(room):
        walls.append(pygame.Rect(0, 0, CX - GAP // 2, WALL))
        walls.append(pygame.Rect(CX + GAP // 2, 0, WIDTH - CX - GAP // 2, WALL))
    else:
        walls.append(pygame.Rect(0, 0, WIDTH, WALL))
    if "S" in room.doors and door_open(room):
        walls.append(pygame.Rect(0, HEIGHT - WALL, CX - GAP // 2, WALL))
        walls.append(pygame.Rect(CX + GAP // 2, HEIGHT - WALL, WIDTH - CX - GAP // 2, WALL))
    else:
        walls.append(pygame.Rect(0, HEIGHT - WALL, WIDTH, WALL))
    if "W" in room.doors and door_open(room):
        walls.append(pygame.Rect(0, 0, WALL, CY - GAP // 2))
        walls.append(pygame.Rect(0, CY + GAP // 2, WALL, HEIGHT - CY - GAP // 2))
    else:
        walls.append(pygame.Rect(0, 0, WALL, HEIGHT))
    if "E" in room.doors and door_open(room):
        walls.append(pygame.Rect(WIDTH - WALL, 0, WALL, CY - GAP // 2))
        walls.append(pygame.Rect(WIDTH - WALL, CY + GAP // 2, WALL, HEIGHT - CY - GAP // 2))
    else:
        walls.append(pygame.Rect(WIDTH - WALL, 0, WALL, HEIGHT))
    return walls


def door_zone(direction):
    # зона у двери, по которой ловим переход в соседнюю комнату
    if direction == "N":
        return pygame.Rect(CX - GAP // 2, 0, GAP, WALL + 18)
    if direction == "S":
        return pygame.Rect(CX - GAP // 2, HEIGHT - WALL - 18, GAP, WALL + 18)
    if direction == "W":
        return pygame.Rect(0, CY - GAP // 2, WALL + 18, GAP)
    return pygame.Rect(WIDTH - WALL - 18, CY - GAP // 2, WALL + 18, GAP)


def door_strip(direction):
    # тонкая полоска двери, когда комната уже зачищена
    if direction == "N":
        return pygame.Rect(CX - GAP // 2, WALL, GAP, 6)
    if direction == "S":
        return pygame.Rect(CX - GAP // 2, HEIGHT - WALL - 6, GAP, 6)
    if direction == "W":
        return pygame.Rect(WALL, CY - GAP // 2, 6, GAP)
    return pygame.Rect(WIDTH - WALL - 6, CY - GAP // 2, 6, GAP)


def generate_floor(floor_num):
    # процедурная генерация этажа случайным ростом, крутим пока не выйдет норм
    target = ROOMS_BASE + floor_num * ROOMS_PER_FLOOR
    while True:
        grid = {}
        start = START_CELL
        start_room = Room(start[0], start[1])
        start_room.kind = "start"
        start_room.cleared = True
        grid[start] = start_room
        queue = [start]
        # растим комнаты в случайные стороны, не лепя их слишком плотно
        while queue and len(grid) < target:
            cell = queue.pop(0)
            dirs = DIRS[:]
            random.shuffle(dirs)
            for name, d in dirs:
                if len(grid) >= target:
                    break
                nb = (cell[0] + d[0], cell[1] + d[1])
                if nb in grid:
                    continue
                if not (0 <= nb[0] < GRID and 0 <= nb[1] < GRID):
                    continue
                if filled_neighbors(grid, nb) > 1:
                    continue
                if random.random() < BRANCH_CHANCE:
                    continue
                grid[nb] = Room(nb[0], nb[1])
                queue.append(nb)
        if len(grid) < target:
            continue  # не доросло, начинаем заново
        # проставляем двери между соседями
        for cell, room in grid.items():
            for name, d in DIRS:
                nb = (cell[0] + d[0], cell[1] + d[1])
                if nb in grid:
                    room.doors.add(name)
        deadends = [c for c in grid if c != start and len(grid[c].doors) == 1]
        if len(deadends) < MIN_DEADENDS:
            continue  # мало тупиков под босса/сокровищницу/магазин
        # босс в самый дальний тупик, остальное в случайные
        dist = bfs(grid, start)
        deadends.sort(key=lambda c: dist[c])
        boss_cell = deadends[-1]
        grid[boss_cell].kind = "boss"
        rest = [c for c in deadends if c != boss_cell]
        random.shuffle(rest)
        treasure_cell = rest[0]
        shop_cell = rest[1]
        tr = grid[treasure_cell]
        tr.kind = "treasure"
        tr.cleared = True
        tr.pedestals.append(Pedestal(CX, CY, random_item(), 0))  # бесплатный предмет
        sh = grid[shop_cell]
        sh.kind = "shop"
        sh.cleared = True
        sh.pedestals.append(Pedestal(CX - PEDESTAL_OFFSET, CY, "heal", PRICE_HEAL))
        sh.pedestals.append(Pedestal(CX, CY, random_item(), PRICE_ITEM))
        sh.pedestals.append(Pedestal(CX + PEDESTAL_OFFSET, CY, "map", PRICE_MAP))
        # выбираем планировку под тип комнаты
        for cell, room in grid.items():
            options = LAYOUTS.get(room.kind)
            if options:
                room.layout = random.choice(options)
        return grid, start


class Game:
    # вся партия: игрок, текущий этаж/комната, пули и состояние
    def __init__(self, char=None):
        self.char_id = char["id"] if char else "coder"
        self.player = Player(char)
        self.floor_num = 1
        self.grid, self.start = generate_floor(self.floor_num)
        self.cur = self.start
        self.bullets = []
        self.enemy_bullets = []
        self.kills = 0
        self.full_map = False
        self.state = "playing"
        self.frame = 0
        self.events = []
        start_room = self.grid[self.cur]
        start_room.visited = True
        start_room.obstacles = build_obstacles(start_room.layout)
        start_room.built = True

    def room(self):
        # текущая комната
        return self.grid[self.cur]

    def emit(self, name):
        # копим событие кадра, main потом проиграет звук
        self.events.append(name)

    def neighbor_cell(self, direction):
        # клетка-сосед в заданную сторону
        for name, d in DIRS:
            if name == direction:
                return (self.cur[0] + d[0], self.cur[1] + d[1])
        return None

    def door_color(self, direction):
        # красим дверь по типу комнаты за ней
        nb = self.neighbor_cell(direction)
        if nb in self.grid:
            k = self.grid[nb].kind
            if k == "treasure":
                return TREASURE_COL
            if k == "shop":
                return SHOP_COL
            if k == "boss":
                return BOSS_DOOR_COL
        return DOOR_COLOR

    def enter_room(self, cell, from_dir):
        # переход в комнату: строим препятствия, ставим игрока у нужной двери
        self.cur = cell
        room = self.room()
        room.visited = True
        if not room.built:
            room.obstacles = build_obstacles(room.layout)
            room.built = True
        self.bullets = []
        self.enemy_bullets = []
        if from_dir == "N":
            self.player.x, self.player.y = CX, WALL + ENTER_OFFSET
        elif from_dir == "S":
            self.player.x, self.player.y = CX, HEIGHT - WALL - ENTER_OFFSET
        elif from_dir == "W":
            self.player.x, self.player.y = WALL + ENTER_OFFSET, CY
        elif from_dir == "E":
            self.player.x, self.player.y = WIDTH - WALL - ENTER_OFFSET, CY
        if room.kind == "normal" and not room.spawned:
            self.spawn_enemies(room)
            room.spawned = True
        if room.kind == "boss" and not room.cleared and room.boss is None:
            kind = random.choice(BOSS_KINDS)  # случайный тип босса
            room.boss = Boss(kind, BOSS_HP_BASE + self.floor_num * BOSS_HP_PER_FLOOR, self.floor_num)

    def record_floor(self):
        # запоминаем лучший этаж в сейв
        rec = SAVE["characters"].get(self.char_id, {})
        rec["best_floor"] = max(rec.get("best_floor", 0), self.floor_num)
        SAVE["characters"][self.char_id] = rec
        save_progress(SAVE)

    def record_win(self):
        # отмечаем персонажа как пройденного
        rec = SAVE["characters"].get(self.char_id, {})
        rec["completed"] = True
        rec["best_floor"] = max(rec.get("best_floor", 0), self.floor_num)
        SAVE["characters"][self.char_id] = rec
        save_progress(SAVE)

    def spawn_enemies(self, room):
        # сколько и каких врагов накидать, не впритык к игроку и не в стену
        count = SPAWN_BASE + self.floor_num + random.randint(0, SPAWN_RAND) + current_diff["spawn"]
        count = max(1, count)
        pool = ["chaser", "fast", "shooter"]
        if self.floor_num >= TIER2_FLOOR:
            pool += ["tank", "splitter"]  # с этого этажа добавляем потяжелее
        blockers = [o.rect for o in room.obstacles]
        half = SPAWN_RECT // 2
        for i in range(count):
            x = y = 0
            for attempt in range(SPAWN_TRIES):
                # тыкаем случайную точку, пока не попадём в свободную
                x = random.randint(WALL + SPAWN_MARGIN, WIDTH - WALL - SPAWN_MARGIN)
                y = random.randint(WALL + SPAWN_MARGIN, HEIGHT - WALL - SPAWN_MARGIN)
                er = pygame.Rect(x - half, y - half, SPAWN_RECT, SPAWN_RECT)
                if math.hypot(x - self.player.x, y - self.player.y) <= SPAWN_MIN_DIST:
                    continue
                if hits_wall(er, blockers):
                    continue
                break
            room.enemies.append(Enemy(random.choice(pool), x, y, self.floor_num))

    def make_bullets(self, dx, dy):
        # стрельба игрока: тройной даёт разлёт, двойной — две параллельные
        p = self.player
        spreads = [-TRIPLE_SPREAD, 0, TRIPLE_SPREAD] if p.triple else [0]
        shots = []
        for sp in spreads:
            nx = dx * math.cos(sp) - dy * math.sin(sp)
            ny = dx * math.sin(sp) + dy * math.cos(sp)
            shots.append((nx, ny, 0, 0))
        if p.double:
            perp = (-dy, dx)
            extra = []
            for (nx, ny, ox, oy) in shots:
                extra.append((nx, ny, perp[0] * DOUBLE_OFFSET, perp[1] * DOUBLE_OFFSET))
                extra.append((nx, ny, -perp[0] * DOUBLE_OFFSET, -perp[1] * DOUBLE_OFFSET))
            shots = shots + extra
        for (nx, ny, ox, oy) in shots:
            b = Bullet(p.x + ox, p.y + oy, nx, ny, True)
            b.life = p.bullet_life
            b.damage = p.damage
            b.speed = max(3, p.bullet_speed)
            b.radius = max(3, int(p.tear_size))
            if p.pierce:
                b.pierce = True
            if p.homing:
                b.homing = True
            self.bullets.append(b)
            self.emit("shot")  # звук на каждую вылетевшую пулю

    def apply_item(self, kind):
        # навешиваем эффект предмета: статы по ключам + флаги
        p = self.player
        d = ITEM_DEFS.get(kind)
        if d is None:
            return
        stats = d.get("stats", {})
        if "max_half" in stats:
            p.max_half += stats["max_half"]
        for key, val in stats.items():
            if key == "full_map":
                self.full_map = True
            elif key == "max_shield":
                p.max_shield += val
                p.shield = p.max_shield
            elif key == "max_half":
                pass
            elif key == "half":
                p.half = min(p.max_half, p.half + val)
            elif key == "damage":
                p.damage = max(1, p.damage + val)
            elif key == "cooldown_max":
                p.cooldown_max = max(5, p.cooldown_max + val)
            elif key == "bullet_speed":
                p.bullet_speed = max(3, p.bullet_speed + val)
            elif key == "bullet_life":
                p.bullet_life = max(20, p.bullet_life + val)
            elif key == "tear_size":
                p.tear_size = max(3, p.tear_size + val)
            elif key == "speed":
                p.speed = max(1.0, p.speed + val)
            elif key == "luck":
                p.luck += val
        for flag in d.get("flags", []):
            setattr(p, flag, True)

    def try_drop_coin(self, x, y):
        # шанс выронить монету с врага, удача повышает
        p = self.player
        chance = COIN_DROP + COIN_DROP_LUCK * p.luck
        chance = min(max(chance, COIN_DROP_MIN), COIN_DROP_MAX)
        if random.random() < chance:
            self.room().coins.append(Coin(x, y))

    def break_barrel(self, obstacle):
        # из разбитой бочки может выпасть монета и сердце
        chance = BARREL_COIN + BARREL_COIN_LUCK * self.player.luck
        chance = min(max(chance, COIN_DROP_MIN), BARREL_COIN_MAX)
        if random.random() < chance:
            self.room().coins.append(Coin(obstacle.rect.centerx, obstacle.rect.centery))
        self.try_drop_heart(obstacle.rect.centerx, obstacle.rect.centery)

    def try_drop_heart(self, x, y):
        # редкий дроп сердца: целое реже, половинка чаще
        r = random.random()
        if r < HEART_FULL_CHANCE:
            self.room().hearts.append(Heart(x, y, "full"))
        elif r < HEART_HALF_CHANCE:
            self.room().hearts.append(Heart(x, y, "half"))

    def hurt_player(self, amount):
        # урон игроку: неуязвимость спасает, щит съедает удар первым
        p = self.player
        if p.invuln > 0:
            return
        if p.shield > 0:
            p.shield -= 1
            p.invuln = INVULN_SHIELD
            self.emit("hurt")
            return
        p.half -= amount
        p.invuln = INVULN_HIT
        self.emit("hurt")
        if not p.alive:
            p.half = 0
            self.state = "lose"
            self.emit("lose")
            self.record_floor()

    def nearest_target(self, x, y):
        # ближайший враг или босс — для самонаводящихся пуль
        room = self.room()
        best = None
        bestd = math.inf
        for e in room.enemies:
            d = math.hypot(e.x - x, e.y - y)
            if d < bestd:
                bestd = d
                best = e
        if room.boss is not None:
            d = math.hypot(room.boss.x - x, room.boss.y - y)
            if d < bestd:
                best = room.boss
        return best

    def update(self, keys):
        # главный апдейт кадра: ввод, физика, столкновения, подборы, переходы
        p = self.player
        room = self.room()
        self.frame += 1
        self.events = []  # события этого кадра под звук

        # передвижение игрока (wasd), откат если влезли в стену
        old_x, old_y = p.x, p.y
        if keys[pygame.K_w]:
            p.y -= p.speed
        if keys[pygame.K_s]:
            p.y += p.speed
        if keys[pygame.K_a]:
            p.x -= p.speed
        if keys[pygame.K_d]:
            p.x += p.speed
        walls = get_walls(room)
        solids = [o for o in room.obstacles if o.solid()]
        move_blockers = walls + [o.rect for o in room.obstacles if o.solid() or o.is_pit()]
        resolve_move(p, old_x, old_y, move_blockers)  # скользим вдоль стены, а не залипаем

        # анимация ходьбы и куда смотрим
        p.moving = keys[pygame.K_w] or keys[pygame.K_s] or keys[pygame.K_a] or keys[pygame.K_d]
        if keys[pygame.K_a]:
            p.facing = -1
        elif keys[pygame.K_d]:
            p.facing = 1
        if p.moving:
            p.anim += ANIM_STEP
        else:
            p.anim = 0.0

        # тикаем таймеры: неуязвимость, перезарядка, восстановление щита
        if p.invuln > 0:
            p.invuln -= 1
        if p.cooldown > 0:
            p.cooldown -= 1
        if p.shield < p.max_shield:
            p.shield_recharge += 1
            if p.shield_recharge >= SHIELD_RECHARGE:
                p.shield += 1
                p.shield_recharge = 0

        # стрельба стрелками, если перезарядка прошла
        if p.cooldown == 0:
            fired = False
            if keys[pygame.K_UP]:
                self.make_bullets(0, -1)
                fired = True
            elif keys[pygame.K_DOWN]:
                self.make_bullets(0, 1)
                fired = True
            elif keys[pygame.K_LEFT]:
                self.make_bullets(-1, 0)
                fired = True
            elif keys[pygame.K_RIGHT]:
                self.make_bullets(1, 0)
                fired = True
            if fired:
                p.cooldown = p.cooldown_max

        # наши пули: самонаведение, полёт, удар по стенам и бочкам
        for b in self.bullets[:]:
            if b.homing:
                target = self.nearest_target(b.x, b.y)
                if target is not None:
                    tx = target.x - b.x
                    ty = target.y - b.y
                    d = math.hypot(tx, ty)
                    if d != 0:
                        b.dx += (tx / d - b.dx) * HOMING_TURN
                        b.dy += (ty / d - b.dy) * HOMING_TURN
                        nd = math.hypot(b.dx, b.dy)
                        if nd != 0:
                            b.dx /= nd
                            b.dy /= nd
            b.update()
            if b.life <= 0 or hits_wall(b.get_rect(), walls):
                if b in self.bullets:
                    self.bullets.remove(b)
                continue
            for o in solids:
                if b.get_rect().colliderect(o.rect):
                    if o.kind == "barrel":
                        o.hp -= b.damage
                        if o.hp <= 0 and o in room.obstacles:
                            room.obstacles.remove(o)
                            self.break_barrel(o)
                    if not b.pierce and b in self.bullets:
                        self.bullets.remove(b)
                    break

        # вражеские пули: летят, бьют по игроку или гаснут о стены
        for b in self.enemy_bullets[:]:
            b.update()
            if b.life <= 0 or hits_wall(b.get_rect(), walls) or hits_wall(b.get_rect(), [o.rect for o in solids]):
                if b in self.enemy_bullets:
                    self.enemy_bullets.remove(b)
            elif b.get_rect().colliderect(p.get_rect()):
                self.hurt_player(1)
                if b in self.enemy_bullets:
                    self.enemy_bullets.remove(b)

        # враги: двигаем, бьём игрока в упор, ловим попадания наших пуль
        enemy_shots_before = len(self.enemy_bullets)
        for enemy in room.enemies[:]:
            eox, eoy = enemy.x, enemy.y
            enemy.update(p, self.enemy_bullets, room)
            if not enemy.phases:
                resolve_move(enemy, eox, eoy, move_blockers)  # скользит у стены, как и игрок
            if enemy.spawn_timer > 0:
                continue
            if enemy.get_rect().colliderect(p.get_rect()):
                self.hurt_player(enemy.damage)
            eid = id(enemy)
            for b in self.bullets[:]:
                if not b.get_rect().colliderect(enemy.get_rect()):
                    continue
                last = b.hit_targets.get(eid)
                if last is not None and self.frame - last < REHIT_FRAMES:
                    continue  # пробивающая не лупит одну цель каждый кадр
                enemy.hp -= b.damage
                b.hit_targets[eid] = self.frame
                if not b.pierce and b in self.bullets:
                    self.bullets.remove(b)
                if not enemy.alive:
                    if enemy in room.enemies:
                        room.enemies.remove(enemy)
                    self.kills += 1
                    self.emit("enemy_die")
                    if enemy.splits:
                        # сплиттер на смерти плодит мелких
                        child_kind, child_n = enemy.splits
                        for j in range(child_n):
                            room.enemies.append(Enemy(child_kind,
                                                      enemy.x + random.randint(-SPLITTER_SPREAD, SPLITTER_SPREAD),
                                                      enemy.y + random.randint(-SPLITTER_SPREAD, SPLITTER_SPREAD),
                                                      self.floor_num))
                    self.try_drop_coin(enemy.x, enemy.y)
                    self.try_drop_heart(enemy.x, enemy.y)
                    if p.vampire and random.random() < VAMPIRE_CHANCE:
                        p.half = min(p.max_half, p.half + 1)
                    break
                self.emit("enemy_hit")
                if not b.pierce:
                    break
        for _ in range(max(0, len(self.enemy_bullets) - enemy_shots_before)):
            self.emit("shot")  # звук на каждую пулю, что вылетела у врагов

        # босс: бьём, на смерти открываем люк и кидаем награду
        if room.boss is not None:
            boss = room.boss
            boss_shots_before = len(self.enemy_bullets)
            boss.update(p, self.enemy_bullets, room)
            for _ in range(max(0, len(self.enemy_bullets) - boss_shots_before)):
                self.emit("shot")
            if boss.get_rect().colliderect(p.get_rect()):
                self.hurt_player(1)
            bid = id(boss)
            for b in self.bullets[:]:
                if not b.get_rect().colliderect(boss.get_rect()):
                    continue
                last = b.hit_targets.get(bid)
                if last is not None and self.frame - last < REHIT_FRAMES:
                    continue
                boss.hp -= b.damage
                b.hit_targets[bid] = self.frame
                if not b.pierce and b in self.bullets:
                    self.bullets.remove(b)
                if not boss.alive:
                    room.boss = None
                    room.cleared = True
                    room.trapdoor = True
                    self.enemy_bullets = []
                    self.emit("boss_die")
                    if BOSS_POOL:
                        room.pedestals.append(Pedestal(CX, CY - BOSS_PEDESTAL_DY,
                                                       random.choice(BOSS_POOL), 0))
                    break
                self.emit("enemy_hit")
                if not b.pierce:
                    break

        # подбор монет
        for coin in room.coins[:]:
            if coin.get_rect().colliderect(p.get_rect()):
                p.coins += 1
                room.coins.remove(coin)
                self.emit("coin")

        # подбор сердец, только если не полное хп
        for h in room.hearts[:]:
            if p.half < p.max_half and h.get_rect().colliderect(p.get_rect()):
                p.half = min(p.max_half, p.half + (2 if h.kind == "full" else 1))
                room.hearts.remove(h)
                self.emit("heart")

        # тумбы: бесплатные берём сразу, в магазине — если хватает монет
        for ped in room.pedestals:
            if ped.bought:
                continue
            if ped.get_rect().colliderect(p.get_rect()):
                if ped.price == 0:
                    self.apply_item(ped.kind)
                    ped.bought = True
                    self.emit("heart")
                elif p.coins >= ped.price:
                    p.coins -= ped.price
                    self.apply_item(ped.kind)
                    ped.bought = True
                    self.emit("heart")

        # комната считается зачищенной, когда врагов не осталось
        if room.kind == "normal" and room.spawned and len(room.enemies) == 0:
            room.cleared = True

        # встал на люк — уходим на следующий этаж
        if room.trapdoor:
            trapdoor = pygame.Rect(CX - TRAPDOOR_SIZE // 2, CY - TRAPDOOR_SIZE // 2, TRAPDOOR_SIZE, TRAPDOOR_SIZE)
            if trapdoor.colliderect(p.get_rect()):
                self.next_floor()
                return

        # дошёл до двери зачищенной комнаты — переходим к соседу
        if room.cleared:
            for name, d in DIRS:
                if name in room.doors and door_zone(name).colliderect(p.get_rect()):
                    nb = self.neighbor_cell(name)
                    if nb in self.grid:
                        self.enter_room(nb, OPPOSITE[name])
                        return

    def next_floor(self):
        # следующий этаж, либо победа если прошли последний
        if self.floor_num >= MAX_FLOOR:
            self.state = "win"
            self.emit("win")
            self.record_win()
            return
        self.floor_num += 1
        self.grid, self.start = generate_floor(self.floor_num)
        self.cur = self.start
        self.bullets = []
        self.enemy_bullets = []
        self.player.x, self.player.y = CX, CY
        start_room = self.grid[self.cur]
        start_room.visited = True
        start_room.obstacles = build_obstacles(start_room.layout)
        start_room.built = True
