import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.enemy import KingSlime, Slime
from src.game import Game
from src.item import BronzeSword, LeatherCap, TrainingShirt, TravelerPants
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

    def test_enemies_remain_supported_on_every_map(self):
        game = Game()
        for map_id, definition in game.map_definitions.items():
            spawn_id = next(iter(definition["spawns"]))
            game.load_map(map_id, spawn_id)

            for _ in range(180):
                game.update()

            self.assertTrue(game.enemies, map_id)
            for enemy in game.enemies:
                self.assertLessEqual(enemy.rect.bottom, game.screen_height, map_id)

    def test_first_village_platform_is_reachable_by_jumping(self):
        game = Game()
        platform = sorted(game.platforms, key=lambda item: item.rect.top)[-2]
        game.player.rect.midbottom = (platform.rect.centerx, game.screen_height - 40)
        game.player.on_ground = True
        game.player.jump()

        landed = False
        for _ in range(60):
            game.player.update(game.platforms.sprites())
            if game.player.on_ground and game.player.rect.bottom == platform.rect.top:
                landed = True
                break

        self.assertTrue(landed)

    def test_boss_cannot_be_knocked_outside_arena(self):
        game = Game()
        game.load_map("slime_hollow", "west_entry")
        boss = game.boss_instance

        boss.rect.right = game.screen_width - 1
        boss.apply_knockback(1, 100)
        for _ in range(30):
            game.update()

        self.assertGreaterEqual(boss.rect.left, 0)
        self.assertLessEqual(boss.rect.right, game.screen_width)
        self.assertLessEqual(boss.rect.bottom, game.screen_height)

    def test_bronze_sword_increases_melee_damage_and_range(self):
        player = Player(100, 100, 32, 64, 5, -10, 0.5)
        base_damage = player.melee_damage
        player.facing_right = True

        message = player.equip_bronze_sword()
        player.start_attack()

        self.assertIn("Equipped Bronze Sword", message)
        self.assertEqual(player.melee_damage, base_damage + BronzeSword().attack_bonus)
        self.assertEqual(player.attack_hitbox.width, BronzeSword().attack_range)

    def test_inventory_hotkeys_open_and_equip_sword(self):
        game = Game()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_i))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q))

        game.handle_input()

        self.assertTrue(game.inventory_open)
        self.assertEqual(game.player.equipped_weapon.item_id, "bronze_sword")

    def test_level_up_awards_five_allocatable_stat_points(self):
        player = Player(0, 0, 32, 64, 5, -10, 0.5)

        player.gain_exp(player.exp_to_next_level)

        self.assertEqual(player.level, 2)
        self.assertEqual(player.stat_points, 5)
        self.assertEqual(player.allocate_stat("strength"), "Strength increased to 5.")
        self.assertEqual(player.stat_points, 4)
        self.assertEqual(player.total_stat("strength"), 5)

    def test_armor_slots_add_stats_and_reduce_damage(self):
        player = Player(0, 0, 32, 64, 5, -10, 0.5)
        player.equip_armor(LeatherCap())
        player.equip_armor(TrainingShirt())
        player.equip_armor(TravelerPants())

        self.assertEqual(player.defense, 7)
        self.assertEqual(player.total_stat("strength"), 5)
        self.assertEqual(player.total_stat("dexterity"), 5)
        self.assertEqual(player.total_stat("luck"), 5)

        player.take_damage(20)
        self.assertEqual(player.hp, 87)

    def test_inventory_equipment_and_stat_hotkeys(self):
        game = Game()
        game.player.stat_points = 1
        for key in (pygame.K_i, pygame.K_w, pygame.K_e, pygame.K_r, pygame.K_1):
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))

        game.handle_input()
        game.draw()

        self.assertEqual(game.player.equipment["helmet"].item_id, "leather_cap")
        self.assertEqual(game.player.equipment["shirt"].item_id, "training_shirt")
        self.assertEqual(game.player.equipment["pants"].item_id, "traveler_pants")
        self.assertEqual(game.player.stats["strength"], 5)
        self.assertEqual(game.player.stat_points, 0)

    def test_dragging_sword_to_weapon_slot_equips_it(self):
        game = Game()
        game.inventory_open = True
        game.draw()
        item_pos = game.inventory_item_rects["bronze_sword"].center
        slot_pos = game.equipment_slot_rects["weapon"].center
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=item_pos, button=1))
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=slot_pos, button=1))

        game.handle_input()

        self.assertEqual(game.player.equipped_weapon.item_id, "bronze_sword")
        self.assertIsNone(game.dragged_item_id)

    def test_inventory_tabs_change_with_mouse_click(self):
        game = Game()
        game.inventory_open = True
        game.draw()
        use_tab_pos = game.inventory_tab_rects["use"].center
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=use_tab_pos, button=1))

        game.handle_input()
        game.draw()

        self.assertEqual(game.inventory_tab, "use")
        self.assertIn("health_potion", game.inventory_item_rects)

    def test_s_opens_stats_and_plus_button_allocates_point(self):
        game = Game()
        game.player.stat_points = 1
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s))
        game.handle_input()
        game.draw()
        strength_button = game.stat_button_rects["strength"].center
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=strength_button, button=1))

        game.handle_input()

        self.assertTrue(game.stats_open)
        self.assertEqual(game.player.stats["strength"], 5)
        self.assertEqual(game.player.stat_points, 0)


if __name__ == "__main__":
    unittest.main()
