import pygame

class Quest:
    def __init__(self, q_id, name, objective_type, objective_target, objective_count, reward_exp, is_repeatable=True):
        self.id = q_id
        self.name = name
        self.objective_type = objective_type # e.g., 'kill'
        self.objective_target = objective_target # e.g., 'Slime'
        self.objective_count = objective_count # e.g., 5
        self.reward_exp = reward_exp
        self.is_repeatable = is_repeatable

    def get_description(self):
        return f"Quest: {self.name}\nObjective: {self.objective_type} {self.objective_count} {self.objective_target}s\nReward: {self.reward_exp} EXP"

class NPC(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name, initial_dialogue, quest_active_dialogue, quest_complete_dialogue, quest_offered):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill((0, 200, 0))  # Green NPC
        self.rect = self.image.get_rect(topleft=(x, y))
        self.name = name

        self.dialogue_initial = initial_dialogue
        self.dialogue_quest_active = quest_active_dialogue
        self.dialogue_quest_complete = quest_complete_dialogue
        self.quest_offered = quest_offered # This will be a Quest object

        self.is_talking = False
        self.current_dialogue = ""

    def start_talk(self, player_quest_status):
        self.is_talking = True
        if self.quest_offered is None:
            self.current_dialogue = self.dialogue_initial
            return
        if not player_quest_status or not player_quest_status['accepted']:
            self.current_dialogue = self.dialogue_initial
        elif player_quest_status['accepted'] and not player_quest_status['completed']:
            progress = player_quest_status['current_count']
            target = self.quest_offered.objective_count
            self.current_dialogue = f"{self.dialogue_quest_active} ({progress}/{target})"
        elif player_quest_status['completed']:
            self.current_dialogue = self.dialogue_quest_complete

    def stop_talk(self):
        self.is_talking = False
        self.current_dialogue = ""

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        # Optional: Draw name above NPC
        # font = pygame.font.Font(None, 20)
        # name_text = font.render(self.name, True, (255,255,255))
        # screen.blit(name_text, (self.rect.centerx - name_text.get_width() / 2, self.rect.y - 20))
