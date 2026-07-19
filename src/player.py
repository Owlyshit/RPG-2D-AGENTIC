class Player:
    def __init__(self, name, job_class="Beginner"):
        self.name = name
        self.level = 1
        self.experience = 0
        self.health = 100
        self.mana = 50
        self.job_class = job_class
        self.inventory = []
        self.equipment = {} # e.g., {"weapon": None, "armor": None}

    def gain_experience(self, exp_points):
        self.experience += exp_points
        # Placeholder for level-up logic
        print(f"{self.name} gained {exp_points} experience points!")

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            print(f"{self.name} has been defeated!")
        else:
            print(f"{self.name} took {amount} damage. Health: {self.health}")

    def use_mana(self, amount):
        if self.mana >= amount:
            self.mana -= amount
            print(f"{self.name} used {amount} mana. Mana: {self.mana}")
            return True
        else:
            print(f"{self.name} doesn't have enough mana!")
            return False

    def add_to_inventory(self, item):
        self.inventory.append(item)
        print(f"{item} added to {self.name}'s inventory.")

    def __str__(self):
        return (f"Player: {self.name}\n"
                f"Level: {self.level} (EXP: {self.experience})\n"
                f"Class: {self.job_class}\n"
                f"HP: {self.health} / MP: {self.mana}\n"
                f"Inventory: {', '.join(self.inventory) if self.inventory else 'Empty'}")

# Example usage (for testing purposes, will be removed later)
if __name__ == "__main__":
    hero = Player("Mapler", "Warrior")
    print(hero)
    hero.gain_experience(50)
    hero.take_damage(20)
    hero.add_to_inventory("Red Potion")
    hero.use_mana(10)
    print(hero)