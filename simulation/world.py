import random
import pygame
import matplotlib as plt
from simulation.creature import Creature
from simulation.food import Food
from simulation.bush import Bush
from config import SCREEN_WIDTH, SCREEN_HEIGHT, CREATURE_COUNT, FOOD_COUNT, FOOD_SPAWN_INTERVAL, LOG_INTERVAL
from config import LAKE_X, LAKE_Y, LAKE_WIDTH, LAKE_HEIGHT

class World:
    def __init__(self):
        self.frame_count = 0
        self.frame = 0
        self.history = []
        self.death_causes = {'starvation': 0, 'dehydration': 0, 'exhaustion': 0}
        self.creatures = [self.spawn_creature() for _ in range(CREATURE_COUNT)]
        self.bushes = []
        bush_count = 5
        attempts = 0
        max_attempts = 1000
        while len(self.bushes) < bush_count and attempts < max_attempts:
            new_bush = self.spawn_bush()
            new_rect = pygame.Rect(new_bush.x, new_bush.y, 64, 64)
            if all(not new_rect.colliderect(pygame.Rect(b.x, b.y, 64, 64)) for b in self.bushes):
                self.bushes.append(new_bush)
            attempts += 1
        self.food = []
        for bush in self.bushes:
            for _ in range(random.randint(1, 3)):
                bush.grow_food(Food)
                self.food.extend(bush.food)

    def spawn_creature(self):
        # Clamp so creature is always fully visible (40x40 sprite)
        while True:
            x = random.randint(0, SCREEN_WIDTH - 40)
            y = random.randint(0, SCREEN_HEIGHT - 40)
            # Check if center would be in the lake ellipse
            cx = x + 20
            cy = y + 20
            lx = LAKE_X + LAKE_WIDTH / 2
            ly = LAKE_Y + LAKE_HEIGHT / 2
            rx = LAKE_WIDTH / 2
            ry = LAKE_HEIGHT / 2
            in_lake = ((cx - lx) / rx) ** 2 + ((cy - ly) / ry) ** 2 <= 1
            if not in_lake:
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
                        # Eating only resets hunger; no energy gain
                        bush.remove_food(f)
                        if f.targeted_by:
                            f.targeted_by.target = None
                        break

        # Remove dead creatures and count causes
        survivors = []
        for c in self.creatures:
            if c.energy > 0:
                survivors.append(c)
            else:
                cause = getattr(c, 'death_cause', None)
                if cause in self.death_causes:
                    self.death_causes[cause] += 1
        self.creatures = survivors

        # Reproduce if energy is sufficient and a male and female intersect
        from config import HUNGER_THRESHOLD, THIRST_THRESHOLD, REPRODUCTION_COOLDOWN
        eligible_males = [c for c in self.creatures if getattr(c, 'sex', None) == "male" and c.energy > 80 and c.hunger < HUNGER_THRESHOLD and c.thirst < THIRST_THRESHOLD and c.age > 600 and c.reproduction_cooldown == 0]
        eligible_females = [c for c in self.creatures if getattr(c, 'sex', None) == "female" and c.energy > 80 and c.hunger < HUNGER_THRESHOLD and c.thirst < THIRST_THRESHOLD and c.age > 600 and c.reproduction_cooldown == 0]
        used_males = set()
        used_females = set()
        new_creatures = []
        for female in eligible_females:
            female_rect = pygame.Rect(female.x, female.y, 40, 40)
            for male in eligible_males:
                if male in used_males:
                    continue
                male_rect = pygame.Rect(male.x, male.y, 40, 40)
                if female_rect.colliderect(male_rect):
                    # Both parents pay energy cost and get cooldown
                    female.energy /= 2
                    male.energy /= 2
                    female.reproduction_cooldown = REPRODUCTION_COOLDOWN
                    male.reproduction_cooldown = REPRODUCTION_COOLDOWN
                    child = Creature.create_child(female, male)
                    new_creatures.append(child)
                    used_males.add(male)
                    used_females.add(female)
                    break
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
        # Draw lake first (blue ellipse)
        pygame.draw.ellipse(screen, (0, 100, 200), (LAKE_X, LAKE_Y, LAKE_WIDTH, LAKE_HEIGHT))
        for bush in self.bushes:
            bush.draw(screen)
        for creature in self.creatures:
            creature.draw(screen)