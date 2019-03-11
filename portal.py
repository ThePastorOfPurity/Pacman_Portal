import pygame
from maze import Block
from imagerect import ImageRect
from sounds import Sounds
from pygame.sprite import Sprite


class Portal(Block):

    P_TYPE_1 = 1
    P_TYPE_2 = 2
    TYPE_1_COLOR = (0, 255, 255)
    TYPE_2_COLOR = (255, 128, 0)

    def __init__(self, screen, x, y, direction, maze, p_type=P_TYPE_1):
        self.screen = screen
        self.maze = maze
        self.direction = direction
        self.p_type = p_type
        if p_type == Portal.P_TYPE_1:
            self.images = ImageRect('blue-portal-bg.png', sheet=True, pos_offsets=[(0, 0, 32, 32),
                                                                                             (32, 0, 32, 32),
                                                                                             (64, 0, 32, 32),
                                                                                             (0, 32, 32, 32),
                                                                                             (32, 32, 32, 32),
                                                                                             (64, 32, 32, 32),
                                                                                             (0, 64, 32, 32)],
                                              resize=(self.maze.block_size, self.maze.block_size),
                                              animation_delay=250)
            image, _ = self.images.get_image()
        else:
            self.images = ImageRect('orange-portal-bg.png', sheet=True, pos_offsets=[(0, 0, 32, 32),
                                                                                               (32, 0, 32, 32),
                                                                                               (64, 0, 32, 32),
                                                                                               (0, 32, 32, 32),
                                                                                               (32, 32, 32, 32),
                                                                                               (64, 32, 32, 32),
                                                                                               (0, 64, 32, 32)],
                                              resize=(self.maze.block_size, self.maze.block_size),
                                              animation_delay=250)
            image, _ = self.images.get_image()
        super().__init__(x, y, maze.block_size, maze.block_size, image)

    def get_nearest_col(self):
        return (self.rect.x - (self.screen.get_width() // 5)) // self.maze.block_size

    def get_nearest_row(self):
        return (self.rect.y - (self.screen.get_height() // 12)) // self.maze.block_size

    def update(self):
        self.image = self.images.next_image()

    def blit(self):
        self.screen.blit(self.image, self.rect)


class PortalProjectile(Sprite):
    def __init__(self, screen, source, direction, p_type=Portal.P_TYPE_1, size=(5, 5), speed=10):
        super().__init__()
        self.screen = screen
        self.source = source
        self.direction = direction
        self.speed = speed
        self.p_type = p_type
        self.image = pygame.Surface(size)
        if p_type == Portal.P_TYPE_1:
            self.image.fill(Portal.TYPE_1_COLOR)
        else:
            self.image.fill(Portal.TYPE_2_COLOR)
        self.rect = self.image.get_rect()
        self.rect.centerx, self.rect.centery = source.rect.centerx, source.rect.centery
        x_offset = int(source.rect.width * 0.5)
        y_offset = int(source.rect.height * 0.5)
        if direction == 'l':
            self.rect.centerx -= x_offset
        elif direction == 'r':
            self.rect.centerx += x_offset
        elif direction == 'u':
            self.rect.centery -= y_offset
        else:
            self.rect.centery += y_offset

    def update(self):
        if self.direction == 'l':
            self.rect.centerx -= self.speed
        elif self.direction == 'r':
            self.rect.centerx += self.speed
        elif self.direction == 'u':
            self.rect.centery -= self.speed
        else:
            self.rect.centery += self.speed

    def is_off_screen(self):
        if self.rect.x < 0 or self.rect.y < 0 or \
                self.rect.x > self.screen.get_width() + self.rect.width or \
                self.rect.y > self.screen.get_height() + self.rect.height:
            return True
        return False

    def blit(self):
        self.screen.blit(self.image, self.rect)


class PortalController:
    PORTAL_AUDIO_CHANNEL = 3

    def __init__(self, screen, user, maze):
        self.screen = screen
        self.maze = maze
        self.user = user
        self.sounds = Sounds(sound_files=['portal-open.wav', 'portal-travel.wav'], keys=['open', 'travel'],
                                          channel=PortalController.PORTAL_AUDIO_CHANNEL)
        self.blue_portal = pygame.sprite.GroupSingle()  # portals as GroupSingle, which only allows one per group
        self.blue_projectile = None
        self.orange_portal = pygame.sprite.GroupSingle()
        self.orange_projectile = None
        self.portal_directions = {'l': 'r', 'r': 'l', 'u': 'd', 'd': 'u'}

    def clear_portals(self):
        self.blue_portal.empty()
        self.orange_portal.empty()
        self.blue_projectile = None
        self.orange_projectile = None

    def fire_blue(self):
        if self.user.direction is not None:
            self.blue_projectile = PortalProjectile(screen=self.screen, source=self.user, direction=self.user.direction,
                                                    p_type=Portal.P_TYPE_1)

    def fire_orange(self):
        if self.user.direction is not None:
            self.orange_projectile = PortalProjectile(screen=self.screen, source=self.user,
                                                      direction=self.user.direction, p_type=Portal.P_TYPE_2)

    def create_blue(self, x, y, direction):
        if self.blue_portal:
            old_x, old_y = self.blue_portal.sprite.rect.x, self.blue_portal.sprite.rect.y
            self.maze.maze_blocks.add(
                Block(old_x, old_y, self.maze.block_size, self.maze.block_size, self.maze.block_image)
            )
        self.blue_portal.add(Portal(screen=self.screen, x=x, y=y, direction=direction,
                                    maze=self.maze, p_type=Portal.P_TYPE_1))

    def create_orange(self, x, y, direction):
        if self.orange_portal:
            old_x, old_y = self.orange_portal.sprite.rect.x, self.orange_portal.sprite.rect.y
            self.maze.maze_blocks.add(
                Block(old_x, old_y, self.maze.block_size, self.maze.block_size, self.maze.block_image)
            )
        self.orange_portal.add(Portal(screen=self.screen, x=x, y=y, direction=direction,
                                      maze=self.maze, p_type=Portal.P_TYPE_2))

    def update(self):
        self.blue_portal.update()
        self.orange_portal.update()
        if self.blue_projectile:
            self.blue_projectile.update()
            if pygame.sprite.spritecollideany(self.blue_projectile, self.blue_portal) or \
                    pygame.sprite.spritecollideany(self.blue_projectile, self.orange_portal):
                self.blue_projectile = None
                return
            collision = pygame.sprite.spritecollideany(self.blue_projectile, self.maze.maze_blocks)
            if collision:
                x, y = collision.rect.x, collision.rect.y
                collision.kill()
                direction = self.portal_directions[self.blue_projectile.direction]
                self.blue_projectile = None
                self.create_blue(x, y, direction)
                self.sounds.play('open')
            elif self.blue_projectile.is_off_screen():
                self.blue_projectile = None
        if self.orange_projectile:
            self.orange_projectile.update()
            if pygame.sprite.spritecollideany(self.orange_projectile, self.blue_portal) or \
                    pygame.sprite.spritecollideany(self.orange_projectile, self.orange_portal):
                self.orange_projectile = None
                return
            collision = pygame.sprite.spritecollideany(self.orange_projectile, self.maze.maze_blocks)
            if collision:
                x, y = collision.rect.x, collision.rect.y
                collision.kill()
                direction = self.portal_directions[self.orange_projectile.direction]
                self.orange_projectile = None
                self.create_orange(x, y, direction)
                self.sounds.play('open')
            elif self.orange_projectile.is_off_screen():
                self.orange_projectile = None

    def portables_usable(self):
        return self.blue_portal and self.orange_portal

    def collide_portals(self, other):
        return pygame.sprite.spritecollideany(other, self.blue_portal) or \
            pygame.sprite.spritecollideany(other, self.orange_portal)

    def check_portals(self, *args):
        for arg in args:
            if pygame.sprite.spritecollideany(arg, self.blue_portal) and self.orange_portal:
                i, j = self.orange_portal.sprite.get_nearest_row(), self.orange_portal.sprite.get_nearest_col()
                if self.orange_portal.sprite.direction == 'l':
                    j -= 1
                elif self.orange_portal.sprite.direction == 'r':
                    j += 1
                elif self.orange_portal.sprite.direction == 'u':
                    i -= 1
                else:
                    i += 1
                x, y = ((self.screen.get_width()) // 5 + (j * self.maze.block_size)), \
                       ((self.screen.get_height()) // 12 + (i * self.maze.block_size))
                arg.rect.x, arg.rect.y = x, y
                self.sounds.play('travel')
            elif pygame.sprite.spritecollideany(arg, self.orange_portal) and self.blue_portal:
                i, j = self.blue_portal.sprite.get_nearest_row(), self.blue_portal.sprite.get_nearest_col()
                if self.blue_portal.sprite.direction == 'l':
                    j -= 1
                elif self.blue_portal.sprite.direction == 'r':
                    j += 1
                elif self.blue_portal.sprite.direction == 'u':
                    i -= 1
                else:
                    i += 1
                x, y = ((self.screen.get_width() // 5) + (j * self.maze.block_size)), \
                       ((self.screen.get_height() // 12) + (i * self.maze.block_size))
                arg.rect.x, arg.rect.y = x, y
                self.sounds.play('travel')

    def blit(self):
        if self.blue_projectile:
            self.blue_projectile.blit()
        if self.orange_projectile:
            self.orange_projectile.blit()
        if self.blue_portal:
            self.blue_portal.sprite.blit()
        if self.orange_portal:
            self.orange_portal.sprite.blit()
