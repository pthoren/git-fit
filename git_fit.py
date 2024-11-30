

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import platform
import subprocess
from time import sleep
import importlib
from typing import List, Dict
import csv
import json
import os

DEBUG = False

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
    workout_hours_start: int
    workout_hours_end: int
    exercise_duration: int
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
            exercise_duration=config['exercise_duration'],
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

    def previous_sets(self, exercise: str) -> List[List[str]]:
        log = self.load_log()
        sets = [row for row in log if row[2] == exercise]
        return sets[:5]

    def previous_cycle(self, categories: List[str]) -> List[List[str]]:
        log = self.load_log()
        categories_set = set(categories)
        cycle = []
        for row in log:
            cycle.append(row)
            category = row[1]
            if category in categories_set:
                categories_set.remove(category)
            if len(categories_set) == 0:
                break
        return cycle

@dataclass
class State:
    remaining_categories: List[str]
    remaining_exercises: Dict[str, List[str]]
    last_executed: str = ""

    def save(self) -> None:
        self.last_executed = datetime.now().isoformat()
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
    def next_exercise(self, config: Config, state: State, skipped_categories: List[str], skipped_exercises: List[str], category: str = None) -> str:  pass

    @abstractmethod
    def record(self, state: State, category: str, exercise: str, reps: int):
        pass

def main():
    config = Config.load()
    state = State.load(config)
    log = ExerciseLog()

    if not config.cooldown.check(state.last_executed):
        print("cooldown")
        return

    current_hour = datetime.now().hour
    if current_hour < config.workout_hours_start or current_hour >= config.workout_hours_end:
        print("off hours")
        return

    routine_class_name = config.routine
    module = importlib.import_module(f'routines.{routine_class_name}')
    RoutineClass = getattr(module, routine_class_name)
    routine = RoutineClass()

    skipped_categories = []
    skipped_exercises = []
    category = None

    while True:
        print('Routine:', routine.__class__.__name__)
        category, exercise = routine.next_exercise(config, state, skipped_categories, skipped_exercises, category)
        previous_sets = log.previous_sets(exercise)
        print(f"Category: {category}")
        print(f"Exercise: {exercise}")
        if previous_sets:
            print(f"Last time you did: {previous_sets[0][3]} reps")
        print ('--')

        value = input("Continue? (y: yes, c: change category, e: change exercise,  s: skip): ").lower()
        if (value == 'c'):
            print('Changing category')
            skipped_categories.append(category)
            category = None
            continue
        if (value == 'e'):
            print('Changing exercise')
            skipped_exercises.append(exercise)
            continue
        elif (value == 's' or value == '0'):
            print('Skipping this time.')
            return
        elif (value == 'y' or value == '1'):
            duration = config.exercise_duration

            speak_text(f"Starting in 10 seconds")
            sleep(5)
            speak_text("Five")
            speak_text("Four")
            speak_text("Three")
            speak_text("Two")
            speak_text("One")
            speak_text("Go")

            if (duration >= 45):
                sleep(duration - 30)
                speak_text("Thirty seconds remaining")
                sleep(15)
            else:
                sleep(duration - 15)

            speak_text("Fifteen seconds remaining")
            sleep(15)

            speak_text("Time's up")

            while True:
                value = input("How many reps did you do?: ").lower()
                try:
                    reps = int(value)
                    if reps > 0:
                        routine.record(state, category, exercise, reps)
                        log.record(category, exercise, reps)
                        state.save()
                        previous_sets = log.previous_sets()
                        print("")
                        print(f'{exercise} history')
                        for set in previous_sets:
                            print(f'{set[0]} {set[3]}')

                        remaining_exercises = state.remaining_exercises[category]
                        if len(remaining_exercises) == 0 and len(skipped_exercises) == 0:
                            print(f'All exercises completed in category {category}!')
                            # print stats

                        if DEBUG:
                            print(f'Remaining exercises in category {category}: {remaining_exercises}')

                        if len(state.remaining_categories) == 0 and len(skipped_categories) == 0:
                            print('All categories completed!')
                            print('This cycle you did:')
                            cycle = log.previous_cycle(config.categories)
                            for set in cycle:
                                print(f'{set[0]} {set[3]}')

                        print('Remaining categories in cycle:', state.remaining_categories.join(", "))
                    return
                except ValueError:
                    pass

def speak_text(text):
    system = platform.system()

    print(text)

    if system == "Darwin":  # macOS
        subprocess.run(["say", text])

    elif system == "Windows":  # Windows
        subprocess.run([
            "powershell",
            "-Command",
            f"Add-Type –AssemblyName System.speech; "
            f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{text}')"
        ])

    elif system == "Linux":  # Linux
        subprocess.run(["espeak", text])

if __name__ == "__main__":
    main()
