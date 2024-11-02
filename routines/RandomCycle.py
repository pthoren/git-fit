import random
from typing import List
from git_fit import Config, Routine, State

class RandomCycle(Routine):
    def next_exercise(self, config: Config, state: State, skipped_categories: List[str], skipped_exercises: List[str], category: str = None) -> str:
        if not category:
            state.remaining_categories = [cat for cat in state.remaining_categories if cat not in skipped_categories]

            if len(state.remaining_categories) == 0:
                state.remaining_categories = list(config.categories.keys())

            last_skipped_category = skipped_categories[-1] if skipped_categories else None
            category = random.choice(state.remaining_categories)
            while (category == last_skipped_category and len(state.remaining_categories) > 1):
                category = random.choice(state.remaining_categories)

        state.remaining_exercises[category] = [ex for ex in state.remaining_exercises[category] if ex not in skipped_exercises]

        if len(state.remaining_exercises[category]) == 0:
            state.remaining_exercises[category] = config.categories[category]

        last_skipped_exercise = skipped_exercises[-1] if skipped_exercises else None
        exercises = state.remaining_exercises[category]
        exercise = random.choice(exercises)
        while (exercise == last_skipped_exercise and len(exercises) > 1):
            exercise = random.choice(exercises)

        return category, exercise

    def record(self, state, category, exercise, reps):
        state.remaining_exercises[category].remove(exercise)
        state.remaining_categories.remove(category)