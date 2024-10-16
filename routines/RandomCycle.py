import random
from typing import List
from git_fit import Config, Routine, State

class RandomCycle(Routine):
    def next_exercise(self, config: Config, state: State, skipped_categories: List[str], skipped_exercises: List[str]) -> str:
        state.remaining_categories = [cat for cat in state.remaining_categories if cat not in skipped_categories]

        if len(state.remaining_categories) == 0:
            state.remaining_categories = list(config.categories.keys())

        category = random.choice(state.remaining_categories)

        state.remaining_exercises[category] = [ex for ex in state.remaining_exercises[category] if ex not in skipped_exercises]

        if len(state.remaining_exercises[category]) == 0:
            state.remaining_exercises[category] = config.categories[category]

        exercises = state.remaining_exercises[category]
        exercise = random.choice(exercises)

        return category, exercise

    def record(self, state, category, exercise, reps):
        state.remaining_exercises[category].remove(exercise)
        state.remaining_categories.remove(category)