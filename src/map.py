import pygame

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, is_one_way=False):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill((0, 255, 0) if not is_one_way else (0, 150, 0)) # Green for solid, darker green for one-way
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_one_way = is_one_way

class Portal(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, destination_map_id, destination_spawn_point_id):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill((0, 0, 255)) # Blue for portals
        self.rect = self.image.get_rect(topleft=(x, y))
        self.destination_map_id = destination_map_id
        self.destination_spawn_point_id = destination_spawn_point_id

class GameMap:
    def __init__(self, platforms, enemies, portals):
        self.platforms = platforms
        self.enemies = enemies # Not used directly by map, but conceptually part of it
        self.portals = portals # Not used directly by map, but conceptually part of it

    def draw(self, screen):
        for platform in self.platforms:
            screen.blit(platform.image, platform.rect)
        for portal in self.portals:
            screen.blit(portal.image, portal.rect)
        # Enemies are drawn by the main game loop, not the map itself
