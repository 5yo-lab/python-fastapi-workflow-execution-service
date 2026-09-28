from enum import StrEnum
from app.domain.errors import InvalidTransitionError


class State(StrEnum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    APPROVED = "APPROVED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    CANCELLED = "CANCELLED"


class Action(StrEnum):
    START_VALIDATION = "START_VALIDATION"
    START_PROCESSING = "START_PROCESSING"
    CANCEL = "CANCEL"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"


class ActionType(StrEnum):
    VALIDATE = "VALIDATE"
    PROCESS = "PROCESS"


MANUAL_ACTIONS: set[Action] = {
    Action.START_VALIDATION,
    Action.START_PROCESSING,
    Action.CANCEL,
}

AUTOMATED_ACTIONS: set[Action] = {
    Action.APPROVE,
    Action.REJECT,
    Action.COMPLETE,
    Action.FAIL,
}

TERMINAL_STATES: set[State] = {
    State.VALIDATION_FAILED,
    State.PROCESSING_FAILED,
    State.COMPLETED,
    State.CANCELLED,
}

ALLOWED_TRANSITIONS: dict[tuple[State, Action], State] = {
    (State.CREATED, Action.START_VALIDATION): State.VALIDATING,
    (State.CREATED, Action.CANCEL): State.CANCELLED,

    (State.VALIDATING, Action.APPROVE): State.APPROVED,
    (State.VALIDATING, Action.REJECT): State.VALIDATION_FAILED,
    (State.VALIDATING, Action.CANCEL): State.CANCELLED,

    (State.APPROVED, Action.START_PROCESSING): State.PROCESSING,
    (State.APPROVED, Action.CANCEL): State.CANCELLED,

    (State.PROCESSING, Action.COMPLETE): State.COMPLETED,
    (State.PROCESSING, Action.FAIL): State.PROCESSING_FAILED,
}


def is_terminal(state: State) -> bool:
    return state in TERMINAL_STATES


def actions_for_state(state: State) -> set[Action]:
    return {action for (from_state, action) in ALLOWED_TRANSITIONS if from_state == state}


def manual_actions_for_state(state: State) -> set[Action]:
    return actions_for_state(state) & MANUAL_ACTIONS


def get_next_state(state: State, action: Action) -> State:
    try:
        return ALLOWED_TRANSITIONS[(state, action)]
    except KeyError:
        raise InvalidTransitionError(f"Cannot apply {action} while workflow is in {state} state")


def action_type_for_transition(action: Action) -> ActionType | None:
    mapping: dict[Action, ActionType] = {
        Action.START_VALIDATION: ActionType.VALIDATE,
        Action.START_PROCESSING: ActionType.PROCESS,
    }
    return mapping.get(action)