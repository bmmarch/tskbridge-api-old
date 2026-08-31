# Placeholder service for the model (inside src/projects)

from .model import TaskModel

class TaskService:
    """A tiny in-memory service placeholder. Replace with DB-backed implementation."""

    def __init__(self):
        self._next_id = 1
        self._items = {}

    def create(self, title: str) -> TaskModel:
        model = TaskModel(self._next_id, title)
        self._items[self._next_id] = model
        self._next_id += 1
        return model

    def list(self):
        return [m.to_dict() for m in self._items.values()]
