"""Project service for database operations."""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .model import Project, ProjectStatus


class ProjectService:
    """Service for managing Project database operations."""

    def __init__(self, db: Session):
        """Initialize the service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create(
        self,
        name: str,
        team_id: int,
        description: Optional[str] = None,
        status: ProjectStatus = ProjectStatus.ACTIVE,
    ) -> Project:
        """Create a new project.

        Args:
            name: Project name
            team_id: ID of the team that owns the project
            description: Optional project description
            status: Initial project status (defaults to ACTIVE)

        Returns:
            Created Project instance

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            project = Project(
                name=name,
                description=description,
                team_id=team_id,
                status=status,
            )
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            return project
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Failed to create project: {str(e)}") from e

    def update_status(self, project_id: int, status: ProjectStatus) -> Optional[Project]:
        """Update the status of a project.

        Args:
            project_id: ID of the project to update
            status: New project status

        Returns:
            Updated Project instance, or None if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return None
            project.status = status
            self.db.commit()
            self.db.refresh(project)
            return project
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Failed to update project status: {str(e)}") from e

    def get_by_team(self, team_id: int) -> List[Project]:
        """Retrieve all projects for a specific team.

        Args:
            team_id: ID of the team

        Returns:
            List of Project instances belonging to the team

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return self.db.query(Project).filter(Project.team_id == team_id).all()
        except SQLAlchemyError as e:
            raise ValueError(f"Failed to retrieve projects for team: {str(e)}") from e

    def get_by_id(self, project_id: int) -> Optional[Project]:
        """Retrieve a project by ID.

        Args:
            project_id: ID of the project

        Returns:
            Project instance, or None if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return self.db.query(Project).filter(Project.id == project_id).first()
        except SQLAlchemyError as e:
            raise ValueError(f"Failed to retrieve project: {str(e)}") from e

    def delete(self, project_id: int) -> bool:
        """Delete a project by ID.

        Args:
            project_id: ID of the project to delete

        Returns:
            True if project was deleted, False if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return False
            self.db.delete(project)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Failed to delete project: {str(e)}") from e

    def list_all(self, limit: int = 100, offset: int = 0) -> List[Project]:
        """List all projects with pagination.

        Args:
            limit: Maximum number of projects to return
            offset: Number of projects to skip

        Returns:
            List of Project instances

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return self.db.query(Project).limit(limit).offset(offset).all()
        except SQLAlchemyError as e:
            raise ValueError(f"Failed to list projects: {str(e)}") from e
