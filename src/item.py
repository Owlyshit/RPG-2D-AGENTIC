class Item:
    def __init__(self, item_id, name, stack_limit=99):
        self.item_id = item_id
        self.name = name
        self.stack_limit = stack_limit

class HealthPotion(Item):
    def __init__(self):
        super().__init__("health_potion", "Health Potion")
        self.restore_hp_amount = 30

class ManaPotion(Item):
    def __init__(self):
        super().__init__("mana_potion", "Mana Potion")
        self.restore_mp_amount = 20

class Weapon(Item):
    def __init__(self, item_id, name, attack_bonus, attack_range):
        super().__init__(item_id, name, stack_limit=1)
        self.attack_bonus = attack_bonus
        self.attack_range = attack_range

class BronzeSword(Weapon):
    def __init__(self):
        super().__init__("bronze_sword", "Bronze Sword", attack_bonus=8, attack_range=42)

class Armor(Item):
    def __init__(self, item_id, name, slot, defense, stat_bonuses=None):
        super().__init__(item_id, name, stack_limit=1)
        self.slot = slot
        self.defense = defense
        self.stat_bonuses = stat_bonuses or {}

class LeatherCap(Armor):
    def __init__(self):
        super().__init__("leather_cap", "Leather Cap", "helmet", defense=2, stat_bonuses={"dexterity": 1})

class TrainingShirt(Armor):
    def __init__(self):
        super().__init__("training_shirt", "Training Shirt", "shirt", defense=3, stat_bonuses={"strength": 1})

class TravelerPants(Armor):
    def __init__(self):
        super().__init__("traveler_pants", "Traveler Pants", "pants", defense=2, stat_bonuses={"luck": 1})
