import random
from simulation.creature import Creature
from simulation.food import Food
from config import SCREEN_WIDTH, SCREEN_HEIGHT, CREATURE_COUNT, FOOD_COUNT

class World:
    def __init__(self):
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
        
        #Regenerate food
        while len(self.food) < FOOD_COUNT:
            self.food.append(self.spawn_food())
    
    def draw(self, screen):
        for food in self.food:
            food.draw(screen)
        for creature in self.creatures:
            creature.draw(screen)