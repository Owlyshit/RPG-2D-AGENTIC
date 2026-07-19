import pygame

class Quest:
    def __init__(self, quest_id, title, description, objective_type, target_data, reward_exp):
        self.quest_id = quest_id
        self.title = title
        self.description = description
        self.objective_type = objective_type # e.g., 'DEFEAT_ENEMY'
        self.target_data = target_data       # e.g., {'enemy_type': 'Slime', 'count': 5}
        self.reward_exp = reward_exp

        self.is_active = False
        self.is_completed = False
        self.is_reward_claimed = False
        self.current_progress = 0

    def update_progress(self, event_type, data):
        if not self.is_active or self.is_completed:
            return

        if self.objective_type == 'DEFEAT_ENEMY':
            if event_type == 'ENEMY_DEFEATED' and data['enemy_type'] == self.target_data['enemy_type']:
                self.current_progress += 1
                if self.current_progress >= self.target_data['count']:
                    self.current_progress = self.target_data['count'] # Cap progress
                    self.is_completed = True
                    print(f"Quest '{self.title}' completed!")

    def get_progress_string(self):
        if self.objective_type == 'DEFEAT_ENEMY':
            return f"Defeat {self.target_data['enemy_type']}s: {self.current_progress}/{self.target_data['count']}"
        return ""

