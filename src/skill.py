import pygame

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, damage, speed, color, width=10, height=10):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction # -1 for left, 1 for right
        self.damage = damage
        self.speed = speed
        self.vel_x = self.speed * self.direction

    def update(self, platforms):
        self.rect.x += self.vel_x
        # Remove if off screen
        if self.rect.left > pygame.display.get_surface().get_width() or self.rect.right < 0:
            self.kill()

        # Collision with platforms (projectiles disappear on hitting a solid platform)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # Only consider non-one-way platforms as solid for projectiles
                if not platform.is_one_way:
                    self.kill()
                    return

class Fireball(Projectile):
    def __init__(self, x, y, direction, damage, speed):
        super().__init__(x, y, direction, damage, speed, (255, 100, 0), width=15, height=15) # Orange fireball
        self.name = "Fireball"

class IceBolt(Projectile):
    def __init__(self, x, y, direction, damage, speed, slow_duration, slow_percentage):
        super().__init__(x, y, direction, damage, speed, (0, 200, 255), width=12, height=12) # Cyan ice bolt
        self.name = "IceBolt"
        self.slow_duration = slow_duration # frames
        self.slow_percentage = slow_percentage # e.g., 0.5 for 50% slow

