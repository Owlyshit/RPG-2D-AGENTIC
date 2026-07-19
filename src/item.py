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
