

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import importlib
from typing import List, Dict
import csv
import json
import os

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


# config: silence when late at night?

@dataclass
class Config:
    cooldown: Cooldown
    workout_hours_start: int
    workout_hours_end: int
    routine: str
    categories: Dict[str, List[str]]

    @staticmethod
    def load():
        with open('config.json', 'r') as file:
            config = json.load(file)

        cooldown = Cooldown(**config['cooldown'])

        return Config(
            cooldown=cooldown,
            workout_hours_start=config['workout_hours']['start'],
            workout_hours_end=config['workout_hours']['end'],
            routine=config['routine'],
            categories=config['categories'])

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
    def next_exercise(self, config: Config, state: State, skipped_categories: List[str]) -> str:
        pass

    @abstractmethod
    def record(self, state: State, category: str, exercise: str, reps: float):
        pass

def main():
    config = Config.load()
    state = State.load(config)
    log = ExerciseLog()

    if not config.cooldown.check(state.last_executed):
        print("cooldown")
        return

    current_hour = datetime.now().hour
    if current_hour <= config.workout_hours_start or current_hour >= config.workout_hours_end:
        print("off hours")
        return

    routine_class_name = config.routine
    module = importlib.import_module(f'routines.{routine_class_name}')
    RoutineClass = getattr(module, routine_class_name)
    routine = RoutineClass()

    skipped_categories = []

    while True:
        print('Routine:', routine.__class__.__name__)
        category, exercise = routine.next_exercise(config, state, skipped_categories)
        print(f"Category: {category}")
        print(f"Exercise: {exercise}")
        print ('--')

        value = input("How many reps did you do? (0 = skip, c = change category): ")
        if (value == 'c'):
            print('Changing category')
            skipped_categories.append(category)
            continue
        elif (value == '0'):
            print('Skipping this time.')
            return
        else:
            reps = int(value)
            if (reps > 0):
                routine.record(state, category, exercise)
                log.record(category, exercise, reps)
                state.save()
                print('Remaining categories:', state.remaining_categories)
                print('Remaining exercises:', state.remaining_exercises[category])
                return
        reps = int(input("How many reps did you do? (0 = skip, c = change category): "))

if __name__ == "__main__":
    main()