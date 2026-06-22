import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import engine


class NoKeys:
    # заглушка клавиатуры
    def __getitem__(self, key):
        return False


def test_items_loaded():
    # предметы и пулы из json
    assert "damage" in engine.ITEM_DEFS
    assert len(engine.ITEM_POOL) > 0
    assert len(engine.BOSS_POOL) > 0


def test_characters_loaded():
    # персонажи
    assert len(engine.CHARACTERS) >= 2
    for ch in engine.CHARACTERS:
        assert "id" in ch
        assert "name" in ch


def test_bfs_distances():
    # bfs считает расстояния правильно
    grid = {(0, 0): 1, (0, 1): 1, (0, 2): 1, (1, 2): 1}
    dist = engine.bfs(grid, (0, 0))
    assert dist[(0, 0)] == 0
    assert dist[(0, 1)] == 1
    assert dist[(0, 2)] == 2
    assert dist[(1, 2)] == 3


def test_generate_floor_invariants():
    # этаж генерится валидным: один босс в дальнем тупике, есть магазин и сокровищница
    for floor in range(1, 4):
        for _ in range(20):
            grid, start = engine.generate_floor(floor)
            assert grid[start].kind == "start"
            bosses = [c for c, r in grid.items() if r.kind == "boss"]
            assert len(bosses) == 1
            boss = bosses[0]
            assert len(grid[boss].doors) == 1
            dist = engine.bfs(grid, start)
            assert len(dist) == len(grid)
            for c in grid:
                assert grid[c].kind in ("start", "normal", "boss", "treasure", "shop")
            specials = [r.kind for r in grid.values()]
            assert "treasure" in specials
            assert "shop" in specials
            for c, room in grid.items():
                if room.kind in ("treasure", "shop"):
                    assert len(room.doors) == 1
            assert dist[boss] == max(dist[c] for c in grid)


def test_apply_item_stat():
    # предмет на стат поднимает урон
    g = engine.Game()
    base = g.player.damage
    g.apply_item("damage")
    assert g.player.damage == base + 1


def test_apply_item_flag():
    # предмет-флаг включает тройной выстрел
    g = engine.Game()
    assert g.player.triple is False
    g.apply_item("triple")
    assert g.player.triple is True


def test_player_character_overrides():
    # выбранный персонаж перебивает дефолтные статы/флаги
    admin = next(c for c in engine.CHARACTERS if c["id"] == "admin")
    p = engine.Player(admin)
    assert p.max_half == 8
    tester = next(c for c in engine.CHARACTERS if c["id"] == "tester")
    p2 = engine.Player(tester)
    assert p2.pierce is True


def test_save_round_trip(tmp_path, monkeypatch):
    # сейв записался и прочитался без потерь
    path = tmp_path / "save.json"
    monkeypatch.setattr(engine, "SAVE_PATH", str(path))
    data = {"difficulty": "hard",
            "characters": {"coder": {"completed": True, "best_floor": 3}}}
    engine.save_progress(data)
    loaded = engine.load_save()
    assert loaded["difficulty"] == "hard"
    assert loaded["characters"]["coder"]["completed"] is True
    assert loaded["characters"]["coder"]["best_floor"] == 3


def test_record_win(tmp_path, monkeypatch):
    # победа отмечает персонажа пройденным
    path = tmp_path / "save.json"
    monkeypatch.setattr(engine, "SAVE_PATH", str(path))
    monkeypatch.setattr(engine, "SAVE", {"difficulty": "normal", "characters": {}})
    g = engine.Game(engine.CHARACTERS[0])
    g.record_win()
    assert engine.SAVE["characters"][g.char_id]["completed"] is True


def test_difficulty_scales_enemy_hp():
    # на сложной хп врага больше
    engine.current_diff = engine.DIFFICULTIES["normal"]
    e_normal = engine.Enemy("tank", 100, 100, 1)
    engine.current_diff = engine.DIFFICULTIES["hard"]
    e_hard = engine.Enemy("tank", 100, 100, 1)
    engine.current_diff = engine.DIFFICULTIES["normal"]
    assert e_hard.hp > e_normal.hp


