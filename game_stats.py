import json


class GameStats:
    """Track statistics for Alien Invasion."""

    def __init__(self, ai_game):
        """Initialize statistics."""
        self.settings = ai_game.settings
        self.reset_stats()

        # start alien invasion in an inactive state
        self.game_active = False

        # try to load high score from file
        # if file is missing set high score to 0
        try:
            with open('high_scores.txt', 'r') as file:
                self.high_score = int(file.readline())
        except FileNotFoundError:
            self.high_score = 0


    def reset_stats(self):
        """Initialize statistics that can change during the game."""
        self.ships_left = self.settings.ship_limit
        self.score = 0
        self.level = 1

    def save_stats(self):
        with open('high_scores.txt', 'w') as file:
            json.dump(self.high_score, file)
