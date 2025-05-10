import pytest

from lazy_settings.conf import settings
from lazy_settings.test.utils import override_settings, modify_settings

from . import global_settings

pytestmark = pytest.mark.anyio

settings.clear()
settings.register(global_settings)


@pytest.mark.order(1)
@override_settings(A_SETTING="something new")
def test_override_settings_function_decorator():
    assert settings.A_SETTING == "something new"


@pytest.mark.order(2)
def test_override_settings_function_decorator_cleanup():
    assert settings.A_SETTING == "something"


@pytest.mark.order(3)
@override_settings(A_SETTING="something new")
async def test_override_settings_async_function_decorator():
    assert settings.A_SETTING == "something new"


@pytest.mark.order(4)
async def test_override_settings_async_function_decorator_cleanup():
    assert settings.A_SETTING == "something"


def test_override_settings_context_manager_in_function():
    with override_settings(A_SETTING="context!!"):
        assert settings.A_SETTING == "context!!"

    assert settings.A_SETTING == "something"


async def test_override_settings_context_manager_in_async_function():
    with override_settings(A_SETTING="context!!"):
        assert settings.A_SETTING == "context!!"

    assert settings.A_SETTING == "something"


@pytest.mark.order(5)
@modify_settings(LIST_BASED_SETTING={"append": "things", "prepend": "first things"})
def test_modify_settings_fucntion_decorator():
    assert settings.LIST_BASED_SETTING == ["first things", "one", "two", "things"]


@pytest.mark.order(6)
def test_modify_settings_function_decorator_cleanup():
    assert settings.LIST_BASED_SETTING == ["one", "two"]


@pytest.mark.order(7)
@modify_settings(LIST_BASED_SETTING={"append": "things", "prepend": "first things"})
async def test_modify_settings_async_fucntion_decorator():
    assert settings.LIST_BASED_SETTING == ["first things", "one", "two", "things"]


@pytest.mark.order(8)
async def test_modify_settings_async_function_decorator_cleanup():
    assert settings.LIST_BASED_SETTING == ["one", "two"]


def test_modify_settings_context_manager_in_function():
    with modify_settings(
        LIST_BASED_SETTING={"append": "three", "prepend": "zero"},
    ):
        assert settings.LIST_BASED_SETTING == ["zero", "one", "two", "three"]
    assert settings.LIST_BASED_SETTING == ["one", "two"]


async def test_modify_settings_context_manager_in_async_function():
    with modify_settings(
        LIST_BASED_SETTING={"append": "three", "prepend": "zero"},
    ):
        assert settings.LIST_BASED_SETTING == ["zero", "one", "two", "three"]
    assert settings.LIST_BASED_SETTING == ["one", "two"]


@override_settings(A_SETTING="new value", NEW_SETTING="this wasn't in the file")
class TestOverridentSettings:
    def test_overriden_settings(self):
        assert settings.A_SETTING == "new value"
        assert settings.NEW_SETTING == "this wasn't in the file"

    @override_settings(A_SETTING="another one")
    def test_override_after_override(self):
        assert settings.A_SETTING == "another one"

    def test_override_with_context_manager(self):
        assert settings.A_SETTING == "new value"
        with override_settings(A_SETTING="context!"):
            assert settings.A_SETTING == "context!"

        assert settings.A_SETTING == "new value"

    def test_class_decorator_is_accessed(self, mocker):
        spy_decorator = mocker.spy(override_settings, "decorate_class")

        @override_settings(A_SETTING="a")
        class TestClass:
            def test_something(self):
                assert 2 == 2

        spy_decorator.assert_called_once()
        assert spy_decorator.spy_return == TestClass

    def test_callable_decorator_accessed(self, mocker):
        spy_decorator = mocker.spy(override_settings, "decorate_callable")

        @override_settings(A_SETTING="a")
        def test_callable():
            assert 2 == 2

        spy_decorator.assert_called_once()
        assert spy_decorator.spy_return == test_callable

    def test_enable_and_disable_accessed(self, mocker):
        spy_enable = mocker.spy(override_settings, "enable")
        spy_disable = mocker.spy(override_settings, "disable")

        # TODO: test enable and disable when used as a decorator
        with override_settings(A_SETTING="a"):
            pass

        spy_enable.assert_called_once()
        spy_disable.assert_called_once()


