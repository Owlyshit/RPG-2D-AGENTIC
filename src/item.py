class Item:
    def __init__(self, name, description="", item_type="General", value=0):
        self.name = name
        self.description = description
        self.item_type = item_type
        self.value = value

    def use(self, target=None):
        """
        Placeholder method for using an item.
        Actual implementation will depend on the item_type.
        """
        print(f"Using {self.name}...")
        if self.item_type == "Consumable":
            print(f"'{self.name}' consumed.")
            return True # Item was consumed
        elif self.item_type == "Equipment":
            print(f"'{self.name}' equipped.")
            # Logic to equip the item
            return False # Not consumed, but equipped
        else:
            print(f"Cannot use '{self.name}' directly.")
            return False

    def __str__(self):
        return (f"{self.name} (Type: {self.item_type})\n"
                f"  Description: {self.description}\n"
                f"  Value: {self.value} mesos") # Using 'mesos' for MapleStory flavor

# Example usage (for testing purposes, will be removed later)
if __name__ == "__main__":
    red_potion = Item("Red Potion", "Restores a small amount of HP", "Consumable", 50)
    print(red_potion)
    red_potion.use()

    sword = Item("Beginner's Sword", "A simple sword for new adventurers", "Equipment", 100)
    print(sword)
    sword.use()

    quest_letter = Item("Mysterious Letter", "A letter with a strange seal", "Quest Item")
    print(quest_letter)
    quest_letter.use()