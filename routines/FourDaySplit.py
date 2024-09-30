from git_fit import Routine


class FourDaySplit(Routine):
    def next_exercise(self) -> str:
        return super().get_next_exercise()

    def record(self, state, category, exercise):
        return super().record(category, exercise)