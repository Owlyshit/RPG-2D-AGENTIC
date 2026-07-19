import pygame
import sys
from src.player import Player
from src.enemy import Slime, KingSlime # Import KingSlime
from src.map import Platform, Portal, GameMap
from src.npc import NPC, Quest
from src.skill import Fireball # Import Fireball

# Simple data class for spawn points
class SpawnPoint:
    def __init__(self, x, y, enemy_type, respawn_delay, initial_patrol_range=None, initial_walk_speed=None):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type # String, e.g., 'Slime', 'KingSlime'
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

        # Load Sounds (Placeholder - replace with actual paths)
        try:
            self.jump_sound = pygame.mixer.Sound('assets/sounds/jump.wav')
        except pygame.error:
            print("Warning: jump.wav not found. Playing dummy sound.")
            self.jump_sound = DummySound()
        try:
            self.melee_sound = pygame.mixer.Sound('assets/sounds/melee.wav')
        except pygame.error:
            print("Warning: melee.wav not found. Playing dummy sound.")
            self.melee_sound = DummySound()
        try:
            self.magic_sound = pygame.mixer.Sound('assets/sounds/magic.wav')
        except pygame.error:
            print("Warning: magic.wav not found. Playing dummy sound.")
            self.magic_sound = DummySound()
        try:
            self.player_hit_sound = pygame.mixer.Sound('assets/sounds/player_hit.wav')
        except pygame.error:
            print("Warning: player_hit.wav not found. Playing dummy sound.")
            self.player_hit_sound = DummySound()
        try:
            self.enemy_hit_sound = pygame.mixer.Sound('assets/sounds/enemy_hit.wav')
        except pygame.error:
            print("Warning: enemy_hit.wav not found. Playing dummy sound.")
            self.enemy_hit_sound = DummySound()
        try:
            self.enemy_death_sound = pygame.mixer.Sound('assets/sounds/enemy_death.wav')
        except pygame.error:
            print("Warning: enemy_death.wav not found. Playing dummy sound.")
            self.enemy_death_sound = DummySound()
        
        # Set sound volumes (optional, default is 1.0)
        # self.jump_sound.set_volume(0.5)

        self.setup_map()

        self.player = Player(
            x=100, y=self.screen_height - 100,
            width=32, height=64,
            walk_speed=self.player_walk_speed,
            jump_strength=self.player_jump_strength,
            gravity=self.gravity
        )
        self.all_sprites.add(self.player)

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

        self.HUD_X = 10
        self.HUD_Y = 10
        self.BAR_WIDTH = 150
        self.BAR_HEIGHT = 15
        self.BAR_SPACING = 5
        self.LEVEL_OFFSET_X = self.BAR_WIDTH + 20

        self.dialogue_active = False
        self.current_npc = None


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
        elif spawn_point.enemy_type == 'KingSlime': # Handle KingSlime spawning
            new_enemy = KingSlime(
                x=spawn_point.x,
                y=spawn_point.y,
                patrol_range=spawn_point.initial_patrol_range if spawn_point.initial_patrol_range else 50, # KingSlime might have smaller patrol
                walk_speed=spawn_point.initial_walk_speed if spawn_point.initial_walk_speed else self.enemy_walk_speed * 0.7,
                gravity=self.gravity
            )
        
        if new_enemy:
            self.enemies.add(new_enemy)
            self.all_sprites.add(new_enemy)
            spawn_point.spawned_enemy_ref = new_enemy
            spawn_point.is_active = True
            print(f"Respawned {spawn_point.enemy_type} at ({spawn_point.x}, {spawn_point.y})")


    def setup_map(self):
        # Define platforms
        platforms_data = [
            (0, self.screen_height - 40, self.screen_width, 40, False),  # Ground
            (150, self.screen_height - 150, 200, 20, False),
            (450, self.screen_height - 250, 150, 20, True),  # One-way platform
        ]
        for x, y, w, h, one_way in platforms_data:
            platform = Platform(x, y, w, h, one_way)
            self.platforms.add(platform)
            self.all_sprites.add(platform)

        # Define Enemy Spawn Points
        self.enemy_spawn_points.append(SpawnPoint(300, self.screen_height - 80, 'Slime', 300, initial_patrol_range=100, initial_walk_speed=self.enemy_walk_speed))
        self.enemy_spawn_points.append(SpawnPoint(550, self.screen_height - 80, 'Slime', 300, initial_patrol_range=100, initial_walk_speed=self.enemy_walk_speed))
        self.enemy_spawn_points.append(SpawnPoint(200, self.screen_height - 180, 'Slime', 300, initial_patrol_range=50, initial_walk_speed=self.enemy_walk_speed)) # Another slime on a platform
        self.enemy_spawn_points.append(SpawnPoint(500, self.screen_height - 280, 'KingSlime', 600, initial_patrol_range=70, initial_walk_speed=self.enemy_walk_speed)) # Replaced a slime with KingSlime
        self.enemy_spawn_points.append(SpawnPoint(700, self.screen_height - 80, 'Slime', 300, initial_patrol_range=120, initial_walk_speed=self.enemy_walk_speed)) # A fifth slime

        # Initial enemy spawn
        for sp in self.enemy_spawn_points:
            self.spawn_enemy(sp)

        # Define portals
        portal1 = Portal(x=self.screen_width - 80, y=self.screen_height - 100, width=60, height=60, destination_map_id="map_2", destination_spawn_point_id="entry_1")
        self.portals.add(portal1)
        self.all_sprites.add(portal1)

        # Define Quests
        slime_trouble_quest = Quest(
            q_id='slime_trouble',
            name='Slime Trouble',
            objective_type='kill',
            objective_target='Slime',
            objective_count=5,
            reward_exp=50,
            is_repeatable=True
        )

        # Define NPC (Farmer John)
        farmer_john = NPC(
            x=self.screen_width / 2 - 50,
            y=self.screen_height - 104, # Adjust Y to stand on ground
            width=32, height=64,
            name="Farmer John",
            initial_dialogue="Hello there! Can you help me? The slimes are multiplying! Will you defeat 5 for me?",
            quest_active_dialogue="Keep up the good work! Those slimes won't defeat themselves.",
            quest_complete_dialogue="Ah, thank you, brave adventurer! Here's your reward!",
            quest_offered=slime_trouble_quest
        )
        self.npcs.add(farmer_john)
        self.all_sprites.add(farmer_john)
        self.farmer_john = farmer_john # Store reference for easier access

        self.game_map = GameMap(self.platforms.sprites(), self.enemies.sprites(), self.portals.sprites())


    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
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
                    new_fireball = self.player.cast_fireball()
                    if new_fireball:
                        self.projectiles.add(new_fireball)
                        self.all_sprites.add(new_fireball)
                        self.magic_sound.play() # Play magic sound
                elif event.key == pygame.K_e:
                    if self.dialogue_active and self.current_npc:
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
                    else:
                        # Check for NPC interaction
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
                else: # Any other key press during dialogue should just advance/close (for now)
                    if self.dialogue_active:
                         self.current_npc.stop_talk()
                         self.dialogue_active = False
                         self.current_npc = None
                    else:
                         self.player.handle_input(event)
            else: # If not KEYDOWN, pass other events directly to player for continuous movement
                self.player.handle_input(event)


    def update(self):
        if not self.dialogue_active: # Only update game elements if not talking to NPC
            self.all_sprites.update(self.platforms.sprites()) # Pass platforms for collision
            self.projectiles.update(self.platforms.sprites()) # Update projectiles

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
            for enemy in self.enemies:
                if isinstance(enemy, KingSlime) and enemy.is_stomping_jump and enemy.on_ground: # KingSlime just landed from a stomp
                    # Check if player is in stomp damage range
                    distance_x = abs(self.player.rect.centerx - enemy.rect.centerx)
                    distance_y = abs(self.player.rect.bottom - enemy.rect.bottom) # Check proximity to ground
                    if distance_x <= enemy.stomp_land_damage_range and distance_y <= 10: # Player is on the ground near KingSlime
                        if not self.player.invincible:
                            print("Player hit by King Slime stomp!")
                            self.player.take_damage(enemy.stomp_aoe_damage)
                            self.player_hit_sound.play()
                            knockback_direction = 1 if self.player.rect.centerx > enemy.rect.centerx else -1
                            self.player.apply_knockback(knockback_direction, 10) # Stronger knockback from stomp


            # Player-portal collision
            for portal in pygame.sprite.spritecollide(self.player, self.portals, False):
                print(f"Player entered portal! Destination: {portal.destination_map_id}, Spawn: {portal.destination_spawn_point_id}")
                # Simulate map transition (for now, just print and maybe reposition player)
                self.player.rect.x = 50
                self.player.rect.y = self.screen_height - 100 # Reset player position
                # In a real game, this would load a new map

            # Projectile-enemy collision
            for projectile in self.projectiles:
                collided_enemies = pygame.sprite.spritecollide(projectile, self.enemies, False)
                for enemy in collided_enemies:
                    if not enemy.invincible:
                        enemy.take_damage(projectile.damage)
                        self.enemy_hit_sound.play() # Play enemy hit sound
                        # Apply knockback to enemy
                        knockback_direction = 1 if enemy.rect.centerx > projectile.rect.centerx else -1
                        enemy.apply_knockback(knockback_direction, 10)
                        if enemy.hp <= 0:
                            self.player.gain_exp(enemy.exp_reward)
                            self.player.increment_quest_kill_count(type(enemy).__name__) # type(enemy).__name__ gives 'Slime' or 'KingSlime'
                            # Find spawn point for defeated enemy
                            for sp in self.enemy_spawn_points:
                                if sp.spawned_enemy_ref == enemy:
                                    sp.is_active = False
                                    sp.current_respawn_timer = sp.respawn_delay
                                    sp.spawned_enemy_ref = None
                                    break
                            enemy.kill()
                            self.enemy_death_sound.play() # Play enemy death sound
                            print(f"{type(enemy).__name__} defeated! Player gained {enemy.exp_reward} EXP. Player EXP: {self.player.exp}")
                    projectile.kill() # Fireball disappears on hit (even if enemy is invincible)
                    break # Fireball hits only one enemy and disappears

            # Melee Attack logic
            if self.player.is_attacking:
                if self.player.attack_hitbox.width > 0:
                    for enemy in pygame.sprite.spritecollide(self.player.attack_hitbox, self.enemies, False):
                        if not enemy.invincible:
                            enemy.take_damage(self.player.attack_damage)
                            self.enemy_hit_sound.play() # Play enemy hit sound
                            knockback_direction = 1 if enemy.rect.centerx > self.player.rect.centerx else -1
                            enemy.apply_knockback(knockback_direction, 10)
                            if enemy.hp <= 0:
                                self.player.gain_exp(enemy.exp_reward)
                                self.player.increment_quest_kill_count(type(enemy).__name__) # type(enemy).__name__ gives 'Slime' or 'KingSlime'
                                # Find spawn point for defeated enemy
                                for sp in self.enemy_spawn_points:
                                    if sp.spawned_enemy_ref == enemy:
                                        sp.is_active = False
                                        sp.current_respawn_timer = sp.respawn_delay
                                        sp.spawned_enemy_ref = None
                                        break
                                enemy.kill()
                                self.enemy_death_sound.play() # Play enemy death sound
                                print(f"{type(enemy).__name__} defeated! Player gained {enemy.exp_reward} EXP. Player EXP: {self.player.exp}")
            
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


    def draw_hud(self):
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
        lines = text.split('\\n')
        y_offset = 10
        for line in lines:
            text_surface = self.dialogue_font.render(line, True, self.TEXT_COLOR)
            self.screen.blit(text_surface, (box_x + 10, box_y + y_offset))
            y_offset += text_surface.get_height() + 5


    def draw(self):
        self.screen.fill((135, 206, 235))  # Sky blue background
        self.all_sprites.draw(self.screen) # Draw all sprites
        self.player.draw(self.screen) # Draw player (and potentially debug hitboxes)
        self.draw_hud() # Draw HUD after all other elements

        if self.dialogue_active and self.current_npc:
            self.draw_dialogue_box(self.current_npc.current_dialogue)


        pygame.display.flip()

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
