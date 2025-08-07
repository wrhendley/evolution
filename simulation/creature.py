import numpy as np
import random
import pygame
from config import MUTATION_RATE

class Creature:
    def __init__(self, x, y, genes = None, brain = None):
        self.x = x
        self.y = y
        self.energy = 100
        self.age = 0
        
        self.speed = genes['speed'] if genes else 2
        self.vision = genes['vision'] if genes else 100
        
        self.brain = brain or {
            "input_weights": np.random.randn(5,6),
            "hidden_weights": np.random.randn(6,3)
        }
    
    def think(self, inputs):
        h = np.dot(inputs, self.brain['input_weights'])
        h = np.tanh(h)
        o = np.dot(h, self.brain['hidden_weights'])
        return np.tanh(o)

    def move(self, nearest_food):
        dx = nearest_food.x - self.x
        dy = nearest_food.y - self.y
        
        inputs = [
            dx / self.vision,
            dy / self.vision,
            self.energy / 100,
            self.age / 1000,
            random.random(), # Exploration factor
        ]
        
        output = self.think(inputs)
        self.x += output[0] * self.speed
        self.y += output[1] * self.speed
        self.energy -= 0.2
    
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
    
    def find_nearest_food(self, food_list):
        closest = None
        min_dist = float('inf')
        vision_squared = self.vision ** 2  # avoid using sqrt for performance

        for food in food_list:
            dx = self.x - food.x
            dy = self.y - food.y
            distance_squared = dx * dx + dy * dy

            if distance_squared <= vision_squared and distance_squared < min_dist:
                min_dist = distance_squared
                closest = food

        return closest