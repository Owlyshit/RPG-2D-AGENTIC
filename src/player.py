import pygame
from src.skill import Fireball # Import Fireball
from src.item import HealthPotion, ManaPotion # Import potion items

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
        self.ATTACK_COOLDOWN_TIME = 30 # frames (0.5 seconds at 60 FPS)
        self.attack_hitbox = pygame.Rect(0, 0, 0, 0)

        # Attack Animation attributes
        self.attack_animation_timer = 0
        self.attack_animation_duration = 15 # frames, should be <= ATTACK_COOLDOWN_TIME
        self.default_color = (255, 0, 0)
        self.attack_color = (255, 165, 0) # Orange during attack

        self.invincible = False
        self.invincibility_timer = 0
        self.INVINCIBILITY_DURATION = 60 # frames

        # Double Jump attribute
        self.can_double_jump = False

        # Magic Skill attributes (Fireball)
        self.magic_damage = 30
        self.fireball_mp_cost = 10
        self.fireball_cooldown = 60 # frames (1 second)
        self.fireball_current_cooldown = 0
        self.fireball_speed = 8

        # Dash attributes
        self.is_dashing = False
        self.dash_duration = 15 # frames
        self.dash_speed = 15
        self.dash_cooldown = 90 # frames (1.5 seconds)
        self.dash_current_cooldown = 0
        self.dash_invincibility_duration = 15 # frames, same as dash_duration

        # Quest tracking
        self.active_quests = {}

        # Inventory and Consumables
        self.inventory = {
            "health_potion": 5,
            "mana_potion": 3,
        } # item_id: quantity
        self.POTION_MAX_STACK = 99
        self.potion_cooldown_timer = 0
        self.POTION_COOLDOWN_DURATION = 60 # frames (1 second)


    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if self.on_ground:
                    self.jump()
                    self.can_double_jump = True # Allow double jump after first jump
                elif self.can_double_jump:
                    self.jump() # Perform second jump
                    self.can_double_jump = False # Consume double jump
            if event.key == pygame.K_j and not self.is_attacking and self.attack_cooldown <= 0 and not self.is_dashing:
                self.start_attack()
            if event.key == pygame.K_k and not self.is_dashing: # Can't cast while dashing
                return self.cast_fireball() # Return fireball if cast successfully
            if event.key == pygame.K_LSHIFT and self.dash_current_cooldown <= 0:
                self.start_dash()
            if event.key == pygame.K_1: # Use Health Potion
                return self.use_health_potion()
            if event.key == pygame.K_2: # Use Mana Potion
                return self.use_mana_potion()
        return None # No fireball cast or no relevant key pressed

    def jump(self):
        self.vel_y = self.jump_strength
        self.on_ground = False

    def start_attack(self):
        self.is_attacking = True
        self.attack_cooldown = self.ATTACK_COOLDOWN_TIME
        self.attack_animation_timer = self.attack_animation_duration # Start animation timer
        # Define attack hitbox relative to player
        if self.facing_right:
            self.attack_hitbox = pygame.Rect(self.rect.right, self.rect.centery - 10, 30, 20)
        else:
            self.attack_hitbox = pygame.Rect(self.rect.left - 30, self.rect.centery - 10, 30, 20)

    def cast_fireball(self):
        if self.mp >= self.fireball_mp_cost and self.fireball_current_cooldown <= 0:
            self.mp -= self.fireball_mp_cost
            self.fireball_current_cooldown = self.fireball_cooldown
            
            # Fireball spawn position
            fb_x = self.rect.centerx + (self.rect.width // 2 * (1 if self.facing_right else -1))
            fb_y = self.rect.centery

            fireball = Fireball(fb_x, fb_y, (1 if self.facing_right else -1), self.magic_damage, self.fireball_speed)
            print(f"Player cast Fireball! MP: {self.mp}/{self.max_mp}")
            return fireball
        elif self.mp < self.fireball_mp_cost:
            print("Not enough MP to cast Fireball!")
        elif self.fireball_current_cooldown > 0:
            print("Fireball is on cooldown!")
        return None

    def start_dash(self):
        self.is_dashing = True
        self.dash_current_cooldown = self.dash_cooldown
        self.start_invincibility(duration=self.dash_invincibility_duration) # Gain invincibility during dash
        print("Player dashing!")


    def update(self, platforms):
        # Handle dash state
        if self.is_dashing:
            self.vel_x = self.dash_speed * (1 if self.facing_right else -1)
            self.vel_y = 0 # No vertical movement during dash
            # Dash duration timer
            self.dash_duration -= 1
            if self.dash_duration <= 0:
                self.is_dashing = False
                self.dash_duration = 15 # Reset for next dash
                self.vel_x = 0 # Stop horizontal dash movement
        else: # Normal horizontal movement if not dashing
            keys = pygame.key.get_pressed()
            self.vel_x = 0
            if not self.is_attacking: # Cannot move while attacking (simple version)
                if keys[pygame.K_a]:
                    self.vel_x = -self.walk_speed
                    self.facing_right = False
                if keys[pygame.K_d]:
                    self.vel_x = self.walk_speed
                    self.facing_right = True

        # Apply gravity if not dashing and not on ground
        if not self.is_dashing:
            self.vel_y += self.gravity
            if self.vel_y > 10:  # Terminal velocity
                self.vel_y = 10

        # Separate X and Y movement for collision detection
        # Handle X movement and collision
        self.rect.x += self.vel_x
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if not platform.is_one_way: # Only solid platforms block X movement
                    if self.vel_x > 0: # Moving right, hit left side of platform
                        self.rect.right = platform.rect.left
                    elif self.vel_x < 0: # Moving left, hit right side of platform
                        self.rect.left = platform.rect.right
                    self.vel_x = 0 # Stop horizontal movement if collided with wall
                    if self.is_dashing: # If dashing into a wall, stop dash prematurely
                        self.is_dashing = False
                        self.dash_duration = 15 # Reset for next dash


        # Handle Y movement and collision
        was_on_ground = self.on_ground # Store previous on_ground state
        self.on_ground = False # Assume not on ground until collision confirms
        self.rect.y += self.vel_y

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if platform.is_one_way:
                    keys = pygame.key.get_pressed() # Re-get keys for this frame if needed
                    # Only collide if falling onto it AND not pressing down
                    if self.vel_y >= 0 and self.rect.bottom - self.vel_y <= platform.rect.top + 5 and not keys[pygame.K_s]:
                        self.rect.bottom = platform.rect.top
                        self.vel_y = 0
                        self.on_ground = True
                    # If player jumps up through a one-way platform, don't collide, let it pass through.
                    # If player is pressing down, they should fall through. This is handled by the `not keys[pygame.K_s]` condition above.
                else: # Solid platform
                    # Collision from top (falling onto it)
                    if self.vel_y > 0 and self.rect.bottom - self.vel_y <= platform.rect.top + 5:
                        self.rect.bottom = platform.rect.top
                        self.vel_y = 0
                        self.on_ground = True
                    # Collision from bottom (jumping into it)
                    elif self.vel_y < 0 and self.rect.top - self.vel_y >= platform.rect.bottom - 5:
                        self.rect.top = platform.rect.bottom
                        self.vel_y = 0

        # Reset double jump if landed
        if self.on_ground and not was_on_ground:
            self.can_double_jump = True # Reset ability to double jump when on ground


        # Update attack state
        if self.is_attacking:
            self.attack_cooldown -= 1
            self.attack_animation_timer -= 1 # Decrement animation timer
            if self.attack_animation_timer <= 0: # Deactivate hitbox after animation
                self.attack_hitbox = pygame.Rect(0,0,0,0)
            if self.attack_cooldown <= 0:
                self.is_attacking = False
                self.attack_cooldown = 0
                self.attack_animation_timer = 0 # Reset animation timer

        # Update magic cooldown
        if self.fireball_current_cooldown > 0:
            self.fireball_current_cooldown -= 1

        # Update dash cooldown
        if self.dash_current_cooldown > 0 and not self.is_dashing: # Only decrement if not currently dashing
            self.dash_current_cooldown -= 1

        # Update invincibility
        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False
                self.image.set_alpha(255) # Make player fully visible
        
        # Update potion cooldown
        if self.potion_cooldown_timer > 0:
            self.potion_cooldown_timer -= 1

        # Ensure HP does not go below 0 or above max
        if self.hp < 0:
            self.hp = 0
        elif self.hp > self.max_hp:
            self.hp = self.max_hp
        # Ensure MP does not go below 0 or above max
        if self.mp < 0:
            self.mp = 0
        elif self.mp > self.max_mp:
            self.mp = self.max_mp

    def take_damage(self, damage):
        if not self.invincible:
            self.hp -= damage
            print(f"Player took {damage} damage. HP: {self.hp}")
            self.start_invincibility()

    def start_invincibility(self, duration=None):
        if duration is None:
            duration = self.INVINCIBILITY_DURATION
        # If new invincibility is longer, or player is not invincible, set it
        if not self.invincible or duration > self.invincibility_timer:
            self.invincible = True
            self.invincibility_timer = duration
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

    def add_item(self, item_instance, quantity=1):
        item_id = item_instance.item_id
        current_quantity = self.inventory.get(item_id, 0)
        if current_quantity >= item_instance.stack_limit:
            print(f"Inventory for {item_instance.name} is full!")
            return False # Cannot add, stack is full
        
        # Add item, respecting stack limit
        can_add = min(quantity, item_instance.stack_limit - current_quantity)
        if can_add > 0:
            self.inventory[item_id] = current_quantity + can_add
            print(f"Added {can_add} {item_instance.name}(s). Current: {self.inventory[item_id]}")
            return True
        return False

    def use_health_potion(self):
        if self.potion_cooldown_timer > 0:
            return "Potion on cooldown!"
        
        hp_potion_id = HealthPotion().item_id
        if self.inventory.get(hp_potion_id, 0) <= 0:
            return "No Health Potions!"
        
        if self.hp == self.max_hp:
            return "HP is already full!"

        # Use potion
        restore_amount = HealthPotion().restore_hp_amount
        self.hp = min(self.max_hp, self.hp + restore_amount)
        self.inventory[hp_potion_id] -= 1
        self.potion_cooldown_timer = self.POTION_COOLDOWN_DURATION
        return f"Used Health Potion! HP: {self.hp}/{self.max_hp}"

    def use_mana_potion(self):
        if self.potion_cooldown_timer > 0:
            return "Potion on cooldown!"

        mp_potion_id = ManaPotion().item_id
        if self.inventory.get(mp_potion_id, 0) <= 0:
            return "No Mana Potions!"

        if self.mp == self.max_mp:
            return "MP is already full!"

        # Use potion
        restore_amount = ManaPotion().restore_mp_amount
        self.mp = min(self.max_mp, self.mp + restore_amount)
        self.inventory[mp_potion_id] -= 1
        self.potion_cooldown_timer = self.POTION_COOLDOWN_DURATION
        return f"Used Mana Potion! MP: {self.mp}/{self.max_mp}"

    def draw(self, screen):
        # Determine player color
        if self.is_attacking and self.attack_animation_timer > 0:
            current_player_color = self.attack_color
        elif self.is_dashing and self.dash_duration > 0: # Visual for dashing
            current_player_color = (0, 255, 255) # Cyan while dashing
        else:
            current_player_color = self.default_color

        # Draw player body
        player_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        player_surface.fill(current_player_color)
        if self.invincible and self.invincibility_timer % 10 < 5: # Flashing effect
            player_surface.set_alpha(128)
        screen.blit(player_surface, self.rect)

        # Draw attack animation (simple visual cue)
        if self.is_attacking and self.attack_animation_timer > 0:
            animation_progress = (self.attack_animation_duration - self.attack_animation_timer) / self.attack_animation_duration
            
            # Simple expanding rectangle animation
            animation_width = int(30 * (1 + animation_progress * 0.5)) # Grows by 50%
            animation_height = int(20 * (1 + animation_progress * 0.2)) # Grows by 20%
            
            if self.facing_right:
                anim_rect = pygame.Rect(self.rect.right, self.rect.centery - animation_height // 2, animation_width, animation_height)
            else:
                anim_rect = pygame.Rect(self.rect.left - animation_width, self.rect.centery - animation_height // 2, animation_width, animation_height)
            
            pygame.draw.rect(screen, (255, 200, 0), anim_rect, 0, border_radius=3) # Yellow-orange fill
            pygame.draw.rect(screen, (255, 255, 0), anim_rect, 1, border_radius=3) # Yellow outline
