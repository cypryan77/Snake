import random

class Food:
    def __init__(self, grid_width, grid_height, snake_body):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.respawn(snake_body)

    def respawn(self, snake_body):
        while True:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            if (x, y) not in snake_body:
                self.position = (x, y)
                break
