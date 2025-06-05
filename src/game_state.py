import random

MAX_LIVES_CONST = 3 # Define directly in this module

class GameState:
    def __init__(self, grid_width, grid_height):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.score = 0
        self.lives = 3
        self.current_level = 1
        self.level_food_counter = 0  # Food eaten in the current level
        self.game_over = False
        self.glitch_active = False
        self.powerup_on_grid = None
        self.active_powerup_effect = None
        self.BG_COLOR = (0,0,0) # Default BG Black
        self.MAX_LIVES = MAX_LIVES_CONST # Use the module constant

    def increase_score(self, points):
        self.score += points

    def lose_life(self):
        self.lives -= 1
        print(f"Lost a life! {self.lives} lives remaining.") # Placeholder feedback
        if self.lives <= 0:
            self.game_over = True
            print("Game Over!") # Placeholder feedback

    def level_up(self, snake_body_ref): # Added snake_body_ref for powerup spawning
        self.current_level += 1
        self.level_food_counter = 0
        print(f"Level Up! Reached Level {self.current_level}")

        # Extra Life Chance
        if random.random() < 0.40: # 40% chance
            if self.lives < self.MAX_LIVES:
                self.lives += 1
                print(f"Earned an extra life! Lives: {self.lives}")
            else:
                print(f"Extra life chance hit, but already at max lives ({self.lives}).")

        # Spawn Glitch PowerUp
        if not self.powerup_on_grid and not self.active_powerup_effect:
            spawn_pos = self._get_random_empty_cell(snake_body_ref, self.grid_width, self.grid_height)
            if spawn_pos:
                from .powerups import GlitchEffect, PowerUpSpawnable # Local import for now
                # Ensure Food object is not at spawn_pos too (important if food exists)
                # This check might need to be more robust by passing food_pos
                self.powerup_on_grid = PowerUpSpawnable(spawn_pos, "Glitch", GlitchEffect, color=(128, 0, 128)) # Purple for Glitch
                print(f"Glitch PowerUp spawned at {spawn_pos}")

    def _get_random_empty_cell(self, snake_body, grid_width, grid_height, food_pos=None):
       # Ensure to import random (done at top of file)
       max_attempts = grid_width * grid_height # Safety break for nearly full grids
       attempts = 0
       while attempts < max_attempts:
           pos = (random.randint(0, grid_width - 1), random.randint(0, grid_height - 1))
           if pos not in snake_body and (food_pos is None or pos != food_pos):
               return pos
           attempts += 1
       return None # Could not find an empty cell

    def reset_game(self):
        # Placeholder for resetting the game state
        # This should also reset snake and food if called from a full game reset context
        self.score = 0
        self.lives = self.MAX_LIVES # Reset to max lives
        self.current_level = 1
        self.level_food_counter = 0
        self.game_over = False
        self.glitch_active = False
        self.powerup_on_grid = None
        self.active_powerup_effect = None
        self.BG_COLOR = (0,0,0)
        # Note: Snake and Food would need to be reset externally or by passing them in.
        pass
