import unittest
import config
from unittest.mock import MagicMock, patch
from simulation.world import World
from simulation.creature import Creature
from simulation.food import Food

class TestWorld(unittest.TestCase):
    def setUp(self):
        # Patch Creature and Food to avoid side effects
        self.creature_patch = patch('simulation.world.Creature', autospec=True)
        self.food_patch = patch('simulation.world.Food', autospec=True)
        self.mock_creature = self.creature_patch.start()
        self.mock_food = self.food_patch.start()
        # Patch config constants
        self.config_patch = patch.multiple(
            'simulation.world',
            SCREEN_WIDTH=100,
            SCREEN_HEIGHT=100,
            CREATURE_COUNT=2,
            FOOD_COUNT=2,
            FOOD_SPAWN_INTERVAL=3
        )
        self.config_patch.start()
        self.addCleanup(self.creature_patch.stop)
        self.addCleanup(self.food_patch.stop)
        self.addCleanup(self.config_patch.stop)

    def test_initialization(self):
        world = World()
        self.assertEqual(len(world.creatures), 2)
        self.assertEqual(len(world.food), 2)
        self.assertEqual(world.frame_count, 0)
        self.assertEqual(world.frame, 0)
        self.assertEqual(world.history, [])

    def test_spawn_creature_and_food(self):
        world = World()
        mock_creature = world.spawn_creature()
        mock_food = world.spawn_food()
        self.assertTrue(isinstance(mock_creature, Creature))
        self.assertTrue(isinstance(mock_food, Food))

    def test_update_removes_dead_creatures(self):
        world = World()
        print("World type:", type(world))
        # Set up creatures with one dead
        alive_creature = MagicMock()
        dead_creature = MagicMock()
        alive_creature.energy = 10
        dead_creature.energy = 0
        world.creatures = [alive_creature, dead_creature]
        world.food = []
        world.update()
        self.assertIn(alive_creature, world.creatures)
        self.assertNotIn(dead_creature, world.creatures)

    def test_update_creature_eats_food(self):
        world = World()
        mock_creature = MagicMock()
        mock_food = MagicMock()
        mock_creature.energy = 10
        mock_creature.collides_with.return_value = True
        mock_food.targeted_by = None
        world.creatures = [mock_creature]
        world.food = [mock_food]
        world.update()
        self.assertEqual(mock_creature.energy, 30)
        self.assertNotIn(mock_food, world.food)

    def test_update_creature_reproduces(self):
        world = World()
        mock_creature = MagicMock()
        mock_creature.energy = 200
        mock_creature.genes = {'vision': 1, 'speed': 1}
        mock_creature.reproduce.return_value = MagicMock()
        world.creatures = [mock_creature]
        world.food = []
        world.update()
        self.assertEqual(len(world.creatures), 2)
        mock_creature.reproduce.assert_called_once()

    def test_update_spawns_food(self):
        world = World()
        mock_creature = MagicMock()
        mock_creature.energy = 10
        world.creatures = [mock_creature]
        world.frame_count = 2  # So after update, frame_count % FOOD_SPAWN_INTERVAL == 0
        world.food = []
        world.update()
        self.assertEqual(len(world.food), 1)

    def test_update_history_tracking(self):
        world = World()
        mock_creature = MagicMock()
        mock_creature.energy = 10
        mock_creature.genes = {'vision': 2, 'speed': 3}
        mock_creature.collides_with.return_value = False
        world.creatures = [mock_creature]
        mock_food_1, mock_food_2 = MagicMock(), MagicMock()
        world.food = [mock_food_1, mock_food_2]
        world.update()
        self.assertEqual(len(world.history), 1)
        frame, avg_vision, avg_speed, total_food, total_population = world.history[0]
        self.assertEqual(avg_vision, 2)
        self.assertEqual(avg_speed, 3)
        self.assertEqual(total_food, 2)
        self.assertEqual(total_population, 1)

    def test_draw_calls_draw_on_food_and_creatures(self):
        world = World()
        food = MagicMock()
        creature = MagicMock()
        world.food = [food]
        world.creatures = [creature]
        screen = MagicMock()
        world.draw(screen)
        food.draw.assert_called_with(screen)
        creature.draw.assert_called_with(screen)

if __name__ == '__main__':
    unittest.main()