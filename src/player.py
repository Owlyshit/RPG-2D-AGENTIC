import pygame

class Player:
    def __init__(self, x, y):
        self.width = 32
        self.height = 48
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = (0, 128, 255) # Blue

        self.hp = 100
        self.maxHp = 100
        self.attackPower = 10
        self.exp = 0
        self.level = 1

        self.walkSpeed = 5
        self.jumpStrength = -12  # Negative for upward movement
        self.gravity = 0.5
        self.dy = 0
        self.dx = 0 # Will be reset each frame, controlled by input

        self.isGrounded = False
        self.facingDirection = 1 # 1 for right, -1 for left

        self.isAttacking = False
        self.attackCooldown = 30 # frames (e.g., 0.5 seconds at 60 FPS)
        self.attackTimer = 0
        self.attackRange_base_width = 40
        self.attackRange_base_height = 30
        self.attackRange_rect = pygame.Rect(0, 0, self.attackRange_base_width, self.attackRange_base_height)

        # Quest-related attributes
        self.active_quests = []


    def update(self):
        # Apply gravity
        if not self.isGrounded:
            self.dy += self.gravity
            if self.dy > 10: # Cap falling speed
                self.dy = 10

        # Update attack timer
        if self.isAttacking:
            self.attackTimer -= 1
            if self.attackTimer <= 0:
                self.isAttacking = False

        # Apply movement
        self.rect.x += self.dx
        self.rect.y += self.dy

        # Reset horizontal movement for next frame unless input is constant
        self.dx = 0

    def move_left(self):
        self.dx = -self.walkSpeed
        self.facingDirection = -1

    def move_right(self):
        self.dx = self.walkSpeed
        self.facingDirection = 1

    def jump(self):
        if self.isGrounded:
            self.dy = self.jumpStrength
            self.isGrounded = False

    def attack(self):
        # Only allow attack if not already attacking and cooldown is over
        if not self.isAttacking and self.attackTimer <= 0:
            self.isAttacking = True
            self.attackTimer = self.attackCooldown # Attack lasts for 'attackCooldown' frames


    def get_attack_rect(self):
        if self.isAttacking:
            # Position the attack rect relative to player and facing direction
            if self.facingDirection == 1: # Facing right
                # Attack rect origin is player's right side, centered vertically
                self.attackRange_rect.topleft = (self.rect.right, self.rect.centery - self.attackRange_base_height // 2)
            else: # Facing left
                # Attack rect origin is player's left side, centered vertically
                self.attackRange_rect.topright = (self.rect.left, self.rect.centery - self.attackRange_base_height // 2)
            return self.attackRange_rect
        return None

    def take_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
        # print(f"Player took {damage} damage. HP: {self.hp}") # For debugging

    def gain_exp(self, exp_amount):
        self.exp += exp_amount
        # Basic leveling up (can be expanded later)
        if self.exp >= self.level * 100:
            self.level += 1
            self.maxHp += 10
            self.hp = self.maxHp
            self.attackPower += 2
            print(f"Player leveled up to {self.level}!")

    def is_alive(self):
        return self.hp > 0

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        if self.isAttacking:
            attack_rect = self.get_attack_rect()
            if attack_rect:
                pygame.draw.rect(screen, (255, 0, 0), attack_rect, 2) # Red outline for attack hitbox

    # --- Quest Methods ---
    def accept_quest(self, quest):
        if not any(q.quest_id == quest.quest_id for q in self.active_quests):
            quest.is_active = True
            self.active_quests.append(quest)
            print(f"Player accepted quest: {quest.title}")

    def update_quest_progress(self, event_type, data):
        for quest in self.active_quests:
            quest.update_progress(event_type, data)

    def claim_quest_reward(self, quest_to_claim):
        # Find the quest in active_quests to ensure it's the player's actual quest object
        for quest in self.active_quests:
            if quest.quest_id == quest_to_claim.quest_id and quest.is_completed and not quest.is_reward_claimed:
                self.gain_exp(quest.reward_exp)
                quest.is_reward_claimed = True
                print(f"Player claimed {quest.reward_exp} EXP for quest '{quest.title}'")
                # Optionally remove claimed quests or move to a 'completed_quests' list
                # For now, we'll keep it in active_quests but marked as claimed
                return # Reward claimed, exit loop
