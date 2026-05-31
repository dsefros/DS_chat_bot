import importlib


def test_handlers_import_without_database_work() -> None:
    module = importlib.import_module("ds_chat_bot.handlers")

    assert module.router.name == "main"


def test_main_import_without_database_work() -> None:
    module = importlib.import_module("ds_chat_bot.main")

    assert callable(module.run_bot)


def test_profile_handlers_import_successfully() -> None:
    module = importlib.import_module("ds_chat_bot.profile_handlers")

    assert module.router.name == "profiles"


def test_keyboards_import_successfully() -> None:
    module = importlib.import_module("ds_chat_bot.keyboards")

    assert module.main_reply_keyboard() is not None


def test_bot_command_list_includes_find_partner() -> None:
    module = importlib.import_module("ds_chat_bot.main")

    commands = {command.command: command.description for command in module.create_bot_commands()}

    assert commands["start"] == "старт"
    assert commands["connect"] == "меню"
    assert commands["profile"] == "моя анкета"
    assert commands["edit_profile"] == "изменить анкету"
    assert commands["find_partner"] == "найти партнера"
    assert commands["cancel"] == "отменить текущее действие"
