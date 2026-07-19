import pygame
import random

class Slime(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_range, walk_speed, gravity, width=32, height=32, color=(0, 0, 255), hp=50, max_hp=50, contact_damage=10, exp_reward=10):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color) # Blue slime
        self.rect = self.image.get_rect(topleft=(x, y))

        self.vel_x = walk_speed
        self.vel_y = 0
        self.walk_speed = walk_speed
        self.gravity = gravity
        self.on_ground = False
        self.facing_right = True

        self.start_x = x
        self.patrol_range = patrol_range # Distance to patrol left/right from start_x

        self.hp = hp
        self.max_hp = max_hp
        self.contact_damage = contact_damage
        self.exp_reward = exp_reward

        self.invincible = False
        self.invincibility_timer = 0
        self.INVINCIBILITY_DURATION = 30 # frames

    def update(self, platforms):
        # Apply gravity
        self.vel_y += self.gravity
        if self.vel_y > 10:  # Terminal velocity
            self.vel_y = 10

        # Update position
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # Collision detection with platforms
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # Slimes should treat all platforms as solid for simplicity
                if self.vel_y > 0 and self.rect.bottom - self.vel_y <= platform.rect.top: # Falling and hit top
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0 and self.rect.top - self.vel_y >= platform.rect.bottom: # Jumping and hit bottom
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0
                elif self.vel_x > 0 and self.rect.right - self.vel_x <= platform.rect.left: # Moving right and hit left side
                    self.rect.right = platform.rect.left
                    self.vel_x = -self.vel_x # Turn around
                elif self.vel_x < 0 and self.rect.left - self.vel_x >= platform.rect.right: # Moving left and hit right side
                    self.rect.left = platform.rect.right
                    self.vel_x = -self.vel_x # Turn around

        # Patrolling logic
        if self.on_ground:
            if self.vel_x > 0 and self.rect.x > self.start_x + self.patrol_range:
                self.vel_x = -self.walk_speed
                self.facing_right = False
            elif self.vel_x < 0 and self.rect.x < self.start_x - self.patrol_range:
                self.vel_x = self.walk_speed
                self.facing_right = True

        # Update invincibility
        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False
                self.image.set_alpha(255) # Make enemy fully visible

        # Ensure HP does not go below 0
        if self.hp < 0:
            self.hp = 0


    def take_damage(self, damage):
        if not self.invincible:
            self.hp -= damage
            print(f"Slime took {damage} damage. HP: {self.hp}")
            self.start_invincibility()

    def start_invincibility(self):
        self.invincible = True
        self.invincibility_timer = self.INVINCIBILITY_DURATION
        self.image.set_alpha(128) # Visual cue for invincibility

    def apply_knockback(self, direction, strength):
        self.vel_x = direction * strength * 0.5 # Slimes move slower with knockback
        self.vel_y = -strength / 3 # Minor vertical knockback

class MiniSlime(Slime):
    def __init__(self, x, y, patrol_range, walk_speed, gravity):
        super().__init__(
            x, y,
            patrol_range=patrol_range,
            walk_speed=walk_speed * 1.2, # Mini Slime is a bit faster
            gravity=gravity,
            width=24, # Smaller
            height=24, # Smaller
            color=(0, 200, 0), # Green color
            hp=20, # Less HP
            max_hp=20,
            contact_damage=5, # Less contact damage
            exp_reward=5 # Less EXP
        )
        self.name = "MiniSlime" # For quest tracking and identification


