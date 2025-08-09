import random
import matplotlib as plt
from simulation.creature import Creature
from simulation.food import Food
from config import SCREEN_WIDTH, SCREEN_HEIGHT, CREATURE_COUNT, FOOD_COUNT, FOOD_SPAWN_INTERVAL

class World:
    def __init__(self):
        self.frame_count = 0
        self.frame = 0
        self.history = []
        self.creatures = [self.spawn_creature() for _ in range(CREATURE_COUNT)]
        self.food = [self.spawn_food() for _ in range(FOOD_COUNT)]

    def spawn_creature(self):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        return Creature(x, y)
    
    def spawn_food(self):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        return Food(x, y)
    
    def update(self):
        self.frame_count += 1
        for creature in self.creatures:
            creature.update(self.food, (SCREEN_WIDTH, SCREEN_HEIGHT), self.creatures)
            for f in self.food:
                if creature.collides_with(f):
                    creature.energy += 20
                    self.food.remove(f)
                    if f.targeted_by:
                        f.targeted_by.target = None
                    break

        # Remove dead creatures
        self.creatures = [c for c in self.creatures if c.energy > 0]

        # Reproduce if energy is sufficient
        new_creatures = []
        for c in self.creatures:
            if c.energy > 150:
                c.energy /= 2
                child = c.reproduce()
                new_creatures.append(child)
        self.creatures.extend(new_creatures)

        # Spawn one new food at a fixed interval
        if self.frame_count % FOOD_SPAWN_INTERVAL == 0 and len(self.food) < FOOD_COUNT:
            self.food.append(self.spawn_food())

        # Track average vision, speed, and metabolism every frame
        if self.creatures:
            avg_vision = sum(c.genes['vision'] for c in self.creatures) / len(self.creatures)
            avg_speed = sum(c.genes['speed'] for c in self.creatures) / len(self.creatures)
            avg_metabolism = sum(c.genes.get('metabolism', 0.2) for c in self.creatures) / len(self.creatures)
        else:
            avg_vision = 0
            avg_speed = 0
            avg_metabolism = 0
        # Track total food and total population
        total_food = len(self.food)
        total_population = len(self.creatures)
        self.history.append((self.frame_count, avg_vision, avg_speed, avg_metabolism, total_food, total_population))
        self.frame += 1

    def draw(self, screen):
        for food in self.food:
            food.draw(screen)
        for creature in self.creatures:
            creature.draw(screen)