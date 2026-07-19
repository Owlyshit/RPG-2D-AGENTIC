class Map:
    def __init__(self, name, width, height, tile_data=None):
        self.name = name
        self.width = width
        self.height = height
        self.tile_data = tile_data if tile_data is not None else self._generate_placeholder_map()
        self.entities = [] # To hold players, enemies, items on the map
        self.spawn_points = [] # For player or monster spawning
        self.portals = [] # Connections to other maps

    def _generate_placeholder_map(self):
        # A simple placeholder for a 2D map structure
        # '0' could represent air, '1' ground, etc.
        return [['0' for _ in range(self.width)] for _ in range(self.height)]

    def add_entity(self, entity, x, y):
        # For now, just add to a list. Later, check bounds and tile validity.
        self.entities.append({'entity': entity, 'x': x, 'y': y})
        print(f"Added {entity.name} to {self.name} at ({x},{y}).")

    def remove_entity(self, entity):
        self.entities = [e for e in self.entities if e['entity'] != entity]
        print(f"Removed {entity.name} from {self.name}.")

    def __str__(self):
        map_str = f"--- Map: {self.name} ({self.width}x{self.height}) ---\n"
        for row in self.tile_data:
            map_str += "".join(row) + "\n"
        if self.entities:
            map_str += "Entities on map:\n"
            for entity_data in self.entities:
                map_str += f"- {entity_data['entity'].name} at ({entity_data['x']},{entity_data['y']})\n"
        return map_str

# Example usage (for testing purposes, will be removed later)
if __name__ == "__main__":
    from player import Player
    from enemy import Enemy

    maple_island = Map("Maple Island", 80, 20)
    print(maple_island)

    player1 = Player("BeginnerHero")
    slime = Enemy("Orange Slime", "Slime", 30, 8, 1, 3)

    maple_island.add_entity(player1, 10, 18)
    maple_island.add_entity(slime, 25, 18)

    print(maple_island)