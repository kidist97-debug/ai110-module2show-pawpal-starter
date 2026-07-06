import os
import sys

# Allow importing pawpal_system.py from the project root (one level up).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    """Calling mark_complete() should flip the task from not-done to done."""
    task = Task(description="Morning walk", duration_minutes=30)

    assert task.completed is False  # starts incomplete

    task.mark_complete()

    assert task.completed is True   # now complete


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet should increase that pet's task count by one."""
    pet = Pet(id="p1", name="Rex", species="dog", age=4)

    assert len(pet.get_tasks()) == 0  # no tasks yet

    pet.add_task(Task(description="Feed", duration_minutes=5))

    assert len(pet.get_tasks()) == 1  # one task after adding
