class Enemy:
    def __init__(self, name, species, health, attack, defense, experience_on_defeat):
        self.name = name
        self.species = species
        self.health = health
        self.attack = attack
        self.defense = defense
        self.experience_on_defeat = experience_on_defeat

    def take_damage(self, amount):
        actual_damage = max(0, amount - self.defense) # Simple damage reduction
        self.health -= actual_damage
        print(f"{self.name} took {actual_damage} damage. Health: {self.health}")
        if self.health <= 0:
            print(f"{self.name} has been defeated!")
            return True # Enemy defeated
        return False # Enemy not defeated

    def attack_player(self, player):
        # Placeholder for a more complex attack logic
        damage_to_player = self.attack # For now, direct attack value
        print(f"{self.name} attacks {player.name} for {damage_to_player} damage!")
        return damage_to_player

    def __str__(self):
        return (f"Enemy: {self.name} ({self.species})\n"
                f"HP: {self.health}\n"
                f"Attack: {self.attack}, Defense: {self.defense}\n"
                f"Grants {self.experience_on_defeat} EXP on defeat")

# Example usage (for testing purposes, will be removed later)
if __name__ == "__main__":
    from player import Player # Assuming player.py is in the same directory
    slime = Enemy("Green Slime", "Slime", 50, 10, 2, 5)
    print(slime)

    hero = Player("TestHero")
    damage = slime.attack_player(hero)
    hero.take_damage(damage)

    print("\nSlime takes damage:")
    slime.take_damage(15)
    slime.take_damage(40) # Should defeat the slime