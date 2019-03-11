import pygame
from pygame.sprite import Sprite
from scoreboard import Scoreboard
from imagerect import ImageRect


class StartScreen:

    def __init__(self, screen):
        self.screen = screen
        self.ghost_intros = [
            Chase(screen, chasers=['ghost-red.png', 'ghost-pink.png',
                                        'ghost-blue.png', 'ghost-orange.png'],
                       chased=['pacman-horiz.png'], chaser_detail='ghost-eyes.png'),
            Chase(screen, chasers=['ghost-ppellet.png', 'ghost-ppellet.png',
                                        'ghost-ppellet.png', 'ghost-ppellet.png'],
                       chased=['pacman-horiz.png'], reverse=True),
            GhostScreen(screen, 'ghost-red.png', 'Blinky'),
            GhostScreen(screen, 'ghost-pink.png', 'Pinky'),
            GhostScreen(screen, 'ghost-blue.png', 'Inky'),
            GhostScreen(screen, 'ghost-orange.png', 'Clyde')
        ]
        self.run = set()
        self.index = 0
        self.last = None
        self.time = 5000

    def update(self):
        if not self.last:
            self.last = pygame.time.get_ticks()
        elif abs(self.last - pygame.time.get_ticks()) > self.time:
            self.run.add(self.index)
            self.index = (self.index + 1) % len(self.ghost_intros)
            self.last = pygame.time.get_ticks()
        if self.index in (0, 1) and self.index in self.run:
            self.ghost_intros[self.index].reset_positions()
            self.run.remove(self.index)
        self.ghost_intros[self.index].update()

    def blit(self):
        self.ghost_intros[self.index].blit()


class GhostScreen:
    def __init__(self, screen, g_file, name):
        self.screen = screen
        self.title_card = Title(screen, name, pos=(screen.get_width() // 2, screen.get_height() // 2))
        self.ghost = Animate(screen, g_file, sheet_offsets=[(0, 0, 32, 32), (0, 32, 32, 32)],
                                     pos=(self.title_card.rect.right + self.title_card.rect.width // 2,
                                          screen.get_height() // 2),
                                     detail='ghost-eyes.png',
                                     frame_delay=150)

    def update(self):
        self.ghost.update()

    def blit(self):
        self.title_card.blit()
        self.ghost.blit()


class Animate(Sprite):
    def __init__(self, screen, sprite_sheet, sheet_offsets, pos=(0, 0), resize=None,
                 detail=None, frame_delay=None, flip=False):
        super().__init__()
        self.screen = screen
        if not resize:
            resize = (self.screen.get_height() // 10, self.screen.get_height() // 10)
        self.image_manager = ImageRect(sprite_sheet, sheet=True, pos_offsets=sheet_offsets,
                                          resize=resize, animation_delay=frame_delay)
        if flip:
            self.image_manager.flip()
        self.image, self.rect = self.image_manager.get_image()
        if detail:
            self.detail_piece = ImageRect(detail, sheet=True, pos_offsets=sheet_offsets,
                                             resize=resize).all_images()[0]
            if flip:
                self.image_manager.flip()
            self.image.blit(self.detail_piece, (0, 0))
        else:
            self.detail_piece = None
        self.rect.centerx, self.rect.centery = pos

    def update(self):
        self.image = self.image_manager.next_image()
        if self.detail_piece:
            self.image.blit(self.detail_piece, (0, 0))

    def blit(self):
        self.screen.blit(self.image, self.rect)


class Title(Sprite):
    def __init__(self, screen, text,  pos=(0, 0), color=Scoreboard.white, size=42):
        super().__init__()
        self.screen = screen
        self.text = text
        self.color = color
        self.image = None
        self.rect = None
        self.pos = pos
        self.font = pygame.font.Font('fonts/LuckiestGuy-Regular.ttf', size)
        self.prep_image()

    def position(self, n_pos=None):
        if not n_pos:
            self.rect.centerx, self.rect.centery = self.pos
        else:
            self.rect.centerx, self.rect.centery = n_pos

    def prep_image(self):
        self.image = self.font.render(self.text, True, self.color)
        self.rect = self.image.get_rect()
        self.position()

    def blit(self):
        self.screen.blit(self.image, self.rect)


class Chase:
    def __init__(self, screen, chasers, chased, reverse=False, speed=5, chaser_detail=None, chased_detail=None):
        self.screen = screen
        self.chasers = []
        self.chased = []
        self.x_start = 0 if not reverse else screen.get_width()
        self.speed = speed if not reverse else -speed
        self.chaser_positions = []
        self.chased_positions = []
        self.y_pos = (screen.get_height() // 2)
        x_offset = self.x_start
        for chaser in chasers:
            self.chaser_positions.append(x_offset)
            animation = Animate(screen, chaser, sheet_offsets=[(0, 0, 32, 32), (0, 32, 32, 32)],
                                        pos=(x_offset, self.y_pos),
                                        detail=chaser_detail,
                                        frame_delay=150,
                                        flip=reverse)
            x_offset += int(animation.rect.width * 1.5)
            self.chasers.append(animation)
        x_offset += (self.speed * 2)
        for target in chased:
            self.chased_positions.append(x_offset)
            animation = Animate(screen, target, sheet_offsets=[(0, 0, 32, 32),
                                                                       (32, 0, 32, 32),
                                                                       (0, 32, 32, 32),
                                                                       (32, 32, 32, 32),
                                                                       (0, 64, 32, 32)],
                                        pos=(x_offset, self.y_pos),
                                        detail=chased_detail,
                                        frame_delay=150,
                                        flip=reverse)
            x_offset += int(animation.rect.width * 1.5)
            self.chased.append(animation)

    def reset_positions(self):
        for chaser, c_offset in zip(self.chasers, self.chaser_positions):
            chaser.rect.centerx, chaser.rect.centery = c_offset, self.y_pos
        for target, t_offset in zip(self.chased, self.chased_positions):
            target.rect.centerx, target.rect.centery = t_offset, self.y_pos

    def update(self):
        for chaser in self.chasers:
            chaser.rect.centerx += self.speed
            chaser.update()
        for target in self.chased:
            target.rect.centerx += self.speed
            target.update()

    def blit(self):
        for chaser in self.chasers:
            chaser.blit()
        for target in self.chased:
            target.blit()
