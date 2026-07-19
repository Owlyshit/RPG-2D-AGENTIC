import pygame
from src.quest import Quest

class NPC:
    def __init__(self, x, y, name, quest_to_assign=None):
        self.width = 32
        self.height = 48
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = (0, 0, 200) # Dark Blue
        self.name = name
        self.quest = quest_to_assign # The quest this NPC is associated with

        self.dialogue_states = {
            "initial": f"Hello, I am {self.name}. No quests for you at the moment.",
            "quest_available": f"Greetings, adventurer! The slimes in the area have become a menace. Defeat {self.quest.target_data['count']} of them for me and I'll reward you handsomely. Press 'E' to accept.",
            "quest_accepted": f"Thank you for your help! Come back when you've defeated the slimes. Current progress: {self.quest.get_progress_string()}(Dynamic)",
            "quest_completed": f"Amazing work! You've cleared the area of slimes. Here's your reward: {self.quest.reward_exp} EXP. Press 'E' to claim.",
            "reward_claimed": f"Thank you again, brave adventurer! Your efforts have made our village safer. Come back if you need anything else."
        }
        self.current_dialogue_key = "initial"
        self.interaction_prompt = "Press 'E' to interact"
        self.show_prompt = False

    def update(self, player):
        # Update dialogue state based on player's quest status
        if self.quest:
            player_quest = next((q for q in player.active_quests if q.quest_id == self.quest.quest_id), None)
            if player_quest:
                if player_quest.is_reward_claimed:
                    self.current_dialogue_key = "reward_claimed"
                elif player_quest.is_completed:
                    self.current_dialogue_key = "quest_completed"
                else:
                    self.current_dialogue_key = "quest_accepted"
                    # Update quest progress string in dialogue dynamically
                    self.dialogue_states["quest_accepted"] = \
                        f"Thank you for your help! Come back when you've defeated the slimes. Current progress: {player_quest.get_progress_string()}"
            else:
                self.current_dialogue_key = "quest_available"
        else:
            self.current_dialogue_key = "initial" # If NPC has no quest, default to initial

    def interact(self, player):
        print(f"NPC ({self.name}): {self._get_dialogue_text()}")
        
        if self.quest:
            player_quest = next((q for q in player.active_quests if q.quest_id == self.quest.quest_id), None)

            if not player_quest and self.current_dialogue_key == "quest_available":
                # Player accepts quest
                new_quest = Quest(self.quest.quest_id, self.quest.title, self.quest.description,
                                  self.quest.objective_type, self.quest.target_data, self.quest.reward_exp)
                player.accept_quest(new_quest)
                # The update method will set the correct dialogue key next frame
                print(f"Player accepted quest: {self.quest.title}")
            elif player_quest and player_quest.is_completed and not player_quest.is_reward_claimed:
                # Player claims reward
                player.claim_quest_reward(player_quest)
                # The update method will set the correct dialogue key next frame
                print(f"Player claimed reward for quest: {self.quest.title}")

    def _get_dialogue_text(self):
        return self.dialogue_states.get(self.current_dialogue_key, "(No dialogue defined)")

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        font = pygame.font.Font(None, 20)
        name_text = font.render(self.name, True, (255, 255, 255))
        screen.blit(name_text, (self.rect.x + self.width // 2 - name_text.get_width() // 2, self.rect.y - 20))

        if self.show_prompt:
            prompt_text = font.render(self.interaction_prompt, True, (255, 255, 255))
            screen.blit(prompt_text, (self.rect.x + self.width // 2 - prompt_text.get_width() // 2, self.rect.y - 40))
