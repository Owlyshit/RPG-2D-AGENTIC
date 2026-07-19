import pygame

class Platform:
    def __init__(self, x, y, width, height, isOneWay=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = (150, 75, 0) # Brown
        self.isOneWay = isOneWay
        if self.isOneWay:
            self.color = (100, 50, 0) # Darker brown for one-way

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class Portal:
    def __init__(self, x, y, width, height, destinationMapId, destinationSpawnPoint_x, destinationSpawnPoint_y):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = (0, 255, 255) # Cyan
        self.destinationMapId = destinationMapId
        self.destinationSpawnPoint_x = destinationSpawnPoint_x
        self.destinationSpawnPoint_y = destinationSpawnPoint_y

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        font = pygame.font.Font(None, 20)
        text = font.render(f"Map {self.destinationMapId}", True, (0, 0, 0))
        screen.blit(text, (self.rect.x + 5, self.rect.y + 5))


class Map:
    def __init__(self, map_id, width, height, spawn_x=0, spawn_y=0):
        self.map_id = map_id
        self.width = width
        self.height = height
        self.platforms = []
        self.portals = []
        self.enemies = []
        self.npcs = [] # New list for NPCs
        self.spawn_point_x = spawn_x
        self.spawn_point_y = spawn_y
        self.background_color = (135, 206, 235) # Sky blue
        self.map_boundaries = pygame.Rect(0, 0, width, height) # For clamping player movement


    def add_platform(self, platform):
        self.platforms.append(platform)

    def add_portal(self, portal):
        self.portals.append(portal)

    def add_enemy(self, enemy):
        self.enemies.append(enemy)

    def add_npc(self, npc): # New method to add NPCs
        self.npcs.append(npc)

    def draw(self, screen):
        screen.fill(self.background_color)
        for platform in self.platforms:
            platform.draw(screen)
        for portal in self.portals:
            portal.draw(screen)
        # Enemies and NPCs are drawn by the Game class after map drawing
