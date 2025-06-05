import pygame
import sys
from src.snake import Snake
from src.food import Food
from src.game_state import GameState

# --- Constants ---
FONT_NAME = "assets/pixel_font.ttf"
GRID_SIZE = 20  # pixels
FONT_SIZE = GRID_SIZE # Target font size, may be adjusted for default font
GRID_WIDTH = 32  # number of cells
GRID_HEIGHT = 24  # number of cells

SCREEN_WIDTH = GRID_WIDTH * GRID_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * GRID_SIZE

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)  # Snake color
RED = (255, 0, 0)    # Food color
GRID_COLOR = (40, 40, 40) # Light grey for grid lines

# Speed-related constants for difficulty scaling
MIN_SNAKE_FPS = 5.0  # Starting FPS
MAX_SNAKE_FPS = 15.0 # Maximum FPS
FPS_GAIN_PER_LEVEL = 0.5 # FPS increase per level

# HUD Icon constants
MINI_SNAKE_ICON_SIZE = GRID_SIZE // 2
MINI_SNAKE_ICON_GAP = GRID_SIZE // 4
MAX_LIVES_DISPLAY = 5 # Max icons to draw for lives

FOOD_PER_LEVEL = 10 # Number of food items to eat to level up

# --- Helper Functions ---
def calculate_target_fps(level, min_fps, max_fps, gain_per_level):
    if level <= 0: # Should not happen with current game logic, but good for robustness
        level = 1
    target_fps = min_fps + (level - 1) * gain_per_level
    return min(max_fps, target_fps)

# --- Pygame Initialization ---
pygame.init() # Initializes all Pygame modules, including font

# Font Loading
try:
    hud_font = pygame.font.Font(FONT_NAME, FONT_SIZE)
    print(f"Successfully loaded font: {FONT_NAME}")
except pygame.error as e:
    print(f"Warning: Font '{FONT_NAME}' not found or failed to load ({e}). Using default system font.")
    hud_font = pygame.font.Font(None, FONT_SIZE + 4) # Default font might need slightly larger size for readability
except Exception as e: # Catch any other unexpected error during font loading
    print(f"An unexpected error occurred while loading font: {e}. Using default system font.")
    hud_font = pygame.font.Font(None, FONT_SIZE + 4)


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Retro Snake")
clock = pygame.time.Clock()

# --- Game Objects ---
# Initial snake position at the center of the grid
start_x = GRID_WIDTH // 2
start_y = GRID_HEIGHT // 2

snake = Snake(start_x, start_y, GRID_WIDTH, GRID_HEIGHT)
# Pass snake.body to food to ensure food doesn't spawn on the snake
food = Food(GRID_WIDTH, GRID_HEIGHT, snake.body)
game_state = GameState(GRID_WIDTH, GRID_HEIGHT) # Pass grid dimensions

# --- Drawing Functions ---
def draw_grid(surface):
    for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))

