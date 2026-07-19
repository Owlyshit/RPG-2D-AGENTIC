import pygame

class Slime(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_range, walk_speed, gravity):
        super().__init__()
        self.image = pygame.Surface((32, 32))
        self.image.fill((0, 0, 255)) # Blue slime
        self.rect = self.image.get_rect(topleft=(x, y))

        self.vel_x = walk_speed
        self.vel_y = 0
        self.walk_speed = walk_speed
        self.gravity = gravity
        self.on_ground = False
        self.facing_right = True

        self.start_x = x
        self.patrol_range = patrol_range # Distance to patrol left/right from start_x

        self.hp = 50
        self.max_hp = 50
        self.contact_damage = 10
        self.exp_reward = 10

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
