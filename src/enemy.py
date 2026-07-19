import pygame

class Slime:
    def __init__(self, x, y, patrol_start_x, patrol_end_x):
        self.initial_x = x
        self.initial_y = y
        self.width = 32
        self.height = 32
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = (0, 200, 0) # Green

        self.hp = 30
        self.maxHp = 30
        self.contactDamage = 5
        self.expReward = 10

        self.patrolStart_x = patrol_start_x
        self.patrolEnd_x = patrol_end_x
        self.walkSpeed = 2
        self.currentDirection = 1 # 1 for right, -1 for left

        self.gravity = 0.5
        self.dy = 0 # Vertical velocity

        self.is_active = True
        self.isGrounded = False # Similar to player, for gravity application
        self.respawnTimer = 0
        self.respawnCooldown = 300 # frames (e.g., 5 seconds at 60 FPS)
        self.last_hit_by_player_attack_id = None # To prevent multiple EXP for one attack

    def update(self):
        if self.is_active:
            # Apply gravity
            if not self.isGrounded:
                self.dy += self.gravity
                if self.dy > 10: # Cap falling speed
                    self.dy = 10

            # Patrol movement
            # Store original x for collision resolution
            original_x = self.rect.x
            self.rect.x += self.walkSpeed * self.currentDirection

            # Check patrol boundaries
            if self.currentDirection == 1 and self.rect.right > self.patrolEnd_x:
                self.currentDirection = -1
            elif self.currentDirection == -1 and self.rect.left < self.patrolStart_x:
                self.currentDirection = 1

            # Vertical movement is applied, collision with platforms will adjust dy and isGrounded
            self.rect.y += self.dy

        else: # If not active (defeated)
            self.respawnTimer -= 1
            if self.respawnTimer <= 0:
                self.respawn()

    def take_damage(self, damage):
        if self.is_active:
            self.hp -= damage
            # print(f"Slime took {damage} damage. HP: {self.hp}") # For debugging
            if self.hp <= 0:
                self.die()
                return self.expReward # Return EXP reward if defeated
        return 0

    def die(self):
        self.is_active = False
        self.respawnTimer = self.respawnCooldown
        # Move off-screen or make non-collidable
        self.rect.x = -1000 # Off-screen
        self.rect.y = -1000
        # print("Slime defeated!") # For debugging

    def respawn(self):
        self.is_active = True
        self.hp = self.maxHp
        self.rect.x = self.initial_x
        self.rect.y = self.initial_y
        self.currentDirection = 1 # Reset direction
        self.dy = 0 # Reset vertical velocity
        self.isGrounded = False # Ensure gravity applies on respawn
        self.last_hit_by_player_attack_id = None # Reset for new life
        # print("Slime respawned!") # For debugging

    def draw(self, screen):
        if self.is_active:
            pygame.draw.rect(screen, self.color, self.rect)
