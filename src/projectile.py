import pygame

class Fireball:
    def __init__(self, x, y, direction):
        self.rect = pygame.Rect(x, y, 16, 16) # Fireball size
        self.color = (255, 100, 0) # Orange/Red
        self.speed = 7 * direction # Direction will be -1 or 1
        self.damage = 20
        self.is_active = True
        self.lifespan = 90 # frames
        self.timer = self.lifespan

    def update(self):
        if not self.is_active:
            return
        self.rect.x += self.speed
        self.timer -= 1
        if self.timer <= 0:
            self.is_active = False

    def draw(self, screen, camera_offset_x):
        if self.is_active:
            pygame.draw.ellipse(screen, self.color, self.rect.move(-camera_offset_x, 0))
