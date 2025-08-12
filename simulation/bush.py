import pygame
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT

class Bush:
    BUSH_SPRITE = pygame.transform.scale(pygame.image.load('assets/bush.png'), (64, 64))

    def __init__(self, x=None, y=None):
        self.x = x if x is not None else random.randint(0, SCREEN_WIDTH - 64)
        self.y = y if y is not None else random.randint(0, SCREEN_HEIGHT - 64)
        self.food = []  # List of Food objects growing on this bush

    def grow_food(self, FoodClass, max_food=3):
        # Only grow food if less than max_food on bush
        if len(self.food) < max_food:
            # Place food at bush center (or random offset for variety)
            fx = self.x + 16 + random.randint(-8, 8)
            fy = self.y + 16 + random.randint(-8, 8)
            self.food.append(FoodClass(fx, fy))

    def remove_food(self, food_obj):
        if food_obj in self.food:
            self.food.remove(food_obj)

    def draw(self, screen):
        screen.blit(self.BUSH_SPRITE, (self.x, self.y))
        for food in self.food:
            food.draw(screen)
