import numpy as np
import random
import pygame
import math
from simulation.utils import clamp, sign
from config import MUTATION_RATE, ENERGY_COST_PER_UNIT, VISION_MIN, VISION_MAX, SPEED_MIN, SPEED_MAX, HUNGER_MAX, HUNGER_THRESHOLD
from config import LAKE_X, LAKE_Y, LAKE_WIDTH, LAKE_HEIGHT, THIRST_MAX, THIRST_THRESHOLD, REST_ENERGY_GAIN

# Load and scale the creature sprite once (as a class variable)
CREATURE_SPRITE = pygame.transform.scale(
    pygame.image.load('assets/creature.png'), (40, 40)
)

class Creature:
    def __init__(self, x, y, genes = None, brain = None, sex=None):
        # Prevent spawning with center in the lake ellipse
        while True:
            cx = x + 20
            cy = y + 20
            lx = LAKE_X + LAKE_WIDTH / 2
            ly = LAKE_Y + LAKE_HEIGHT / 2
            rx = LAKE_WIDTH / 2
            ry = LAKE_HEIGHT / 2
            in_lake = ((cx - lx) / rx) ** 2 + ((cy - ly) / ry) ** 2 <= 1
            if not in_lake:
                break
            x = random.randint(0, 800 - 40)
            y = random.randint(0, 600 - 40)
        self.x = x
        self.y = y
        self.target = None
        self.energy = 150
        self.age = 0
        self.hunger = 0  # Hunger starts at 0 (not hungry)
        self.thirst = 0  # Thirst starts at 0 (not thirsty)

        self.genes = genes if genes is not None else self.generate_random_genes()
        self.genes['color'] = self.genes.get('color', {
            'R': 128,
            'G': 128,
            'B': 128
        })
        self.sex = sex if sex is not None else random.choice(["male", "female"])
        self.wander_direction = (0, 0)
        self.wander_timer = 0
        self.reproduction_cooldown = 0
        self.resting = False

        self.brain = brain or {
            "input_weights": np.random.randn(5,6),
            "hidden_weights": np.random.randn(6,3)
        }

    @staticmethod
    def create_child(mother, father):
        # Average genes
        child_genes = {}
        for key in mother.genes:
            if key == 'color':
                child_genes['color'] = {
                    'R': int((mother.genes['color']['R'] + father.genes['color']['R']) / 2),
                    'G': int((mother.genes['color']['G'] + father.genes['color']['G']) / 2),
                    'B': int((mother.genes['color']['B'] + father.genes['color']['B']) / 2)
                }
            else:
                child_genes[key] = (mother.genes[key] + father.genes[key]) / 2
        # Create child, then mutate its genes
        child = Creature(mother.x, mother.y, genes=child_genes)
        child.genes = child.mutate_genes()
        return child
    
    def update(self, food_list, world_bounds, creatures):
        self.age += 1
        self.hunger += .5  # Increase hunger every update
        self.thirst += .5  # Increase thirst every update
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= 1
        if self.hunger > HUNGER_MAX:
            self.energy = 0
            self.death_cause = 'starvation'
            return
        if self.thirst > THIRST_MAX:
            self.energy = 0
            self.death_cause = 'dehydration'
            return
        direction = self.think(food_list, creatures)
        # If standing still, regain energy (resting)
        if direction == (0, 0):
            self.energy = min(150, self.energy + REST_ENERGY_GAIN)
        self.move(direction, world_bounds)
        self.try_drink()
        # Check for exhaustion (energy depleted)
        if self.energy <= 0 and not hasattr(self, 'death_cause'):
            self.death_cause = 'exhaustion'
    
    def think(self, food_list, creatures):
        # If currently resting, continue to rest unless energy is full or hunger/thirst crosses threshold
        if self.resting:
            # If hunger or thirst crosses threshold, immediately stop resting to address need
            if self.hunger >= HUNGER_THRESHOLD or self.thirst >= THIRST_THRESHOLD:
                self.resting = False
            # If energy is full, stop resting
            elif self.energy >= 100:
                self.resting = False
            else:
                return (0, 0)
        # Only start resting if energy is low and no urgent hunger/thirst
        if not self.resting and self.energy < 30 and self.hunger < HUNGER_THRESHOLD and self.thirst < THIRST_THRESHOLD:
            self.resting = True
            return (0, 0)
        # Prioritize whichever need is closer to max (hunger or thirst)
        hunger_urgency = self.hunger / HUNGER_MAX
        thirst_urgency = self.thirst / THIRST_MAX
        if thirst_urgency > hunger_urgency and self.thirst >= THIRST_THRESHOLD:
            # Only seek lake if it is within vision range (ellipse edge or center)
            cx = self.x + 20
            cy = self.y + 20
            lx = LAKE_X + LAKE_WIDTH / 2
            ly = LAKE_Y + LAKE_HEIGHT / 2
            rx = LAKE_WIDTH / 2
            ry = LAKE_HEIGHT / 2
            # Distance from creature center to lake edge (ellipse)
            # We'll use the closest point: project to ellipse center
            dx_ = (cx - lx) / rx
            dy_ = (cy - ly) / ry
            dist_to_lake = math.sqrt(dx_**2 + dy_**2)
            # If inside lake, just wander (should be drinking)
            if dist_to_lake <= 1:
                return self._wander()
            # If within vision, seek lake
            avg_radius = (rx + ry) / 2
            euclid_dist = math.hypot(cx - lx, cy - ly)
            if euclid_dist - avg_radius <= self.genes['vision']:
                lake_cx = LAKE_X + LAKE_WIDTH // 2
                lake_cy = LAKE_Y + LAKE_HEIGHT // 2
                dx = lake_cx - (self.x + 20)
                dy = lake_cy - (self.y + 20)
                return (sign(dx), sign(dy))
            # Otherwise, wander until lake is seen
            return self._wander()
        elif hunger_urgency >= thirst_urgency and self.hunger >= HUNGER_THRESHOLD:
            # Seek food
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
        # Not hungry or thirsty: wander
        return self._wander()

    def try_drink(self):
        # If any part of the creature is in the lake (ellipse), reset thirst
        if self._in_lake():
            self.thirst = 0

    def _in_lake(self):
        # Check if the center or any corner of the creature is inside the lake ellipse
        points = [
            (self.x + 20, self.y + 20),  # center
            (self.x, self.y),            # top-left
            (self.x + 39, self.y),       # top-right
            (self.x, self.y + 39),       # bottom-left
            (self.x + 39, self.y + 39)   # bottom-right
        ]
        lx = LAKE_X + LAKE_WIDTH / 2
        ly = LAKE_Y + LAKE_HEIGHT / 2
        rx = LAKE_WIDTH / 2
        ry = LAKE_HEIGHT / 2
        for px, py in points:
            if ((px - lx) / rx) ** 2 + ((py - ly) / ry) ** 2 <= 1:
                return True
        return False

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
        # Try to move, but block if would enter the lake (ellipse)
        new_x = clamp(self.x + dx, 0, world_bounds[0] - 40)
        new_y = clamp(self.y + dy, 0, world_bounds[1] - 40)
        # Check if center would be in the lake ellipse
        cx = new_x + 20
        cy = new_y + 20
        lx = LAKE_X + LAKE_WIDTH / 2
        ly = LAKE_Y + LAKE_HEIGHT / 2
        rx = LAKE_WIDTH / 2
        ry = LAKE_HEIGHT / 2
        in_lake = ((cx - lx) / rx) ** 2 + ((cy - ly) / ry) ** 2 <= 1
        if not in_lake:
            self.x = new_x
            self.y = new_y
    
    def distance_to(self, other):
        return math.hypot(other.x - self.x, other.y - self.y)
    
    def generate_random_genes(self):
        return {
            'vision': random.uniform(VISION_MIN, VISION_MAX),
            'speed': random.uniform(SPEED_MIN, SPEED_MAX),
            'metabolism': random.uniform(0.02, 0.2),
        }

    def collides_with(self, food):
        dx = self.x - food.x
        dy = self.y - food.y
        if dx * dx + dy * dy < 100:
            self.hunger = 0  # Reset hunger when eating
            # No longer restore energy here
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
                        new_genes[key] = max(0.001, new_genes[key])
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
        # # Center the vision circle on the center of the sprite
        # center_x = int(self.x + 20 - self.genes['vision'])
        # center_y = int(self.y + 20 - self.genes['vision'])
        # screen.blit(vision_surface, (center_x, center_y))

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