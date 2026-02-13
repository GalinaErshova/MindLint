"""FSM-состояния для многошагового анализа."""

from aiogram.fsm.state import State, StatesGroup


class AnalysisStates(StatesGroup):
    waiting_for_clarification = State()
