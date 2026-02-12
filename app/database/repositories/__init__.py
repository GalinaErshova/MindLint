"""Экспорт репозиториев."""

from app.database.repositories.user import UserRepository
from app.database.repositories.analysis import AnalysisRepository

__all__ = ["UserRepository", "AnalysisRepository"]
