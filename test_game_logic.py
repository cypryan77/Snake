import unittest
# Assuming main.py contains all game logic classes and constants
# To import from main.py, we might need to ensure it's in PYTHONPATH or adjust sys.path
# For simplicity, the test runner usually handles this if main.py is in the same directory.
from main import Snake, GRID_WIDTH, GRID_HEIGHT # Import other constants as needed

# Define Snake direction constants locally for test clarity
SNAKE_UP = (0, -1)
SNAKE_DOWN = (0, 1)
SNAKE_LEFT = (-1, 0)
SNAKE_RIGHT = (1, 0)

class TestSnakeMovement(unittest.TestCase):
    def setUp(self):
        # Initialize snake for each test to ensure isolation
        # Snake(start_x, start_y, grid_width, grid_height)
        self.snake = Snake(GRID_WIDTH // 2, GRID_HEIGHT // 2, GRID_WIDTH, GRID_HEIGHT)

    def test_normal_wrap_right_edge(self):
        self.snake.body = [(GRID_WIDTH - 1, GRID_HEIGHT // 2)] # Head at right edge
        self.snake.direction = SNAKE_RIGHT
        self.snake.move(glitch_active_flag=False)
        self.assertEqual(self.snake.body[0], (0, GRID_HEIGHT // 2), "Snake should wrap from right to left")

    def test_normal_wrap_left_edge(self):
        self.snake.body = [(0, GRID_HEIGHT // 2)]
        self.snake.direction = SNAKE_LEFT
        self.snake.move(glitch_active_flag=False)
        self.assertEqual(self.snake.body[0], (GRID_WIDTH - 1, GRID_HEIGHT // 2), "Snake should wrap from left to right")

    def test_normal_wrap_bottom_edge(self):
        self.snake.body = [(GRID_WIDTH // 2, GRID_HEIGHT - 1)]
        self.snake.direction = SNAKE_DOWN
        self.snake.move(glitch_active_flag=False)
        self.assertEqual(self.snake.body[0], (GRID_WIDTH // 2, 0), "Snake should wrap from bottom to top")

    def test_normal_wrap_top_edge(self):
        self.snake.body = [(GRID_WIDTH // 2, 0)]
        self.snake.direction = SNAKE_UP
        self.snake.move(glitch_active_flag=False)
        self.assertEqual(self.snake.body[0], (GRID_WIDTH // 2, GRID_HEIGHT - 1), "Snake should wrap from top to bottom")

    # Glitch Wrap Tests (Top -> Right, Right -> Bottom, Bottom -> Left, Left -> Top)
    def test_glitch_wrap_top_to_right(self):
        # Head at (10, 0), moving UP. Should appear at (GRID_WIDTH-1, 10)
        original_x, original_y = 10, 0
        self.snake.body = [(original_x, original_y)] # Snake of length 1 for simplicity in this test
        self.snake.direction = SNAKE_UP
        self.snake.move(glitch_active_flag=True)
        expected_x, expected_y = GRID_WIDTH - 1, original_x
        self.assertEqual(self.snake.body[0], (expected_x, expected_y), f"Glitch Top->Right failed. Expected ({expected_x},{expected_y})")

    def test_glitch_wrap_right_to_bottom(self):
        original_x, original_y = GRID_WIDTH - 1, 10
        self.snake.body = [(original_x, original_y)]
        self.snake.direction = SNAKE_RIGHT
        self.snake.move(glitch_active_flag=True)
        expected_x, expected_y = original_y, GRID_HEIGHT - 1
        self.assertEqual(self.snake.body[0], (expected_x, expected_y), f"Glitch Right->Bottom failed. Expected ({expected_x},{expected_y})")

    def test_glitch_wrap_bottom_to_left(self):
        original_x, original_y = 10, GRID_HEIGHT - 1
        self.snake.body = [(original_x, original_y)]
        self.snake.direction = SNAKE_DOWN
        self.snake.move(glitch_active_flag=True)
        expected_x, expected_y = 0, original_x
        self.assertEqual(self.snake.body[0], (expected_x, expected_y), f"Glitch Bottom->Left failed. Expected ({expected_x},{expected_y})")

    def test_glitch_wrap_left_to_top(self):
        original_x, original_y = 0, 10
        self.snake.body = [(original_x, original_y)]
        self.snake.direction = SNAKE_LEFT
        self.snake.move(glitch_active_flag=True)
        expected_x, expected_y = original_y, 0
        self.assertEqual(self.snake.body[0], (expected_x, expected_y), f"Glitch Left->Top failed. Expected ({expected_x},{expected_y})")


class TestSnakeCollision(unittest.TestCase):
    def setUp(self):
        self.snake = Snake(GRID_WIDTH // 2, GRID_HEIGHT // 2, GRID_WIDTH, GRID_HEIGHT)

    def test_no_collision_on_start(self):
        # Default snake: [(16,12), (15,12), (14,12)]
        self.assertFalse(self.snake.check_collision_self(), "New snake should not have self-collision")

    def test_simple_self_collision(self):
        # Force a collision: Head (10,10) moves into a body segment also at (10,10)
        self.snake.body = [(10,10), (11,10), (10,10), (9,10)]
        self.assertTrue(self.snake.check_collision_self(), "Snake should detect self-collision")

    def test_no_collision_when_shield_active(self):
        self.snake.body = [(10,10), (11,10), (10,10), (9,10)] # Collision state
        self.snake.shield_active = True
        self.assertFalse(self.snake.check_collision_self(), "Collision should be ignored when shield is active")


class TestInputManager(unittest.TestCase):
    def setUp(self):
        self.snake = Snake(GRID_WIDTH // 2, GRID_HEIGHT // 2, GRID_WIDTH, GRID_HEIGHT)
        self.snake.direction = SNAKE_RIGHT # Default starting direction

    def test_prevent_180_degree_up_down(self):
        self.snake.direction = SNAKE_UP # Current direction is UP
        self.snake.change_direction(SNAKE_DOWN) # Intend to go DOWN
        self.snake.update_actual_direction()    # Apply intention
        self.assertEqual(self.snake.direction, SNAKE_UP, "Should not allow 180-degree turn from UP to DOWN")

    def test_prevent_180_degree_left_right(self):
        self.snake.direction = SNAKE_LEFT # Current direction is LEFT
        self.snake.change_direction(SNAKE_RIGHT) # Intend to go RIGHT
        self.snake.update_actual_direction()
        self.assertEqual(self.snake.direction, SNAKE_LEFT, "Should not allow 180-degree turn from LEFT to RIGHT")

    def test_allow_90_degree_turn_up_left(self):
        self.snake.direction = SNAKE_UP # Current direction is UP
        self.snake.change_direction(SNAKE_LEFT) # Intend to go LEFT
        self.snake.update_actual_direction()
        self.assertEqual(self.snake.direction, SNAKE_LEFT, "Should allow 90-degree turn from UP to LEFT")

    def test_queued_input_processed_correctly(self):
        self.snake.direction = SNAKE_RIGHT
        self.snake.change_direction(SNAKE_UP) # Player presses UP
        # Before update_actual_direction, snake should still be RIGHT
        self.assertEqual(self.snake.direction, SNAKE_RIGHT)
        self.assertEqual(self.snake.intended_direction, SNAKE_UP)

        self.snake.update_actual_direction() # Apply the queued direction
        self.assertEqual(self.snake.direction, SNAKE_UP, "Direction should be UP after update")


if __name__ == '__main__':
    unittest.main()
