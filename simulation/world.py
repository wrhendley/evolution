import random
import matplotlib as plt
from simulation.creature import Creature
from simulation.food import Food
from simulation.bush import Bush
from config import SCREEN_WIDTH, SCREEN_HEIGHT, CREATURE_COUNT, FOOD_COUNT, FOOD_SPAWN_INTERVAL, LOG_INTERVAL

class World:
    def __init__(self):
        self.frame_count = 0
        self.frame = 0
        self.history = []
        self.creatures = [self.spawn_creature() for _ in range(CREATURE_COUNT)]
        self.bushes = [self.spawn_bush() for _ in range(5)]  # Spawn 5 bushes
        self.food = []
        for bush in self.bushes:
            for _ in range(random.randint(1, 3)):
                bush.grow_food(Food)
                self.food.extend(bush.food)

    def spawn_creature(self):
        # Clamp so creature is always fully visible (10x10 rect)
        x = random.randint(0, SCREEN_WIDTH - 10)
        y = random.randint(0, SCREEN_HEIGHT - 10)
        return Creature(x, y)
    
    def spawn_bush(self):
        return Bush()
    
    def update(self):
        self.frame_count += 1
        # Update food list from all bushes
        self.food = []
        for bush in self.bushes:
            self.food.extend(bush.food)

        for creature in self.creatures:
            creature.update(self.food, (SCREEN_WIDTH, SCREEN_HEIGHT), self.creatures)
            for bush in self.bushes:
                for f in list(bush.food):
                    if creature.collides_with(f):
                        creature.energy += 20
                        bush.remove_food(f)
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

        # Grow food on bushes at a fixed interval
        if self.frame_count % FOOD_SPAWN_INTERVAL == 0:
            for bush in self.bushes:
                bush.grow_food(Food)

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
        if self.frame_count % LOG_INTERVAL == 0:
            self.history.append((self.frame_count, avg_vision, avg_speed, avg_metabolism, total_food, total_population))
        self.frame += 1

    def draw(self, screen):
        for bush in self.bushes:
            bush.draw(screen)
        for creature in self.creatures:
            creature.draw(screen)