def draw_snake(surface, snake_obj):
    for segment in snake_obj.body:
        gx, gy = segment
        rect = pygame.Rect(gx * GRID_SIZE, gy * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(surface, GREEN, rect)

def draw_food(surface, food_obj):
    gx, gy = food_obj.position
    rect = pygame.Rect(gx * GRID_SIZE, gy * GRID_SIZE, GRID_SIZE, GRID_SIZE)
    pygame.draw.rect(surface, RED, rect)

# --- HUD Function ---
def draw_hud(surface, game_state_obj, font, color, current_fps_display=None): # Added current_fps_display
    # Score Display
    score_str = f"SCORE: {game_state_obj.score}"
    score_surf = font.render(score_str, True, color) # Anti-aliasing True for smoother text
    score_rect = score_surf.get_rect(topleft=(GRID_SIZE, GRID_SIZE // 2))
    surface.blit(score_surf, score_rect)

    # Lives Display (Miniature Snake Icons)
    lives_display_x_start = SCREEN_WIDTH - GRID_SIZE # Align with where text used to be (right edge)
    # Text HUD elements are typically aligned with their top at GRID_SIZE // 2
    # We want the center of the icon to be aligned with the center of the text line.
    # Text font size is FONT_SIZE (GRID_SIZE), so text center is (GRID_SIZE // 2) + (GRID_SIZE // 2) = GRID_SIZE
    icon_center_y = GRID_SIZE # Target Y for the center of the icon
    icon_rect_top = icon_center_y - (MINI_SNAKE_ICON_SIZE // 2)

    num_lives_to_show = min(game_state_obj.lives, MAX_LIVES_DISPLAY)
    for i in range(num_lives_to_show):
        # Calculate X position for each icon, drawing from right to left
        icon_x = lives_display_x_start - (i * (MINI_SNAKE_ICON_SIZE + MINI_SNAKE_ICON_GAP)) - MINI_SNAKE_ICON_SIZE
        icon_rect = pygame.Rect(icon_x, icon_rect_top, MINI_SNAKE_ICON_SIZE, MINI_SNAKE_ICON_SIZE)
        pygame.draw.rect(surface, GREEN, icon_rect)
        # Consider adding a darker green border or a small "eye" dot for more detail if desired later.
        # For now, a simple green square.

    # Level Display
    level_str = f"LEVEL: {game_state_obj.current_level}"
    level_surf = font.render(level_str, True, color)
    level_rect = level_surf.get_rect(midtop=(SCREEN_WIDTH // 2, GRID_SIZE // 2))
    surface.blit(level_surf, level_rect)

    # FPS Display (Optional)
    if current_fps_display is not None: # Allow current_fps_display to be optional
        fps_str = f"FPS: {current_fps_display:.1f}"
        fps_surf = font.render(fps_str, True, color)
        fps_rect = fps_surf.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - GRID_SIZE // 2))
        surface.blit(fps_surf, fps_rect)

# --- Main Game Loop ---
# Calculate initial FPS
current_fps = calculate_target_fps(game_state.current_level, MIN_SNAKE_FPS, MAX_SNAKE_FPS, FPS_GAIN_PER_LEVEL)

running = True
while running and not game_state.game_over:
    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                snake.change_direction(Snake.UP)
            elif event.key == pygame.K_DOWN:
                snake.change_direction(Snake.DOWN)
            elif event.key == pygame.K_LEFT:
                snake.change_direction(Snake.LEFT)
            elif event.key == pygame.K_RIGHT:
                snake.change_direction(Snake.RIGHT)
            elif event.key == pygame.K_ESCAPE:
                running = False

    # Game Logic
    snake.update_actual_direction() # Apply queued direction change
    snake.move(game_state.glitch_active) # Pass glitch_active flag

    # Self-Collision Check
    if snake.check_collision_self() and not (game_state.active_powerup_effect and game_state.active_powerup_effect.powerup_type_name == "Shield"): # Assuming a Shield powerup might grant invincibility
        game_state.lose_life()
        if not game_state.game_over:
            snake.reset(start_x, start_y)
            food.respawn(snake.body)
            # Potentially clear active powerups on death or let them persist through lives. For now, let them persist.
            # game_state.active_powerup_effect = None
            # game_state.glitch_active = False
            # game_state.BG_COLOR = BLACK

    # PowerUp Collection
    if game_state.powerup_on_grid and snake.body[0] == game_state.powerup_on_grid.position:
        if game_state.active_powerup_effect: # Deactivate previous before activating new one
            game_state.active_powerup_effect.deactivate(game_state, snake)

        effect_module = game_state.powerup_on_grid.effect_class # Get the class
        game_state.active_powerup_effect = effect_module()    # Instantiate it
        game_state.active_powerup_effect.activate(game_state, snake)
        game_state.powerup_on_grid = None # Remove from grid

    # Update Active PowerUp Effect
    if game_state.active_powerup_effect:
        game_state.active_powerup_effect.update(game_state, snake)
        if not game_state.active_powerup_effect.is_active: # If effect timed out
            game_state.active_powerup_effect = None
            # Ensure glitch_active is also reset if it was the one that expired
            # The effect's deactivate method should handle this.

    # Food Consumption Check
    if not game_state.game_over and snake.body[0] == food.position:
        snake.grow()
        game_state.increase_score(10)
        game_state.level_food_counter += 1
        print(f"Score: {game_state.score}, Food this level: {game_state.level_food_counter}/{FOOD_PER_LEVEL}")

        if game_state.level_food_counter >= FOOD_PER_LEVEL:
            game_state.level_up(snake.body) # Pass snake_body for powerup spawning logic
            # Food might need to be respawned if powerup spawns on it
            if game_state.powerup_on_grid and game_state.powerup_on_grid.position == food.position:
                 food.respawn(snake.body) # Respawn food if powerup overwrote it

        food.respawn(snake.body)

    # Check if spawnable powerup has expired
    if game_state.powerup_on_grid and hasattr(game_state.powerup_on_grid, 'is_expired'):
        if game_state.powerup_on_grid.is_expired(pygame.time.get_ticks()):
            print(f"{game_state.powerup_on_grid.powerup_type_name} power-up expired from grid.")
            game_state.powerup_on_grid = None


    # Rendering
    screen.fill(game_state.BG_COLOR) # Use dynamic BG_COLOR
    draw_grid(screen)
    draw_snake(screen, snake)
    draw_food(screen, food)
    if game_state.powerup_on_grid: # Draw powerup if it exists
        game_state.powerup_on_grid.draw(screen, GRID_SIZE)
    draw_hud(screen, game_state, hud_font, WHITE, current_fps)
    pygame.display.flip()

    # Clock Tick & FPS Update for next frame
    current_fps = calculate_target_fps(game_state.current_level, MIN_SNAKE_FPS, MAX_SNAKE_FPS, FPS_GAIN_PER_LEVEL)
    clock.tick(current_fps)

# --- Game Over Screen ---
if game_state.game_over:
    screen.fill(BLACK) # Clear screen for game over message

    # Determine Game Over font (larger than HUD font)
    try:
        # Attempt to load the custom font at a larger size
        game_over_title_font = pygame.font.Font(FONT_NAME, FONT_SIZE * 2)
    except:
        # Fallback to system font if custom font fails or wasn't loaded initially
        game_over_title_font = pygame.font.Font(None, (FONT_SIZE + 4) * 2) # Larger default

    title_text = "GAME OVER"
    title_surf = game_over_title_font.render(title_text, True, WHITE)
    title_rect = title_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - GRID_SIZE * 2))
    screen.blit(title_surf, title_rect)

    final_score_str = f"FINAL SCORE: {game_state.score}"
    score_surf = hud_font.render(final_score_str, True, WHITE) # Use hud_font for consistency
    score_rect = score_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + GRID_SIZE))
    screen.blit(score_surf, score_rect)

    final_level_str = f"REACHED LEVEL: {game_state.current_level}"
    level_surf = hud_font.render(final_level_str, True, WHITE) # Use hud_font for consistency
    level_rect = level_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + GRID_SIZE * 2.5))
    screen.blit(level_surf, level_rect)

    pygame.display.flip()
    pygame.time.wait(3000) # Wait for 3 seconds

# --- Quit Pygame ---
pygame.quit()
sys.exit()
