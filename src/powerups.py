import pygame
import random

POWERUP_DURATION_TICKS = 100 # Approx 10 seconds if FPS is 10, adjust based on typical FPS

class PowerUpEffect:
    """Base class for active power-up effects."""
    def __init__(self, duration_ticks):
        self.duration_ticks = duration_ticks
        self.remaining_ticks = duration_ticks
        self.is_active = True

    def update(self, game_state, snake): # Called each game tick
        if self.is_active:
            self.remaining_ticks -= 1
            if self.remaining_ticks <= 0:
                self.deactivate(game_state, snake)
                self.is_active = False

    def apply_effect(self, game_state, snake):
        """Apply instantaneous or ongoing changes when effect is active."""
        pass

    def activate(self, game_state, snake):
        """Called once when the power-up is collected."""
        print(f"{self.__class__.__name__} activated.")
        self.is_active = True
        self.remaining_ticks = self.duration_ticks # Reset duration on activation
        pass

    def deactivate(self, game_state, snake):
        """Called once when the power-up duration expires or is manually deactivated."""
        print(f"{self.__class__.__name__} deactivated.")
        self.is_active = False
        pass

class GlitchEffect(PowerUpEffect):
    """Represents the 'Glitch' power-up effect."""
    def __init__(self):
        super().__init__(duration_ticks=POWERUP_DURATION_TICKS)
        self.original_bg_color = None # Store the original background color

    def activate(self, game_state, snake):
        super().activate(game_state, snake)
        game_state.glitch_active = True # Set a flag in game_state

        self.original_bg_color = game_state.BG_COLOR # Store original BG color
        game_state.BG_COLOR = (random.randint(30, 100), random.randint(30, 100), random.randint(30, 100)) # Set new random darkish BG

    def deactivate(self, game_state, snake):
        super().deactivate(game_state, snake)
        game_state.glitch_active = False # Reset the flag

        if self.original_bg_color is not None: # Restore original BG color
            game_state.BG_COLOR = self.original_bg_color
            self.original_bg_color = None # Clear stored color

class PowerUpSpawnable:
    """Represents a power-up item on the grid that can be collected."""
    def __init__(self, position, effect_class, powerup_type_name="GenericPowerUp", color=(255, 255, 0)): # Yellow default
        self.position = position
        self.powerup_type_name = powerup_type_name
        self.effect_class = effect_class  # e.g., GlitchEffect (the class itself, not an instance)
        self.color = color
        self.creation_time = pygame.time.get_ticks() # For animation or timed disappearance
        self.blink = False

    def draw(self, surface, grid_size):
        # Simple blink effect
        if (pygame.time.get_ticks() - self.creation_time) % 1000 < 500: # Blink every 1 second
             self.blink = True
        else:
             self.blink = False

        if not self.blink:
            rect = pygame.Rect(self.position[0] * grid_size, self.position[1] * grid_size, grid_size, grid_size)
            pygame.draw.rect(surface, self.color, rect)

            # Draw a letter 'G' for Glitch
            if self.powerup_type_name == "Glitch":
                try:
                    # Using a system font for simplicity for the letter
                    font = pygame.font.Font(None, grid_size)
                    text_surf = font.render("G", True, (0,0,0)) # Black 'G'
                    text_rect = text_surf.get_rect(center=rect.center)
                    surface.blit(text_surf, text_rect)
                except Exception as e:
                    print(f"Error rendering powerup letter: {e}") # Fallback if font fails
                    pygame.draw.circle(surface, (0,0,0), rect.center, grid_size // 4) # Draw a black dot if text fails

    def is_expired(self, current_ticks, lifespan_ms=10000): # e.g., 10 seconds lifespan
        return (current_ticks - self.creation_time) > lifespan_ms

# Example of another powerup for future use
# class SpeedBoostEffect(PowerUpEffect):
#     def __init__(self):
#         super().__init__(duration_ticks=POWERUP_DURATION_TICKS // 2) # Shorter duration
#         self.original_fps_gain = 0

#     def activate(self, game_state, snake):
#         super().activate(game_state, snake)
#         # Access FPS settings if they are part of game_state or globally accessible
#         # This is a placeholder, assumes FPS_GAIN_PER_LEVEL is accessible for modification
#         # self.original_fps_gain = main_module.FPS_GAIN_PER_LEVEL
#         # main_module.FPS_GAIN_PER_LEVEL *= 2 # Double speed gain
#         print("Speed Boost Activated (Conceptual)")

#     def deactivate(self, game_state, snake):
#         super().deactivate(game_state, snake)
#         # main_module.FPS_GAIN_PER_LEVEL = self.original_fps_gain
#         print("Speed Boost Deactivated (Conceptual)")

# class ShieldEffect(PowerUpEffect):
#    def __init__(self):
#        super().__init__(duration_ticks=POWERUP_DURATION_TICKS * 1.5) # Longer
#
#    def activate(self, game_state, snake):
#        super().activate(game_state, snake)
#        snake.shielded = True # Add a 'shielded' attribute to Snake class
#        print("Shield Activated")

#    def deactivate(self, game_state, snake):
#        super().deactivate(game_state, snake)
#        snake.shielded = False
#        print("Shield Deactivated")

# To use these, you'd also add them to a list of possible powerups to spawn.
# e.g., `POSSIBLE_POWERUPS = [("Glitch", GlitchEffect, (255,0,255)), ("Speed", SpeedBoostEffect, (0,255,255))]`
# And then randomly select from this list when spawning.
# For now, only Glitch is implemented as requested.