@override_settings(A_SETTING="new value", NEW_SETTING="this wasn't in the file")
class TestOverridentSettingsAsync:
    @override_settings(A_SETTING="another one")
    async def test_override_after_override(self):
        assert settings.A_SETTING == "another one"

    async def test_override_with_context_manager(self):
        assert settings.A_SETTING == "new value"
        with override_settings(A_SETTING="context!"):
            assert settings.A_SETTING == "context!"

        assert settings.A_SETTING == "new value"

    async def test_callable_decorator_accessed(self, mocker):
        spy_decorator = mocker.spy(override_settings, "decorate_callable")

        @override_settings(A_SETTING="a")
        async def test_callable():
            assert 2 == 2

        spy_decorator.assert_called_once()
        assert spy_decorator.spy_return == test_callable

    async def test_enable_and_disable_accessed(self, mocker):
        spy_enable = mocker.spy(override_settings, "enable")
        spy_disable = mocker.spy(override_settings, "disable")

        # TODO: test enable and disable when used as a decorator
        with override_settings(A_SETTING="a"):
            pass

        spy_enable.assert_called_once()
        spy_disable.assert_called_once()


@modify_settings(LIST_BASED_SETTING={"append": "three", "prepend": "zero"})
class TestModifySettings:
    def test_modified_settings(self):
        assert len(settings.LIST_BASED_SETTING) == 4
        assert settings.LIST_BASED_SETTING[0] == "zero"
        assert settings.LIST_BASED_SETTING[-1] == "three"

    @modify_settings(LIST_BASED_SETTING={"remove": "two"})
    def test_modify_after_modify(self):
        assert len(settings.LIST_BASED_SETTING) == 3
        assert "two" not in settings.LIST_BASED_SETTING

    def test_modify_with_context_manager(self):
        assert len(settings.LIST_BASED_SETTING) == 4
        with modify_settings(
            LIST_BASED_SETTING={"append": "four", "prepend": "less than zero"},
        ):
            assert len(settings.LIST_BASED_SETTING) == 6
            assert settings.LIST_BASED_SETTING[0] == "less than zero"
            assert settings.LIST_BASED_SETTING[-1] == "four"

        assert len(settings.LIST_BASED_SETTING) == 4

    def test_class_decorator_is_accessed(self, mocker):
        spy_decorator = mocker.spy(modify_settings, "decorate_class")

        @modify_settings(LIST_BASED_SETTING={"append": "four"})
        class TestClass:
            def test_something(self):
                assert 2 == 2

        spy_decorator.assert_called_once()
        assert spy_decorator.spy_return == TestClass

    def test_callable_decorator_accessed(self, mocker):
        spy_decorator = mocker.spy(modify_settings, "decorate_callable")

        @modify_settings(LIST_BASED_SETTING={"append": "four"})
        def test_callable():
            assert 2 == 2

        spy_decorator.assert_called_once()
        assert spy_decorator.spy_return == test_callable

    def test_enable_and_disable_accessed(self, mocker):
        spy_enable = mocker.spy(modify_settings, "enable")
        spy_disable = mocker.spy(modify_settings, "disable")

        # TODO: test enable and disable when used as a decorator
        with modify_settings(LIST_BASED_SETTING={"append": "four"}):
            pass

        spy_enable.assert_called_once()
        spy_disable.assert_called_once()


@modify_settings(LIST_BASED_SETTING={"append": "three", "prepend": "zero"})
class TestModifySettingsAsync:
    @modify_settings(LIST_BASED_SETTING={"remove": "two"})
    async def test_modify_after_modify(self):
        assert len(settings.LIST_BASED_SETTING) == 3
        assert "two" not in settings.LIST_BASED_SETTING

    async def test_modify_with_context_manager(self):
        assert len(settings.LIST_BASED_SETTING) == 4
        with modify_settings(
            LIST_BASED_SETTING={"append": "four", "prepend": "less than zero"},
        ):
            assert len(settings.LIST_BASED_SETTING) == 6
            assert settings.LIST_BASED_SETTING[0] == "less than zero"
            assert settings.LIST_BASED_SETTING[-1] == "four"

        assert len(settings.LIST_BASED_SETTING) == 4

    async def test_callable_decorator_accessed(self, mocker):
        spy_decorator = mocker.spy(modify_settings, "decorate_callable")

        @modify_settings(LIST_BASED_SETTING={"append": "four"})
        async def test_callable():
            assert 2 == 2

        spy_decorator.assert_called_once()
        assert spy_decorator.spy_return == test_callable

    async def test_enable_and_disable_accessed(self, mocker):
        spy_enable = mocker.spy(modify_settings, "enable")
        spy_disable = mocker.spy(modify_settings, "disable")

        # TODO: test enable and disable when used as a decorator
        with modify_settings(LIST_BASED_SETTING={"append": "four"}):
            pass

        spy_enable.assert_called_once()
        spy_disable.assert_called_once()
