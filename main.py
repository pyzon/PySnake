import os
import random
from enum import Enum

import pygame
from pygame.locals import *
import colors


# Direction enumeration
class Direction(Enum):
    RIGHT = 0
    UP = 1
    LEFT = 2
    DOWN = 3

    def is_opposite(self, direction):
        if self.name == "LEFT" and direction.name == "RIGHT" or \
                self.name == "UP" and direction.name == "DOWN" or \
                self.name == "RIGHT" and direction.name == "LEFT" or \
                self.name == "DOWN" and direction.name == "UP":
            return True
        else:
            return False


# Field class
# A tile on the map, can hold a thing
class Field:
    def __init__(self, map, x: int, y: int):
        self.position = (x, y)
        self.map = map
        self.thing = None


# Thing class
# Can be snake head, snake body, apple, wall
# It is on a field
class Thing:
    def __init__(self, field):
        self.field = field
        field.thing = self

    # Sets the place of the thing
    def set_field(self, field):
        self.field = field
        field.thing = self

    def move(self, where, grow):
        previous_field = self.field
        self.set_field(where)
        previous_field.thing = None

    def step_on(self, who):
        pass

    # Abstract draw function
    def draw(self, surf, cell_width, cell_height):
        pass


# Snake Head class
class SnakeHead(Thing):
    def __init__(self, field, direction):
        super(SnakeHead, self).__init__(field)
        self.followed_by = None
        self.direction = direction
        self.score = 0
        self.speed = 1.0
        self.lives = 3

    # Connects the head with the following body part
    def connect_behind(self, behind):
        self.followed_by = behind
        behind.following = self

    def move(self, where, grow):
        previous_field = self.field
        super().move(where, grow)
        if self.followed_by is not None:
            self.followed_by.move(previous_field, grow)

    def inc_score(self, amount):
        self.score += amount

    # Drawing function
    def draw(self, surf, cell_width, cell_height):
        margin = 0.1
        pygame.draw.ellipse(surf, colors.SNAKE,
                            [(self.field.position[0] + margin) * cell_width,
                             (self.field.position[1] + margin) * cell_height,
                             (1 - 2 * margin) * cell_width,
                             (1 - 2 * margin) * cell_height])


# Snake Body class
class SnakeBody(Thing):
    def __init__(self, field):
        super(SnakeBody, self).__init__(field)
        self.following = None
        self.followed_by = None

    # Connects this body part with the body part it is following
    def connect_ahead(self, ahead):
        self.following = ahead
        ahead.followed_by = self

    # Moves the body part
    # If it is a tail and the grow flag is set, it grows a new body part
    def move(self, where, grow):
        previous_field = self.field
        super().move(where, grow)
        if self.followed_by is not None:
            self.followed_by.move(previous_field, grow)
        elif grow:
            new_body = SnakeBody(previous_field)
            new_body.connect_ahead(self)

    # This happens whenever somebody (a snake head) tries to step on a snake body
    def step_on(self, who):
        # TODO: game over
        pass

    # Draw function
    def draw(self, surf, cell_width, cell_height):
        line_width = min(cell_width, cell_height) * 0.5
        # Position of this body part
        position1 = [int(round((self.field.position[0] + 0.5) * cell_width)),
                     int(round((self.field.position[1] + 0.5) * cell_height))]
        # Position of the body part this body part is following
        position2 = [int(round((self.following.field.position[0] + 0.5) * cell_width)),
                     int(round((self.following.field.position[1] + 0.5) * cell_height))]
        # A line between the two body parts
        # It should go outwards if the two position is at the opposite side of the map
        if (abs(position1[0] - position2[0]) > self.field.map.WIDTH * cell_width / 2) or \
                (abs(position1[1] - position2[1]) > self.field.map.HEIGHT * cell_height / 2):
            pygame.draw.line(surf, colors.SNAKE,
                             position1, [2 * position1[0] - position2[0], 2 * position1[1] - position2[1]],
                             int(round(line_width)))
            pygame.draw.line(surf, colors.SNAKE,
                             [2 * position2[0] - position1[0], 2 * position2[1] - position1[1]], position2,
                             int(round(line_width)))
        else:
            pygame.draw.line(surf, colors.SNAKE, position1, position2, int(round(line_width)))
        # A circle in the current body part to make the joint seamless
        pygame.draw.circle(surf, colors.SNAKE, position1, int(line_width / 2) - 1)


