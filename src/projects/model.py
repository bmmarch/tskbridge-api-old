# Placeholder Python model for the projects package

class TaskModel:
    """Simple placeholder model for tasks. Replace with your real model or dataclass."""

    def __init__(self, id: int, title: str, completed: bool = False):
        self.id = id
        self.title = title
        self.completed = completed

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title, "completed": self.completed}
