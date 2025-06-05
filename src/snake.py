class Snake:
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    def __init__(self, start_x, start_y, grid_width, grid_height):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.body = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        self.direction = self.RIGHT  # Initial actual direction
        self.intended_direction = self.RIGHT # Intended direction by player input
        self.pending_growth = 0

    def move(self, glitch_active_flag=False): # Added glitch_active_flag
        curr_head_x, curr_head_y = self.body[0]
        new_head_x = curr_head_x + self.direction[0]
        new_head_y = curr_head_y + self.direction[1]

        if glitch_active_flag:
            # Glitch Wrap Logic (Offset Wrap Example)
            offset = 5
            if new_head_x >= self.grid_width:
                new_head_x = 0
                new_head_y = (new_head_y + offset) % self.grid_height
            elif new_head_x < 0:
                new_head_x = self.grid_width - 1
                new_head_y = (new_head_y - offset + self.grid_height) % self.grid_height

            if new_head_y >= self.grid_height:
                new_head_y = 0
                new_head_x = (new_head_x + offset) % self.grid_width
            elif new_head_y < 0:
                new_head_y = self.grid_height - 1
                new_head_x = (new_head_x - offset + self.grid_width) % self.grid_width
        else:
            # Normal Wrap-around logic
            if new_head_x >= self.grid_width:
                new_head_x = 0
            elif new_head_x < 0:
                new_head_x = self.grid_width - 1
            if new_head_y >= self.grid_height:
                new_head_y = 0
            elif new_head_y < 0:
                new_head_y = self.grid_height - 1

        self.body.insert(0, (new_head_x, new_head_y))

        if self.pending_growth > 0:
            self.pending_growth -= 1
        else:
            self.body.pop() # Tail is removed only if not growing

    def change_direction(self, new_direction_tuple):
        # This method now simply updates the intended direction.
        # The 180-degree turn prevention is handled in update_actual_direction.
        self.intended_direction = new_direction_tuple

    def update_actual_direction(self):
        # Apply the intended_direction to the actual direction
        # if it's not a 180-degree reversal.
        current_dx, current_dy = self.direction
        intended_dx, intended_dy = self.intended_direction

        # This condition is true if they are not exact opposites.
        # e.g., current (1,0) RIGHT, intended (-1,0) LEFT -> (1 + -1 != 0) is FALSE OR (0 + 0 != 0) is FALSE -> condition is FALSE
        # e.g., current (1,0) RIGHT, intended (0,1) DOWN -> (1 + 0 != 0) is TRUE OR (0 + 1 != 0) is TRUE -> condition is TRUE
        if (intended_dx + current_dx != 0) or (intended_dy + current_dy != 0):
            self.direction = self.intended_direction
        # If the snake is length 1, it can turn any way (no body to collide with immediately)
        # This is an edge case that might be considered if the snake could be length 1.
        # For now, the standard 180-degree check is maintained.

    def grow(self):
        self.pending_growth += 1

    def check_collision_self(self):
        head = self.body[0]
        return head in self.body[1:]

    def reset(self, start_x, start_y):
        self.body = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        self.direction = self.RIGHT
        self.intended_direction = self.RIGHT # Reset intended direction as well
        self.pending_growth = 0
