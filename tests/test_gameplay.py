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

    def test_melee_hitbox_damages_enemy_without_crashing(self):
        game = Game()
        slime = next(enemy for enemy in game.enemies if enemy.name == "Slime")
        game.player.rect.topleft = (100, 500)
        slime.rect.topleft = (game.player.rect.right + 5, game.player.rect.top)
        starting_hp = slime.hp

        game.player.facing_right = True
        game.player.start_attack()
        game.update()

        self.assertEqual(slime.hp, starting_hp - game.player.attack_damage)

    def test_idle_boss_does_not_deal_stomp_damage(self):
        game = Game()
        game.load_map("slime_hollow", "west_entry")
        boss = game.boss_instance
        game.player.rect.bottom = boss.rect.bottom
        game.player.rect.right = boss.rect.left - 10
        self.assertLessEqual(
            abs(game.player.rect.centerx - boss.rect.centerx),
            boss.stomp_land_damage_range,
        )
        starting_hp = game.player.hp

        game.update()

        self.assertEqual(game.player.hp, starting_hp)

    def test_world_contains_three_distinct_maps(self):
        game = Game()

        self.assertEqual(
            set(game.map_definitions),
            {"meadow_village", "whispering_forest", "slime_hollow"},
        )
        self.assertEqual(game.current_map_id, "meadow_village")
        self.assertGreaterEqual(len(game.npcs), 2)

    def test_portal_transition_loads_destination_map(self):
        game = Game()
        game.portal_transition_cooldown = 0
        portal = next(iter(game.portals))
        game.player.rect.center = portal.rect.center

        game.update()

        self.assertEqual(game.current_map_id, "whispering_forest")
        self.assertEqual(game.current_map_name, "Whispering Forest")
        self.assertGreaterEqual(len(game.npcs), 2)
        self.assertGreater(game.portal_transition_cooldown, 0)

    def test_player_progress_persists_between_maps(self):
        game = Game()
        game.player.exp = 42
        game.player.inventory["health_potion"] = 9

        game.load_map("whispering_forest", "west_entry")

        self.assertEqual(game.player.exp, 42)
        self.assertEqual(game.player.inventory["health_potion"], 9)


if __name__ == "__main__":
    unittest.main()
