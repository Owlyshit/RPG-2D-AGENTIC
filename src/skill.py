import pygame

class Fireball(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, damage, speed):
        super().__init__()
        self.image = pygame.Surface((20, 10))
        self.image.fill((255, 100, 0)) # Orange fireball
        self.rect = self.image.get_rect(center=(x, y))

        self.vel_x = speed * direction
        self.damage = damage
        self.lifetime = 120 # frames, about 2 seconds

    def update(self, platforms):
        self.rect.x += self.vel_x
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill() # Remove fireball after its lifetime

        # Remove if off-screen (basic check)
        if self.rect.right < 0 or self.rect.left > pygame.display.get_surface().get_width():
            self.kill()
