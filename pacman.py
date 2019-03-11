import pygame
from portal import PortalController
from pygame.sprite import Sprite
from sounds import Sounds
from imagerect import ImageRect


class Pacman(Sprite):
    audio = 0
    yellow = (255, 255, 0)

    def __init__(self, screen, maze):
        super().__init__()
        self.screen = screen
        self.maze = maze
        self.dead = False
        self.direction = None
        self.event_map = {pygame.KEYDOWN: self.move, pygame.KEYUP: self.reset_movement}
        self.input_map = {pygame.K_UP: self.move_up, pygame.K_LEFT: self.move_left,
                           pygame.K_DOWN: self.move_down, pygame.K_RIGHT: self.move_right,
                           pygame.K_q: self.blue_portal, pygame.K_w: self.orange_portal}


        self.sound_manager = Sounds(sound_files=['pacman-pellet-eat.wav', 'pacman-fruit-eat.wav',
                                                  'pacman-killed.wav', 'pacman-portal.wav'],
                                     keys=['eat', 'fruit', 'dead', 'portal'],
                                     channel=Pacman.audio)

        self.death_frames = ImageRect('pacman-death.png', sheet=True, pos_offsets=[(0, 0, 32, 32),
                                                                                  (32, 0, 32, 32),
                                                                                  (0, 32, 32, 32),
                                                                                  (32, 32, 32, 32),
                                                                                  (0, 64, 32, 32),
                                                                                  (32, 64, 32, 32)],
                                      resize=(self.maze.block_size, self.maze.block_size),
                                      animation_delay=150, repeat=False)

        self.pacmanx = ImageRect('pacman-horiz.png', sheet=True, pos_offsets=[(0, 0, 32, 32),
                                                                                       (32, 0, 32, 32),
                                                                                       (0, 32, 32, 32),
                                                                                       (32, 32, 32, 32),
                                                                                       (0, 64, 32, 32)],
                                          resize=(self.maze.block_size, self.maze.block_size),
                                          reversible=True)
        self.pacmany = ImageRect('pacman-vert.png', sheet=True, pos_offsets=[(0, 0, 32, 32),
                                                                                    (32, 0, 32, 32),
                                                                                    (0, 32, 32, 32),
                                                                                    (32, 32, 32, 32),
                                                                                    (0, 64, 32, 32)],
                                        resize=(self.maze.block_size, self.maze.block_size),
                                        reversible=True)
        self.spawn_set = self.maze.player_spawn[1]
        self.flip_mo = {'use_horiz': True, 'h_flip': False, 'v_flip': False}
        self.movement = False
        self.image, self.rect = self.pacmanx.get_image()
        self.portals = PortalController(screen, self, maze)


    def blue_portal(self):
        self.portals.fire_blue()

    def orange_portal(self):
        self.portals.fire_orange()

    def respawn(self):
        self.dead = False
        self.image, _ = self.pacmanx.get_image()
        self.death_frames.image_index = 0

    def eat(self):
        score = 0
        fruit_count = 0
        ppellet = None
        collision = pygame.sprite.spritecollideany(self, self.maze.pellets)
        if collision:
            collision.kill()
            score += 10
            self.sound_manager.play('eat')
        collision = pygame.sprite.spritecollideany(self, self.maze.fruits)
        if collision:
            collision.kill()
            score += (100 + (fruit_count * 200))
            fruit_count += 1
            self.sound_manager.play('fruit')
        collision = pygame.sprite.spritecollideany(self, self.maze.power_pellets)
        if collision:
            collision.kill()
            score += 50
            ppellet = True
            self.sound_manager.play('eat')
        return score, fruit_count, ppellet

    def reset(self):
        self.rect.centerx, self.rect.centery = self.spawn_set

    def change_direction(self, event):
        if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
            self.moving = False

    def get_nearest_col(self):
        return (self.rect.x - (self.screen.get_width() // 5)) // self.maze.block_size

    def get_nearest_row(self):
        return (self.rect.y - (self.screen.get_height() // 12)) // self.maze.block_size

    def set_death(self):
        self.sound_manager.play('dead')
        self.dead = True
        self.image, _ = self.death_frames.get_image()

    def reset_portals(self):
        self.portals.clear_portals()

    def move(self, event):
        if event.key in self.input_map:
            self.input_map[event.key]()

    def move_up(self):
        if self.direction != 'u':
            self.direction = 'u'
            if self.flip_mo['v_flip']:
                self.pacmany.flip(False, True)
                self.flip_mo['v_flip'] = False
            self.flip_mo['use_horiz'] = False
        self.moving = True

    def move_left(self):
        if self.direction != 'l':
            self.direction = 'l'
            if not self.flip_mo['h_flip']:
                self.pacmanx.flip()
                self.flip_mo['h_flip'] = True
            self.flip_mo['use_horiz'] = True
        self.moving = True

    def move_down(self):
        if self.direction != 'd':
            self.direction = 'd'
            if not self.flip_mo['v_flip']:
                self.pacmany.flip(x_bool=False, y_bool=True)
                self.flip_mo['v_flip'] = True
            self.flip_mo['use_horiz'] = False
        self.movement = True

    def move_right(self):
        if self.direction != 'r':
            self.direction = 'r'
            if self.flip_mo['h_flip']:
                self.pacmanx.flip()
                self.flip_mo['h_flip'] = False
            self.flip_mo['use_horiz'] = True
        self.movement = True

    def reset_movement(self, event):
        if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
            self.movement = False

    def blit(self):
        self.portals.blit()
        self.screen.blit(self.image, self.rect)
