import numpy as np
import random
import pygame
import math
from simulation.utils import clamp, sign
from config import MUTATION_RATE, ENERGY_COST_PER_UNIT, VISION_MIN, VISION_MAX, SPEED_MIN, SPEED_MAX, HUNGER_MAX, HUNGER_THRESHOLD

# Load and scale the creature sprite once (as a class variable)
CREATURE_SPRITE = pygame.transform.scale(
    pygame.image.load('assets/creature.png'), (40, 40)
)

class Creature:
    def __init__(self, x, y, genes = None, brain = None):
        self.x = x
        self.y = y
        self.target = None
        self.energy = 100
        self.age = 0
        self.hunger = 0  # Hunger starts at 0 (not hungry)

        self.genes = genes if genes is not None else self.generate_random_genes()
        self.genes['color'] = self.genes.get('color', {
            'R': 128,
            'G': 128,
            'B': 128
        })
        self.wander_direction = (0, 0)
        self.wander_timer = 0

        self.brain = brain or {
            "input_weights": np.random.randn(5,6),
            "hidden_weights": np.random.randn(6,3)
        }
    
    def update(self, food_list, world_bounds, creatures):
        self.age += 1
        self.hunger += 1  # Increase hunger every update
        if self.hunger > HUNGER_MAX:
            self.energy = 0  # Creature dies from starvation
            return
        direction = self.think(food_list, creatures)
        self.move(direction, world_bounds)
    
    def think(self, food_list, creatures):
        # If hungry, seek food
        if self.hunger >= HUNGER_THRESHOLD:
            if self.target in food_list and self.target.targeted_by is self:
                target = self.target
            else:
                target = self.find_nearest_food(food_list, creatures)
                if target:
                    target.targeted_by = self
                    self.target = target
                else:
                    self.target = None
                    # If hungry but no food, fallback to wandering
                    return self._wander()
            dx = target.x - self.x
            dy = target.y - self.y
            return (sign(dx), sign(dy))

        # Not hungry: wander
        return self._wander()

    def _wander(self):
        # If timer expired, pick a new direction and duration
        if self.wander_timer <= 0:
            # 20% chance to stand still, 80% to move in a direction
            directions = [(0, 0)] * 1 + [(1, 0), (0, 1), (-1, 0), (0, -1)] * 2
            self.wander_direction = random.choice(directions)
            self.wander_timer = random.randint(30, 60)
        self.wander_timer -= 1
        return self.wander_direction

    def move(self, direction, world_bounds):
        dx, dy = direction
        distance = math.sqrt(dx ** 2 + dy ** 2)
        self.energy -= distance * self.genes.get('metabolism', 0.2)  # Use metabolism gene for energy cost
        # Ensure the creature stays fully on screen (10x10 rect)
        self.x = clamp(self.x + dx, 0, world_bounds[0] - 10)
        self.y = clamp(self.y + dy, 0, world_bounds[1] - 10)
    
    def distance_to(self, other):
        return math.hypot(other.x - self.x, other.y - self.y)
    
    def generate_random_genes(self):
        return {
            'vision': random.uniform(VISION_MIN, VISION_MAX),
            'speed': random.uniform(SPEED_MIN, SPEED_MAX),
            'metabolism': random.uniform(0.05, 0.5),
        }

    def collides_with(self, food):
        dx = self.x - food.x
        dy = self.y - food.y
        if dx * dx + dy * dy < 100:
            self.hunger = 0  # Reset hunger when eating
            return True
        return False
    
    def mutate_genes(self):
        new_genes = self.genes.copy()
        for key in list(new_genes.keys()):
            if key == 'color':
                # Mutate each color channel independently
                new_color = new_genes['color'].copy()
                for channel in ['R', 'G', 'B']:
                    if random.random() < MUTATION_RATE * 2:
                        # Mutate by up to +/- 20, clamp to 0-255
                        delta = random.randint(-20, 20)
                        new_color[channel] = max(0, min(255, new_color[channel] + delta))
                new_genes['color'] = new_color
            else:
                if random.random() < MUTATION_RATE:
                    # Multiplicative mutation: scale by 0.9 to 1.1
                    new_genes[key] *= random.uniform(0.9, 1.1)
                    # Prevent negative or zero values
                    if key == 'metabolism':
                        new_genes[key] = max(0.01, new_genes[key])
                    else:
                        new_genes[key] = max(0.1, new_genes[key])
        return new_genes
    
    def reproduce(self):
        return Creature(self.x, self.y, genes=self.mutate_genes())
    
    def draw(self, screen):
        # Optionally tint the sprite to the creature's color gene
        color = self.genes.get('color', {'R':128, 'G':128, 'B':128})
        sprite = CREATURE_SPRITE.copy()
        # Tinting: fill with color, using BLEND_RGBA_MULT for simple tint
        tint = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
        tint.fill((color['R'], color['G'], color['B'], 255))
        sprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(sprite, (self.x, self.y))
        # Draw filled transparent gray vision circle (optional, can uncomment)
        # vision_surface = pygame.Surface((self.genes['vision']*2, self.genes['vision']*2), pygame.SRCALPHA)
        # pygame.draw.circle(
        #     vision_surface,
        #     (128, 128, 128, 90),  # RGBA: gray with alpha
        #     (int(self.genes['vision']), int(self.genes['vision'])),
        #     int(self.genes['vision'])
        # )
        # screen.blit(vision_surface, (int(self.x - self.genes['vision']), int(self.y - self.genes['vision'])))

    def find_nearest_food(self, food_list, other_creatures):
        visible_food = [f for f in food_list if self.distance_to(f) <= self.genes['vision']]
        
        # Get positions of food being targeted by other creatures
        targeted_food = {
            (c.target.x, c.target.y) for c in other_creatures
            if c.target is not self and c.target is not None
        }
        
        # Filter out food that's already assigned
        untargeted_food = [
            f for f in visible_food
            if (f.x, f.y) not in targeted_food
        ]
        
        # Use untargeted food if available, otherwise fall back to any visible food
        candidate_food = untargeted_food if untargeted_food else visible_food
        
        if not candidate_food:
            return None

        return min(candidate_food, key=lambda f: self.distance_to(f))