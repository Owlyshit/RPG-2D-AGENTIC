import pygame

class Item:
    def __init__(self, name, description, icon_path=None):
        self.name = name
        self.description = description
        self.icon = None
        if icon_path:
            try:
                self.icon = pygame.image.load(icon_path).convert_alpha()
            except pygame.error:
                print(f"Warning: Could not load item icon {icon_path}")

    def use(self, player):
        # Generic item has no effect on its own
        pass

class Potion(Item):
    def __init__(self, name, description, icon_path=None, heal_amount=0, mp_restore_amount=0):
        super().__init__(name, description, icon_path)
        self.heal_amount = heal_amount
        self.mp_restore_amount = mp_restore_amount

    def use(self, player):
        if self.heal_amount > 0:
            player.hp = min(player.maxHp, player.hp + self.heal_amount)
            print(f"Player used {self.name}, healed {self.heal_amount} HP. Current HP: {player.hp}")
        if self.mp_restore_amount > 0:
            player.mp = min(player.maxMp, player.mp + self.mp_restore_amount)
            print(f"Player used {self.name}, restored {self.mp_restore_amount} MP. Current MP: {player.mp}")
        return True # Indicate successful use
