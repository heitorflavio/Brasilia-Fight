"""Loop principal e gerenciador de telas."""
import pygame

from . import audio
from .config import FPS, GAME_H, GAME_W, TITLE
from .stage import load_stages


class Game:
    def __init__(self, fullscreen=False):
        pygame.mixer.pre_init(audio.SR, -16, 2, 512)
        pygame.init()
        flags = pygame.SCALED | pygame.RESIZABLE
        if fullscreen:
            flags |= pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((GAME_W, GAME_H), flags)
        pygame.display.set_caption(TITLE)
        audio.init()
        self.clock = pygame.time.Clock()
        self.running = True
        self.difficulty = 1
        self.joysticks = []
        self._scan_joysticks()
        self.stages = load_stages()
        self.stage_idx = 0
        from .scenes import TitleScene
        self.scene = TitleScene(self)

    def _scan_joysticks(self):
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

    def next_stage(self):
        st = self.stages[self.stage_idx % len(self.stages)]
        self.stage_idx += 1
        return st

    def change(self, scene):
        self.scene = scene

    def step(self, events):
        for e in events:
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_F11 or (e.key == pygame.K_RETURN and e.mod & pygame.KMOD_ALT):
                    pygame.display.toggle_fullscreen()
                elif e.key == pygame.K_m:
                    audio.toggle_music()
            elif e.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                self._scan_joysticks()
        scene = self.scene
        scene.handle(events)
        if self.scene is scene:
            scene.update()
        self.scene.draw(self.screen)

    def run(self):
        while self.running:
            self.step(pygame.event.get())
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
