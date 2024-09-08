from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import json
import random

from dataclasses import dataclass, field
from typing import List, Dict

class Routine(ABC):
    @abstractmethod
    def next_exercise(self) -> str:
        pass

    @abstractmethod
    def record(self):
        pass


@dataclass
class Cooldown:
    days: int
    hours: int
    minutes: int

@dataclass
class Config:
    cooldown: Cooldown
    routine: Routine
    categories: Dict[str, List[str]]

@dataclass
class State:
    remaining_categories: List[str]
    remaining_exercises: Dict[str, List[str]]
    last_executed: str = ""

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

    def record(self):
        return super().save()

class FourDaySplit(Routine):
    def next_exercise(self) -> str:
        return super().get_next_exercise()
    def record(self):
        return super().save()

def load_config(path: str = 'config.json') -> Config:
    with open(path, 'r') as f:
        config = json.load(f)

    cooldown = Cooldown(**config['cooldown'])

    routine: Routine = globals()[config['routine']]()

    return Config(cooldown=cooldown, routine=routine, categories=config['categories'])

def load_state(config: Config) -> State:
    try:
        with open(".state.json", 'r') as file:
            state_dict = json.load(file)
            return State(**state_dict)
    except FileNotFoundError:
        return State(remaining_categories=list(config.categories.keys()), remaining_exercises=config.categories)

def check_cooldown(cooldown: Cooldown, last_executed: str) -> bool:
  if not last_executed:
      return True
  else:
      last_executed_dt = datetime.fromisoformat(last_executed)
      duration = timedelta(**cooldown.__dict__)
      return last_executed_dt < datetime.now() - duration

def get_exercise(config: Config, state: State) -> str:
    return "exercise"

def main():
    config = load_config()
    state = load_state(config)

    if not check_cooldown(config.cooldown, state.last_executed):
        print("cooldown")
        return

    routine = config.routine
    category, exercise = routine.next_exercise(config, state)
    print(f"{category}: {exercise}")

if __name__ == "__main__":
    main()