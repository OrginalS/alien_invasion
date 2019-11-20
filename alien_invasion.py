import sys
from time import sleep

import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button, Border
from ship import Ship
from bullet import Bullet
from alien import Alien


class AlienInvasion:
    """overall class to manage game assets and behavior"""

    def __init__(self):
        """initialize the game, and create game resources"""
        pygame.init()
        self.settings = Settings()

        self.screen = pygame.display.set_mode(
            (1200, 800)
        )
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height
        pygame.display.set_caption("Alien Invasion")

        # create an instance to store game statistics
        # and create a scoreboard
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self._create_fleet()

        # make the play button
        self.play_button = Button(self, "Play")

        # make the difficulty buttons
        self.easy_button = Button(self, "Easy", (0, 155, 0),
                                  (self.settings.screen_width // 4,
                                   self.settings.screen_height // 4)
                                  )
        self.medium_button = Button(self, "Medium", (255, 140, 0),
                                    (self.settings.screen_width // 2,
                                     self.settings.screen_height // 4)
                                    )
        self.hard_button = Button(self, "Hard", (255, 0, 0),
                                  (self.settings.screen_width - self.settings.screen_width // 4,
                                   self.settings.screen_height // 4)
                                  )

        # make the difficulty button border
        self.difficulty_border = Border(self,
                                        (self.settings.screen_width // 4,
                                         self.settings.screen_height // 4)
                                        )


    def run_game(self):
        """start the main loop for the game"""
        while True:
            self._check_events()

            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()

            self._update_screen()

    def _check_events(self):
        """Respond to keypresses and mouse events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stats.save_stats()
                sys.exit()
            # key press
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            # key release
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)
                self._check_difficulty_button(mouse_pos)

    def _check_keydown_events(self, event):
        """Respond to keypresses."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_ESCAPE:
            self.stats.save_stats()
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()
        elif event.key == pygame.K_p:
            self._check_play_button(pygame.mouse.get_pos(), 1)

    def _check_keyup_events(self, event):
        """Respond to key releases."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        """Create a new bullet and add it to the bullets group."""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_screen(self):
        """Update images on the screen, and flip to the new screen."""
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)

        # draw the score information
        self.sb.show_score()

        # draw the buttons if the game is inactive
        if not self.stats.game_active:
            self.difficulty_border.draw_border()
            self.play_button.draw_button()
            self.easy_button.draw_button()
            self.medium_button.draw_button()
            self.hard_button.draw_button()

        pygame.display.flip()

    def _update_bullets(self):
        """Update position of bullets and get rid of old bullets."""
        # update bullet positions
        self.bullets.update()

        # get rid of bullets that have disappeared.
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """Respond to bullet-alien collisions."""
        # remove any bullets and aliens that have collided.
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()

        if not self.aliens:
            # destroy existing bullets and create new fleet.
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            # increase level
            self.stats.level += 1
            self.sb.prep_level()

    def _create_fleet(self):
        """Create the fleet of aliens."""
        # create an alien and find the number of aliens in a row
        # spacing between each alien is equal to one alien width
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = available_space_x // (2 * alien_width)

        # determine the number of rows of aliens that fit on the screen
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height -
                             (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)

        # create the full fleet of aliens
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        """Create an alien and place it in the row."""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)

    def _check_fleet_edges(self):
        """Respond appropriately if any aliens have reached an edge."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """Drop the entire fleet and change the fleet's direction."""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _update_aliens(self):
        """
        Check if the fleet is at and edge,
        then update the positions of all aliens in the fleet.
        """
        self._check_fleet_edges()
        self.aliens.update()

        # look for alien-ship collisions
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        # look for aliens hitting the bottom of the screen
        self._check_aliens_bottom()

    def _ship_hit(self):
        """Respond to the ship being hit by an alien."""
        if self.stats.ships_left > 0:
            # decrement ships_left and update scoreboard
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            # get rid of any remaining aliens and bullets
            self.aliens.empty()
            self.bullets.empty()

            # create a new fleet and center the ship
            self._create_fleet()
            self.ship.center_ship()

            # pause
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _check_aliens_bottom(self):
        """Check if any aliens have reached the bottom of the screen."""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                # treat this the same as if the ship got hit
                self._ship_hit()
                break

    def _check_difficulty_button(self, mouse_pos):
        """Set difficulty."""
        if self.easy_button.rect.collidepoint(mouse_pos):
            self.settings.difficulty(1)
            self.difficulty_border.rect.center = self.easy_button.rect.center
        elif self.medium_button.rect.collidepoint(mouse_pos):
            self.settings.difficulty(2)
            self.difficulty_border.rect.center = self.medium_button.rect.center
        elif self.hard_button.rect.collidepoint(mouse_pos):
            self.settings.difficulty(3)
            self.difficulty_border.rect.center = self.hard_button.rect.center

    def _check_play_button(self, mouse_pos, x=0):
        """Start a new game when the player clicks Play."""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if x:
            button_clicked = True
        if button_clicked and not self.stats.game_active:
            # reset the game settings
            self.settings.initialize_dynamic_settings()
            self.stats.reset_stats()
            self.stats.game_active = True
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            # get rid of any remaining aliens and bullets
            self.aliens.empty()
            self.bullets.empty()

            # create a new fleet and center the ship
            self._create_fleet()
            self.ship.center_ship()

            # hide the mouse cursor
            pygame.mouse.set_visible(False)


if __name__ == '__main__':
    # make a game instance, and run the game
    ai = AlienInvasion()
    ai.run_game()
