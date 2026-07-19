import pygame
import sys
from src.player import Player
from src.enemy import Slime
from src.map import Platform, Portal, GameMap

class Game:
    def __init__(self):
        pygame.init()
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
        self.font = pygame.font.Font(None, 24) # Default font, size 24

        self.HP_COLOR = (255, 0, 0) # Red
        self.MP_COLOR = (0, 0, 255) # Blue
        self.EXP_COLOR = (255, 255, 0) # Yellow
        self.TEXT_COLOR = (255, 255, 255) # White
        self.BAR_BACKGROUND_COLOR = (50, 50, 50) # Dark gray

        self.HUD_X = 10
        self.HUD_Y = 10
        self.BAR_WIDTH = 150
        self.BAR_HEIGHT = 15
        self.BAR_SPACING = 5
        self.LEVEL_OFFSET_X = self.BAR_WIDTH + 20


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

        # Define enemies
        slime1 = Slime(x=300, y=self.screen_height - 80, patrol_range=100, walk_speed=self.enemy_walk_speed, gravity=self.gravity)
        self.enemies.add(slime1)
        self.all_sprites.add(slime1)

        # Define portals
        portal1 = Portal(x=self.screen_width - 80, y=self.screen_height - 100, width=60, height=60, destination_map_id="map_2", destination_spawn_point_id="entry_1")
        self.portals.add(portal1)
        self.all_sprites.add(portal1)

        self.game_map = GameMap(self.platforms.sprites(), self.enemies.sprites(), self.portals.sprites())


    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            self.player.handle_input(event) # Pass events to player for movement/attack

    def update(self):
        self.all_sprites.update(self.platforms.sprites()) # Pass platforms for collision

        # Player-enemy collision (contact damage)
        for enemy in pygame.sprite.spritecollide(self.player, self.enemies, False):
            if not self.player.invincible:
                self.player.take_damage(enemy.contact_damage)
                # Apply knockback
                knockback_direction = 1 if self.player.rect.centerx > enemy.rect.centerx else -1
                self.player.apply_knockback(knockback_direction, 5)

        # Player-portal collision
        for portal in pygame.sprite.spritecollide(self.player, self.portals, False):
            print(f"Player entered portal! Destination: {portal.destination_map_id}, Spawn: {portal.destination_spawn_point_id}")
            # Simulate map transition (for now, just print and maybe reposition player)
            self.player.rect.x = 50
            self.player.rect.y = self.screen_height - 100 # Reset player position
            # In a real game, this would load a new map

        # Attack logic
        if self.player.is_attacking:
            # Check for collisions only when attack hitbox is active
            if self.player.attack_hitbox.width > 0: # Check if hitbox is not empty
                for enemy in pygame.sprite.spritecollide(self.player.attack_hitbox, self.enemies, False):
                    if not enemy.invincible:
                        enemy.take_damage(self.player.attack_damage)
                        # Apply knockback to enemy
                        knockback_direction = 1 if enemy.rect.centerx > self.player.rect.centerx else -1
                        enemy.apply_knockback(knockback_direction, 10)
                        if enemy.hp <= 0:
                            self.player.gain_exp(enemy.exp_reward)
                            enemy.kill() # Remove defeated enemy
                            print(f"Slime defeated! Player gained {enemy.exp_reward} EXP. Player EXP: {self.player.exp}")
                            # Respawn logic would go here, or handled by a separate enemy manager

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
        if self.player.exp_to_next_level > 0: # Avoid division by zero if exp_to_next_level is 0
            exp_ratio = (self.player.exp / self.player.exp_to_next_level)
        exp_bar_fill = exp_ratio * self.BAR_WIDTH
        pygame.draw.rect(self.screen, self.BAR_BACKGROUND_COLOR, (exp_bar_x, exp_bar_y, self.BAR_WIDTH, self.BAR_HEIGHT))
        pygame.draw.rect(self.screen, self.EXP_COLOR, (exp_bar_x, exp_bar_y, exp_bar_fill, self.BAR_HEIGHT))
        exp_text = self.font.render(f"EXP: {self.player.exp}/{self.player.exp_to_next_level}", True, self.TEXT_COLOR)
        self.screen.blit(exp_text, (exp_bar_x + self.BAR_WIDTH + self.BAR_SPACING, exp_bar_y))

        # Level Display
        level_text = self.font.render(f"Level: {self.player.level}", True, self.TEXT_COLOR)
        self.screen.blit(level_text, (self.HUD_X + self.LEVEL_OFFSET_X, self.HUD_Y + (self.BAR_HEIGHT + self.BAR_SPACING) * 3))


    def draw(self):
        self.screen.fill((135, 206, 235))  # Sky blue background
        self.all_sprites.draw(self.screen) # Draw all sprites
        self.player.draw(self.screen) # Draw player (and potentially debug hitboxes)
        self.draw_hud() # Draw HUD after all other elements

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(60) # 60 FPS

        pygame.quit()
        sys.exit()
