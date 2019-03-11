import pygame
from pygame import time
from pygame.sprite import Sprite
from pygame.sprite import Group
from imagerect import ImageRect
from pygame import sysfont
from pygame.sprite import spritecollideany


class Ghost(Sprite):
    audio = 1

    def __init__(self, screen, maze, target, spawn, sounds, ghost= 'ghost-red.png'):
        super().__init__()
        self.screen = screen
        self.maze = maze
        self.maze_block = Group()
        self.target = target
        self.direction = None
        self.last = None
        self.state = {'normal': False, 'blue': False, 'return': False, 'rubber_band': False}
        self.blink = False
        self.last_blink = time.get_ticks()
        self.score_display = None
        self.normal_frames = ImageRect(ghost, sheet=True, pos_offsets=[(0, 0, 32, 32), (0, 32, 32, 32)],
                                       resize=(self.maze.block_size, self.maze.block_size),
                                       animation_delay=250)
        self.image, self.rect = self.normal_frames.get_image()

        self.start_position = spawn[1]
        self.reset()
        self.tile = spawn[0]
        self.speed = maze.block_size / 10
        self.blink_i = 250
        self.eat = None
        self.return_path = None
        self.return_offset = 1000
        self.grid = maze.map_lines
        self.sounds = sounds
        self.blue_i = 5000
        self.blue_start = None

        self.eyes = ImageRect('ghost-eyes.png', sheet=True, pos_offsets=[(0, 0, 32, 32), (32, 0, 32, 32),
                                                                            (0, 32, 32, 32), (32, 32, 32, 32)],
                                 resize=(self.maze.block_size, self.maze.block_size),
                                 keys=['r', 'u', 'd', 'l'])
        self.font = sysfont.SysFont(None, 22)
        self.blue_frames = ImageRect('ghost-ppellet.png', sheet=True, pos_offsets=[(0, 0, 32, 32), (0, 32, 32, 32)],
                                        resize=(self.maze.block_size, self.maze.block_size),
                                        animation_delay=150)
        self.blue_white = ImageRect('ghost-ppellet-warn.png', sheet=True, pos_offsets=[(0, 0, 32, 32),
                                                                                            (0, 32, 32, 32)],
                                         resize=(self.maze.block_size, self.maze.block_size),
                                         animation_delay=150)
        self.neutral_eye, _ = self.eyes.get_image(key='r')

    @staticmethod
    def arr_path(maze_map, start, target):
        path = []
        tried = set()
        done = False
        curr_tile = start
        while not done:
            if curr_tile == target:
                done = True
            else:
                options = [
                    (curr_tile[0] + 1, curr_tile[1]),
                    (curr_tile[0] - 1, curr_tile[1]),
                    (curr_tile[0], curr_tile[1] + 1),
                    (curr_tile[0], curr_tile[1] - 1)
                ]
                test = (abs(target[0] - start[0]), abs(target[1] - start[0]))
                prefer = test.index(max(test[0], test[1]))
                if prefer == 0:
                    options.sort(key=lambda x: x[0], reverse=True)
                else:
                    options.sort(key=lambda x: x[1], reverse=True)
                backtrack = True
                for opt in options:
                    try:
                        if maze_map[opt[0]][opt[1]] not in ('x',) and opt not in tried:
                            backtrack = False
                            path.append(opt)
                            tried.add(opt)
                            curr_tile = opt
                            break
                    except IndexError:
                        continue
                if backtrack:
                    curr_tile = path.pop()
        return path

    def blit(self):
        self.screen.blit(self.image, self.rect)

    def ghost_eaten(self):
        self.state['return'] = True
        self.state['blue'] = False
        self.tile = (self.get_nearest_row(), self.get_nearest_col())
        self.return_path = Ghost.arr_path(self.grid, self.tile, self.tile)
        self.direction = self.get_direction()
        self.image = self.font.render('200', True, (255, 255, 255))
        self.eat = time.get_ticks()

    def begin_blue(self):
        if not self.state['return']:
            self.state['blue'] = True

    def stop_blue(self, resume_audio = True):
        self.state['blue'] = False
        self.state['return'] = False
        self.image, _ = self.normal_frames.get_image()

    def get_nearest_col(self):
        return (self.rect.left - (self.screen.get_width() // 5)) // self.maze.block_size

    def get_nearest_row(self):
        return (self.rect.top - (self.screen.get_height() // 12)) // self.maze.block_size

    def is_at_intersection(self):
        directions = 0
        self.tile = (self.get_nearest_row(), self.get_nearest_col())
        if self.grid[self.tile[0] - 1][self.tile[1]] not in ('x', ):
            directions += 1
        if self.grid[self.tile[0] + 1][self.tile[1]] not in ('x', ):
            directions += 1
        if self.grid[self.tile[0]][self.tile[1] - 1] not in ('x', ):
            directions += 1
        if self.grid[self.tile[0]][self.tile[1] + 1] not in ('x', ):
            directions += 1
        return True if directions > 2 else False

    def update(self):
        if self.state['normal']:
            if not self.state['blue'] and not self.state['return']:
                self.update_neutral()
            elif self.state['blue']:
                self.update_blue()
            elif self.state['return']:
                self.update_return()
            self.last = (self.rect.centerx, self.rect.centery)

    def update_neutral(self):
        options = self.direction_options()
        if self.is_at_intersection() or self.last == (self.rect.centerx, self.rect.centery):
            self.direction = self.chase_path(options)
        if self.direction == 'u' and 'u' in options:
            self.rect.centery -= self.speed
        elif self.direction == 'l' and 'l' in options:
            self.rect.centerx -= self.speed
        elif self.direction == 'd' and 'd' in options:
            self.rect.centery += self.speed
        elif self.direction == 'r' and 'r' in options:
            self.rect.centerx += self.speed
        self.set_eyes(self.direction or 'r')
        self.image = self.normal_frames.next_image()

    def update_blue(self):
        self.image = self.blue_frames.next_image()
        options = self.direction_options()
        if self.is_at_intersection() or self.last == (self.rect.centerx, self.rect.centery):
            self.direction = self.flee_path(options)
        if self.direction == 'u' and 'u' in options:
            self.rect.centery -= self.speed
        elif self.direction == 'l' and 'l' in options:
            self.rect.centerx -= self.speed
        elif self.direction == 'd' and 'd' in options:
            self.rect.centery += self.speed
        elif self.direction == 'r' and 'r' in options:
            self.rect.centerx += self.speed
        if abs(self.blue_start - time.get_ticks()) > self.blue_i:
            self.stop_blue()
        elif abs(self.blue_start - time.get_ticks()) > int(self.blue_i * 0.5):
            if self.blink:
                self.image = self.blue_white.next_image()
                self.blink = False
                self.last_blink = time.get_ticks()
            elif abs(self.last_blink - time.get_ticks()) > self.blink_i:
                self.blink = True

    def update_return(self):
        if abs(self.eat - time.get_ticks()) > self.return_offset:
            self.image, _ = self.eyes.get_image(key=self.direction)
            test = self.check_path()
            if test == '*':
                self.state['return'] = False
                self.direction = self.chase_path(self.direction_options())
            else:
                self.direction = self.get_direction()
            if self.direction == 'u':
                self.rect.centery -= self.speed
            elif self.direction == 'l':
                self.rect.centerx -= self.speed
            elif self.direction == 'd':
                self.rect.centery += self.speed
            elif self.direction == 'r':
                self.rect.centerx += self.speed

    def enable(self):
        options = self.direction_options()
        self.direction = options[0]
        self.state['normal'] = True
        self.sounds.play_loop('std')

    def disable(self):
        self.direction = None
        self.state['normal'] = False
        self.state['return'] = False
        self.return_path = None
        if self.state['blue']:
            self.stop_blue(resume_audio=False)
        self.image, _ = self.normal_frames.get_image()
        self.sounds.stop()

    def get_direction(self):
        try:
            next_step = self.return_path[0]
            if next_step[0] > self.tile[0]:
                return 'd'
            if next_step[0] < self.tile[0]:
                return 'u'
            if next_step[1] > self.tile[1]:
                return 'r'
            if next_step[1] < self.tile[1]:
                return 'l'
        except IndexError as ie:
            print('Error while trying to get new path direction', ie)
            return None

    def direction_options(self):
        tests = {
            'u': self.rect.move((0, -self.speed)),
            'l': self.rect.move((-self.speed, 0)),
            'd': self.rect.move((0, self.speed)),
            'r': self.rect.move((self.speed, 0))
        }
        remove = []
        original_pos = self.rect

        for d, t in tests.items():
            self.rect = t
            if spritecollideany(self, self.maze.maze_blocks) and d not in remove:
                remove.append(d)
            if spritecollideany(self, self.target.portals.blue_portal) and d not in remove:
                remove.append(d)
            if spritecollideany(self, self.target.portals.orange_portal) and d not in remove:
                remove.append(d)
        for rem in remove:
            del tests[rem]
        self.rect = original_pos
        return list(tests.keys())

    def chase_path(self, options):
        pick_direction = None
        target_pos = (self.target.rect.centerx, self.target.rect.centery)
        test = (abs(target_pos[0]), abs(target_pos[1]))
        prefer = test.index(max(test[0], test[1]))
        if prefer == 0:
            if target_pos[prefer] < self.rect.centerx:
                pick_direction = 'l'
            elif target_pos[prefer] > self.rect.centerx:
                pick_direction = 'r'
        else:   # y direction
            if target_pos[prefer] < self.rect.centery:
                pick_direction = 'u'
            elif target_pos[prefer] > self.rect.centery:
                pick_direction = 'd'
        if pick_direction not in options:
            if 'u' in options:
                return 'u'
            if 'l' in options:
                return 'l'
            if 'r' in options:
                return 'r'
            if 'd' in options:
                return 'd'
        else:
            return pick_direction

    def flee_path(self, options):
        pick_direction = None
        target_pos = (self.target.rect.centerx, self.target.rect.centery)
        test = (abs(target_pos[0]), abs(target_pos[1]))
        prefer = test.index(max(test[0], test[1]))
        if prefer == 0:
            if target_pos[prefer] < self.rect.centerx:
                pick_direction = 'r'
            elif target_pos[prefer] > self.rect.centerx:
                pick_direction = 'l'
        else:
            if target_pos[prefer] < self.rect.centery:
                pick_direction = 'd'
            elif target_pos[prefer] > self.rect.centery:
                pick_direction = 'u'
        if pick_direction not in options:
            if 'u' in options:
                return 'u'
            if 'l' in options:
                return 'l'
            if 'd' in options:
                return 'd'
            if 'r' in options:
                return 'r'
        else:
            return pick_direction

    def reset(self):
        self.rect.left, self.rect.top = self.start_position

    def check_path(self):
        self.tile = (self.get_nearest_row(), self.get_nearest_col())
        if self.return_path and self.tile == self.return_path[0]:
            del self.return_path[0]
            if not len(self.return_path) > 0:
                return '*'
        return None

    def set_eyes(self, look_direction):
        self.image, _ = self.normal_frames.get_image()
        self.neutral_eye, _ = self.eyes.get_image(key=look_direction)
        self.image.blit(self.neutral_eye, (0, 0))
