from config import SCREEN_WIDTH, SCREEN_HEIGHT
import pygame

class Food:
    FOOD_SPRITE = pygame.transform.scale(
        pygame.image.load('assets/food.png'), (20, 20)
    )
    def __init__(self, x, y, energy=20):
        self.radius = 4 # Size for drawing
        # Clamp so food is always fully visible
        self.x = min(max(x, self.radius), SCREEN_WIDTH - self.radius)
        self.y = min(max(y, self.radius), SCREEN_HEIGHT - self.radius)
        self.energy = energy
        self.targeted_by = None
    
    def draw(self, screen):
        screen.blit(self.FOOD_SPRITE, (int(self.x), int(self.y)))