"""Контейнер зависимостей приложения."""
from src.app import PawsApp
from src.auth import AuthManager
from src.demo import seed_demo_data

paws_core = PawsApp()
auth_manager = AuthManager()

# Инициализируем тестовые данные сразу при создании контейнера
seed_demo_data(paws_core, auth_manager)