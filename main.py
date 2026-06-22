import pygame

from settings import DIFF_KEYS, FPS, RESOLUTIONS, SETTINGS_ROWS, VOLUME_STEP
import engine
import view
import audio

# главный цикл, ввод и переключение экранов


def main():
    screen, clock = view.init_window()
    audio.init_audio()

    # app — на каком мы сейчас экране, остальные _idx это курсоры в меню
    app = "menu"
    main_idx = 0
    char_idx = 0
    pause_idx = 0
    settings_idx = 0
    settings_draft = None  # черновик настроек, пока не нажмём "применить"
    game = None
    main_opts = ["Начать игру", "Настройки", "Выход"]
    running = True

    while running:
        clock.tick(FPS)
        # разбираем нажатия клавиш под текущий экран
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            if event.type != pygame.KEYDOWN:
                continue
            key = event.key
            up = key in (pygame.K_UP, pygame.K_w)
            down = key in (pygame.K_DOWN, pygame.K_s)
            left = key in (pygame.K_LEFT, pygame.K_a)
            right = key in (pygame.K_RIGHT, pygame.K_d)
            ok = key in (pygame.K_RETURN, pygame.K_SPACE)

            if app == "menu":
                if up:
                    main_idx = (main_idx - 1) % len(main_opts)
                elif down:
                    main_idx = (main_idx + 1) % len(main_opts)
                elif ok:
                    if main_idx == 0:
                        app = "select"
                    elif main_idx == 1:
                        settings_idx = 0
                        settings_draft = dict(engine.SAVE)  # копия текущих настроек на редактирование
                        app = "settings"
                    else:
                        running = False
                elif key == pygame.K_ESCAPE:
                    running = False

            elif app == "select":
                if up:
                    char_idx = (char_idx - 1) % len(engine.CHARACTERS)
                elif down:
                    char_idx = (char_idx + 1) % len(engine.CHARACTERS)
                elif ok:
                    game = engine.Game(engine.CHARACTERS[char_idx])  # новая игра выбранным героем
                    app = "play"
                elif key == pygame.K_ESCAPE:
                    app = "menu"

            elif app == "settings":
                if up:
                    settings_idx = (settings_idx - 1) % SETTINGS_ROWS
                elif down:
                    settings_idx = (settings_idx + 1) % SETTINGS_ROWS
                elif left or right:
                    step = -1 if left else 1
                    if settings_idx == 0:
                        # сложность по кругу, меняем только черновик
                        cur = DIFF_KEYS.index(settings_draft["difficulty"])
                        settings_draft["difficulty"] = DIFF_KEYS[(cur + step) % len(DIFF_KEYS)]
                    elif settings_idx == 1:
                        # разрешение
                        settings_draft["resolution_idx"] = (settings_draft["resolution_idx"] + step) % len(RESOLUTIONS)
                    elif settings_idx == 2:
                        # вкл/выкл полный экран
                        settings_draft["fullscreen"] = not settings_draft["fullscreen"]
                    elif settings_idx == 3:
                        # громкость
                        new_vol = settings_draft["master_volume"] + step * VOLUME_STEP
                        settings_draft["master_volume"] = max(0.0, min(1.0, round(new_vol, 2)))
                elif ok and settings_idx == 4:
                    # применить — только тут черновик реально сохраняется и срабатывает
                    engine.set_difficulty(settings_draft["difficulty"])
                    engine.set_resolution(settings_draft["resolution_idx"])
                    engine.set_fullscreen(settings_draft["fullscreen"])
                    engine.set_master_volume(settings_draft["master_volume"])
                    view.apply_video()
                    audio.apply_volume()
                elif key == pygame.K_ESCAPE:
                    app = "menu"

            elif app == "play":
                if key == pygame.K_ESCAPE:
                    if game.state == "playing":
                        pause_idx = 0
                        app = "pause"
                    else:
                        app = "menu"
                elif key == pygame.K_r and game.state != "playing":
                    game = engine.Game(engine.CHARACTERS[char_idx])  # рестарт после конца

            elif app == "pause":
                if up:
                    pause_idx = (pause_idx - 1) % 3
                elif down:
                    pause_idx = (pause_idx + 1) % 3
                elif ok:
                    if pause_idx == 0:
                        app = "play"
                    elif pause_idx == 1:
                        game = engine.Game(engine.CHARACTERS[char_idx])
                        app = "play"
                    else:
                        app = "menu"
                elif key == pygame.K_ESCAPE:
                    app = "play"

        # обновляем игру и проигрываем накопленные за кадр звуки
        if app == "play" and game.state == "playing":
            keys = pygame.key.get_pressed()
            game.update(keys)
            audio.play_events(game.events)

        # музыка под экран: меню или этаж/босс
        if app in ("menu", "select", "settings"):
            audio.music("menu")
        elif app == "play" and game.state == "playing":
            audio.music("boss" if game.room().boss is not None else "floor")

        # рисуем нужный экран
        if app == "menu":
            view.draw_menu("Debug.exe", "Главное меню", main_opts, main_idx,
                           "")
        elif app == "select":
            view.draw_select(char_idx)
        elif app == "settings":
            view.draw_settings(settings_idx, settings_draft)
        elif app == "play":
            view.draw_game(game)
        elif app == "pause":
            view.draw_game(game)
            view.draw_pause(pause_idx)

        view.present()

    pygame.quit()


if __name__ == "__main__":
    main()
