

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Dict
import csv
import json
import os
import random

@dataclass
class ExerciseLog:
    file_path: str = 'log.csv'
    headers: List[str] = field(default_factory=lambda: ['timestamp', 'category', 'exercise', 'reps'])

    def __post_init__(self):
        if not os.path.exists(self.file_path):
            self._initialize_log_file()

    def _initialize_log_file(self):
        # Initialize the CSV file with the correct headers
        with open(self.file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.headers)

    def record(self, category: str, exercise: str, reps: int):
        new_entry = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), category, exercise, str(reps)]

        with open(self.file_path, mode='r') as file:
            existing_entries = list(csv.reader(file))

        # Insert the new entry at the beginning
        updated_entries = [existing_entries[0]] + [new_entry] + existing_entries[1:]

        # Write the updated log back to the file
        with open(self.file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(updated_entries)

    def load_log(self) -> List[List[str]]:
        if os.path.exists(self.file_path):
            with open(self.file_path, mode='r') as file:
                return list(csv.reader(file))
        else:
            print("Log file not found.")
            return []


@dataclass
class State:
    remaining_categories: List[str]
    remaining_exercises: Dict[str, List[str]]
    last_executed: str = ""

    def save(self) -> None:
        with open('.state.json', 'w') as file:
            json.dump(asdict(self), file, indent=4)

    @staticmethod
    def load(config):
        try:
            with open(".state.json", 'r') as file:
                state_dict = json.load(file)
                return State(**state_dict)
        except FileNotFoundError:
            return State(remaining_categories=list(config.categories.keys()), remaining_exercises=config.categories)

class Routine(ABC):
    @abstractmethod
    def next_exercise(self) -> str:
        pass

    @abstractmethod
    def record(self, state: State, category: str, exercise: str, reps: float):
        pass

@dataclass
class Cooldown:
    days: int
    hours: int
    minutes: int

    def check(self, last_executed: str):
        if not last_executed:
            return True
        else:
            last_executed_dt = datetime.fromisoformat(last_executed)
            duration = timedelta(**self.__dict__)
            return last_executed_dt < datetime.now() - duration

@dataclass
class Config:
    cooldown: Cooldown
    routine: Routine
    categories: Dict[str, List[str]]

    @staticmethod
    def load():
        with open('config.json', 'r') as file:
            config = json.load(file)

        cooldown = Cooldown(**config['cooldown'])
        routine = globals()[config['routine']]()

        return Config(cooldown=cooldown, routine=routine, categories=config['categories'])

class RandomCycle(Routine):
    def next_exercise(self, config: Config, state: State) -> str:
        if len(state.remaining_categories) == 0:
            state.remaining_categories = list(config.categories.keys())

        category = random.choice(state.remaining_categories)

        if len(state.remaining_exercises[category]) == 0:
            state.remaining_exercises[category] = config.categories[category]

        exercises = state.remaining_exercises[category]
        exercise = random.choice(exercises)

        return category, exercise

    def record(self, state, category, exercise, reps):
        state.remaining_exercises[category].remove(exercise)
        state.remaining_categories.remove(category)

class FourDaySplit(Routine):
    def next_exercise(self) -> str:
        return super().get_next_exercise()

    def record(self, state, category, exercise):
        return super().record(category, exercise)

def main():
    config = Config.load()
    state = State.load(config)
    log = ExerciseLog()

    if not config.cooldown.check(state.last_executed):
        print("cooldown")
        return

    routine = config.routine
    print('Routine:', routine.__class__.__name__)
    category, exercise = routine.next_exercise(config, state)
    print(f"Category: {category}")
    print(f"Exercise: {exercise}")
    print ('--')

    reps = int(input("How many reps did you do?: "))
    if (reps > 0):
        routine.record(state, category, exercise)
        log.record(category, exercise, reps)
        state.save()
        print('Remaining categories:', state.remaining_categories)
        print('Remaining exercises:', state.remaining_exercises[category])

if __name__ == "__main__":
    main()