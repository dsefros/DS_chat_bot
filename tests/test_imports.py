import importlib


def test_handlers_import_without_database_work() -> None:
    module = importlib.import_module("ds_chat_bot.handlers")

    assert module.router.name == "main"


def test_main_import_without_database_work() -> None:
    module = importlib.import_module("ds_chat_bot.main")

    assert callable(module.run_bot)
