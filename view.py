import os
import pygame

from settings import (
    BAR_WIDTH, BG_COLOR, BIG_FONT_SIZE, BOSS_COLOR, BOSS_DOOR_COL, BOSS_NAMES,
    BOSS_SPRITE_OUTLINE, CAPTION, COIN_COLOR, CX, CY, DIFFICULTIES, DIRS,
    ENEMY_COLOR, ENEMY_SPRITE_OUTLINE, ENTITY_OUTLINE, FLOOR_COLOR, FONT_SIZE,
    HEIGHT, LOGO_CENTER_X, LOGO_CENTER_Y, LOGO_HEIGHT, LOGO_WIDTH, MAX_FLOOR,
    MENU_LEFT_X, MENU_OPTIONS_TOP, MINIMAP_CELL, PALETTE,
    RESOLUTIONS, SHOP_COL, SMALL_FONT_SIZE, SPAWN_BLINK, SPRITE_DIR,
    TEXT_COLOR, TRAPDOOR_SIZE, TREASURE_COL, WALL, WALL_COLOR, WIDTH,
)
import engine

# тут вся отрисовка, логику не трогаем

screen = None
display = None
clock = None
font = None
big_font = None
small_font = None
PLAYER_WALK_FRAMES = 0

sprite_cache = {}
scaled_cache = {}


def apply_video():
    # пересоздаём настоящее окно под выбранное разрешение и режим из настроек
    global display
    res = RESOLUTIONS[engine.SAVE["resolution_idx"]]
    flags = pygame.FULLSCREEN if engine.SAVE["fullscreen"] else 0
    display = pygame.display.set_mode(res, flags)


def present():
    # рисуем всегда в свой холст фиксированного размера, тут растягиваем его на настоящее окно
    if display.get_size() == screen.get_size():
        display.blit(screen, (0, 0))
    else:
        pygame.transform.scale(screen, display.get_size(), display)
    pygame.display.flip()


def init_window():
    # открываем окно и грузим шрифты, зовём один раз на старте
    global screen, clock, font, big_font, small_font, PLAYER_WALK_FRAMES
    pygame.init()
    screen = pygame.Surface((WIDTH, HEIGHT))
    apply_video()
    pygame.display.set_caption(CAPTION)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", FONT_SIZE)
    big_font = pygame.font.SysFont("arial", BIG_FONT_SIZE)
    small_font = pygame.font.SysFont("arial", SMALL_FONT_SIZE)
    PLAYER_WALK_FRAMES = count_frames("player_walk_")
    return screen, clock


