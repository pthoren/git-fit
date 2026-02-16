import random
from datetime import datetime
from typing import List
from git_fit import Config, Routine, State

class ToFailure(Routine):
    timed = False

    def _is_first_of_day(self, state: State) -> bool:
        if not state.last_executed:
            return True
        last_date = datetime.fromisoformat(state.last_executed).date()
        return last_date != datetime.now().date()

    def next_exercise(self, config: Config, state: State, skipped_categories: List[str], skipped_exercises: List[str], category: str = None) -> str:
        if not category:
            state.remaining_categories = [cat for cat in state.remaining_categories if cat not in skipped_categories]

            if len(state.remaining_categories) == 0:
                state.remaining_categories = list(config.categories.keys())

            available = state.remaining_categories
            if self._is_first_of_day(state) and len(available) > 1:
                available = [cat for cat in available if cat != 'stretches']

            last_skipped_category = skipped_categories[-1] if skipped_categories else None
            category = random.choice(available)
            while (category == last_skipped_category and len(available) > 1):
                category = random.choice(available)

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