def test_hits_wall_collision():
    # проверка столкновения прямоугольников
    walls = [pygame.Rect(0, 0, 50, 50)]
    assert engine.hits_wall(pygame.Rect(10, 10, 20, 20), walls) is True
    assert engine.hits_wall(pygame.Rect(200, 200, 20, 20), walls) is False


def test_pickup_heart_integration():
    # подбор сердца лечит и убирает его из комнаты
    g = engine.Game()
    p = g.player
    p.half = p.max_half - 2
    room = g.room()
    room.hearts.append(engine.Heart(p.x, p.y, "full"))
    g.update(NoKeys())
    assert p.half == p.max_half
    assert len(room.hearts) == 0


def test_build_obstacles_matches_layout():
    # число препятствий совпадает с символами в планировке
    layout = engine.LAYOUTS["normal"][0]
    obstacles = engine.build_obstacles(layout)
    expected = sum(row.count("#") + row.count("X") + row.count("O") + row.count("B")
                   for row in layout)
    assert len(obstacles) == expected


def test_entity_hierarchy():
    # все объекты наследуют Entity, круглые ещё и CircleEntity
    p = engine.Player()
    e = engine.Enemy("fast", 100, 100, 1)
    b = engine.Boss("spreader", 30, 1)
    for obj in (p, e, b, engine.Bullet(0, 0, 1, 0, True),
                engine.Coin(0, 0), engine.Heart(0, 0, "full"),
                engine.Pedestal(0, 0, "damage", 0), engine.Obstacle("rock", 0, 0)):
        assert isinstance(obj, engine.Entity)
        assert obj.get_rect().width > 0
    assert isinstance(e, engine.CircleEntity)
    assert not isinstance(p, engine.CircleEntity)


def test_enemy_hp_encapsulation():
    # hp через свойство не уходит в минус
    e = engine.Enemy("tank", 100, 100, 1)
    e.hp = -10
    assert e.hp == 0
    assert e.alive is False
    e.hp = 3
    assert e.alive is True


def test_player_alive_property():
    # alive у игрока завязан на hp
    p = engine.Player()
    assert p.alive is True
    p.half = 0
    assert p.alive is False


def test_astar_routes_around_wall():
    # путь огибает стену через дырку
    blocked = {(3, r) for r in range(0, engine.ROWS - 1)}
    path = engine.astar(blocked, (1, 4), (6, 4))
    assert path is not None
    assert path[0] == (1, 4) and path[-1] == (6, 4)
    assert all(cell not in blocked for cell in path[1:-1])


def test_astar_blocked_returns_none():
    # глухая стена — пути нет
    walled = {(3, r) for r in range(0, engine.ROWS)}
    assert engine.astar(walled, (1, 4), (6, 4)) is None


def test_ranged_enemy_shoots():
    # шутер стреляет, когда таймер дозрел
    shooter = engine.Enemy("shooter", engine.WALL + 50, engine.CY, 1)
    shooter.spawn_timer = 0
    shooter.shoot_timer = engine.SHOOTER_CD - 1
    target = engine.Player()
    target.x, target.y = engine.WIDTH - engine.WALL - 50, engine.CY
    bullets = []
    shooter.update(target, bullets)
    assert len(bullets) == 1
    assert bullets[0].from_player is False


def test_splitter_spawns_children_on_death():
    # сплиттер на смерти плодит двух мелких и шлёт событие
    g = engine.Game()
    enemy = engine.Enemy("splitter", g.player.x + 40, g.player.y, 1)
    enemy.spawn_timer = 0
    enemy.hp = 1
    g.room().enemies = [enemy]
    bullet = engine.Bullet(enemy.x, enemy.y, 1, 0, True)
    bullet.damage = 5
    g.bullets = [bullet]
    g.update(NoKeys())
    assert g.kills == 1
    assert "enemy_die" in g.events
    assert sum(1 for e in g.room().enemies if e.kind == "small") == 2


def test_shot_event_emitted():
    # выстрел кладёт событие в очередь под звук
    g = engine.Game()

    class UpKey:
        def __getitem__(self, key):
            return key == pygame.K_UP

    g.update(UpKey())
    assert "shot" in g.events
