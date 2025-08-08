import unittest
import numpy as np
import simulation.utils
import sys
from unittest.mock import Mock, patch
from simulation.creature import Creature
from config import MUTATION_RATE, ENERGY_COST_PER_UNIT, VISION_MIN, VISION_MAX, SPEED_MIN, SPEED_MAX

# Mock config values
sys.modules['config'] = Mock(
    MUTATION_RATE=1.0,  # Always mutate for test
    ENERGY_COST_PER_UNIT=1.0,
    VISION_MIN=10,
    VISION_MAX=100,
    SPEED_MIN=1,
    SPEED_MAX=10
)

# Mock clamp and sign
simulation.utils.clamp = lambda v, mn, mx: max(mn, min(mx, v))
simulation.utils.sign = lambda x: (x > 0) - (x < 0)

class DummyFood:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.targeted_by = None

class TestCreature(unittest.TestCase):
    def setUp(self):
        self.creature = Creature(50, 50)
        self.world_bounds = (100, 100)

    def test_initialization(self):
        c = Creature(10, 20)
        self.assertEqual(c.x, 10)
        self.assertEqual(c.y, 20)
        self.assertEqual(c.energy, 100)
        self.assertIn('vision', c.genes)
        self.assertIn('speed', c.genes)
        self.assertIsInstance(c.brain, dict)

    def test_move_and_energy(self):
        initial_energy = self.creature.energy
        self.creature.move((3, 4), self.world_bounds)  # distance = 5
        self.assertEqual(self.creature.x, 53)
        self.assertEqual(self.creature.y, 54)
        self.assertEqual(self.creature.energy, initial_energy - 5 * ENERGY_COST_PER_UNIT)

    def test_move_clamping(self):
        self.creature.move((100, 100), (60, 60))
        self.assertEqual(self.creature.x, 60)
        self.assertEqual(self.creature.y, 60)

    def test_distance_to(self):
        other = DummyFood(53, 54)
        dist = self.creature.distance_to(other)
        self.assertAlmostEqual(dist, 5)

    def test_generate_random_genes(self):
        genes = self.creature.generate_random_genes()
        self.assertTrue(VISION_MIN <= genes['vision'] <= VISION_MAX)
        self.assertTrue(SPEED_MIN <= genes['speed'] <= SPEED_MAX)

    def test_collides_with(self):
        food = DummyFood(self.creature.x + 5, self.creature.y)
        self.assertTrue(self.creature.collides_with(food))
        far_food = DummyFood(self.creature.x + 20, self.creature.y)
        self.assertFalse(self.creature.collides_with(far_food))

    @patch('simulation.creature.MUTATION_RATE', 1)
    def test_mutate_genes(self):
        self.creature.genes = {'vision': 5.0, 'speed': 2.0}
        mutated = self.creature.mutate_genes()
        self.assertNotEqual(mutated, self.creature.genes)
        self.assertTrue(mutated['vision'] >= 0.1)
        self.assertTrue(mutated['speed'] >= 0.1)

    @patch('simulation.creature.MUTATION_RATE', 1)
    def test_reproduce(self):
        child = self.creature.reproduce()
        self.assertIsInstance(child, Creature)
        self.assertNotEqual(child.genes, self.creature.genes)
        self.assertEqual(child.x, self.creature.x)
        self.assertEqual(child.y, self.creature.y)

    def test_find_nearest_food(self):
        food1 = DummyFood(60, 50)
        food2 = DummyFood(80, 50)
        self.creature.genes['vision'] = 20
        nearest = self.creature.find_nearest_food([food1, food2], [])
        self.assertEqual(nearest, food1)

    def test_find_nearest_food_none_visible(self):
        food1 = DummyFood(100, 100)
        self.creature.genes['vision'] = 10
        nearest = self.creature.find_nearest_food([food1], [])
        self.assertIsNone(nearest)

    def test_find_nearest_food_untargeted(self):
        food1 = DummyFood(60, 50)
        food2 = DummyFood(55, 50)
        other_creature = Creature(0, 0)
        other_creature.target = food1
        self.creature.genes['vision'] = 20
        nearest = self.creature.find_nearest_food([food1, food2], [other_creature])
        self.assertEqual(nearest, food2)

    def test_think_random_when_no_food(self):
        with patch('random.choice', return_value=(1, 0)):
            direction = self.creature.think([], [])
            self.assertEqual(direction, (1, 0))

    def test_update_increments_age(self):
        self.creature.think = Mock(return_value=(1, 0))
        self.creature.move = Mock()
        self.creature.update([], self.world_bounds, [])
        self.assertEqual(self.creature.age, 1)
        self.creature.move.assert_called_once()

if __name__ == '__main__':
    unittest.main()