class KingSlime(Slime): # This is now the Boss Slime
    def __init__(self, x, y, patrol_range, walk_speed, gravity):
        super().__init__(
            x, y,
            patrol_range=patrol_range,
            walk_speed=walk_speed * 0.7, # King Slime is slower
            gravity=gravity,
            width=64, # Larger
            height=64, # Larger
            color=(70, 0, 150), # Darker purple/blue
            hp=500, # Significantly more HP for boss
            max_hp=500, # Set max HP for King Slime
            contact_damage=25, # More contact damage
            exp_reward=500 # Much more EXP
        )
        self.name = "KingSlime" # For quest tracking

        # Boss States
        self.state = "IDLE" # IDLE, JUMP_ATTACK, SUMMON_MINIONS, HURT, DEFEATED
        self.target_player = None # Reference to player for advanced AI

        # Jump Attack specific attributes (enhanced from stomp)
        self.jump_attack_cooldown = 240 # frames (4 seconds)
        self.jump_attack_current_cooldown = random.randint(60, self.jump_attack_cooldown) # Random initial cooldown
        self.jump_strength = -12 # Higher jump for boss
        self.stomp_land_damage_range = 80 # pixels radius around King Slime on landing
        self.stomp_aoe_damage = 40 # Damage dealt by stomp land
        self.is_mid_air_jump_attack = False # Flag to track boss is in the air for jump attack

        # Summon Minions specific attributes
        self.summon_minions_cooldown = 360 # frames (6 seconds)
        self.summon_minions_current_cooldown = random.randint(120, self.summon_minions_cooldown)
        self.num_minions_to_summon = random.randint(1, 3)
        self.minions_spawned_callback = None # Callback to Game class to spawn minions

        # General Boss Attributes
        self.attack_damage = 0 # Handled by contact_damage and stomp_aoe_damage
        self.attack_range = 0 # Handled by contact_damage and stomp_aoe_damage
        self.minion_spawn_cooldown = 0 # Not used directly, managed by summon_minions_current_cooldown

        self.last_attack_type = None # To alternate attacks

    def set_minion_spawn_callback(self, callback):
        self.minions_spawned_callback = callback

    def update(self, platforms):
        # Store previous on_ground state before calling super.update
        was_on_ground_before_update = self.on_ground

        # Check if boss is defeated
        if self.hp <= 0 and self.state != "DEFEATED":
            self.state = "DEFEATED"
            self.vel_x = 0
            self.vel_y = 0
            # Play death animation/sound etc. (handled by Game class for now)
            return # Stop further updates for defeated boss

        super().update(platforms) # Update basic movement, gravity, and invincibility

        # State machine for boss behavior
        if self.state == "IDLE":
            if self.on_ground:
                # Decide next action based on cooldowns and strategy
                self.jump_attack_current_cooldown -= 1
                self.summon_minions_current_cooldown -= 1

                if self.jump_attack_current_cooldown <= 0 and self.last_attack_type != "JUMP_ATTACK":
                    self.state = "JUMP_ATTACK"
                    print("King Slime preparing Jump Attack!")
                elif self.summon_minions_current_cooldown <= 0 and self.last_attack_type != "SUMMON_MINIONS":
                    self.state = "SUMMON_MINIONS"
                    print("King Slime preparing Summon Minions!")
                else:
                    # If both cooldowns are active or just attacked, just patrol or stand still
                    pass # Super.update handles patrolling

        elif self.state == "JUMP_ATTACK":
            if self.on_ground and not self.is_mid_air_jump_attack: # Initiating jump
                self.vel_y = self.jump_strength
                self.on_ground = False
                self.is_mid_air_jump_attack = True
                self.vel_x = 0 # Stop horizontal movement during jump attack
            elif self.on_ground and self.is_mid_air_jump_attack: # Just landed after a jump attack
                # Trigger AoE damage here (Game class will handle player collision)
                self.is_mid_air_jump_attack = False # Reset flag
                self.jump_attack_current_cooldown = self.jump_attack_cooldown # Reset cooldown
                self.state = "IDLE" # Return to idle
                self.last_attack_type = "JUMP_ATTACK"
                print("King Slime Jump Attack landed!")

        elif self.state == "SUMMON_MINIONS":
            if self.on_ground:
                if self.minions_spawned_callback:
                    # Pass the boss's position to spawn minions near it
                    self.minions_spawned_callback(self.rect.centerx, self.rect.bottom - 20, self.num_minions_to_summon)
                self.summon_minions_current_cooldown = self.summon_minions_cooldown # Reset cooldown
                self.state = "IDLE" # Return to idle
                self.last_attack_type = "SUMMON_MINIONS"
                print(f"King Slime summoned {self.num_minions_to_summon} minions!")

        # Visual feedback for invincibility (flashing)
        if self.invincible and self.invincibility_timer % 10 < 5:
            self.image.set_alpha(128)
        else:
            self.image.set_alpha(255)

        # For KingSlime, override default patrol to be more stationary or target player
        # For now, it will simply stay still if not doing a special attack.
        # More advanced AI for movement can be added later.
        if self.on_ground and self.state == "IDLE":
            self.vel_x = 0 # KingSlime mostly stationary when idle
            # If we want it to move, we can re-enable patrol or add player-tracking
            # super().update(platforms) would re-enable basic patrol
            
        # Ensure it doesn't move when in air for jump attack
        if self.is_mid_air_jump_attack:
            self.vel_x = 0

    def take_damage(self, damage):
        if self.state == "DEFEATED":
            return # Cannot take damage if defeated

        if not self.invincible:
            self.hp -= damage
            print(f"KingSlime took {damage} damage. HP: {self.hp}")
            self.start_invincibility()
            if self.hp <= 0:
                self.state = "DEFEATED"
                print("King Slime defeated!")

    def reset_boss_state(self):
        """Resets boss HP, state, and cooldowns. Call when player leaves arena mid-fight."""
        self.hp = self.max_hp
        self.state = "IDLE"
        self.vel_x = 0
        self.vel_y = 0
        self.is_mid_air_jump_attack = False
        self.jump_attack_current_cooldown = random.randint(60, self.jump_attack_cooldown)
        self.summon_minions_current_cooldown = random.randint(120, self.summon_minions_cooldown)
        self.invincible = False
        self.invincibility_timer = 0
        print("King Slime state reset.")

