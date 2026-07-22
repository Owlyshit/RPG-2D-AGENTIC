import pygame
import sys
import random # Added for potion drops
from src.player import Player
from src.enemy import Slime, KingSlime, MiniSlime # Import MiniSlime
from src.map import Platform, Portal, GameMap
from src.npc import NPC, Quest
from src.skill import IceBolt
from src.save_manager import DEFAULT_SAVE_FILE, load_game, save_game
from src.item import (
    BronzeSword, HealthPotion, LeatherCap, ManaPotion,
    TrainingShirt, TravelerPants,
)

# Simple data class for spawn points
class SpawnPoint:
    def __init__(self, x, y, enemy_type, respawn_delay, initial_patrol_range=None, initial_walk_speed=None):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type # String, e.g., 'Slime', 'KingSlime', 'MiniSlime'
        self.respawn_delay = respawn_delay # in frames
        self.current_respawn_timer = 0
        self.is_active = False # True if an enemy is currently spawned at this point
        self.spawned_enemy_ref = None # Reference to the actual enemy sprite
        self.initial_patrol_range = initial_patrol_range
        self.initial_walk_speed = initial_walk_speed

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init() # Initialize mixer for sounds

        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("MapleStory-inspired RPG")

        self.clock = pygame.time.Clock()
        self.running = True

        self.gravity = 0.5
        self.player_jump_strength = -10
        self.player_walk_speed = 5
        self.enemy_walk_speed = 1

        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.portals = pygame.sprite.Group()
        self.npcs = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group() # New group for projectiles

        self.enemy_spawn_points = [] # List to manage enemy respawns
        self.boss_instance = None # To hold a reference to the KingSlime boss
        self.current_map_id = None
        self.current_map_name = ""
        self.map_background_color = (135, 206, 235)
        self.portal_transition_cooldown = 0

        # Game state for notifications
        self.notification_message = ""
        self.notification_timer = 0 # frames
        self.NOTIFICATION_DURATION = 120 # frames (2 seconds)

        # Load Sounds (Placeholder - replace with actual paths)
        try:
            self.jump_sound = pygame.mixer.Sound('assets/sounds/jump.wav')
        except (pygame.error, FileNotFoundError):
            print("Warning: jump.wav not found. Playing dummy sound.")
            self.jump_sound = DummySound()
        try:
            self.melee_sound = pygame.mixer.Sound('assets/sounds/melee.wav')
        except (pygame.error, FileNotFoundError):
            print("Warning: melee.wav not found. Playing dummy sound.")
            self.melee_sound = DummySound()
        try:
            self.magic_sound = pygame.mixer.Sound('assets/sounds/magic.wav')
        except (pygame.error, FileNotFoundError):
            print("Warning: magic.wav not found. Playing dummy sound.")
            self.magic_sound = DummySound()
        try:
            self.player_hit_sound = pygame.mixer.Sound('assets/sounds/player_hit.wav')
        except (pygame.error, FileNotFoundError):
            print("Warning: player_hit.wav not found. Playing dummy sound.")
            self.player_hit_sound = DummySound()
        try:
            self.enemy_hit_sound = pygame.mixer.Sound('assets/sounds/enemy_hit.wav')
        except (pygame.error, FileNotFoundError):
            print("Warning: enemy_hit.wav not found. Playing dummy sound.")
            self.enemy_hit_sound = DummySound()
        try:
            self.enemy_death_sound = pygame.mixer.Sound('assets/sounds/enemy_death.wav')
        except (pygame.error, FileNotFoundError):
            print("Warning: enemy_death.wav not found. Playing dummy sound.")
            self.enemy_death_sound = DummySound()
        try:
            self.potion_sound = pygame.mixer.Sound('assets/sounds/potion.wav') # New potion sound
        except (pygame.error, FileNotFoundError):
            print("Warning: potion.wav not found. Playing dummy sound.")
            self.potion_sound = DummySound()
        
        # Set sound volumes (optional, default is 1.0)
        # self.jump_sound.set_volume(0.5)

        self.player = Player(
            x=100, y=self.screen_height - 100,
            width=32, height=64,
            walk_speed=self.player_walk_speed,
            jump_strength=self.player_jump_strength,
            gravity=self.gravity
        )
        self.all_sprites.add(self.player)
        self.map_definitions = self._build_map_definitions()
        self.load_map("meadow_village", "start")

        # HUD setup
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.dialogue_font = pygame.font.Font(None, 28)

        self.HP_COLOR = (255, 0, 0)
        self.MP_COLOR = (0, 0, 255)
        self.EXP_COLOR = (255, 255, 0)
        self.TEXT_COLOR = (255, 255, 255)
        self.BAR_BACKGROUND_COLOR = (50, 50, 50)
        self.DIALOGUE_BG_COLOR = (0, 0, 0, 180)
        self.NOTIFICATION_COLOR = (255, 255, 255)

        self.HUD_X = 10
        self.HUD_Y = 10
        self.BAR_WIDTH = 150
        self.BAR_HEIGHT = 15
        self.BAR_SPACING = 5
        self.LEVEL_OFFSET_X = self.BAR_WIDTH + 20

        self.dialogue_active = False
        self.current_npc = None
        self.inventory_open = False
        self.stats_open = False
        self.inventory_tab = "equip"
        self.dragged_item_id = None
        self.inventory_tab_rects = {}
        self.inventory_item_rects = {}
        self.equipment_slot_rects = {}
        self.stat_button_rects = {}
        self.save_file = DEFAULT_SAVE_FILE


    def spawn_enemy(self, spawn_point):
        new_enemy = None
        if spawn_point.enemy_type == 'Slime':
            new_enemy = Slime(
                x=spawn_point.x,
                y=spawn_point.y,
                patrol_range=spawn_point.initial_patrol_range if spawn_point.initial_patrol_range else 100,
                walk_speed=spawn_point.initial_walk_speed if spawn_point.initial_walk_speed else self.enemy_walk_speed,
                gravity=self.gravity
            )
        elif spawn_point.enemy_type == 'MiniSlime': # Handle MiniSlime spawning
            new_enemy = MiniSlime(
                x=spawn_point.x,
                y=spawn_point.y,
                patrol_range=spawn_point.initial_patrol_range if spawn_point.initial_patrol_range else 50,
                walk_speed=spawn_point.initial_walk_speed if spawn_point.initial_walk_speed else self.enemy_walk_speed * 1.2,
                gravity=self.gravity
            )
        elif spawn_point.enemy_type == 'KingSlime': # Handle KingSlime (Boss) spawning
            new_enemy = KingSlime(
                x=spawn_point.x,
                y=spawn_point.y,
                patrol_range=spawn_point.initial_patrol_range if spawn_point.initial_patrol_range else 70,
                walk_speed=spawn_point.initial_walk_speed if spawn_point.initial_walk_speed else self.enemy_walk_speed * 0.7,
                gravity=self.gravity
            )
            new_enemy.set_minion_spawn_callback(self.spawn_minions) # Set the callback for minion spawning
            self.boss_instance = new_enemy # Keep a direct reference to the boss
        
        if new_enemy:
            self.enemies.add(new_enemy)
            self.all_sprites.add(new_enemy)
            spawn_point.spawned_enemy_ref = new_enemy
            spawn_point.is_active = True
            print(f"Respawned {spawn_point.enemy_type} at ({spawn_point.x}, {spawn_point.y})")

    def spawn_minions(self, boss_x, boss_y, count):
        for _ in range(count):
            # Spawn minions near the boss, slightly offset
            offset_x = random.randint(-50, 50)
            # Ensure minion doesn't spawn exactly on the boss, and is on the ground
            spawn_x = boss_x + offset_x
            # Y position will be adjusted by gravity, so just below boss is fine
            spawn_y = boss_y - 20 
            # Create a dummy spawn point for the minion, as they don't respawn independently
            minion_sp = SpawnPoint(spawn_x, spawn_y, 'MiniSlime', 0, initial_patrol_range=30, initial_walk_speed=self.enemy_walk_speed * 1.5)
            new_minion = MiniSlime(
                x=minion_sp.x,
                y=minion_sp.y,
                patrol_range=minion_sp.initial_patrol_range,
                walk_speed=minion_sp.initial_walk_speed,
                gravity=self.gravity
            )
            self.enemies.add(new_minion)
            self.all_sprites.add(new_minion)
            print(f"Spawned a MiniSlime at ({spawn_x}, {spawn_y})")


    def _build_map_definitions(self):
        ground_y = self.screen_height - 40
        return {
            "meadow_village": {
                "name": "Greenleaf Village",
                "background": (135, 206, 235),
                "spawns": {"start": (100, ground_y - 64), "east_entry": (650, ground_y - 64)},
                "platforms": [
                    (0, ground_y, 800, 40, False),
                    (130, 480, 180, 20, True),
                    (410, 400, 170, 20, True),
                ],
                "enemies": [
                    (330, 520, "Slime", 300, 80, 1),
                    (610, 520, "Slime", 300, 70, 1),
                    (200, 400, "Slime", 300, 45, 1),
                ],
                "portals": [(740, 500, 50, 60, "whispering_forest", "west_entry")],
                "npcs": [
                    (360, 496, "Farmer John", "The slimes are multiplying! Defeat five and I'll reward you.", "Keep thinning their numbers!", "The fields are safe again. Thank you!", "slime_quest"),
                    (70, 496, "Mira the Healer", "Rest by the village fountain whenever your journey grows difficult.", "", "", None),
                ],
            },
            "whispering_forest": {
                "name": "Whispering Forest",
                "background": (72, 132, 108),
                "spawns": {"west_entry": (85, ground_y - 64), "east_entry": (660, ground_y - 64)},
                "platforms": [
                    (0, ground_y, 800, 40, False),
                    (100, 480, 150, 20, True),
                    (320, 400, 170, 20, True),
                    (570, 480, 140, 20, True),
                ],
                "enemies": [
                    (220, 520, "Slime", 240, 100, 1.2),
                    (390, 290, "Slime", 240, 60, 1.2),
                    (590, 390, "MiniSlime", 240, 55, 1.5),
                    (680, 520, "Slime", 240, 70, 1.2),
                ],
                "portals": [
                    (10, 500, 50, 60, "meadow_village", "east_entry"),
                    (740, 500, 50, 60, "slime_hollow", "west_entry"),
                ],
                "npcs": [
                    (370, 496, "Ranger Rowan", "The eastern hollow belongs to King Slime. Prepare before entering.", "", "", None),
                    (135, 416, "Lost Explorer", "These old platforms lead through the canopy. I nearly missed the path home.", "", "", None),
                ],
            },
            "slime_hollow": {
                "name": "Slime King's Hollow",
                "background": (72, 61, 109),
                "spawns": {"west_entry": (85, ground_y - 64)},
                "platforms": [
                    (0, ground_y, 800, 40, False),
                    (180, 480, 140, 20, True),
                    (480, 480, 140, 20, True),
                ],
                "enemies": [
                    (510, 456, "KingSlime", 36000, 70, 0.7),
                    (260, 520, "MiniSlime", 360, 60, 1.4),
                ],
                "portals": [(10, 500, 50, 60, "whispering_forest", "east_entry")],
                "npcs": [
                    (100, 496, "Scholar Pip", "King Slime alternates between crushing leaps and summoning minions.", "", "", None),
                ],
            },
        }

    def _make_slime_quest(self):
        return Quest(
            q_id='slime_trouble', name='Slime Trouble', objective_type='kill',
            objective_target='Slime', objective_count=5, reward_exp=50,
            is_repeatable=True,
        )

    def load_map(self, map_id, spawn_point_id):
        definition = self.map_definitions[map_id]
        self.all_sprites.empty()
        self.platforms.empty()
        self.enemies.empty()
        self.portals.empty()
        self.npcs.empty()
        self.projectiles.empty()
        self.enemy_spawn_points = []
        self.boss_instance = None

        self.current_map_id = map_id
        self.current_map_name = definition["name"]
        self.map_background_color = definition["background"]
        self.all_sprites.add(self.player)

        platforms_data = definition["platforms"]
        for x, y, w, h, one_way in platforms_data:
            platform = Platform(x, y, w, h, one_way)
            self.platforms.add(platform)
            self.all_sprites.add(platform)

        for x, y, enemy_type, delay, patrol, speed in definition["enemies"]:
            self.enemy_spawn_points.append(SpawnPoint(x, y, enemy_type, delay, patrol, speed))

        # Initial enemy spawn
        for sp in self.enemy_spawn_points:
            self.spawn_enemy(sp)

        for x, y, w, h, destination, destination_spawn in definition["portals"]:
            portal = Portal(x, y, w, h, destination, destination_spawn)
            self.portals.add(portal)
            self.all_sprites.add(portal)

        for x, y, name, initial, active, complete, quest_key in definition["npcs"]:
            quest = self._make_slime_quest() if quest_key == "slime_quest" else None
            npc = NPC(x, y, 32, 64, name, initial, active, complete, quest)
            self.npcs.add(npc)
            self.all_sprites.add(npc)

        self.game_map = GameMap(self.platforms.sprites(), self.enemies.sprites(), self.portals.sprites())
        self.player.rect.topleft = definition["spawns"][spawn_point_id]
        self.player.vel_x = 0
        self.player.vel_y = 0
        self.portal_transition_cooldown = 30
        self.display_notification(self.current_map_name, 90)


    def display_notification(self, message, duration=120):
        self.notification_message = message
        self.notification_timer = duration
        print(f"Notification: {message}") # Also print to console for debugging

    def _inventory_catalog(self):
        return {
            "bronze_sword": BronzeSword(),
            "leather_cap": LeatherCap(),
            "training_shirt": TrainingShirt(),
            "traveler_pants": TravelerPants(),
            "health_potion": HealthPotion(),
            "mana_potion": ManaPotion(),
        }

    def _equip_dragged_item(self, item_id, slot):
        item = self._inventory_catalog()[item_id]
        if slot == "weapon" and item_id == "bronze_sword":
            return self.player.equip_weapon(item)
        if getattr(item, "slot", None) == slot:
            return self.player.equip_armor(item)
        return f"{item.name} does not fit the {slot} slot."

    def _handle_inventory_mouse(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for tab, rect in self.inventory_tab_rects.items():
                if rect.collidepoint(event.pos):
                    self.inventory_tab = tab
                    return
            for item_id, rect in self.inventory_item_rects.items():
                if rect.collidepoint(event.pos):
                    self.dragged_item_id = item_id
                    return
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragged_item_id:
            message = None
            for slot, rect in self.equipment_slot_rects.items():
                if rect.collidepoint(event.pos):
                    message = self._equip_dragged_item(self.dragged_item_id, slot)
                    break
            if message:
                self.display_notification(message)
            self.dragged_item_id = None

    def _handle_stats_mouse(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for stat, rect in self.stat_button_rects.items():
                if rect.collidepoint(event.pos):
                    self.display_notification(self.player.allocate_stat(stat))
                    return

    def _build_save_state(self):
        quests = {
            quest_id: {
                "completed": status["completed"],
                "current_count": status["current_count"],
            }
            for quest_id, status in self.player.active_quests.items()
        }
        return {
            "map_id": self.current_map_id,
            "player": {
                "level": self.player.level,
                "exp": self.player.exp,
                "exp_to_next_level": self.player.exp_to_next_level,
                "hp": self.player.hp,
                "max_hp": self.player.max_hp,
                "mp": self.player.mp,
                "max_mp": self.player.max_mp,
                "attack_damage": self.player.attack_damage,
                "stats": self.player.stats,
                "stat_points": self.player.stat_points,
                "inventory": self.player.inventory,
                "weapon": self.player.equipped_weapon.item_id if self.player.equipped_weapon else None,
                "equipment": {
                    slot: item.item_id if item else None
                    for slot, item in self.player.equipment.items()
                },
                "quests": quests,
            },
        }

    def save_current_game(self):
        save_game(self._build_save_state(), self.save_file)
        self.display_notification("Game saved.")

    def load_saved_game(self):
        state = load_game(self.save_file)
        if not state:
            self.display_notification("No valid save file found.")
            return False
        player_state = state.get("player", {})
        required = ("level", "exp", "hp", "max_hp", "mp", "max_mp", "stats", "inventory")
        if any(key not in player_state for key in required):
            self.display_notification("Save file is incomplete.")
            return False

        for attribute in ("level", "exp", "exp_to_next_level", "hp", "max_hp", "mp", "max_mp", "attack_damage", "stat_points"):
            if attribute in player_state:
                setattr(self.player, attribute, player_state[attribute])
        self.player.stats = dict(player_state["stats"])
        self.player.inventory = dict(player_state["inventory"])
        self.player.equipped_weapon = None
        self.player.equipment = {"helmet": None, "shirt": None, "pants": None}
        catalog = self._inventory_catalog()
        weapon_id = player_state.get("weapon")
        if weapon_id in catalog:
            self.player.equip_weapon(catalog[weapon_id])
        for slot, item_id in player_state.get("equipment", {}).items():
            if slot in self.player.equipment and item_id in catalog:
                self.player.equip_armor(catalog[item_id])

        self.player.active_quests = {}
        for quest_id, saved_status in player_state.get("quests", {}).items():
            if quest_id == "slime_trouble":
                quest = self._make_slime_quest()
                self.player.active_quests[quest_id] = {
                    "accepted": True,
                    "completed": bool(saved_status.get("completed", False)),
                    "current_count": int(saved_status.get("current_count", 0)),
                    "quest_obj": quest,
                }
        map_id = state.get("map_id", "meadow_village")
        if map_id not in self.map_definitions:
            map_id = "meadow_village"
        spawn_id = next(iter(self.map_definitions[map_id]["spawns"]))
        self.load_map(map_id, spawn_id)
        self.display_notification("Game loaded.")
        return True

    def handle_player_defeat(self):
        lost_exp = min(self.player.exp, max(1, self.player.exp // 10)) if self.player.exp else 0
        self.player.exp -= lost_exp
        self.player.hp = self.player.max_hp
        self.player.mp = self.player.max_mp
        self.player.invincible = False
        self.player.invincibility_timer = 0
        self.load_map("meadow_village", "start")
        self.display_notification(f"You were defeated. Lost {lost_exp} EXP and returned to town.", 180)


    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if self.inventory_open and event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                self._handle_inventory_mouse(event)
                continue
            if self.stats_open and event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_stats_mouse(event)
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:
                    self.save_current_game()
                    continue
                if event.key == pygame.K_F9:
                    self.load_saved_game()
                    continue
                if event.key == pygame.K_i:
                    self.inventory_open = not self.inventory_open
                    self.stats_open = False
                    self.dragged_item_id = None
                    continue
                if event.key == pygame.K_s:
                    self.stats_open = not self.stats_open
                    self.inventory_open = False
                    continue
                if self.stats_open:
                    stat_keys = {
                        pygame.K_1: "strength", pygame.K_2: "dexterity",
                        pygame.K_3: "intelligence", pygame.K_4: "luck",
                    }
                    if event.key in stat_keys:
                        self.display_notification(self.player.allocate_stat(stat_keys[event.key]))
                    continue
                if self.inventory_open:
                    equipment_keys = {
                        pygame.K_q: lambda: self.player.equip_bronze_sword(),
                        pygame.K_w: lambda: self.player.equip_starter_armor("helmet"),
                        pygame.K_e: lambda: self.player.equip_starter_armor("shirt"),
                        pygame.K_r: lambda: self.player.equip_starter_armor("pants"),
                    }
                    stat_keys = {
                        pygame.K_1: "strength", pygame.K_2: "dexterity",
                        pygame.K_3: "intelligence", pygame.K_4: "luck",
                    }
                    if event.key in equipment_keys:
                        self.display_notification(equipment_keys[event.key]())
                    elif event.key in stat_keys:
                        self.display_notification(self.player.allocate_stat(stat_keys[event.key]))
                    continue

                # Potion usage should not be blocked by dialogue
                if event.key == pygame.K_1: # Use Health Potion
                    message = self.player.use_health_potion()
                    self.display_notification(message)
                    if "Used" in message: # Check if potion was successfully used
                        self.potion_sound.play()
                    continue # Process next event or skip other keydowns
                if event.key == pygame.K_2: # Use Mana Potion
                    message = self.player.use_mana_potion()
                    self.display_notification(message)
                    if "Used" in message: # Check if potion was successfully used
                        self.potion_sound.play()
                    continue # Process next event or skip other keydowns

                if self.dialogue_active and self.current_npc: # If in dialogue, only 'E' is processed for dialogue advance
                    if event.key == pygame.K_e:
                        # Player is interacting with an NPC
                        if self.current_npc.quest_offered:
                            quest_id = self.current_npc.quest_offered.id
                            player_quest_status = self.player.get_quest_status(quest_id)

                            if not player_quest_status['accepted']:
                                # Offer quest
                                self.player.accept_quest(self.current_npc.quest_offered)
                                self.current_npc.stop_talk()
                                self.dialogue_active = False
                                self.current_npc = None
                            elif player_quest_status['completed']:
                                # Turn in quest
                                self.player.turn_in_quest(quest_id)
                                self.current_npc.stop_talk()
                                self.dialogue_active = False
                                self.current_npc = None
                            else:
                                # Quest active, just close dialogue
                                self.current_npc.stop_talk()
                                self.dialogue_active = False
                                self.current_npc = None
                        else:
                            # NPC has no quest, just close dialogue
                            self.current_npc.stop_talk()
                            self.dialogue_active = False
                            self.current_npc = None
                    # No else, because if in dialogue, other keys are ignored, handled by continue from potion usage

                else: # Not in dialogue
                    if event.key == pygame.K_SPACE:
                        if self.player.on_ground:
                            self.player.jump()
                            self.jump_sound.play() # Play jump sound
                        elif self.player.can_double_jump:
                            self.player.jump()
                            self.player.can_double_jump = False
                            self.jump_sound.play() # Play jump sound (for double jump)
                    elif event.key == pygame.K_j and not self.player.is_attacking and self.player.attack_cooldown <= 0:
                        self.player.start_attack()
                        self.melee_sound.play() # Play melee sound
                    elif event.key == pygame.K_k: # Cast Fireball
                        result = self.player.cast_fireball()
                        if isinstance(result, str):
                            self.display_notification(result)
                        elif result:
                            self.projectiles.add(result)
                            self.all_sprites.add(result)
                            self.magic_sound.play() # Play magic sound
                    elif event.key == pygame.K_l: # Cast Ice Bolt
                        result = self.player.cast_icebolt()
                        if isinstance(result, str):
                            self.display_notification(result)
                        elif result:
                            self.projectiles.add(result)
                            self.all_sprites.add(result)
                            self.magic_sound.play() # Play magic sound
                    elif event.key == pygame.K_e: # Check for NPC interaction
                        for npc in self.npcs:
                            if self.player.rect.colliderect(npc.rect.inflate(50, 50)): # Slightly larger interaction area
                                self.current_npc = npc
                                self.dialogue_active = True
                                quest_id = npc.quest_offered.id if npc.quest_offered else None
                                player_quest_status = self.player.get_quest_status(quest_id) if quest_id else None
                                npc.start_talk(player_quest_status)
                                break
                        else: # No NPC found, pass input to player
                            self.player.handle_input(event) # This will handle other player movements outside of dialogue
                    else:
                        self.player.handle_input(event)
            else: # If not KEYDOWN, pass other events directly to player for continuous movement
                # Ensure player.handle_input doesn't get potion keys if already handled above
                if event.type == pygame.KEYUP and (event.key == pygame.K_1 or event.key == pygame.K_2): # Ignore key-up for potions
                    pass
                else:
                    self.player.handle_input(event)


    def update(self):
        if self.portal_transition_cooldown > 0:
            self.portal_transition_cooldown -= 1
        # Player.update handles cooldowns during gameplay. Dialogue pauses regular
        # updates, so keep only the potion cooldown moving while dialogue is open.
        if self.dialogue_active and self.player.potion_cooldown_timer > 0:
            self.player.potion_cooldown_timer -= 1

        if not self.dialogue_active and not self.inventory_open and not self.stats_open:
            self.all_sprites.update(self.platforms.sprites()) # Pass platforms for collision

            # Update notification timer
            if self.notification_timer > 0:
                self.notification_timer -= 1
            else:
                self.notification_message = ""

            # Handle enemy respawn logic
            for sp in self.enemy_spawn_points:
                if not sp.is_active:
                    sp.current_respawn_timer -= 1
                    if sp.current_respawn_timer <= 0:
                        self.spawn_enemy(sp)

            # Player-enemy collision (contact damage)
            for enemy in pygame.sprite.spritecollide(self.player, self.enemies, False):
                if not self.player.invincible:
                    self.player.take_damage(enemy.contact_damage)
                    self.player_hit_sound.play() # Play player hit sound
                    # Apply knockback
                    knockback_direction = 1 if self.player.rect.centerx > enemy.rect.centerx else -1
                    self.player.apply_knockback(knockback_direction, 5)

            # Check for KingSlime stomp attack damage
            # This check is now explicitly for KingSlime's JUMP_ATTACK state after landing
            if self.boss_instance and isinstance(self.boss_instance, KingSlime):
                if self.boss_instance.just_landed_jump_attack:
                    # Check if player is in stomp damage range
                    distance_x = abs(self.player.rect.centerx - self.boss_instance.rect.centerx)
                    distance_y = abs(self.player.rect.bottom - self.boss_instance.rect.bottom) # Check proximity to ground
                    if distance_x <= self.boss_instance.stomp_land_damage_range and distance_y <= 10: # Player is on the ground near KingSlime
                        if not self.player.invincible:
                            print("Player hit by King Slime stomp!")
                            self.player.take_damage(self.boss_instance.stomp_aoe_damage)
                            self.player_hit_sound.play()
                            knockback_direction = 1 if self.player.rect.centerx > self.boss_instance.rect.centerx else -1
                            self.player.apply_knockback(knockback_direction, 10) # Stronger knockback from stomp


            # Player-portal collision
            for portal in pygame.sprite.spritecollide(self.player, self.portals, False):
                if self.portal_transition_cooldown > 0:
                    break
                print(f"Player entered portal! Destination: {portal.destination_map_id}, Spawn: {portal.destination_spawn_point_id}")
                self.load_map(portal.destination_map_id, portal.destination_spawn_point_id)
                break

            # Projectile-enemy collision
            for projectile in self.projectiles:
                collided_enemies = pygame.sprite.spritecollide(projectile, self.enemies, False)
                for enemy in collided_enemies:
                    if not enemy.invincible:
                        enemy.take_damage(projectile.damage)
                        if isinstance(projectile, IceBolt) and enemy.hp > 0:
                            enemy.apply_slow_effect(
                                projectile.slow_duration,
                                projectile.slow_percentage,
                            )
                        self.enemy_hit_sound.play() # Play enemy hit sound
                        # Apply knockback to enemy
                        knockback_direction = 1 if enemy.rect.centerx > projectile.rect.centerx else -1
                        enemy.apply_knockback(knockback_direction, 10)
                        if enemy.hp <= 0:
                            self.player.gain_exp(enemy.exp_reward)
                            self.player.increment_quest_kill_count(type(enemy).__name__) # type(enemy).__name__ gives 'Slime' or 'KingSlime' or 'MiniSlime'
                            # Potion drop logic
                            self._handle_enemy_drop(enemy.rect.centerx, enemy.rect.centery, enemy)

                            # If the defeated enemy is the KingSlime, also check for a unique item drop (placeholder)
                            if isinstance(enemy, KingSlime):
                                print("King Slime defeated! Unique item drop (placeholder).")
                                # Add actual item drop logic here

                            # Find spawn point for defeated enemy
                            enemy_was_spawned_at_point = False
                            for sp in self.enemy_spawn_points:
                                if sp.spawned_enemy_ref == enemy:
                                    sp.is_active = False
                                    sp.current_respawn_timer = sp.respawn_delay
                                    sp.spawned_enemy_ref = None
                                    enemy_was_spawned_at_point = True
                                    break
                            # Minions don't have a respawn point, they just die
                            enemy.kill()
                            self.enemy_death_sound.play() # Play enemy death sound
                            print(f"{type(enemy).__name__} defeated! Player gained {enemy.exp_reward} EXP. Player EXP: {self.player.exp}")
                    projectile.kill() # Projectile disappears on hit (even if enemy is invincible)
                    break # Projectiles hit only one enemy

            # Melee Attack logic
            if self.player.is_attacking:
                if self.player.attack_hitbox.width > 0:
                    collided_enemies = [
                        enemy for enemy in self.enemies
                        if self.player.attack_hitbox.colliderect(enemy.rect)
                    ]
                    for enemy in collided_enemies:
                        if not enemy.invincible:
                            enemy.take_damage(self.player.melee_damage)
                            self.enemy_hit_sound.play() # Play enemy hit sound
                            knockback_direction = 1 if enemy.rect.centerx > self.player.rect.centerx else -1
                            enemy.apply_knockback(knockback_direction, 10)
                            if enemy.hp <= 0:
                                self.player.gain_exp(enemy.exp_reward)
                                self.player.increment_quest_kill_count(type(enemy).__name__) # type(enemy).__name__ gives 'Slime' or 'KingSlime' or 'MiniSlime'
                                # Potion drop logic
                                self._handle_enemy_drop(enemy.rect.centerx, enemy.rect.centery, enemy)

                                # If the defeated enemy is the KingSlime, also check for a unique item drop (placeholder)
                                if isinstance(enemy, KingSlime):
                                    print("King Slime defeated! Unique item drop (placeholder).")
                                    # Add actual item drop logic here

                                # Find spawn point for defeated enemy
                                enemy_was_spawned_at_point = False
                                for sp in self.enemy_spawn_points:
                                    if sp.spawned_enemy_ref == enemy:
                                        sp.is_active = False
                                        sp.current_respawn_timer = sp.respawn_delay
                                        sp.spawned_enemy_ref = None
                                        enemy_was_spawned_at_point = True
                                        break
                                # Minions don't have a respawn point, they just die
                                enemy.kill()
                                self.enemy_death_sound.play() # Play enemy death sound
                                print(f"{type(enemy).__name__} defeated! Player gained {enemy.exp_reward} EXP. Player EXP: {self.player.exp}")
            
            # Bosses cannot be knocked outside the playable arena.
            if self.boss_instance and self.boss_instance.alive():
                self.boss_instance.rect.left = max(0, self.boss_instance.rect.left)
                self.boss_instance.rect.right = min(self.screen_width, self.boss_instance.rect.right)
                if self.boss_instance.rect.bottom > self.screen_height:
                    self.boss_instance.rect.bottom = self.screen_height - 40
                    self.boss_instance.vel_y = 0

            # Boundary checks for player (falling off map)
            if self.player.rect.top > self.screen_height:
                print("Player fell off the map!")
                self.player.rect.x = 100
                self.player.rect.y = self.screen_height - 100
                self.player.take_damage(10) # Small HP penalty

            # Map boundary for horizontal movement
            if self.player.rect.left < 0:
                self.player.rect.left = 0
            if self.player.rect.right > self.screen_width:
                self.player.rect.right = self.screen_width
            if self.player.hp <= 0:
                self.handle_player_defeat()

    def _handle_enemy_drop(self, x, y, enemy):
        luck_bonus = max(0, self.player.total_stat("luck") - 4) * 0.005
        drop_chance = random.random() - luck_bonus
        dropped_item = None

        # Check subclasses before Slime because KingSlime and MiniSlime inherit it.
        if isinstance(enemy, KingSlime):
            if drop_chance < 0.5: # 50% chance for KingSlime to drop a potion
                if random.random() < 0.7: # Higher chance for HP potion from boss
                    dropped_item = HealthPotion()
                else:
                    dropped_item = ManaPotion()
        elif isinstance(enemy, Slime):
            if drop_chance < 0.2: # 20% chance for a potion
                if random.random() < 0.6: # 60% of time it's HP potion
                    dropped_item = HealthPotion()
                else: # 40% of time it's MP potion
                    dropped_item = ManaPotion()

        if dropped_item:
            if self.player.add_item(dropped_item, 1): # Try to add 1 of the dropped item
                self.display_notification(f"Picked up {dropped_item.name}!")
            else:
                self.display_notification(f"Inventory for {dropped_item.name} is full!")


    def draw_hud(self):
        map_text = self.font.render(self.current_map_name, True, self.TEXT_COLOR)
        self.screen.blit(map_text, (self.screen_width - map_text.get_width() - 12, 12))

        # HP Bar
        hp_bar_x = self.HUD_X
        hp_bar_y = self.HUD_Y
        hp_bar_fill = (self.player.hp / self.player.max_hp) * self.BAR_WIDTH
        pygame.draw.rect(self.screen, self.BAR_BACKGROUND_COLOR, (hp_bar_x, hp_bar_y, self.BAR_WIDTH, self.BAR_HEIGHT))
        pygame.draw.rect(self.screen, self.HP_COLOR, (hp_bar_x, hp_bar_y, hp_bar_fill, self.BAR_HEIGHT))
        hp_text = self.font.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, self.TEXT_COLOR)
        self.screen.blit(hp_text, (hp_bar_x + self.BAR_WIDTH + self.BAR_SPACING, hp_bar_y))

        # MP Bar
        mp_bar_x = self.HUD_X
        mp_bar_y = self.HUD_Y + self.BAR_HEIGHT + self.BAR_SPACING
        mp_bar_fill = (self.player.mp / self.player.max_mp) * self.BAR_WIDTH
        pygame.draw.rect(self.screen, self.BAR_BACKGROUND_COLOR, (mp_bar_x, mp_bar_y, self.BAR_WIDTH, self.BAR_HEIGHT))
        pygame.draw.rect(self.screen, self.MP_COLOR, (mp_bar_x, mp_bar_y, mp_bar_fill, self.BAR_HEIGHT))
        mp_text = self.font.render(f"MP: {self.player.mp}/{self.player.max_mp}", True, self.TEXT_COLOR)
        self.screen.blit(mp_text, (mp_bar_x + self.BAR_WIDTH + self.BAR_SPACING, mp_bar_y))

        # EXP Bar
        exp_bar_x = self.HUD_X
        exp_bar_y = self.HUD_Y + (self.BAR_HEIGHT + self.BAR_SPACING) * 2
        exp_ratio = 0
        if self.player.exp_to_next_level > 0:
            exp_ratio = (self.player.exp / self.player.exp_to_next_level)
        exp_bar_fill = exp_ratio * self.BAR_WIDTH
        pygame.draw.rect(self.screen, self.BAR_BACKGROUND_COLOR, (exp_bar_x, exp_bar_y, self.BAR_WIDTH, self.BAR_HEIGHT))
        pygame.draw.rect(self.screen, self.EXP_COLOR, (exp_bar_x, exp_bar_y, exp_bar_fill, self.BAR_HEIGHT))
        exp_text = self.font.render(f"EXP: {self.player.exp}/{self.player.exp_to_next_level}", True, self.TEXT_COLOR)
        self.screen.blit(exp_text, (exp_bar_x + self.BAR_WIDTH + self.BAR_SPACING, exp_bar_y))

        # Level Display
        level_text = self.font.render(f"Level: {self.player.level}", True, self.TEXT_COLOR)
        self.screen.blit(level_text, (self.HUD_X + self.LEVEL_OFFSET_X, self.HUD_Y + (self.BAR_HEIGHT + self.BAR_SPACING) * 3))

        # Potion quantities (below other HUD elements, or to the right)
        potion_hud_y = self.HUD_Y + (self.BAR_HEIGHT + self.BAR_SPACING) * 4
        hp_potion_count = self.player.inventory.get(HealthPotion().item_id, 0)
        mp_potion_count = self.player.inventory.get(ManaPotion().item_id, 0)

        hp_potion_text = self.font.render(f"HP Potions (1): {hp_potion_count}", True, self.TEXT_COLOR)
        self.screen.blit(hp_potion_text, (self.HUD_X, potion_hud_y))
        mp_potion_text = self.font.render(f"MP Potions (2): {mp_potion_count}", True, self.TEXT_COLOR)
        self.screen.blit(mp_potion_text, (self.HUD_X, potion_hud_y + self.BAR_HEIGHT + self.BAR_SPACING))

        # Potion Cooldown Display
        if self.player.potion_cooldown_timer > 0:
            cooldown_seconds = self.player.potion_cooldown_timer / 60
            cooldown_text = self.font.render(f"Potion CD: {cooldown_seconds:.1f}s", True, (255, 100, 100)) # Reddish color for cooldown
            self.screen.blit(cooldown_text, (self.HUD_X + self.BAR_WIDTH + 20, potion_hud_y + (self.BAR_HEIGHT + self.BAR_SPACING) * 0.5))

        # Magic skill hotkeys and cooldowns
        skill_hud_y = potion_hud_y + (self.BAR_HEIGHT + self.BAR_SPACING) * 2
        fireball_seconds = self.player.fireball_current_cooldown / 60
        icebolt_seconds = self.player.icebolt_current_cooldown / 60
        fireball_status = "Ready" if fireball_seconds <= 0 else f"{fireball_seconds:.1f}s"
        icebolt_status = "Ready" if icebolt_seconds <= 0 else f"{icebolt_seconds:.1f}s"
        fireball_text = self.font.render(f"Fireball (K): {fireball_status}", True, self.TEXT_COLOR)
        icebolt_text = self.font.render(f"Ice Bolt (L): {icebolt_status}", True, self.TEXT_COLOR)
        self.screen.blit(fireball_text, (self.HUD_X, skill_hud_y))
        self.screen.blit(icebolt_text, (self.HUD_X, skill_hud_y + self.BAR_HEIGHT + self.BAR_SPACING))

        weapon_name = self.player.equipped_weapon.name if self.player.equipped_weapon else "Fists"
        melee_text = self.font.render(
            f"Melee (J): {weapon_name} | ATK {self.player.melee_damage}",
            True,
            self.TEXT_COLOR,
        )
        self.screen.blit(melee_text, (self.HUD_X, skill_hud_y + (self.BAR_HEIGHT + self.BAR_SPACING) * 2))
        inventory_hint = self.font.render("Inventory (I)", True, self.TEXT_COLOR)
        self.screen.blit(inventory_hint, (self.HUD_X, skill_hud_y + (self.BAR_HEIGHT + self.BAR_SPACING) * 3))
        save_hint = self.font.render("Save F5 | Load F9 | Stats S", True, self.TEXT_COLOR)
        self.screen.blit(save_hint, (self.HUD_X, skill_hud_y + (self.BAR_HEIGHT + self.BAR_SPACING) * 4))

    def draw_inventory(self):
        panel = pygame.Rect(90, 75, 620, 440)
        pygame.draw.rect(self.screen, (37, 45, 58), panel, border_radius=12)
        pygame.draw.rect(self.screen, (218, 174, 84), panel, 4, border_radius=12)
        title = self.dialogue_font.render("Item Inventory", True, (255, 232, 160))
        self.screen.blit(title, (panel.x + 20, panel.y + 14))

        self.inventory_tab_rects = {}
        for index, tab in enumerate(("equip", "use", "etc")):
            rect = pygame.Rect(panel.x + 190 + index * 105, panel.y + 12, 96, 34)
            self.inventory_tab_rects[tab] = rect
            color = (204, 156, 70) if self.inventory_tab == tab else (67, 76, 92)
            pygame.draw.rect(self.screen, color, rect, border_radius=7)
            label = self.font.render(tab.title(), True, self.TEXT_COLOR)
            self.screen.blit(label, label.get_rect(center=rect.center))

        content = pygame.Rect(panel.x + 18, panel.y + 62, panel.width - 36, 345)
        pygame.draw.rect(self.screen, (25, 31, 43), content, border_radius=8)
        self.inventory_item_rects = {}
        self.equipment_slot_rects = {}
        catalog = self._inventory_catalog()

        if self.inventory_tab == "equip":
            slots = [("helmet", 125, 82), ("shirt", 125, 158), ("pants", 125, 234), ("weapon", 18, 158)]
            for slot, x, y in slots:
                rect = pygame.Rect(content.x + x, content.y + y, 96, 58)
                self.equipment_slot_rects[slot] = rect
                pygame.draw.rect(self.screen, (59, 69, 86), rect, border_radius=6)
                pygame.draw.rect(self.screen, (142, 155, 180), rect, 2, border_radius=6)
                equipped = self.player.equipped_weapon if slot == "weapon" else self.player.equipment[slot]
                label = equipped.name if equipped else slot.title()
                text_surface = self.font.render(label, True, self.TEXT_COLOR)
                self.screen.blit(text_surface, text_surface.get_rect(center=rect.center))

            gear_ids = ["bronze_sword", "leather_cap", "training_shirt", "traveler_pants"]
            for index, item_id in enumerate(gear_ids):
                rect = pygame.Rect(content.x + 285, content.y + 24 + index * 72, 270, 58)
                self.inventory_item_rects[item_id] = rect
                pygame.draw.rect(self.screen, (52, 62, 78), rect, border_radius=6)
                item = catalog[item_id]
                count = self.player.inventory.get(item_id, 0)
                text_surface = self.font.render(f"{item.name}  x{count}", True, self.TEXT_COLOR)
                self.screen.blit(text_surface, (rect.x + 12, rect.y + 18))
            hint = self.font.render("Drag gear onto a matching slot", True, (255, 220, 120))
            self.screen.blit(hint, (content.x + 14, content.y + 12))
        elif self.inventory_tab == "use":
            for index, item_id in enumerate(("health_potion", "mana_potion")):
                rect = pygame.Rect(content.x + 24 + index * 210, content.y + 45, 190, 70)
                self.inventory_item_rects[item_id] = rect
                item = catalog[item_id]
                count = self.player.inventory.get(item_id, 0)
                pygame.draw.rect(self.screen, (74, 65, 82), rect, border_radius=7)
                text_surface = self.font.render(f"{item.name} x{count}", True, self.TEXT_COLOR)
                self.screen.blit(text_surface, text_surface.get_rect(center=rect.center))
            hint = self.font.render("Use potions with 1 and 2 during gameplay", True, (255, 220, 120))
            self.screen.blit(hint, (content.x + 24, content.y + 145))
        else:
            lines = ["Etc items and quest materials will appear here.", "Slime Gel x0", "Forest Leaf x0", "Boss Crystal x0"]
            for index, line in enumerate(lines):
                text_surface = self.font.render(line, True, self.TEXT_COLOR)
                self.screen.blit(text_surface, (content.x + 24, content.y + 30 + index * 42))

        if self.dragged_item_id:
            item = catalog[self.dragged_item_id]
            mouse_x, mouse_y = pygame.mouse.get_pos()
            drag_rect = pygame.Rect(mouse_x - 55, mouse_y - 20, 110, 40)
            pygame.draw.rect(self.screen, (218, 174, 84), drag_rect, border_radius=6)
            label = self.font.render(item.name, True, (25, 31, 43))
            self.screen.blit(label, label.get_rect(center=drag_rect.center))

        close_hint = self.font.render("I - Close", True, self.TEXT_COLOR)
        self.screen.blit(close_hint, (panel.right - 90, panel.y + 18))

    def draw_stats(self):
        panel = pygame.Rect(205, 95, 390, 410)
        pygame.draw.rect(self.screen, (37, 45, 58), panel, border_radius=12)
        pygame.draw.rect(self.screen, (218, 174, 84), panel, 4, border_radius=12)
        title = self.dialogue_font.render("Character Stats", True, (255, 232, 160))
        self.screen.blit(title, (panel.x + 22, panel.y + 18))
        summary = [
            f"Level: {self.player.level}", f"Available AP: {self.player.stat_points}",
            f"Attack: {self.player.melee_damage}", f"Defense: {self.player.defense}",
        ]
        for index, line in enumerate(summary):
            text_surface = self.font.render(line, True, self.TEXT_COLOR)
            self.screen.blit(text_surface, (panel.x + 24 + (index % 2) * 180, panel.y + 65 + (index // 2) * 32))

        self.stat_button_rects = {}
        stats = [("strength", "STR", "Melee damage"), ("dexterity", "DEX", "Attack speed"), ("intelligence", "INT", "Spell damage"), ("luck", "LUK", "Item drops")]
        for index, (stat, label, effect) in enumerate(stats):
            y = panel.y + 145 + index * 58
            value = self.player.total_stat(stat)
            text_surface = self.font.render(f"{label}  {value}   {effect}", True, self.TEXT_COLOR)
            self.screen.blit(text_surface, (panel.x + 25, y + 10))
            button = pygame.Rect(panel.right - 58, y, 34, 34)
            self.stat_button_rects[stat] = button
            pygame.draw.rect(self.screen, (91, 154, 86), button, border_radius=6)
            plus = self.dialogue_font.render("+", True, self.TEXT_COLOR)
            self.screen.blit(plus, plus.get_rect(center=button.center))
        close_hint = self.font.render("S - Close   (1/2/3/4 also allocate)", True, self.TEXT_COLOR)
        self.screen.blit(close_hint, (panel.x + 24, panel.bottom - 34))


    def draw_dialogue_box(self, text):
        # Draw semi-transparent background
        box_width = self.screen_width - 100
        box_height = 100
        box_x = 50
        box_y = self.screen_height - box_height - 20
        dialogue_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self.screen, self.DIALOGUE_BG_COLOR, dialogue_rect, border_radius=5)
        pygame.draw.rect(self.screen, (255, 255, 255), dialogue_rect, 2, border_radius=5) # White border

        # Render text
        lines = text.split('\n')
        y_offset = 10
        for line in lines:
            text_surface = self.dialogue_font.render(line, True, self.TEXT_COLOR)
            self.screen.blit(text_surface, (box_x + 10, box_y + y_offset))
            y_offset += text_surface.get_height() + 5


    def draw(self):
        self.screen.fill(self.map_background_color)
        self.all_sprites.draw(self.screen) # Draw all sprites
        self.player.draw(self.screen) # Draw player (and potentially debug hitboxes)
        self.draw_hud() # Draw HUD after all other elements

        if self.dialogue_active and self.current_npc:
            self.draw_dialogue_box(self.current_npc.current_dialogue)
        if self.inventory_open:
            self.draw_inventory()
        if self.stats_open:
            self.draw_stats()
        
        # Draw global notifications
        if self.notification_timer > 0:
            self.draw_notification(self.notification_message)


        pygame.display.flip()

    def draw_notification(self, message):
        text_surface = self.font.render(message, True, self.NOTIFICATION_COLOR)
        text_rect = text_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 4))
        self.screen.blit(text_surface, text_rect)

    def run(self):
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(60) # 60 FPS

        pygame.quit()
        sys.exit()

# Dummy sound class if sound files are not found
class DummySound:
    def play(self):
        pass
    def set_volume(self, volume):
        pass
