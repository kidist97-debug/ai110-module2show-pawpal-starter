from dataclasses import dataclass, field
from enum import Enum


class Category(Enum):
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    RABBIT = "rabbit"
    OTHER = "other"


class TaskType(Enum):
    WALK = "walk"
    FEED = "feed"
    MEDS = "meds"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"


@dataclass
class CareTask:
    id: str
    name: str
    task_type: TaskType
    duration_minutes: int
    priority: int
    pet_id: str
    frequency: str = "daily"
    preferred_time: str | None = None

    def is_high_priority(self) -> bool:
        """Return True if this task is high priority."""
        raise NotImplementedError


@dataclass
class Pet:
    id: str
    name: str
    age: int
    sex: str
    category: Category
    weight: float
    tasks: list[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        """Attach a care task to this pet."""
        raise NotImplementedError

    def get_tasks_by_type(self, task_type: TaskType) -> list[CareTask]:
        """Return all tasks of a given type (e.g. all meds)."""
        raise NotImplementedError


@dataclass
class Owner:
    name: str
    email: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)
    budget_per_pet: dict = field(default_factory=dict)
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        raise NotImplementedError

    def total_pets(self) -> int:
        """Return the number of pets this owner has."""
        raise NotImplementedError


@dataclass
class DailyPlan:
    date: str
    pet: Pet
    scheduled_tasks: list[CareTask] = field(default_factory=list)
    deferred_tasks: list[CareTask] = field(default_factory=list)
    total_time: int = 0
    explanation: str = ""

    def add_task(self, task: CareTask) -> None:
        """Add a task to the scheduled list and update total_time."""
        raise NotImplementedError

    def summary(self) -> str:
        """Return a short overview of the plan."""
        raise NotImplementedError

    def to_text(self) -> str:
        """Return the full plan formatted for the Streamlit UI."""
        raise NotImplementedError


class Planner:
    """Builds a DailyPlan from a pet's tasks and the owner's constraints."""

    def generate_plan(self, pet: Pet, owner: Owner) -> DailyPlan:
        """Main entry point: produce a daily plan for one pet."""
        raise NotImplementedError

    def _prioritize(self, tasks: list[CareTask]) -> list[CareTask]:
        """Sort tasks by priority (and urgency)."""
        raise NotImplementedError

    def _fit_to_availability(
        self, tasks: list[CareTask], available_minutes: int
    ) -> list[CareTask]:
        """Keep tasks until time runs out; return the ones that fit."""
        raise NotImplementedError

    def _build_explanation(
        self,
        scheduled: list[CareTask],
        deferred: list[CareTask],
        owner: Owner,
    ) -> str:
        """Generate the 'why I chose this plan' text."""
        raise NotImplementedError
