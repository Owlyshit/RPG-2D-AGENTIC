import pygame

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, walk_speed, jump_strength, gravity):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill((255, 0, 0))  # Red player
        self.rect = self.image.get_rect(topleft=(x, y))

        self.vel_x = 0
        self.vel_y = 0
        self.walk_speed = walk_speed
        self.jump_strength = jump_strength
        self.gravity = gravity
        self.on_ground = False
        self.facing_right = True

        self.hp = 100
        self.max_hp = 100
        self.mp = 50
        self.max_mp = 50
        self.attack_damage = 20
        self.exp = 0
        self.level = 1
        self.exp_to_next_level = 100

        self.is_attacking = False
        self.attack_cooldown = 0
        self.ATTACK_COOLDOWN_TIME = 30 # frames
        self.attack_hitbox = pygame.Rect(0, 0, 0, 0)

        self.invincible = False
        self.invincibility_timer = 0
        self.INVINCIBILITY_DURATION = 60 # frames

        # Quest tracking
        # Stores {quest_id: {'accepted': True/False, 'completed': True/False, 'current_count': int, 'quest_obj': Quest_object}}
        self.active_quests = {}


    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.on_ground:
                self.jump()
            if event.key == pygame.K_j and not self.is_attacking and self.attack_cooldown <= 0:
                self.start_attack()

    def jump(self):
        self.vel_y = self.jump_strength
        self.on_ground = False

    def start_attack(self):
        self.is_attacking = True
        self.attack_cooldown = self.ATTACK_COOLDOWN_TIME
        # Define attack hitbox relative to player
        if self.facing_right:
            self.attack_hitbox = pygame.Rect(self.rect.right, self.rect.centery - 10, 30, 20)
        else:
            self.attack_hitbox = pygame.Rect(self.rect.left - 30, self.rect.centery - 10, 30, 20)

    def update(self, platforms):
        # Handle horizontal movement
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        if not self.is_attacking: # Cannot move while attacking (simple version)
            if keys[pygame.K_a]:
                self.vel_x = -self.walk_speed
                self.facing_right = False
            if keys[pygame.K_d]:
                self.vel_x = self.walk_speed
                self.facing_right = True

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
                if platform.is_one_way:
                    # Only collide if falling onto it
                    if self.vel_y > 0 and self.rect.bottom - self.vel_y <= platform.rect.top:
                        self.rect.bottom = platform.rect.top
                        self.vel_y = 0
                        self.on_ground = True
                else:
                    # Solid platform collision
                    if self.vel_y > 0 and self.rect.bottom - self.vel_y <= platform.rect.top: # Falling and hit top
                        self.rect.bottom = platform.rect.top
                        self.vel_y = 0
                        self.on_ground = True
                    elif self.vel_y < 0 and self.rect.top - self.vel_y >= platform.rect.bottom: # Jumping and hit bottom
                        self.rect.top = platform.rect.bottom
                        self.vel_y = 0
                    elif self.vel_x > 0 and self.rect.right - self.vel_x <= platform.rect.left: # Moving right and hit left side
                        self.rect.right = platform.rect.left
                        self.vel_x = 0
                    elif self.vel_x < 0 and self.rect.left - self.vel_x >= platform.rect.right: # Moving left and hit right side
                        self.rect.left = platform.rect.right
                        self.vel_x = 0

        # Update attack state
        if self.is_attacking:
            self.attack_cooldown -= 1
            if self.attack_cooldown <= (self.ATTACK_COOLDOWN_TIME - 15): # Attack hitbox active for a duration
                self.attack_hitbox = pygame.Rect(0,0,0,0) # Deactivate hitbox
            if self.attack_cooldown <= 0:
                self.is_attacking = False
                self.attack_cooldown = 0

        # Update invincibility
        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False
                self.image.set_alpha(255) # Make player fully visible

        # Ensure HP does not go below 0
        if self.hp < 0:
            self.hp = 0
        # Ensure MP does not go below 0 or above max
        if self.mp < 0:
            self.mp = 0
        if self.mp > self.max_mp:
            self.mp = self.max_mp

    def take_damage(self, damage):
        if not self.invincible:
            self.hp -= damage
            print(f"Player took {damage} damage. HP: {self.hp}")
            self.start_invincibility()

    def start_invincibility(self):
        self.invincible = True
        self.invincibility_timer = self.INVINCIBILITY_DURATION
        self.image.set_alpha(128) # Visual cue for invincibility

    def apply_knockback(self, direction, strength):
        self.vel_x = direction * strength
        self.vel_y = -strength / 2 # Minor vertical knockback

    def gain_exp(self, amount):
        self.exp += amount
        # Basic level up logic (can be expanded)
        while self.exp >= self.exp_to_next_level: # Use while loop for multiple level-ups
            self.level += 1
            self.exp -= self.exp_to_next_level # Carry over excess EXP
            self.exp_to_next_level = self.level * 100 + (self.level * 50) # New EXP requirement (slightly increasing)
            self.max_hp += 10
            self.hp = self.max_hp # Heal on level up
            self.max_mp += 5 # Increase max MP
            self.mp = self.max_mp # Restore MP on level up
            self.attack_damage += 5
            print(f"Player Leveled Up! Level: {self.level}, HP: {self.hp}/{self.max_hp}, MP: {self.mp}/{self.max_mp}, Attack: {self.attack_damage}")
        
        # Ensure exp doesn't exceed current level's exp_to_next_level after gaining some
        if self.exp > self.exp_to_next_level:
            self.exp = self.exp_to_next_level - 1 # Prevent exp from showing above max on HUD until next level


    def accept_quest(self, quest_obj):
        if quest_obj.id not in self.active_quests:
            self.active_quests[quest_obj.id] = {
                'accepted': True,
                'completed': False,
                'current_count': 0,
                'quest_obj': quest_obj
            }
            print(f"Quest accepted: {quest_obj.name}")
            return True
        return False

    def increment_quest_kill_count(self, enemy_type):
        for q_id, quest_status in self.active_quests.items():
            quest_obj = quest_status['quest_obj']
            if not quest_status['completed'] and \
               quest_obj.objective_type == 'kill' and \
               quest_obj.objective_target == enemy_type:
                quest_status['current_count'] += 1
                print(f"Quest '{quest_obj.name}' progress: {quest_status['current_count']}/{quest_obj.objective_count}")
                if quest_status['current_count'] >= quest_obj.objective_count:
                    quest_status['completed'] = True
                    print(f"Quest '{quest_obj.name}' completed! Return to NPC.")

    def get_quest_status(self, quest_id):
        return self.active_quests.get(quest_id, {'accepted': False, 'completed': False, 'current_count': 0, 'quest_obj': None})

    def turn_in_quest(self, quest_id):
        if quest_id in self.active_quests and self.active_quests[quest_id]['completed']:
            quest_obj = self.active_quests[quest_id]['quest_obj']
            self.gain_exp(quest_obj.reward_exp)
            print(f"Quest '{quest_obj.name}' turned in. Gained {quest_obj.reward_exp} EXP.")
            if quest_obj.is_repeatable:
                self.active_quests[quest_id]['completed'] = False
                self.active_quests[quest_id]['current_count'] = 0
                print(f"Quest '{quest_obj.name}' reset for repeatability.")
            else:
                del self.active_quests[quest_id] # Remove non-repeatable quest
            return True
        return False


    def draw(self, screen):
        screen.blit(self.image, self.rect)
        if self.is_attacking:
            # For debugging, draw attack hitbox
            pygame.draw.rect(screen, (255, 255, 0), self.attack_hitbox, 2)
