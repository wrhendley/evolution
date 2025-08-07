import numpy as np
import random
import pygame
import math
from simulation.utils import clamp, sign
from config import MUTATION_RATE, ENERGY_COST_PER_UNIT

class Creature:
    def __init__(self, x, y, genes = None, brain = None):
        self.x = x
        self.y = y
        self.energy = 100
        self.age = 0
        
        self.speed = genes['speed'] if genes else 2
        self.vision = genes['vision'] if genes else 100
        self.genes = genes if genes is not None else self.generate_random_genes()
        
        self.brain = brain or {
            "input_weights": np.random.randn(5,6),
            "hidden_weights": np.random.randn(6,3)
        }
    
    def update(self, food_list, world_bounds):
        self.age += 1
        direction = self.think(food_list)
        self.move(direction, world_bounds)
    
    def think(self, food_list):
        # Determine movement direction
        nearest = self.find_nearest_food(food_list)
        if nearest is None:
            return random.choice([-1, 0, 1]), random.choice([-1, 0, 1])
        dx = nearest.x - self.x
        dy = nearest.y - self.y
        return (sign(dx), sign(dy))

    def move(self, direction, world_bounds):
        dx, dy = direction
        distance = math.sqrt(dx ** 2 + dy ** 2)
        self.energy -= distance * ENERGY_COST_PER_UNIT
        self.x = clamp(self.x + dx, 0, world_bounds[0])
        self.y = clamp(self.y + dy, 0, world_bounds[1])
    
    def generate_random_genes(self):
        return {
            'vision': random.uniform(3, 10),
            'speed': random.uniform(.5, 1.5)
        }

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