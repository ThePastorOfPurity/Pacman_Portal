import pygame
from ghost import Ghost
from maze import Maze
from pacman import Pacman
from pygame.sprite import Group
from event import Event
from startscreen import StartScreen
from scoreboard import ScoreController
from scoreboard import NextLevel
from sounds import Sounds
from lives import PacmanLives
from button import Menu, HighScoreScreen


class PacmanPortal:

    black = (0, 0, 0)
    START_EVENT = pygame.USEREVENT + 1
    REBUILD_EVENT = pygame.USEREVENT + 2
    LEVEL_EVENT = pygame.USEREVENT + 3

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pacman Portal")
        self.screen = pygame.display.set_mode((800, 600))
        self.maze = Maze(screen=self.screen, maze_map_file='pacmanportalmaze.txt')
        self.clock = pygame.time.Clock()
        self.ghost_sounds = Sounds(sound_files=['ghost-blue.wav', 'ghost-eaten.wav', 'ghost-std.wav'],
                                                keys=['blue', 'eaten', 'std'],
                                                channel=Ghost.audio)

        self.stock = PacmanLives(screen=self.screen, ct_pos=((self.screen.get_width() // 3),
                                                                      (self.screen.get_height() * 0.965)),
                                          images_size=(self.maze.block_size, self.maze.block_size))
        self.score = ScoreController(screen=self.screen,
                                            sb_pos=((self.screen.get_width() // 5),
                                                    (self.screen.get_height() * 0.965)),
                                            items_image='cherry.png',
                                            itc_pos=(int(self.screen.get_width() * 0.6),
                                                     self.screen.get_height() * 0.965))
        self.next_level = NextLevel(screen=self.screen, score_controller=self.score)
        self.game_over = True
        self.pause = False
        self.player = Pacman(screen=self.screen, maze=self.maze)
        self.ghosts = Group()
        self.ghost_time = 2500
        self.ghosts_stack = None
        self.top_ghost = None
        self.arr_ghost = []
        self.spawn_ghosts()
        self.events = {PacmanPortal.START_EVENT: self.init_ghosts, PacmanPortal.REBUILD_EVENT: self.rebuild_maze, PacmanPortal.LEVEL_EVENT: self.clear_level}

    def init_ghosts(self):
        if not self.top_ghost.state['normal']:
            self.top_ghost.enable()
            self.ghosts_stack = self.arr_ghost.copy()
            pygame.time.set_timer(PacmanPortal.START_EVENT, 0)
            pygame.time.set_timer(PacmanPortal.START_EVENT, self.ghost_time)
        else:
            try:
                g = self.ghosts_stack.pop()
                g.enable()
            except IndexError:
                pygame.time.set_timer(PacmanPortal.START_EVENT, 0)

    def spawn_ghosts(self):
        files = ['ghost-pink.png', 'ghost-blue.png', 'ghost-orange.png', 'ghost-red.png']
        index = 0
        while len(self.maze.ghost_spawn) > 0:
            spawn_info = self.maze.ghost_spawn.pop()
            g = Ghost(screen=self.screen, maze=self.maze, target=self.player,
                      spawn=spawn_info, ghost=files[index], sounds=self.ghost_sounds)
            if files[index] == 'ghost-red.png':
                self.top_ghost = g
            else:
                self.arr_ghost.append(g)
            self.ghosts.add(g)
            index = (index + 1) % len(files)

    def clear_level(self):
        pygame.time.set_timer(PacmanPortal.LEVEL_EVENT, 0)
        self.score.increment_level()
        self.player.reset_portals()
        self.rebuild_maze()

    def check_pacman(self):
        score, fruits, ppellet = self.player.eat()
        if ppellet:
            for i in self.ghosts:
                i.begin_blue()
        ghost_collide = pygame.sprite.spritecollideany(self.player, self.ghosts)
        if ghost_collide and ghost_collide.state['blue']:
            ghost_collide.ghost_eaten()
            self.score.add_score(200)
        elif ghost_collide and not (self.player.dead or ghost_collide.state['return']):
            self.stock.decrement()
            self.player.reset_portals()
            self.player.set_death()
            for g in self.ghosts:
                if g.state['normal']:
                    g.disable()
            pygame.time.set_timer(PacmanPortal.START_EVENT, 0)
            pygame.time.set_timer(PacmanPortal.REBUILD_EVENT, 4000)
        elif not self.maze.pellets_left() and not self.pause:
            pygame.mixer.stop()
            self.pause = True
            pygame.time.set_timer(PacmanPortal.LEVEL_EVENT, 1000)

    def play_game(self):
        e_loop = Event(loop_running=True, actions={**self.player.event_map, **self.events})
        self.next_level.set_show_transition()
        self.game_over = False
        if self.player.dead:
            self.player.respawn()
            self.score.reset_level()
            self.stock.reset_counter()
            self.rebuild_maze()

        while e_loop.loop_running:
            self.clock.tick(60)
            e_loop.check_events()
            self.update_screen()
            if self.game_over:
                pygame.mixer.stop()
                self.score.reset_level()
                e_loop.loop_running = False

    def rebuild_maze(self):
        if self.stock.lives > 0:
            for g in self.ghosts:
                if g.state['normal']:
                    g.disable()
            self.maze.build_maze()
            self.player.reset()
            for g in self.ghosts:
                g.reset_position()
            if self.player.dead:
                self.player.respawn()
            if self.pause:
                self.pause = False
            self.next_level.set_show_transition()
        else:
            self.game_over = True
        pygame.time.set_timer(PacmanPortal.REBUILD_EVENT, 0)

    def update_screen(self):
        if not self.next_level.transition_show:
            self.screen.fill(PacmanPortal.black)
            self.check_pacman()
            self.maze.blit()
            if not self.pause:
                self.ghosts.update()
                self.player.update()
                self.maze.teleport.check_teleport(self.player.rect)
            for g in self.ghosts:
                if self.score.level > 3:
                    if not g.state['rubber_band']:
                        g.increase_speed()
                    self.maze.teleport.check_teleport(g.rect)
                g.blit()
            self.player.blit()
            self.score.blit()
            self.stock.blit()
        elif self.player.dead:
            self.player.update()
            self.player.blit()
        else:
            self.next_level.draw()
            if not self.next_level.transition_show:
                self.init_ghosts()
        pygame.display.flip()

    def runit(self):
        menu = Menu(self.screen)
        hs_screen = HighScoreScreen(self.screen, self.score)
        intro_seq = StartScreen(self.screen)
        e_loop = Event(loop_running=True, actions={pygame.MOUSEBUTTONDOWN: menu.check_buttons})

        while e_loop.loop_running:
            self.clock.tick(60)
            e_loop.check_events()
            self.screen.fill(PacmanPortal.black)
            if not menu.hs_screen:
                intro_seq.update()
                intro_seq.blit()
                menu.update()
                menu.blit()
            else:
                hs_screen.blit()
                hs_screen.check_done()
            if menu.ready_to_play:
                pygame.mixer.music.stop()
                self.play_game()
                for g in self.ghosts:
                    g.reset_speed()
                menu.ready_to_play = False
                self.score.save_high_scores()
                hs_screen.prep_images()
                hs_screen.position()
            pygame.display.flip()


if __name__ == '__main__':
    game = PacmanPortal()
    game.runit()














