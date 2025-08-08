import random
import csv
from simulation.creature import Creature
from simulation.food import Food
from config import SCREEN_WIDTH, SCREEN_HEIGHT, CREATURE_COUNT, FOOD_COUNT, FOOD_SPAWN_INTERVAL

class World:
    def __init__(self):
        self.frame_count = 0
        self.creatures = [self.spawn_creature() for _ in range(CREATURE_COUNT)]
        self.food = [self.spawn_food() for _ in range(FOOD_COUNT)]
        self.log_file = open("gene_log.csv", "w", newline="")
        self.log_writer = csv.writer(self.log_file)
        self.log_writer.writerow(["Frame", "Creature_ID", "Vision", "Speed"])

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

        if self.frame_count % 100 == 0:
            for i, c in enumerate(self.creatures):
                self.log_writer.writerow([self.frame_count, i, c.genes['vision'], c.genes['speed']])
    
    def draw(self, screen):
        for food in self.food:
            food.draw(screen)
        for creature in self.creatures:
            creature.draw(screen)