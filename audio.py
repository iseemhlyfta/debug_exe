import os
import pygame

from settings import ASSETS_DIR, SOUND_FILES, MUSIC_FILES, SFX_VOLUME, MUSIC_VOLUME
import engine

# звук и музыка, если файлов нет — просто молчим, без падений

EXTENSIONS = (".ogg", ".wav")

available = False
sounds = {}
current_music = None


def _find(name):
    # ищем файл по имени с любым из расширений
    for ext in EXTENSIONS:
        path = os.path.join(ASSETS_DIR, name + ext)
        if os.path.exists(path):
            return path
    return None


def init_audio():
    # заводим микшер и заранее грузим все звуки событий
    global available
    try:
        pygame.mixer.init()
        available = True
    except pygame.error:
        available = False
        return
    for event, name in SOUND_FILES.items():
        path = _find(name)
        if path is None:
            continue
        try:
            snd = pygame.mixer.Sound(path)
            snd.set_volume(SFX_VOLUME * engine.SAVE["master_volume"])
            sounds[event] = snd
        except pygame.error:
            pass


def apply_volume():
    # пересчитываем громкость звуков и музыки под новый мастер-уровень
    vol = engine.SAVE["master_volume"]
    for snd in sounds.values():
        snd.set_volume(SFX_VOLUME * vol)
    if available and current_music is not None:
        try:
            pygame.mixer.music.set_volume(MUSIC_VOLUME * vol)
        except pygame.error:
            pass


def play(event):
    # дёрнуть звук по имени события
    snd = sounds.get(event)
    if snd is not None:
        try:
            snd.play()
        except pygame.error:
            pass


def play_events(events):
    # проигрываем пачку событий за кадр
    for event in events:
        play(event)


def music(name):
    # включить фоновую музыку, если она уже играет — ничего не делаем
    global current_music
    if not available or name == current_music:
        return
    track = MUSIC_FILES.get(name)
    if track is None:
        return
    path = _find(track)
    if path is None:
        current_music = name
        return
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(MUSIC_VOLUME * engine.SAVE["master_volume"])
        pygame.mixer.music.play(-1)
        current_music = name
    except pygame.error:
        pass


def stop_music():
    global current_music
    current_music = None
    if available:
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass
