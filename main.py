import pygame
import sys
import random
import math
import json

# --- Pygame Mixer Initialization ---
mixer_initialized = False
try:
    pygame.mixer.init()
    mixer_initialized = True
    print("Pygame mixer initialized successfully.")
except pygame.error as e:
    print(f"Warning: Pygame mixer could not be initialized: {e}")

# --- Dummy Sound Class ---
class DummySound:
    def play(self):
        pass # Does nothing
    def set_volume(self, volume):
        pass # Does nothing

DUMMY_SOUND = DummySound() # Global dummy sound instance

# --- Global Sound Dictionary ---
game_sounds = {}

# --- Sound Loading Helper ---
def load_sound(filename, default_sound_obj):
    if not mixer_initialized:
        return default_sound_obj
    try:
        sound = pygame.mixer.Sound(filename)
        # sound.set_volume(0.5) # Optional: set default volume for all sounds
        return sound
    except pygame.error as e:
        print(f"Warning: Could not load sound '{filename}': {e}")
        return default_sound_obj

# --- Constants ---
# General Game Settings
GRID_SIZE = 20  # pixels per grid cell
GRID_WIDTH = 32  # number of cells horizontally
GRID_HEIGHT = 24  # number of cells vertically
SCREEN_WIDTH = GRID_WIDTH * GRID_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * GRID_SIZE
MAX_LIVES = 3 # Max lives player can have

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)  # Snake color
RED = (255, 0, 0)    # Food color
CYAN = (0, 255, 255) # Shield visual color for snake
YELLOW = (255, 255, 51) # Speed Surge snake color / powerup item color
GRID_COLOR = (40, 40, 40) # Light grey for grid lines
GLITCH_POWERUP_COLOR = (128, 0, 128) # Purple for Glitch power-up item
SHIELD_POWERUP_COLOR = (0, 128, 255) # Blue for Shield power-up item
SPEEDSURGE_POWERUP_COLOR = YELLOW   # Color for Speed Surge power-up item
REVERSECONTROLS_POWERUP_COLOR = (100, 100, 100) # Grey for Reverse Controls item
EXTRALIFE_POWERUP_COLOR = (255, 20, 147) # Deep Pink for Extra Life item
POWERUP_ALERT_COLOR = (255, 0, 0) # Red for HUD alerts

# Font Settings
FONT_NAME = "assets/pixel_font.ttf" # Path to custom font file
FONT_SIZE = GRID_SIZE # Base font size, tied to grid size

# Speed & Difficulty
MIN_SNAKE_FPS = 3.0
MAX_SNAKE_FPS = 8.0
FPS_GAIN_PER_LEVEL = 0.33 # Approx (8-3)/15 levels for ramp-up
FOOD_PER_LEVEL = 10 # Number of food items to eat to level up

# HUD Icons
MINI_SNAKE_ICON_SIZE = GRID_SIZE // 2
MINI_SNAKE_ICON_GAP = GRID_SIZE // 4
MAX_LIVES_DISPLAY = 5 # Max icons to draw for lives (visual limit)

# Power-ups
HIGH_SCORE_FILE = "high_scores.json"
MAX_HIGH_SCORES = 5

POWERUP_SPAWN_CHANCE_P0 = 0.80
POWERUP_SPAWN_CHANCE_DECAY_RATE = 0.12
MIN_POWERUP_SPAWN_CHANCE = 0.10

POWERUP_BASE_FPS_FOR_CALCS = 10.0
# Durations in Ticks (assuming POWERUP_BASE_FPS_FOR_CALCS for conversion from seconds)
GLITCH_DURATION_TICKS = int(8 * POWERUP_BASE_FPS_FOR_CALCS)
SHIELD_DURATION_TICKS = int(5 * POWERUP_BASE_FPS_FOR_CALCS)
TIME_DILATION_DURATION_TICKS = int(4 * POWERUP_BASE_FPS_FOR_CALCS)
REVERSE_CONTROLS_DURATION_TICKS = int(8 * POWERUP_BASE_FPS_FOR_CALCS)
SPEED_SURGE_DURATION_TICKS = int(6 * POWERUP_BASE_FPS_FOR_CALCS) # 60 ticks

SPEED_SURGE_FPS_MULTIPLIER = 1.20
SPEED_SURGE_SCORE_MULTIPLIER = 2

POWERUP_SPAWN_LIFESPAN_MS = 10000

# This list needs to be defined after the effect classes are defined.
# For a single file script, Python executes top-to-bottom. So, classes must be defined first.
# Will be defined properly further down, or referenced by string name if defined early.
# For now, placeholder here, will be correctly defined after class definitions.
# AVAILABLE_POWERUPS = []


# --- Class Definitions ---

class Snake:
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    def __init__(self, start_x, start_y, grid_width, grid_height):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.body = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        self.direction = self.RIGHT
        self.intended_direction = self.RIGHT
        self.pending_growth = 0
        self.shield_active = False
        self.active_effect_color_override = None

    def move(self, glitch_active_flag=False):
        current_head_x, current_head_y = self.body[0]

        intended_next_x = current_head_x + self.direction[0]
        intended_next_y = current_head_y + self.direction[1]

        new_head_x = intended_next_x
        new_head_y = intended_next_y

        if glitch_active_flag:
            final_new_head_x = intended_next_x
            final_new_head_y = intended_next_y
            wrapped = False

            if intended_next_y < 0: # Went off Top edge
                final_new_head_x = self.grid_width - 1 # Appear on Right edge
                final_new_head_y = current_head_x      # Y position becomes original X
                final_new_head_y = max(0, min(final_new_head_y, self.grid_height - 1))
                # print(f"Glitch Wrap: Top -> Right. Prev: ({current_head_x},{current_head_y}), Intended: ({intended_next_x},{intended_next_y}), New: ({final_new_head_x},{final_new_head_y})")
                wrapped = True

            elif intended_next_x >= self.grid_width: # Went off Right edge
                final_new_head_y = self.grid_height - 1 # Appear on Bottom edge
                final_new_head_x = current_head_y       # X position becomes original Y
                final_new_head_x = max(0, min(final_new_head_x, self.grid_width - 1))
                # print(f"Glitch Wrap: Right -> Bottom. Prev: ({current_head_x},{current_head_y}), Intended: ({intended_next_x},{intended_next_y}), New: ({final_new_head_x},{final_new_head_y})")
                wrapped = True

            elif intended_next_y >= self.grid_height: # Went off Bottom edge
                final_new_head_x = 0                  # Appear on Left edge
                final_new_head_y = current_head_x     # Y position becomes original X
                final_new_head_y = max(0, min(final_new_head_y, self.grid_height - 1))
                # print(f"Glitch Wrap: Bottom -> Left. Prev: ({current_head_x},{current_head_y}), Intended: ({intended_next_x},{intended_next_y}), New: ({final_new_head_x},{final_new_head_y})")
                wrapped = True

            elif intended_next_x < 0: # Went off Left edge
                final_new_head_y = 0                  # Appear on Top edge
                final_new_head_x = current_head_y     # X position becomes original Y
                final_new_head_x = max(0, min(final_new_head_x, self.grid_width - 1))
                # print(f"Glitch Wrap: Left -> Top. Prev: ({current_head_x},{current_head_y}), Intended: ({intended_next_x},{intended_next_y}), New: ({final_new_head_x},{final_new_head_y})")
                wrapped = True

            if wrapped:
                new_head_x = final_new_head_x
                new_head_y = final_new_head_y
            # If not wrapped, new_head_x and new_head_y remain as intended_next_x/y from before the if/elif chain.
            # This means if it's within bounds, it moves normally even if glitch is active.

        else:
            # Normal toroidal wrap
            if new_head_x >= self.grid_width: new_head_x = 0
            elif new_head_x < 0: new_head_x = self.grid_width - 1
            if new_head_y >= self.grid_height: new_head_y = 0
            elif new_head_y < 0: new_head_y = self.grid_height - 1

        self.body.insert(0, (new_head_x, new_head_y))

        if self.pending_growth > 0:
            self.pending_growth -= 1
        else:
            self.body.pop()

    def change_direction(self, new_direction_tuple):
        self.intended_direction = new_direction_tuple

    def update_actual_direction(self):
        current_dx, current_dy = self.direction
        intended_dx, intended_dy = self.intended_direction
        if (intended_dx + current_dx != 0) or (intended_dy + current_dy != 0):
            self.direction = self.intended_direction

    def grow(self):
        self.pending_growth += 1

    def check_collision_self(self):
        if self.shield_active:
            return False # Shield prevents self-collision
        return self.body[0] in self.body[1:]

    def reset(self, start_x, start_y):
        self.body = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        self.direction = self.RIGHT
        self.intended_direction = self.RIGHT
        self.pending_growth = 0
        self.shield_active = False
        self.active_effect_color_override = None

class Food:
    def __init__(self, grid_width, grid_height, snake_body):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.respawn(snake_body) # Initial spawn

    def respawn(self, snake_body, powerup_pos=None): # powerup_pos to avoid spawning food on a powerup
        while True:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            new_pos = (x,y)
            if new_pos not in snake_body and (powerup_pos is None or new_pos != powerup_pos) :
                self.position = new_pos
                break

class PowerUpEffect:
    def __init__(self, duration_ticks):
        self.duration_ticks = duration_ticks
        self.remaining_ticks = duration_ticks
        self.is_active = True
        self.powerup_type_name = self.__class__.__name__.replace("Effect","")


    def update(self, game_state, snake):
        if self.is_active:
            self.remaining_ticks -= 1
            if self.remaining_ticks <= 0:
                self.deactivate(game_state, snake)
                self.is_active = False

    def activate(self, game_state, snake):
        print(f"{self.powerup_type_name} PowerUp Activated!")
        self.is_active = True
        self.remaining_ticks = self.duration_ticks

    def deactivate(self, game_state, snake):
        print(f"{self.powerup_type_name} PowerUp Deactivated!")
        self.is_active = False

class GlitchEffect(PowerUpEffect):
    def __init__(self):
        super().__init__(duration_ticks=GLITCH_DURATION_TICKS)
        self.original_bg_color = None

    def activate(self, game_state, snake):
        super().activate(game_state, snake)
        game_state.glitch_active = True
        self.original_bg_color = game_state.BG_COLOR
        game_state.BG_COLOR = (random.randint(30, 100), random.randint(30, 100), random.randint(30, 100))

    def deactivate(self, game_state, snake):
        super().deactivate(game_state, snake)
        game_state.glitch_active = False
        if self.original_bg_color is not None:
            game_state.BG_COLOR = self.original_bg_color
            self.original_bg_color = None

class TemporalShieldEffect(PowerUpEffect):
    def __init__(self):
        super().__init__(duration_ticks=SHIELD_DURATION_TICKS)

    def activate(self, game_state, snake):
        super().activate(game_state, snake) # Calls common print message
        snake.shield_active = True
        # Optional: Could add visual change logic here if not handled by draw_snake

    def deactivate(self, game_state, snake):
        super().deactivate(game_state, snake) # Calls common print message
        snake.shield_active = False
        # Optional: Restore snake's appearance if changed directly by activate

class ReverseControlsEffect(PowerUpEffect): # Ensuring this class is present
    def __init__(self):
        super().__init__(duration_ticks=REVERSE_CONTROLS_DURATION_TICKS)

    def activate(self, game_state, snake):
        super().activate(game_state, snake)
        game_state.reverse_controls_active = True
        game_state.hud_message = "CONTROLS REVERSED!"

    def deactivate(self, game_state, snake):
        super().deactivate(game_state, snake)
        game_state.reverse_controls_active = False
        game_state.hud_message = ""

class ExtraLifeCapsuleEffect(PowerUpEffect): # Ensuring this class is present
    def __init__(self):
        super().__init__(duration_ticks=1)

    def activate(self, game_state, snake):
        print("Extra Life Capsule Collected!")
        if game_state.lives < game_state.MAX_LIVES:
            game_state.lives += 1
            game_state.hud_message = "+1 LIFE!"
            print(f"Gained an extra life! Lives: {game_state.lives}")
        else:
            game_state.hud_message = "MAX LIVES REACHED!"
            print(f"Extra Life Capsule collected, but already at max lives ({game_state.lives}).")
        self.is_active = False

    def deactivate(self, game_state, snake):
        super().deactivate(game_state, snake)

class SpeedSurgeEffect(PowerUpEffect):
    def __init__(self):
        super().__init__(duration_ticks=SPEED_SURGE_DURATION_TICKS)
        self.original_snake_color_override = None

    def activate(self, game_state, snake):
        super().activate(game_state, snake)
        game_state.speed_surge_active = True
        game_state.current_score_multiplier = SPEED_SURGE_SCORE_MULTIPLIER
        game_state.fps_modifier *= SPEED_SURGE_FPS_MULTIPLIER

        self.original_snake_color_override = snake.active_effect_color_override
        snake.active_effect_color_override = YELLOW

    def deactivate(self, game_state, snake):
        super().deactivate(game_state, snake)
        game_state.speed_surge_active = False
        game_state.current_score_multiplier = 1
        if game_state.fps_modifier != 0 and SPEED_SURGE_FPS_MULTIPLIER != 0:
             game_state.fps_modifier /= SPEED_SURGE_FPS_MULTIPLIER
        if abs(game_state.fps_modifier - 1.0) < 0.01:
            game_state.fps_modifier = 1.0

        if snake.active_effect_color_override == YELLOW:
            snake.active_effect_color_override = self.original_snake_color_override

class PowerUpSpawnable:
    def __init__(self, position, effect_class, powerup_type_name="PowerUp", color=(255, 255, 0), char="P"):
        self.position = position
        self.powerup_type_name = powerup_type_name
        self.effect_class = effect_class
        self.color = color
        self.char = char # Store the character
        self.creation_time = pygame.time.get_ticks()
        self.blink_on = True

    def draw(self, surface, grid_size, font): # Added font parameter
        if (pygame.time.get_ticks() - self.creation_time) % 700 < 350:
            self.blink_on = False
        else:
            self.blink_on = True

        if self.blink_on:
            rect = pygame.Rect(self.position[0] * grid_size, self.position[1] * grid_size, grid_size, grid_size)
            pygame.draw.rect(surface, self.color, rect)

            try:
                # Use a slightly smaller font size for the character than the grid_size for padding
                char_font_size = int(grid_size * 0.9) # Adjusted size slightly
                char_display_font = None
                # Attempt to create a new font object with desired size, possibly based on the passed font's name
                if hasattr(font, 'name') and font.name is not None: # font.name can be None for system default
                    try:
                        char_display_font = pygame.font.Font(font.name, char_font_size)
                    except pygame.error: # Fallback if specific font name@size fails
                        char_display_font = pygame.font.Font(None, char_font_size)
                else: # Fallback for default system font
                     char_display_font = pygame.font.Font(None, char_font_size)

                text_surf = char_display_font.render(self.char, True, BLACK) # Character color BLACK for contrast
                text_rect = text_surf.get_rect(center=rect.center)
                surface.blit(text_surf, text_rect)
            except Exception as e:
                print(f"Error rendering powerup char '{self.char}': {e}")
                # Fallback visual if text rendering fails
                pygame.draw.circle(surface, BLACK, rect.center, grid_size // 3) # Slightly larger fallback circle

    def is_expired(self, current_ticks, lifespan_ms=POWERUP_SPAWN_LIFESPAN_MS):
        return (current_ticks - self.creation_time) > lifespan_ms

# List of available power-ups
# Defined here, after all PowerUpEffect classes are defined and before GameState which uses it.
AVAILABLE_POWERUPS = [
    {"name": "Glitch", "effect_class": GlitchEffect, "color": GLITCH_POWERUP_COLOR, "char": "G"},
    {"name": "Shield", "effect_class": TemporalShieldEffect, "color": SHIELD_POWERUP_COLOR, "char": "S"},
    {"name": "TimeDilation", "effect_class": TimeDilationEffect, "color": (255, 165, 0), "char": "T"},
    {"name": "SpeedSurge", "effect_class": SpeedSurgeEffect, "color": SPEEDSURGE_POWERUP_COLOR, "char": "F"},
    {"name": "ReverseControls", "effect_class": ReverseControlsEffect, "color": REVERSECONTROLS_POWERUP_COLOR, "char": "R"},
    {"name": "ExtraLife", "effect_class": ExtraLifeCapsuleEffect, "color": EXTRALIFE_POWERUP_COLOR, "char": "L"}
]

class GameState:
    def __init__(self, grid_width, grid_height, sounds_dict):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.sounds = sounds_dict
        self.score = 0
        self.lives = MAX_LIVES
        self.current_level = 1
        self.level_food_counter = 0
        self.game_over = False

        self.glitch_active = False
        self.powerup_on_grid = None
        self.active_powerup_effect = None
        self.BG_COLOR = BLACK
        self.time_dilation_active = False
        self.fps_modifier = 1.0
        self.speed_surge_active = False
        self.current_score_multiplier = 1
        self.reverse_controls_active = False
        self.hud_message = ""
        self.high_scores = []
        self._load_high_scores()

    def increase_score(self, points):
        self.score += points * self.current_score_multiplier

    def lose_life(self):
        self.lives -= 1
        print(f"Lost a life! {self.lives} lives remaining.")
        if self.lives <= 0:
            self.game_over = True
            self.sounds['game_over'].play()
            print("Game Over!")
        else:
            self.sounds['lose_life'].play()

    def level_up(self, snake_body_ref, food_pos_ref):
        self.current_level += 1
        self.level_food_counter = 0
        self.sounds['level_up'].play()
        print(f"Level Up! Reached Level {self.current_level}")

        if random.random() < 0.40: # 40% chance for extra life
            if self.lives < MAX_LIVES:
                self.lives += 1
                print(f"Earned an extra life! Lives: {self.lives}")
            else:
                print(f"Extra life chance hit, but already at max lives ({self.lives}).")

        # Power-up Spawning Logic
        current_spawn_chance = calculate_powerup_spawn_chance(
            self.current_level,
            POWERUP_SPAWN_CHANCE_P0,
            POWERUP_SPAWN_CHANCE_DECAY_RATE,
            MIN_POWERUP_SPAWN_CHANCE
        )
        print(f"Level {self.current_level}. Power-up spawn chance: {current_spawn_chance:.3f}")

        if random.random() < current_spawn_chance:
            if not self.powerup_on_grid and not self.active_powerup_effect and AVAILABLE_POWERUPS:
                spawn_pos = self._get_random_empty_cell(snake_body_ref, food_pos_ref)
                if spawn_pos:
                    chosen_powerup_data = random.choice(AVAILABLE_POWERUPS)
                    self.powerup_on_grid = PowerUpSpawnable(
                        position=spawn_pos,
                        powerup_type_name=chosen_powerup_data["name"],
                        effect_class=chosen_powerup_data["effect_class"],
                        color=chosen_powerup_data["color"],
                        char=chosen_powerup_data["char"]
                    )
                    self.sounds['powerup_spawn'].play()
                    print(f"{chosen_powerup_data['name']} PowerUp spawned at {spawn_pos}")
            else: # this else is for "if spawn_pos:"
                print(f"Spawn chance success, but no valid empty cell found for powerup.")
        else: # this else is for "if random.random() < current_spawn_chance:"
            print(f"Level {self.current_level}. Rolled for power-up, but it didn't spawn this time (chance: {current_spawn_chance:.3f}).")


    def _get_random_empty_cell(self, snake_body, food_pos):
       max_attempts = self.grid_width * self.grid_height
       attempts = 0
       while attempts < max_attempts:
           pos = (random.randint(0, self.grid_width - 1), random.randint(0, self.grid_height - 1))
           if pos not in snake_body and pos != food_pos:
               return pos
           attempts += 1
       return None

    def reset_game(self):
        self.score = 0
        self.lives = MAX_LIVES
        self.current_level = 1
        self.level_food_counter = 0
        self.game_over = False
        self.glitch_active = False
        if self.active_powerup_effect: # Deactivate any existing effect
            # This needs snake object, which is not directly available here.
            # For simplicity, just clearing. Proper deactivation needs snake state.
            print(f"Resetting game, clearing active powerup: {self.active_powerup_effect.powerup_type_name}")
        self.active_powerup_effect = None
        self.powerup_on_grid = None
        self.BG_COLOR = BLACK

    def _load_high_scores(self):
        try:
            with open(HIGH_SCORE_FILE, 'r') as f:
                loaded_scores = json.load(f)
                if isinstance(loaded_scores, list) and all(isinstance(s, int) for s in loaded_scores):
                    self.high_scores = sorted(loaded_scores, reverse=True)[:MAX_HIGH_SCORES]
                    while len(self.high_scores) < MAX_HIGH_SCORES:
                        self.high_scores.append(0)
                else:
                    print(f"Warning: High score data in '{HIGH_SCORE_FILE}' is not a list of integers. Resetting.")
                    self.high_scores = [0] * MAX_HIGH_SCORES
        except FileNotFoundError:
            print(f"Info: High score file '{HIGH_SCORE_FILE}' not found. Initializing with default scores.")
            self.high_scores = [0] * MAX_HIGH_SCORES
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from '{HIGH_SCORE_FILE}'. Resetting high scores.")
            self.high_scores = [0] * MAX_HIGH_SCORES
        self.high_scores.sort(reverse=True) # Ensure it's sorted

    def _save_high_scores(self):
        try:
            with open(HIGH_SCORE_FILE, 'w') as f:
                json.dump(self.high_scores, f)
        except IOError as e:
            print(f"Error saving high scores to {HIGH_SCORE_FILE}: {e}")

    def update_and_save_high_scores(self, current_score):
        # Only add if score is better than the lowest current high score, or if list isn't full
        if len(self.high_scores) < MAX_HIGH_SCORES or current_score > self.high_scores[-1]:
            self.high_scores.append(current_score)
            self.high_scores.sort(reverse=True)
            self.high_scores = self.high_scores[:MAX_HIGH_SCORES] # Keep only top N scores
            self._save_high_scores()
            print(f"High scores updated. New list: {self.high_scores}")
            return True # Score was added
        print(f"Score {current_score} not high enough. Current high scores: {self.high_scores}")
        return False # Score was not high enough


# --- Helper Functions ---

# List of available power-ups
# Defined here, after all PowerUpEffect classes are defined and before GameState which uses it.
AVAILABLE_POWERUPS = [
    {"name": "Glitch", "effect_class": GlitchEffect, "color": GLITCH_POWERUP_COLOR, "char": "G"},
    {"name": "Shield", "effect_class": TemporalShieldEffect, "color": SHIELD_POWERUP_COLOR, "char": "S"},
    {"name": "TimeDilation", "effect_class": TimeDilationEffect, "color": (255, 165, 0), "char": "T"}, # Orange
    {"name": "SpeedSurge", "effect_class": SpeedSurgeEffect, "color": SPEEDSURGE_POWERUP_COLOR, "char": "F"}, # Bright Yellow
    {"name": "ReverseControls", "effect_class": ReverseControlsEffect, "color": REVERSECONTROLS_POWERUP_COLOR, "char": "R"},
    {"name": "ExtraLife", "effect_class": ExtraLifeCapsuleEffect, "color": EXTRALIFE_POWERUP_COLOR, "char": "L"}
]

def calculate_powerup_spawn_chance(level, p0, decay_rate, min_chance):
    if level < 1: level = 1
    # Using formula P0 * e^(-decay_rate * L)
    # At L=1, chance is p0 * e^(-decay_rate). If p0=0.8, decay=0.12 -> 0.8 * exp(-0.12) = 0.709
    # This means the actual chance at level 1 is slightly less than p0.
    # If p0 is desired for L=1, formula P0 * e^(-decay_rate * (L-1)) could be used.
    # Sticking to the specified P(L) = P₀ * e^(-0.12*L)
    chance = p0 * math.exp(-decay_rate * level)
    return max(min_chance, chance)

def calculate_target_fps(level, min_fps, max_fps, gain_per_level):
    if level <= 0: level = 1
    target_fps = min_fps + (level - 1) * gain_per_level
    return min(max_fps, target_fps)

# --- Pygame Initialization ---
pygame.init() # Initializes Pygame modules (needed before font and potentially other things)
pygame.font.init() # Explicitly initialize font module

# Load Sounds (after mixer init)
if mixer_initialized: # Only load if mixer is working
    game_sounds['collect_food'] = load_sound("assets/collect_food.wav", DUMMY_SOUND)
    game_sounds['level_up'] = load_sound("assets/level_up.wav", DUMMY_SOUND)
    game_sounds['lose_life'] = load_sound("assets/lose_life.wav", DUMMY_SOUND)
    game_sounds['game_over'] = load_sound("assets/game_over.wav", DUMMY_SOUND)
    game_sounds['powerup_spawn'] = load_sound("assets/powerup_spawn.wav", DUMMY_SOUND)
    game_sounds['powerup_collect'] = load_sound("assets/powerup_collect.wav", DUMMY_SOUND)
    game_sounds['powerup_activate'] = load_sound("assets/powerup_activate.wav", DUMMY_SOUND)
    game_sounds['powerup_deactivate'] = load_sound("assets/powerup_deactivate.wav", DUMMY_SOUND)
else: # Populate with dummy sounds if mixer failed
    sound_keys = ['collect_food', 'level_up', 'lose_life', 'game_over',
                  'powerup_spawn', 'powerup_collect', 'powerup_activate', 'powerup_deactivate']
    for key in sound_keys:
        game_sounds[key] = DUMMY_SOUND
    print("Mixer not initialized. All sounds will be dummy sounds.")


# Font Loading
try:
    hud_font = pygame.font.Font(FONT_NAME, FONT_SIZE)
    print(f"Successfully loaded font: {FONT_NAME}")
except Exception as e: # More general exception for font loading
    print(f"Warning: Font '{FONT_NAME}' failed to load ({e}). Using default system font.")
    hud_font = pygame.font.Font(None, FONT_SIZE + 4)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Retro Snake - Consolidated")
clock = pygame.time.Clock()

# --- Game Objects ---
start_x = GRID_WIDTH // 2
start_y = GRID_HEIGHT // 2

game_state = GameState(GRID_WIDTH, GRID_HEIGHT, game_sounds) # Pass game_sounds
snake = Snake(start_x, start_y, GRID_WIDTH, GRID_HEIGHT)
food = Food(GRID_WIDTH, GRID_HEIGHT, snake.body)


# --- Drawing Functions ---
def draw_grid(surface):
    for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))

def draw_snake(surface, snake_obj):
    current_segment_color = GREEN

    if snake_obj.active_effect_color_override:
        current_segment_color = snake_obj.active_effect_color_override

    if snake_obj.shield_active:
        current_segment_color = CYAN

    for segment in snake_obj.body:
        gx, gy = segment
        rect = pygame.Rect(gx * GRID_SIZE, gy * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(surface, current_segment_color, rect)
        if snake_obj.shield_active:
             pygame.draw.rect(surface, WHITE, rect, 1)

def draw_food(surface, food_obj):
    rect = pygame.Rect(food_obj.position[0] * GRID_SIZE, food_obj.position[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
    pygame.draw.rect(surface, RED, rect)

def draw_hud(surface, game_state_obj, font, color, current_fps_val):
    score_str = f"SCORE: {game_state_obj.score}"
    score_surf = font.render(score_str, True, color)
    score_rect = score_surf.get_rect(topleft=(GRID_SIZE, GRID_SIZE // 2))
    surface.blit(score_surf, score_rect)

    icon_center_y = GRID_SIZE
    icon_rect_top = icon_center_y - (MINI_SNAKE_ICON_SIZE // 2)
    num_lives_to_show = min(game_state_obj.lives, MAX_LIVES_DISPLAY)
    for i in range(num_lives_to_show):
        icon_x = SCREEN_WIDTH - GRID_SIZE - (i * (MINI_SNAKE_ICON_SIZE + MINI_SNAKE_ICON_GAP)) - MINI_SNAKE_ICON_SIZE
        icon_rect = pygame.Rect(icon_x, icon_rect_top, MINI_SNAKE_ICON_SIZE, MINI_SNAKE_ICON_SIZE)
        pygame.draw.rect(surface, GREEN, icon_rect)

    level_str = f"LEVEL: {game_state_obj.current_level}"
    level_surf = font.render(level_str, True, color)
    level_rect = level_surf.get_rect(midtop=(SCREEN_WIDTH // 2, GRID_SIZE // 2))
    surface.blit(level_surf, level_rect)

    if current_fps_val is not None:
        fps_str = f"FPS: {current_fps_val:.1f}"
        fps_surf = font.render(fps_str, True, color)
        fps_rect = fps_surf.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - GRID_SIZE // 2))
        surface.blit(fps_surf, fps_rect)

    if game_state_obj.hud_message:
        # For HUD messages, use a slightly smaller or different font if desired, or same hud_font
        # Ensure hud_font is robust for different characters in messages
        alert_font = pygame.font.Font(font.name if hasattr(font, 'name') and font.name else None, FONT_SIZE) # Use main HUD font style
        alert_surf = alert_font.render(game_state_obj.hud_message, True, POWERUP_ALERT_COLOR)
        # Position it e.g. bottom center, above FPS, or top center
        alert_rect = alert_surf.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - GRID_SIZE * 2))
        surface.blit(alert_surf, alert_rect)


# --- Main Game Loop ---
current_fps = calculate_target_fps(game_state.current_level, MIN_SNAKE_FPS, MAX_SNAKE_FPS, FPS_GAIN_PER_LEVEL)
running = True

while running and not game_state.game_over:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            intended_direction_key = None
            if event.key == pygame.K_UP: intended_direction_key = Snake.UP
            elif event.key == pygame.K_DOWN: intended_direction_key = Snake.DOWN
            elif event.key == pygame.K_LEFT: intended_direction_key = Snake.LEFT
            elif event.key == pygame.K_RIGHT: intended_direction_key = Snake.RIGHT
            elif event.key == pygame.K_ESCAPE:
                running = False # Still allow ESC to quit regardless of controls

            if intended_direction_key:
                actual_direction_to_set = intended_direction_key
                if game_state.reverse_controls_active:
                    if intended_direction_key == Snake.UP: actual_direction_to_set = Snake.DOWN
                    elif intended_direction_key == Snake.DOWN: actual_direction_to_set = Snake.UP
                    elif intended_direction_key == Snake.LEFT: actual_direction_to_set = Snake.RIGHT
                    elif intended_direction_key == Snake.RIGHT: actual_direction_to_set = Snake.LEFT
                snake.change_direction(actual_direction_to_set)

    snake.update_actual_direction()
    snake.move(game_state.glitch_active)

    if snake.check_collision_self(): # Simplified: No shield check here for now
        game_state.lose_life()
        if game_state.game_over: # Check if game ended after losing life
            # Game over message will be handled outside the loop
            pass
        else: # Reset snake and continue
            snake.reset(start_x, start_y)
            food.respawn(snake.body, game_state.powerup_on_grid.position if game_state.powerup_on_grid else None)
            # Resetting active powerup effect state on death
            if game_state.active_powerup_effect:
                game_state.active_powerup_effect.deactivate(game_state, snake) # Explicitly deactivate
                game_state.active_powerup_effect = None
            game_state.glitch_active = False # Ensure glitch is off
            game_state.BG_COLOR = BLACK # Reset BG color


    if game_state.powerup_on_grid and snake.body[0] == game_state.powerup_on_grid.position:
        if game_state.active_powerup_effect:
            game_state.active_powerup_effect.deactivate(game_state, snake)

        EffectClass = game_state.powerup_on_grid.effect_class
        game_state.active_powerup_effect = EffectClass()
        game_sounds['powerup_collect'].play() # Play collect sound
        game_state.active_powerup_effect.activate(game_state, snake)
        game_sounds['powerup_activate'].play() # Play activate sound
        game_state.powerup_on_grid = None

    if game_state.active_powerup_effect:
        game_state.active_powerup_effect.update(game_state, snake)
        if not game_state.active_powerup_effect.is_active: # Effect just became inactive this frame
            game_sounds['powerup_deactivate'].play()
            game_state.active_powerup_effect = None
            # Deactivate method of the effect should handle resetting specific game_state flags like glitch_active

    if not game_state.game_over and snake.body[0] == food.position:
        snake.grow()
        game_state.increase_score(10) # GameState's increase_score handles multiplier
        game_sounds['collect_food'].play()
        game_state.level_food_counter += 1
        print(f"Score: {game_state.score}, Food this level: {game_state.level_food_counter}/{FOOD_PER_LEVEL}")

        if game_state.level_food_counter >= FOOD_PER_LEVEL:
            game_state.level_up(snake.body, food.position)
            if game_state.powerup_on_grid and game_state.powerup_on_grid.position == food.position:
                 food.respawn(snake.body, game_state.powerup_on_grid.position)

        food.respawn(snake.body, game_state.powerup_on_grid.position if game_state.powerup_on_grid else None)

    if game_state.powerup_on_grid and game_state.powerup_on_grid.is_expired(pygame.time.get_ticks()):
        print(f"{game_state.powerup_on_grid.powerup_type_name} power-up expired from grid.")
        game_state.powerup_on_grid = None

    screen.fill(game_state.BG_COLOR)
    draw_grid(screen)
    draw_snake(screen, snake)
    draw_food(screen, food)
    if game_state.powerup_on_grid:
        game_state.powerup_on_grid.draw(screen, GRID_SIZE, hud_font) # Pass hud_font

    # Calculate FPS for HUD display and clock tick here, after all game logic for the frame
    base_fps_for_level = calculate_target_fps(game_state.current_level, MIN_SNAKE_FPS, MAX_SNAKE_FPS, FPS_GAIN_PER_LEVEL)
    final_applied_fps_to_use = base_fps_for_level * game_state.fps_modifier # Renamed for clarity

    draw_hud(screen, game_state, hud_font, WHITE, final_applied_fps_to_use) # Pass final_applied_fps to HUD
    pygame.display.flip()

    # Clock Tick uses the final_applied_fps calculated above
    clock.tick(final_applied_fps_to_use)

# --- Game Over Screen ---
if game_state.game_over:
    game_state.update_and_save_high_scores(game_state.score) # Update and save high scores

    screen.fill(BLACK)
    try:
        # Use a slightly smaller font for game over title to make space for high scores
        game_over_font = pygame.font.Font(FONT_NAME, int(FONT_SIZE * 1.8))
        hs_font = pygame.font.Font(FONT_NAME, FONT_SIZE) # Font for high score list
        if hs_font is None: raise ValueError("HS Font not loaded") # Trigger except if FONT_NAME failed
        sub_font = hs_font # Use same font for "Final Score" and "Level" for consistency
    except: # Fallback if custom font failed
        game_over_font = pygame.font.Font(None, int((FONT_SIZE + 4) * 1.8))
        hs_font = pygame.font.Font(None, FONT_SIZE + 2) # Slightly smaller default for HS list
        sub_font = hs_font


    # Game Over Title
    title_surf = game_over_font.render("GAME OVER", True, WHITE)
    title_rect = title_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - GRID_SIZE * 3.5)) # Adjusted Y
    screen.blit(title_surf, title_rect)

    # Final Score
    score_str = f"FINAL SCORE: {game_state.score}"
    score_surf = sub_font.render(score_str, True, WHITE)
    score_rect = score_surf.get_rect(center=(SCREEN_WIDTH / 2, title_rect.bottom + GRID_SIZE * 1))
    screen.blit(score_surf, score_rect)

    # Level Reached
    level_str = f"REACHED LEVEL: {game_state.current_level}"
    level_surf = sub_font.render(level_str, True, WHITE)
    level_rect = level_surf.get_rect(center=(SCREEN_WIDTH / 2, score_rect.bottom + GRID_SIZE * 0.5))
    screen.blit(level_surf, level_rect)

    # High Scores Display
    hs_title_surf = hs_font.render("HIGH SCORES", True, WHITE)
    hs_title_rect = hs_title_surf.get_rect(center=(SCREEN_WIDTH / 2, level_rect.bottom + GRID_SIZE * 1.5))
    screen.blit(hs_title_surf, hs_title_rect)

    current_y_offset = hs_title_rect.bottom + GRID_SIZE * 0.5
    for i, score_val in enumerate(game_state.high_scores):
        # Only show top MAX_HIGH_SCORES and don't show trailing zeros if list isn't full,
        # unless it's the only score (e.g. [0,0,0,0,0] should show "1. 0")
        if score_val == 0 and len([s for s in game_state.high_scores if s > 0]) > 0 and i >= len([s for s in game_state.high_scores if s > 0]):
             if i > 0 : continue # Skip if it's a trailing zero and not the first one

        score_display_str = f"{i + 1}. {score_val}"
        if score_val == game_state.score and game_state.score > 0 and \
           (i == 0 or score_val > game_state.high_scores[i-1 if i > 0 else 0] or \
            (len(game_state.high_scores) <= MAX_HIGH_SCORES and score_val >= (game_state.high_scores[-1] if game_state.high_scores else 0))):
            # Highlight the current new high score (simple color change)
            score_item_surf = hs_font.render(score_display_str, True, YELLOW) # Highlight new high score
        else:
            score_item_surf = hs_font.render(score_display_str, True, WHITE)

        score_item_rect = score_item_surf.get_rect(center=(SCREEN_WIDTH / 2, current_y_offset))
        screen.blit(score_item_surf, score_item_rect)
        current_y_offset += hs_font.get_height() + int(GRID_SIZE * 0.1) # Spacing
        if i >= MAX_HIGH_SCORES - 1: break
        if current_y_offset > SCREEN_HEIGHT - GRID_SIZE: break # Stop if running out of screen space


    pygame.display.flip()
    pygame.time.wait(5000) # Increased wait time to see scores

pygame.quit()
sys.exit()
