import pygame
import sys
from src.player import Player
from src.enemy import Slime
from src.map import Platform, Portal, Map
from src.npc import NPC # New import
from src.quest import Quest # New import

class Game:
    def __init__(self):
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("MapleStory 2D RPG")
        self.clock = pygame.time.Clock()
        self.running = True

        self.player = Player(100, 400) # Initial player position

        self.maps = {}
        self._create_sample_maps()
        self.current_map = self.maps[1] # Start with map 1
        self._teleport_player(self.current_map.spawn_point_x, self.current_map.spawn_point_y)

    def _create_sample_maps(self):
        # Quest Definition
        slime_quest = Quest(
            quest_id="slime_hunt_1",
            title="Slime Hunter",
            description="Defeat 5 mischievous slimes for the villager.",
            objective_type="DEFEAT_ENEMY",
            target_data={'enemy_type': 'Slime', 'count': 5},
            reward_exp=50
        )

        # Map 1
        map1 = Map(1, self.screen_width, self.screen_height, spawn_x=100, spawn_y=400)
        # Ground
        map1.add_platform(Platform(0, self.screen_height - 50, self.screen_width, 50))
        # Floating platforms
        map1.add_platform(Platform(200, 350, 150, 20))
        map1.add_platform(Platform(450, 250, 100, 20, isOneWay=True))
        map1.add_platform(Platform(600, 150, 100, 20))

        # Slime on map 1
        map1.add_enemy(Slime(300, self.screen_height - 82, 250, 400))
        map1.add_enemy(Slime(650, self.screen_height - 82, 600, 750))
        map1.add_enemy(Slime(100, self.screen_height - 82, 50, 150))
        map1.add_enemy(Slime(400, self.screen_height - 82, 350, 450))
        map1.add_enemy(Slime(500, 118, 480, 580)) # Slime on a higher platform

        # NPC on map 1
        map1.add_npc(NPC(50, self.screen_height - 98, "Villager", slime_quest)) # New NPC
        
        # Portal to Map 2
        map1.add_portal(Portal(700, self.screen_height - 150, 50, 100, 2, 50, 400))
        self.maps[1] = map1

        # Map 2
        map2 = Map(2, self.screen_width, self.screen_height, spawn_x=50, spawn_y=400)
        # Ground
        map2.add_platform(Platform(0, self.screen_height - 50, self.screen_width, 50))
        # Floating platforms
        map2.add_platform(Platform(150, 300, 100, 20))
        map2.add_platform(Platform(300, 200, 100, 20, isOneWay=True))

        # Slime on map 2
        map2.add_enemy(Slime(200, self.screen_height - 82, 150, 250))

        # Portal back to Map 1
        map2.add_portal(Portal(self.screen_width - 100, self.screen_height - 150, 50, 100, 1, 650, 400))
        self.maps[2] = map2


    def _teleport_player(self, x, y):
        self.player.rect.x = x
        self.player.rect.y = y
        self.player.dy = 0 # Reset vertical speed on teleport
        self.player.isGrounded = False # Assume not grounded until collision check

    # Collision resolution for player
    def _resolve_player_collisions(self):
        # Store player's intended next position
        player_next_x = self.player.rect.x + self.player.dx
        player_next_y = self.player.rect.y + self.player.dy

        # Check horizontal collisions first
        player_rect_x_only = pygame.Rect(player_next_x, self.player.rect.y, self.player.width, self.player.height)
        for platform in self.current_map.platforms:
            if not platform.isOneWay and player_rect_x_only.colliderect(platform.rect):
                if self.player.dx > 0: # Moving right
                    player_next_x = platform.rect.left - self.player.width
                elif self.player.dx < 0: # Moving left
                    player_next_x = platform.rect.right
                self.player.dx = 0 # Stop horizontal movement

        self.player.rect.x = player_next_x # Update player x after horizontal collision

        # Reset isGrounded before vertical collision check
        self.player.isGrounded = False

        # Check vertical collisions
        player_rect_y_only = pygame.Rect(self.player.rect.x, player_next_y, self.player.width, self.player.height)
        for platform in self.current_map.platforms:
            if player_rect_y_only.colliderect(platform.rect):
                if self.player.dy > 0: # Moving downwards (falling)
                    # Only land on one-way platforms if player is above it
                    if not platform.isOneWay or self.player.rect.bottom <= platform.rect.top:
                        player_next_y = platform.rect.top - self.player.height
                        self.player.dy = 0
                        self.player.isGrounded = True
                elif self.player.dy < 0: # Moving upwards (jumping)
                    if not platform.isOneWay: # Only solid platforms block upward movement
                        player_next_y = platform.rect.bottom
                        self.player.dy = 0

        self.player.rect.y = player_next_y # Update player y after vertical collision

    # Collision resolution for enemies
    def _resolve_enemy_collisions(self, enemy):
        if not enemy.is_active: return

        # Store enemy's intended next position
        enemy_next_x = enemy.rect.x + enemy.walkSpeed * enemy.currentDirection
        enemy_next_y = enemy.rect.y + enemy.dy

        # Check horizontal collisions first (for patrol boundaries)
        enemy_rect_x_only = pygame.Rect(enemy_next_x, enemy.rect.y, enemy.width, enemy.height)
        for platform in self.current_map.platforms:
            # Enemies turn around if they hit a non-one-way platform horizontally
            if not platform.isOneWay and enemy_rect_x_only.colliderect(platform.rect):
                enemy.currentDirection *= -1 # Reverse direction
                enemy_next_x = enemy.rect.x # Revert x to previous position to avoid getting stuck
                break # Only handle one horizontal collision per enemy per frame

        enemy.rect.x = enemy_next_x # Update enemy x after horizontal collision

        # Reset isGrounded before vertical collision check
        enemy.isGrounded = False

        # Check vertical collisions
        enemy_rect_y_only = pygame.Rect(enemy.rect.x, enemy_next_y, enemy.width, enemy.height)
        for platform in self.current_map.platforms:
            if enemy_rect_y_only.colliderect(platform.rect):
                if enemy.dy > 0: # Moving downwards (falling)
                    # Enemies treat all platforms as solid for falling onto
                    enemy_next_y = platform.rect.top - enemy.height
                    enemy.dy = 0
                    enemy.isGrounded = True
                elif enemy.dy < 0: # Moving upwards (should not happen for slime due to gravity only)
                    enemy_next_y = platform.rect.bottom
                    enemy.dy = 0

        enemy.rect.y = enemy_next_y # Update enemy y after vertical collision

    def _handle_player_enemy_contact_damage(self):
        for enemy in self.current_map.enemies:
            if enemy.is_active and self.player.is_alive() and self.player.rect.colliderect(enemy.rect):
                self.player.take_damage(enemy.contactDamage)
                # Simple knockback
                if self.player.rect.centerx < enemy.rect.centerx:
                    self.player.rect.x -= 10 # Knock left
                else:
                    self.player.rect.x += 10 # Knock right
                self.player.dy = -5 # Knock up

    def _handle_player_attack_enemy_collision(self):
        player_attack_rect = self.player.get_attack_rect()
        if player_attack_rect:
            # Generate a unique ID for this attack instance to prevent multiple EXP/damage per attack
            attack_id = id(player_attack_rect) # Using ID of the rect as a unique identifier for this attack animation

            for enemy in self.current_map.enemies:
                if enemy.is_active and player_attack_rect.colliderect(enemy.rect):
                    # Check if this enemy has already been hit by this specific attack instance
                    if not hasattr(enemy, 'last_hit_by_player_attack_id') or \
                       enemy.last_hit_by_player_attack_id != attack_id:
                        exp_gained = enemy.take_damage(self.player.attackPower)
                        if exp_gained > 0:
                            self.player.gain_exp(exp_gained)
                            # Update quest progress when enemy is defeated
                            # Assuming 'Slime' for enemy_type for now. This could be made dynamic.
                            self.player.update_quest_progress('ENEMY_DEFEATED', {'enemy_type': 'Slime'})
                        enemy.last_hit_by_player_attack_id = attack_id # Mark as hit by this attack

    def _handle_portal_collision(self):
        for portal in self.current_map.portals:
            if self.player.rect.colliderect(portal.rect):
                print(f"Entering portal to Map {portal.destinationMapId}")
                self.current_map = self.maps[portal.destinationMapId]
                self._teleport_player(portal.destinationSpawnPoint_x, portal.destinationSpawnPoint_y)
                # Reset any pending attack/damage states on map transition
                self.player.isAttacking = False
                self.player.attackTimer = 0
                return # Only one portal transition per frame

    def _check_out_of_bounds(self):
        # Player falls off bottom of the map
        if self.player.rect.top > self.screen_height:
            print("Player fell off the map!")
            self._teleport_player(self.current_map.spawn_point_x, self.current_map.spawn_point_y)
            self.player.hp = self.player.maxHp # Full HP on respawn

        # Clamp player to map horizontal boundaries
        self.player.rect.x = max(0, min(self.player.rect.x, self.current_map.width - self.player.width))


    def run(self):
        while self.running:
            # Handle user input (key held down)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]:
                self.player.move_left()
            if keys[pygame.K_d]:
                self.player.move_right()

            # Handle single key press events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.player.jump()
                    if event.key == pygame.K_j: # Attack key
                        self.player.attack()
                    if event.key == pygame.K_e: # Interact key
                        # Check for NPC interaction
                        for npc in self.current_map.npcs:
                            if self.player.rect.colliderect(npc.rect.inflate(50, 50)): # Inflate for easier interaction
                                npc.interact(self.player)
                                break # Interact with only one NPC at a time


            # --- Update ---
            # Player update (gravity, attack timer, movement applied)
            self.player.update()
            
            # NPC update (dialogue state)
            for npc in self.current_map.npcs:
                npc.update(self.player)
                # Check if player is near NPC for interaction prompt
                if self.player.rect.colliderect(npc.rect.inflate(50, 50)): # Inflate for easier interaction
                    npc.show_prompt = True
                else:
                    npc.show_prompt = False


            for enemy in self.current_map.enemies:
                enemy.update()
            
            # Resolve collisions based on updated dx, dy
            self._resolve_player_collisions()
            for enemy in self.current_map.enemies:
                self._resolve_enemy_collisions(enemy)

            # Handle interactions after all positions are finalized
            self._handle_player_enemy_contact_damage()
            self._handle_player_attack_enemy_collision()
            self._handle_portal_collision()
            self._check_out_of_bounds()
            
            # Ensure player is alive, otherwise respawn (death condition)
            if not self.player.is_alive():
                print("Player defeated!")
                self._teleport_player(self.current_map.spawn_point_x, self.current_map.spawn_point_y) # Respawn
                self.player.hp = self.player.maxHp # Restore HP
                self.player.isAttacking = False # Clear any attacking state
                self.player.attackTimer = 0


            # --- Render ---
            self.current_map.draw(self.screen) # Draw map background and platforms
            self.player.draw(self.screen)
            for enemy in self.current_map.enemies:
                enemy.draw(self.screen)
            for npc in self.current_map.npcs: # Draw NPCs
                npc.draw(self.screen)


            # Display player HP/EXP (simple text)
            font = pygame.font.Font(None, 24)
            hp_text = font.render(f"HP: {self.player.hp}/{self.player.maxHp}", True, (0, 0, 0))
            exp_text = font.render(f"EXP: {self.player.exp} (Lvl {self.player.level})", True, (0, 0, 0))
            map_text = font.render(f"Map: {self.current_map.map_id}", True, (0, 0, 0))
            self.screen.blit(hp_text, (5, 5))
            self.screen.blit(exp_text, (5, 30))
            self.screen.blit(map_text, (self.screen_width - map_text.get_width() - 5, 5))

            # Display active quests
            y_offset = 60
            for quest in self.player.active_quests:
                quest_title = quest.title
                if quest.is_completed and not quest.is_reward_claimed:
                    quest_status = "(Completed - Claim Reward!)"
                elif quest.is_completed and quest.is_reward_claimed:
                    quest_status = "(Claimed)"
                elif quest.is_active:
                    quest_status = f"({quest.get_progress_string()})"
                else:
                    quest_status = "(Inactive)"

                quest_text = font.render(f"{quest_title}: {quest_status}", True, (0, 0, 0))
                self.screen.blit(quest_text, (5, y_offset))
                y_offset += 25


            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()
