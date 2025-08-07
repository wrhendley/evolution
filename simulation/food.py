import pygame

class Food:
    def __init__(self, x, y, energy=20):
        self.x = x
        self.y = y
        self.energy = energy
        self.radius = 4 # Size for drawing
    
    def draw(self, screen):
        pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), self.radius)