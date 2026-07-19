import pygame

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


class KingSlime(Slime): # Inherit from Slime
    def __init__(self, x, y, patrol_range, walk_speed, gravity):
        super().__init__(
            x, y,
            patrol_range=patrol_range,
            walk_speed=walk_speed * 0.7, # King Slime is slower
            gravity=gravity,
            width=64, # Larger
            height=64, # Larger
            color=(70, 0, 150), # Darker purple/blue
            hp=200, # More HP
            max_hp=200, # Set max HP for King Slime
            contact_damage=25, # More contact damage
            exp_reward=200 # More EXP
        )
        self.name = "KingSlime" # For quest tracking

        # Stomp Attack specific attributes
        self.stomp_cooldown = 180 # frames (3 seconds)
        self.stomp_current_cooldown = self.stomp_cooldown
        self.stomp_jump_strength = -8 # A distinct jump for stomp
        self.stomp_land_damage_range = 70 # pixels radius around King Slime on landing
        self.is_stomping_jump = False # Flag to track stomp jump
        self.stomp_aoe_damage = 30 # Damage dealt by stomp land


    def update(self, platforms):
        # Store previous on_ground state before calling super.update
        was_on_ground_before_update = self.on_ground

        super().update(platforms) # Update basic movement, gravity, and invincibility

        # Stomp attack logic
        if self.on_ground and not was_on_ground_before_update: # Just landed
            if self.is_stomping_jump:
                # Trigger AoE damage here (Game class will handle player collision)
                self.is_stomping_jump = False
                self.stomp_current_cooldown = self.stomp_cooldown # Reset cooldown after landing

        if self.stomp_current_cooldown > 0:
            self.stomp_current_cooldown -= 1

        if self.stomp_current_cooldown <= 0 and self.on_ground and not self.is_stomping_jump:
            # Initiate stomp jump
            self.vel_y = self.stomp_jump_strength
            self.on_ground = False
            self.is_stomping_jump = True
            self.vel_x = 0 # Stop horizontal movement during stomp jump
            print("King Slime initiating stomp jump!")
