import random
import pygame
from config import MUTATION_RATE

class Creature:
    def __init__(self, x, y, genes = None):
        self.x = x
        self.y = y
        self.energy = 100
        self.speed = genes.get('speed', 2) if genes else 2

    def move(self, dx, dy):
        if self.energy > 0:
            self.x += dx * self.speed
            self.y += dy * self.speed
            self.energy -= 1
    
    def collides_with(self, food):
        dx = self.x - food.x
        dy = self.y - food.y
        return dx * dx + dy * dy < 100
    
    def mutate_genes(self):
        new_genes = self.genes.copy()
        for key in new_genes:
            if random.random() < MUTATION_RATE:
                mutation = random.uniform(-0.5, 0.5)
                new_genes[key] += mutation
                new_genes[key] = max(0.1, new_genes[key]) # Prevent negative values
        return new_genes
    
    def reproduce(self):
        return Creature(self.x, self.y, genes=self.mutate_genes())
    
    def draw(self, screen):
        pygame.draw.rect(screen, (0, 0, 255), (self.x, self.y, 10, 10))  # Draw as a blue square