# Apple class
class Apple(Thing):
    def __init__(self, field):
        super(Apple, self).__init__(field)

    # This happens when somebody (a snake head) steps on a apple
    def step_on(self, who):
        who.move(self.field, True)
        who.inc_score(1)
        self.field.map.generate_apple()

    # Drawing function
    def draw(self, surf, cell_width, cell_height):
        margin = 0.2
        pygame.draw.ellipse(surf, colors.APPLE,
                            [(self.field.position[0] + margin) * cell_width,
                             (self.field.position[1] + margin) * cell_height,
                             (1 - 2 * margin) * cell_width,
                             (1 - 2 * margin) * cell_height])


# Wall class
class Wall(Thing):
    def __init__(self, field):
        super(Wall, self).__init__(field)

    # This happens whenever somebody (a snake head) tries to step on a wall
    def step_on(self, who):
        # TODO: game over
        pass

    def draw(self, surf, cell_width, cell_height):
        # TODO: wall draw
        pass


# TODO: class berry (faster)
# TODO: class snail (slower)
# TODO: class mushroom (turn around)
# TODO: class wormhole (teleport)


# Map class
# Contains a 2D array of Fields
class Map:
    def __init__(self):
        self.WIDTH = 20
        self.HEIGHT = 20
        # Filling the map with new fields
        self.fields = [[Field(self, i, j) for j in range(self.HEIGHT)] for i in range(self.WIDTH)]
        # for i in range(self.WIDTH):
        #    for j in range(self.HEIGHT):
        #        self.set_field(i, j, Field(self, i, j))

    # Corrects the coordinates if they overflow the map
    # Returns the corrected pair of coordinates
    def corrected_position(self, position):
        return position[0] % self.WIDTH, position[1] % self.HEIGHT

    # Calculates the position behind a position with a direction
    def behind(self, position, direction):
        if direction == Direction.RIGHT:
            return self.corrected_position((position[0] - 1, position[1]))
        elif direction == Direction.UP:
            return self.corrected_position((position[0], position[1] + 1))
        elif direction == Direction.LEFT:
            return self.corrected_position((position[0] + 1, position[1]))
        elif direction == Direction.DOWN:
            return self.corrected_position((position[0], position[1] - 1))

    # Calculates the position behind a position with a direction
    def front(self, position, direction):
        if direction == Direction.RIGHT:
            return self.corrected_position((position[0] + 1, position[1]))
        elif direction == Direction.UP:
            return self.corrected_position((position[0], position[1] - 1))
        elif direction == Direction.LEFT:
            return self.corrected_position((position[0] - 1, position[1]))
        elif direction == Direction.DOWN:
            return self.corrected_position((position[0], position[1] + 1))

    def set_field(self, position, field):
        """Sets the field at a position"""
        x = position[0]
        y = position[1]
        self.fields[x][y] = field

    # Returns a field at a position
    def get_field(self, position):
        x = position[0]
        y = position[1]
        return self.fields[x][y]

    # Generates an apple on an empty field of the map
    def generate_apple(self):
        # Putting all the empty field into a list
        empty_fields = []
        for i in range(self.WIDTH):
            for j in range(self.HEIGHT):
                if self.get_field((i, j)).thing is None:
                    empty_fields.append(self.get_field((i, j)))
        new_apple = Apple(random.choice(empty_fields))
        return new_apple


