from src.app import PawsApp
from src.auth import AuthManager
from src.cli.menus import run_auth_menu, run_main_menu
from src.demo import seed_demo_data


def main() -> None:
    """Собирает зависимости и запускает консольный интерфейс."""
    app = PawsApp()
    auth = AuthManager(app.storage)
    seed_demo_data(app, auth)

    user = run_auth_menu(auth)
    if user is not None:
        run_main_menu(app, auth)


if __name__ == "__main__":
    main()