def get_sprite(name):
    # достаём картинку из кэша или грузим с диска (png или анимированный gif)
    if name in sprite_cache:
        cached = sprite_cache[name]
        if isinstance(cached, list):
            # gif хранится списком кадров, крутим по времени
            frame_idx = (pygame.time.get_ticks() // 100) % len(cached)
            return cached[frame_idx]
        return cached

    path_png = os.path.join(SPRITE_DIR, name + ".png")
    path_gif = os.path.join(SPRITE_DIR, name + ".gif")

    img = None
    if os.path.exists(path_gif):
        # режем gif на кадры через PIL
        try:
            from PIL import Image
            pil_img = Image.open(path_gif)
            frames = []
            for frame in range(pil_img.n_frames):
                pil_img.seek(frame)
                frame_rgba = pil_img.convert("RGBA")
                raw_data = frame_rgba.tobytes("raw", "RGBA")
                size = frame_rgba.size
                py_image = pygame.image.fromstring(raw_data, size, "RGBA").convert_alpha()
                frames.append(py_image)
            sprite_cache[name] = frames
            if frames:
                frame_idx = (pygame.time.get_ticks() // 100) % len(frames)
                return frames[frame_idx]
        except (OSError, pygame.error):
            pass

    if os.path.exists(path_png):
        try:
            img = pygame.image.load(path_png).convert_alpha()
            sprite_cache[name] = img
        except (OSError, pygame.error):
            img = None
    else:
        sprite_cache[name] = None

    return img


def draw_sprite(name, cx, cy, w, h, flip=False):
    # рисуем спрайт по центру, кэшируем уже отмасштабированный вариант
    base = get_sprite(name)
    if base is None:
        return False
    key = (name, int(w), int(h), flip, id(base))
    img = scaled_cache.get(key)
    if img is None:
        img = pygame.transform.scale(base, (max(1, int(w)), max(1, int(h))))
        if flip:
            img = pygame.transform.flip(img, True, False)
        scaled_cache[key] = img
    screen.blit(img, (int(cx - w / 2), int(cy - h / 2)))
    return True


def count_frames(prefix):
    # считаем сколько кадров ходьбы лежит на диске
    n = 0
    while get_sprite(prefix + str(n)) is not None:
        n += 1
    return n


def draw_player(p):
    # игрок: спрайт ходьбы
    name = "player"
    if p.moving and PLAYER_WALK_FRAMES > 0:
        name = "player_walk_" + str(int(p.anim) % PLAYER_WALK_FRAMES)
    size = p.size + ENTITY_OUTLINE
    draw_sprite(name, p.x, p.y, size, size, p.facing < 0)
    if p.shield > 0:
        pygame.draw.circle(screen, PALETTE["shield"], (int(p.x), int(p.y)), p.size, 2)


def draw_bullet(b):
    # пуля, своя или вражеская
    name = "bullet" if b.from_player else "bullet_enemy"
    draw_sprite(name, b.x, b.y, b.radius * 2, b.radius * 2)


def draw_enemy(e):
    # враг: пока спавнится мигает кольцом, потом своя картинка под тип
    x, y, r = int(e.x), int(e.y), e.radius
    if e.spawn_timer > 0:
        if (e.spawn_timer // SPAWN_BLINK) % 2 == 0:
            pygame.draw.circle(screen, PALETTE["spawn_ring"], (x, y), r, 2)
        return
    outline = 16 if e.kind == "small" else ENEMY_SPRITE_OUTLINE
    sprite_size = r * 2 + outline
    draw_sprite("enemy_" + e.kind, x, y, sprite_size, sprite_size)


def draw_boss(b):
    # босс + полоска хп сверху
    x, y = int(b.x), int(b.y)
    boss_size = b.radius * 2 + BOSS_SPRITE_OUTLINE
    draw_sprite("boss_" + b.kind, x, y, boss_size, boss_size)
    ratio = max(0, b.hp / b.max_hp)
    pygame.draw.rect(screen, PALETTE["bar_back"], (CX - BAR_WIDTH // 2, 14, BAR_WIDTH, 14))
    pygame.draw.rect(screen, BOSS_COLOR, (CX - BAR_WIDTH // 2, 14, int(BAR_WIDTH * ratio), 14))
    t = small_font.render(BOSS_NAMES.get(b.kind, "Вирус-Веер"), True, TEXT_COLOR)
    screen.blit(t, (CX - t.get_width() // 2, 30))


def draw_obstacle(o):
    # препятствия: камень/ящик/яма/бочка
    r = o.rect
    if o.kind == "pit":
        pygame.draw.rect(screen, PALETTE["pit"], r)  # яма - просто чёрный квадрат на весь тайл
        return
    draw_sprite(o.kind, r.centerx, r.centery, r.w, r.h)


def draw_coin(c):
    # монетка, рисуется только спрайтом
    if draw_sprite("coin", c.x, c.y, c.radius * 4, c.radius * 4):
        return


def draw_heart_pickup(h):
    # сердце-подбиралка на полу
    draw_sprite("heart_" + h.kind, h.x, h.y, h.radius * 2, h.radius * 2)


def draw_pedestal(ped):
    # тумба с предметом + ценник
    draw_sprite("pedestal", ped.x, ped.y + 18, 40, 26)
    if not ped.bought:
        # предмет - просто цветной квадрат, как для бета-теста
        rect = pygame.Rect(0, 0, 28, 28)
        rect.center = (int(ped.x), int(ped.y - 6))
        pygame.draw.rect(screen, engine.item_color(ped.kind), rect)
        label = engine.ITEM_NAMES.get(ped.kind, ped.kind)
        t = small_font.render(label, True, TEXT_COLOR)
        screen.blit(t, (ped.x - t.get_width() // 2, ped.y - 44))
        if ped.price > 0:
            pt = small_font.render(str(ped.price) + " мон.", True, COIN_COLOR)
            screen.blit(pt, (ped.x - pt.get_width() // 2, ped.y + 30))


def draw_hud_heart(x, y, state):
    # сердечко в углу: полное/половина/пустое
    s = 30
    draw_sprite("heart_" + state, x + s // 2, y + s // 2, s, s)


def draw_room(game):
    # вся комната: пол, стены, двери, предметы, враги, пули, игрок
    room = game.room()
    pygame.draw.rect(screen, FLOOR_COLOR, (WALL, WALL, WIDTH - 2 * WALL, HEIGHT - 2 * WALL))
    for w in engine.get_walls(room):
        pygame.draw.rect(screen, WALL_COLOR, w)
    for name, d in DIRS:
        if name not in room.doors:
            continue
        color = game.door_color(name)
        if not room.cleared:
            pygame.draw.rect(screen, color, engine.door_zone(name))  # закрытая дверь во всю дырку
        else:
            pygame.draw.rect(screen, color, engine.door_strip(name))

    for o in room.obstacles:
        draw_obstacle(o)
    for ped in room.pedestals:
        draw_pedestal(ped)
    for c in room.coins:
        draw_coin(c)
    for h in room.hearts:
        draw_heart_pickup(h)
    if room.trapdoor:
        # люк на следующий этаж после босса
        box = (CX - TRAPDOOR_SIZE // 2, CY - TRAPDOOR_SIZE // 2, TRAPDOOR_SIZE, TRAPDOOR_SIZE)
        pygame.draw.rect(screen, PALETTE["trapdoor"], box)
        pygame.draw.rect(screen, PALETTE["trapdoor_edge"], box, 4)
        t = small_font.render("ДАЛЕЕ", True, PALETTE["trapdoor_text"])
        screen.blit(t, (CX - t.get_width() // 2, CY - 10))

    for e in room.enemies:
        draw_enemy(e)
    if room.boss is not None:
        draw_boss(room.boss)
    for b in game.bullets:
        draw_bullet(b)
    for b in game.enemy_bullets:
        draw_bullet(b)
    draw_player(game.player)


def draw_hud(game):
    # интерфейс: сердца, монеты, этаж, статы, название комнаты
    p = game.player
    hearts = p.max_half // 2
    for i in range(hearts):
        remaining = p.half - i * 2
        if remaining >= 2:
            st = "full"
        elif remaining == 1:
            st = "half"
        else:
            st = "empty"
        draw_hud_heart(20 + i * 36, 20, st)

    coin_text = font.render("Монеты: " + str(p.coins), True, COIN_COLOR)
    screen.blit(coin_text, (20, 58))
    floor_text = font.render("Этаж: " + str(game.floor_num) + "/" + str(MAX_FLOOR), True, TEXT_COLOR)
    screen.blit(floor_text, (20, 110))

    stats = [
        "Урон " + str(round(p.damage, 1)),
        "Темп " + str(round(60.0 / max(1, p.cooldown_max), 1)) + "/с",
        "Скорость снаряда " + str(round(p.bullet_speed, 1)),
        "Дальность " + str(p.bullet_life),
        "Размер " + str(int(p.tear_size)),
        "Удача " + str(p.luck),
        "Скорость " + str(round(p.speed, 1)),
    ]
    for i, s in enumerate(stats):
        t = small_font.render(s, True, PALETTE["stat_text"])
        screen.blit(t, (20, 142 + i * 17))

    room = game.room()
    name = {"start": "Старт", "normal": "", "boss": "КОМНАТА БОССА",
            "treasure": "Сокровищница", "shop": "Магазин"}.get(room.kind, "")
    if name:
        color = BOSS_COLOR if room.kind == "boss" else TEXT_COLOR
        t = small_font.render(name, True, color)
        screen.blit(t, (CX - t.get_width() // 2, HEIGHT - 28))


def draw_minimap(game):
    # мини-карта в углу, показываем посещённые и соседние комнаты
    cells = game.grid
    rs = [c[0] for c in cells]
    cs = [c[1] for c in cells]
    minr, maxr = min(rs), max(rs)
    minc, maxc = min(cs), max(cs)
    cell = MINIMAP_CELL
    cols = maxc - minc + 1
    rows = maxr - minr + 1
    ox = WIDTH - cols * cell - 24
    oy = 24
    pygame.draw.rect(screen, PALETTE["minimap_back"], (ox - 8, oy - 8, cols * cell + 16, rows * cell + 16))

    neighbors = set()
    for name, d in DIRS:
        neighbors.add((game.cur[0] + d[0], game.cur[1] + d[1]))

    for (r, c), room in cells.items():
        shown = game.full_map or room.visited
        known = shown
        if not known:
            # соседние тоже подсвечиваем, но тускло
            for name, d in DIRS:
                nb = (r + d[0], c + d[1])
                if nb in cells and cells[nb].visited:
                    known = True
                    break
        if not known:
            continue
        x = ox + (c - minc) * cell
        y = oy + (r - minr) * cell
        if shown:
            color = {
                "boss": BOSS_DOOR_COL,
                "treasure": TREASURE_COL,
                "shop": SHOP_COL,
                "start": PALETTE["minimap_start"],
            }.get(room.kind, PALETTE["minimap_room"])
        else:
            color = PALETTE["minimap_unknown"]
        pygame.draw.rect(screen, color, (x + 1, y + 1, cell - 2, cell - 2))
        if (r, c) in neighbors:
            pygame.draw.rect(screen, PALETTE["minimap_near"], (x + 1, y + 1, cell - 2, cell - 2), 1)
        if (r, c) == game.cur:
            pygame.draw.rect(screen, PALETTE["minimap_here"], (x + 1, y + 1, cell - 2, cell - 2), 2)  # где мы сейчас


def draw_option_list(options, index, cx_left, top, step):
    # общий список пунктов для меню и паузы, выбранный со стрелкой
    for i, opt in enumerate(options):
        color = PALETTE["menu_sel"] if i == index else TEXT_COLOR
        prefix = "> " if i == index else "   "
        line = font.render(prefix + opt, True, color)
        screen.blit(line, (cx_left, top + i * step))


def draw_end_screen(title, title_color, info_text):
    # общий экран конца и для победы, и для проигрыша
    t = big_font.render(title, True, title_color)
    screen.blit(t, (CX - t.get_width() // 2, CY - 90))
    info = font.render(info_text, True, TEXT_COLOR)
    screen.blit(info, (CX - info.get_width() // 2, CY))
    r = font.render("R - заново, Esc - в меню", True, TEXT_COLOR)
    screen.blit(r, (CX - r.get_width() // 2, CY + 40))


def draw_game(game):
    # главный рисователь по состоянию игры
    screen.fill(BG_COLOR)
    if game.state == "playing":
        draw_room(game)
        draw_hud(game)
        draw_minimap(game)
    elif game.state == "win":
        draw_end_screen("ПОБЕДА!", PALETTE["win"], "Вирус удалён. Убито: " + str(game.kills))
    elif game.state == "lose":
        draw_end_screen("ИГРА ОКОНЧЕНА", ENEMY_COLOR, "Система рухнула. Убито: " + str(game.kills))


def draw_menu(title, subtitle, options, index, footer):
    # главное меню: лого справа, кнопки слева
    screen.fill(BG_COLOR)
    if not draw_sprite("logo", LOGO_CENTER_X, LOGO_CENTER_Y, LOGO_WIDTH, LOGO_HEIGHT):
        t = big_font.render(title, True, PALETTE["menu_title"])
        screen.blit(t, (LOGO_CENTER_X - t.get_width() // 2, LOGO_CENTER_Y - 40))
    if subtitle:
        s = font.render(subtitle, True, PALETTE["menu_sub"])
        screen.blit(s, (MENU_LEFT_X, MENU_OPTIONS_TOP - 50))
    draw_option_list(options, index, MENU_LEFT_X, MENU_OPTIONS_TOP, 46)
    f = small_font.render(footer, True, PALETTE["menu_foot"])
    screen.blit(f, (MENU_LEFT_X, HEIGHT - 38))


def draw_settings(index, draft):
    # экран настроек: пункты слева (черновик, ещё не применённый), надпись "Настройки" справа
    screen.fill(BG_COLOR)
    t = big_font.render("Настройки", True, PALETTE["menu_title"])
    screen.blit(t, (LOGO_CENTER_X - t.get_width() // 2, LOGO_CENTER_Y - 40))

    diff_name = DIFFICULTIES[draft["difficulty"]]["name"]
    res_w, res_h = RESOLUTIONS[draft["resolution_idx"]]
    full_name = "Вкл" if draft["fullscreen"] else "Выкл"
    vol_name = str(int(draft["master_volume"] * 100)) + "%"
    rows = [
        "Сложность: " + diff_name,
        "Разрешение: " + str(res_w) + "x" + str(res_h),
        "Полный экран: " + full_name,
        "Громкость: " + vol_name,
        "Применить",
    ]
    draw_option_list(rows, index, MENU_LEFT_X, MENU_OPTIONS_TOP, 50)
    f = small_font.render("W/S - выбор, A/D - изменить, Enter - применить, Esc - назад", True, PALETTE["menu_foot"])
    screen.blit(f, (MENU_LEFT_X, HEIGHT - 38))


def draw_select(index):
    # экран выбора персонажа, карточками
    screen.fill(BG_COLOR)
    t = big_font.render("Выбор персонажа", True, PALETTE["menu_title"])
    screen.blit(t, (CX - t.get_width() // 2, 40))
    for i, ch in enumerate(engine.CHARACTERS):
        y = 140 + i * 92
        sel = i == index
        box = pygame.Rect(120, y, WIDTH - 240, 80)
        pygame.draw.rect(screen, PALETTE["select_box_sel"] if sel else PALETTE["select_box"], box)
        pygame.draw.rect(screen, PALETTE["menu_sel"] if sel else PALETTE["select_border"], box, 2)
        rec = engine.SAVE["characters"].get(ch["id"], {})
        title = ch["name"]
        if rec.get("completed"):
            title += "  (пройдено)"  # отметка что уже проходили
        name = font.render(title, True, PALETTE["eye"] if sel else TEXT_COLOR)
        screen.blit(name, (140, y + 10))
        desc = small_font.render(ch["desc"], True, PALETTE["select_desc"])
        screen.blit(desc, (140, y + 46))
    f = small_font.render("W/S - выбор, Enter - играть, Esc - назад", True, PALETTE["menu_foot"])
    screen.blit(f, (CX - f.get_width() // 2, HEIGHT - 30))


def draw_pause(index):
    # пауза: затемняем экран и кидаем меню сверху
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    t = big_font.render("Пауза", True, PALETTE["pause_title"])
    screen.blit(t, (CX - t.get_width() // 2, 140))
    draw_option_list(["Продолжить", "Заново", "В меню"], index, CX - 110, 250, 46)