class App:
    # Static
    cell_size = cell_width, cell_height = 20, 20

    # TODO: refactor the init stuff so the on_init can be called multiple times
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.clock = None
        # The direction the snake will try to go in each frame
        # This can be changed multiple times during a frame since multiple keys can be pressed through one tick
        # however only the last keystroke will count in each frame
        self.next_direction = random.choice([Direction.LEFT, Direction.UP, Direction.RIGHT, Direction.DOWN])
        self.map = Map()
        self.info_bar_height = 20
        self.size = self.width, self.height = self.cell_width * self.map.WIDTH, self.cell_height * self.map.HEIGHT + \
            self.info_bar_height
        # Setting up the snake head
        self.snake = SnakeHead(self.map.fields[random.randrange(self.map.WIDTH)][random.randrange(self.map.HEIGHT)],
                               self.next_direction)
        # For testing
        # self.snake = SnakeHead(self.map.get_field((0, 0)), Direction.DOWN)
        # Setting up the rest of the snake
        next_position = self.map.behind(self.snake.field.position, self.snake.direction)
        previous_snake_part = self.snake
        for i in range(2):
            next_snake_body = SnakeBody(self.map.get_field(next_position))
            next_snake_body.connect_ahead(previous_snake_part)
            # TODO: might want a function that calculates the position behind a body part relative to the direction of the body part that it is following
            next_position = self.map.behind(next_position, self.snake.direction)
            previous_snake_part = next_snake_body
        # Generating an apple
        self.map.generate_apple()

    def on_init(self):
        pygame.init()
        pygame.display.set_caption("Python Snake", "snake")
        icon_path = os.path.join("resources", "snake.png")
        try:
            icon_surf = pygame.image.load(icon_path)
            pygame.display.set_icon(icon_surf)
        except IOError:
            print("Unable to load file: " + icon_path)
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.clock = pygame.time.Clock()
        return self._display_surf

    def on_event(self, event):
        # Handling user input and other events here
        # Handling arrow keys
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                self.next_direction = Direction.RIGHT
            elif event.key == pygame.K_UP:
                self.next_direction = Direction.UP
            elif event.key == pygame.K_LEFT:
                self.next_direction = Direction.LEFT
            elif event.key == pygame.K_DOWN:
                self.next_direction = Direction.DOWN
        # Handling closing the window
        if event.type == pygame.QUIT:
            self._running = False

    def on_loop(self):
        # Stepping things here
        # Setting the next direction of the snake
        if not self.snake.direction.is_opposite(self.next_direction):
            self.snake.direction = self.next_direction
        # Stepping the snake
        next_field = self.map.get_field(self.map.front(self.snake.field.position, self.snake.direction))
        # If the field in front of the snake is empty
        if next_field.thing is None:
            self.snake.move(next_field, False)
        # If the field contains something
        else:
            next_field.thing.step_on(self.snake)

    def draw_map(self, surf, rect: pygame.Rect):
        x = rect.x
        y = rect.y
        cell_width = rect.w
        cell_height = rect.h
        # Drawing grid
        for i in range(self.map.HEIGHT):
            pygame.draw.line(surf, colors.GRID,
                             [x, y + i * cell_height], [x + self.map.WIDTH * cell_width, y + i * cell_height])
        for i in range(self.map.WIDTH):
            pygame.draw.line(surf, colors.GRID,
                             [x + i * cell_width, y], [x + i * cell_width, y + self.map.HEIGHT * cell_height])
        # Drawing things
        for i in range(self.map.WIDTH):
            for j in range(self.map.HEIGHT):
                thing = self.map.get_field((i, j)).thing
                if thing is not None:
                    thing.draw(surf, self.cell_width, self.cell_height)

    def draw_frame(self, surf, outer_rect: pygame.Rect, inner_rect: pygame.Rect, margin, edge_width):
        # left rect
        pygame.draw.rect(surf, colors.FRAME,
                         [outer_rect.left, outer_rect.top, inner_rect.left-outer_rect.left, outer_rect.height])
        # right rect
        pygame.draw.rect(surf, colors.FRAME,
                         [inner_rect.right, outer_rect.top, outer_rect.right-inner_rect.right, outer_rect.height])
        # top rect
        pygame.draw.rect(surf, colors.FRAME,
                         [inner_rect.left, outer_rect.top, inner_rect.width, inner_rect.top-outer_rect.top])
        # bottom rect
        pygame.draw.rect(surf, colors.FRAME,
                         [inner_rect.left, inner_rect.bottom, inner_rect.width, outer_rect.bottom-inner_rect.bottom])
        # outer edge
        pygame.draw.rect(surf, colors.FRAME_EDGE,
                         [outer_rect.left+margin, outer_rect.top+margin,
                          outer_rect.width-2*margin, outer_rect.height-2*margin], edge_width)
        # inner edge
        pygame.draw.rect(surf, colors.FRAME_EDGE,
                         [inner_rect.left-margin, inner_rect.top-margin,
                          inner_rect.width+2*margin, inner_rect.height+2*margin], edge_width)

    def on_render(self):
        # Drawing things here
        # Clearing the screen
        self._display_surf.fill(colors.BACKGROUND)
        # TODO: display the map on specific coordinates, instead of 0,0
        # TODO: make the info bar look nice (with scores and lives)
        self.draw_map(self._display_surf, Rect((0, self.info_bar_height), (self.cell_width, self.cell_height)))
        #self.draw_frame(self._display_surf, Rect())
        # Executing render
        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if self.on_init() is None:
            self._running = False

        while self._running:
            self.clock.tick(5)
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
        self.on_cleanup()


if __name__ == "__main__":
    myApp = App()
    myApp.on_execute()

# TODO: snake speed
# TODO: snake lives
# TODO: score display
# TODO: high scores
# TODO: sprites
# TODO: fancy animations
# TODO: sound
# TODO: menu
# TODO: multiplayer: color is the snake's property
