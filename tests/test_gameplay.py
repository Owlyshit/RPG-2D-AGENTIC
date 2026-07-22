import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.enemy import KingSlime, Slime
from src.game import Game
from src.player import Player
from src.skill import IceBolt


class GameplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((800, 600))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_ice_bolt_uses_mana_and_starts_cooldown(self):
        player = Player(0, 0, 32, 48, 5, -10, 0.5)

        projectile = player.cast_icebolt()

        self.assertIsInstance(projectile, IceBolt)
        self.assertEqual(player.mp, 35)
        self.assertEqual(player.icebolt_current_cooldown, 90)
        self.assertEqual(player.cast_icebolt(), "Ice Bolt is on cooldown!")

    def test_slow_effect_expires_and_restores_speed(self):
        slime = Slime(0, 0, 50, 2, 0.5)

        slime.apply_slow_effect(duration=3, percentage=0.5)
        self.assertEqual(slime.walk_speed, 1)

        for _ in range(3):
            slime.update([])

        self.assertFalse(slime.is_slowed)
        self.assertEqual(slime.walk_speed, 2)

    def test_ice_bolt_event_hits_and_slows_enemy(self):
        game = Game()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_l))

        game.handle_input()

        self.assertEqual(len(game.projectiles), 1)
        projectile = next(iter(game.projectiles))
        slime = next(enemy for enemy in game.enemies if enemy.name == "Slime")
        projectile.rect.center = slime.rect.center

        game.update()

        self.assertEqual(len(game.projectiles), 0)
        self.assertTrue(slime.is_slowed)
        self.assertEqual(slime.walk_speed, slime.original_walk_speed * 0.5)

    def test_game_starts_without_optional_audio_assets(self):
        game = Game()

        game.update()
        game.draw()

        self.assertTrue(game.running)

    def test_potion_cooldown_decrements_once_per_gameplay_frame(self):
        game = Game()
        game.player.potion_cooldown_timer = 60

        game.update()

        self.assertEqual(game.player.potion_cooldown_timer, 59)

    def test_boss_uses_boss_potion_drop_probability(self):
        game = Game()
        boss = KingSlime(0, 0, 50, 1, 0.5)
        initial_potions = sum(game.player.inventory.values())

        # 0.3 misses the regular Slime's 20% drop chance but falls within
        # the boss's 50% chance. The second value selects a health potion.
        with patch("src.game.random.random", side_effect=[0.3, 0.5]):
            game._handle_enemy_drop(0, 0, boss)

        self.assertEqual(sum(game.player.inventory.values()), initial_potions + 1)


if __name__ == "__main__":
    unittest.main()
