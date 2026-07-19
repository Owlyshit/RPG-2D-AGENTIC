class Skill:
    def __init__(self, name, description, mana_cost, skill_type="Attack", base_power=0, cooldown=0):
        self.name = name
        self.description = description
        self.mana_cost = mana_cost
        self.skill_type = skill_type
        self.base_power = base_power
        self.cooldown = cooldown
        self._current_cooldown = 0

    def execute(self, caster, target=None):
        """
        Placeholder method for executing the skill's effect.
        Actual implementation will depend on skill_type and game state.
        Returns True if skill was executed, False otherwise (e.g., not enough mana).
        """
        if caster.mana < self.mana_cost:
            print(f"{caster.name} doesn't have enough mana to cast {self.name}!")
            return False
        if self._current_cooldown > 0:
            print(f"{self.name} is on cooldown for {self._current_cooldown} turns.")
            return False

        caster.mana -= self.mana_cost
        print(f"{caster.name} uses {self.name}! ({self.description})")
        self._current_cooldown = self.cooldown # Start cooldown

        # Basic effect placeholder
        if self.skill_type == "Attack" and target:
            damage = self.base_power # Simplified damage calculation
            print(f"Deals {damage} damage to {target.name}.")
            # target.take_damage(damage) # Would link to Enemy/Player take_damage
        elif self.skill_type == "Heal":
            heal_amount = self.base_power
            print(f"Heals {caster.name} for {heal_amount} HP.")
            # caster.heal(heal_amount) # Would link to Player heal method
        # ... other skill types
        return True

    def reduce_cooldown(self):
        if self._current_cooldown > 0:
            self._current_cooldown -= 1

    def __str__(self):
        return (f"Skill: {self.name} (Type: {self.skill_type})\n"
                f"  Description: {self.description}\n"
                f"  Mana Cost: {self.mana_cost}\n"
                f"  Base Power: {self.base_power}\n"
                f"  Cooldown: {self.cooldown} turns")

# Example usage (for testing purposes, will be removed later)
if __name__ == "__main__":
    # Assuming a simplified caster object for demonstration
    class MockCaster:
        def __init__(self, name, mana):
            self.name = name
            self.mana = mana

        def heal(self, amount):
            self.mana += amount # Just to show it could interact

    class MockTarget:
        def __init__(self, name, hp):
            self.name = name
            self.hp = hp
        def take_damage(self, amount):
            self.hp -= amount
            print(f"{self.name} took {amount} damage. HP: {self.hp}")

    caster = MockCaster("Hero", 100)
    target = MockTarget("Goblin", 50)

    magic_claw = Skill("Magic Claw", "Hurls a magical claw at an enemy.", 10, "Attack", 15, 1)
    heal = Skill("Heal", "Restores HP to an ally.", 20, "Heal", 30, 2)

    print(magic_claw)
    print(heal)

    print("\n--- Testing Magic Claw ---")
    magic_claw.execute(caster, target)
    print(f"Caster Mana: {caster.mana}")
    magic_claw.reduce_cooldown()
    magic_claw.execute(caster, target)

    print("\n--- Testing Heal ---")
    heal.execute(caster)
    print(f"Caster Mana: {caster.mana}")
    heal.execute(caster)
    heal.reduce_cooldown()
    heal.reduce_cooldown()
    heal.execute(caster)