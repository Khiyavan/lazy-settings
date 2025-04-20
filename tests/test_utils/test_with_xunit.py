from unittest import TestCase, IsolatedAsyncioTestCase

import pytest

from lazy_settings.conf import settings
from lazy_settings.test.utils import override_settings, modify_settings

from . import global_settings

settings.clear()
settings.register(global_settings)
mock = None


@override_settings(A_SETTING="new value", NEW_SETTING="this wasn't in the file")
class OverridentSettingsUnitTest(TestCase):
    @pytest.fixture(autouse=True)
    def make_mocker_available(self, mocker):
        global mock
        mock = mocker
        yield mock
        mock = None

    def test_overriden_settings(self):
        self.assertEqual(settings.A_SETTING, "new value")
        self.assertEqual(settings.NEW_SETTING, "this wasn't in the file")

    @override_settings(A_SETTING="another one")
    def test_override_after_override(self):
        self.assertEqual(settings.A_SETTING, "another one")

    def test_override_with_context_manager(self):
        self.assertEqual(settings.A_SETTING, "new value")
        with override_settings(A_SETTING="context!"):
            self.assertEqual(settings.A_SETTING, "context!")

        self.assertEqual(settings.A_SETTING, "new value")

    def test_class_decorator_is_accessed(self):
        spy_decorator = mock.spy(override_settings, "decorate_class")

        @override_settings(A_SETTING="a")
        class TestClass(TestCase):
            def test_something(self):
                self.assertEqual(2, 2)

        spy_decorator.assert_called_once()
        self.assertEqual(spy_decorator.spy_return, TestClass)

    def test_callable_decorator_accessed(self):
        spy_decorator = mock.spy(override_settings, "decorate_callable")

        @override_settings(A_SETTING="a")
        def test_callable():
            self.assertEqual(2, 2)

        spy_decorator.assert_called_once()
        self.assertEqual(spy_decorator.spy_return, test_callable)

    def test_enable_and_disable_accessed(self):
        spy_enable = mock.spy(override_settings, "enable")
        spy_disable = mock.spy(override_settings, "disable")

        # TODO: test enable and disable when used as a decorator
        with override_settings(A_SETTING="a"):
            pass

        spy_enable.assert_called_once()
        spy_disable.assert_called_once()


@override_settings(A_SETTING="new value", NEW_SETTING="this wasn't in the file")
class AsyncOverridentSettingsUnitTest(IsolatedAsyncioTestCase):
    @pytest.fixture(autouse=True)
    def make_mocker_available(self, mocker):
        global mock
        mock = mocker
        yield mock
        mock = None

    @override_settings(A_SETTING="another one")
    async def test_override_after_override(self):
        self.assertEqual(settings.A_SETTING, "another one")

    async def test_override_with_context_manager(self):
        self.assertEqual(settings.A_SETTING, "new value")
        with override_settings(A_SETTING="context!"):
            self.assertEqual(settings.A_SETTING, "context!")

        self.assertEqual(settings.A_SETTING, "new value")

    async def test_callable_decorator_accessed(self):
        spy_decorator = mock.spy(override_settings, "decorate_callable")

        @override_settings(A_SETTING="a")
        async def test_callable():
            self.assertEqual(2, 2)

        spy_decorator.assert_called_once()
        self.assertEqual(spy_decorator.spy_return, test_callable)

    async def test_enable_and_disable_accessed(self):
        spy_enable = mock.spy(override_settings, "enable")
        spy_disable = mock.spy(override_settings, "disable")

        # TODO: test enable and disable when used as a decorator
        with override_settings(A_SETTING="a"):
            pass

        spy_enable.assert_called_once()
        spy_disable.assert_called_once()


@modify_settings(LIST_BASED_SETTING={"append": "three", "prepend": "zero"})
class ModifySettingsUnitTest(TestCase):
    @pytest.fixture(autouse=True)
    def make_mocker_available(self, mocker):
        global mock
        mock = mocker
        yield mock
        mock = None

    def test_modified_settings(self):
        self.assertEqual(len(settings.LIST_BASED_SETTING), 4)
        self.assertEqual(settings.LIST_BASED_SETTING[0], "zero")
        self.assertEqual(settings.LIST_BASED_SETTING[-1], "three")

    @modify_settings(LIST_BASED_SETTING={"remove": "two"})
    def test_modify_after_modify(self):
        self.assertEqual(len(settings.LIST_BASED_SETTING), 3)
        self.assertNotIn("two", settings.LIST_BASED_SETTING)

    def test_modify_with_context_manager(self):
        self.assertEqual(len(settings.LIST_BASED_SETTING), 4)
        with modify_settings(
            LIST_BASED_SETTING={"append": "four", "prepend": "less than zero"},
        ):
            self.assertEqual(len(settings.LIST_BASED_SETTING), 6)
            self.assertEqual(settings.LIST_BASED_SETTING[0], "less than zero")
            self.assertEqual(settings.LIST_BASED_SETTING[-1], "four")

        self.assertEqual(len(settings.LIST_BASED_SETTING), 4)

    def test_class_decorator_is_accessed(self):
        spy_decorator = mock.spy(modify_settings, "decorate_class")

        @modify_settings(LIST_BASED_SETTING={"append": "four"})
        class TestClass(TestCase):
            def test_something(self):
                self.assertEqual(2, 2)

        spy_decorator.assert_called_once()
        self.assertEqual(spy_decorator.spy_return, TestClass)

    def test_callable_decorator_accessed(self):
        spy_decorator = mock.spy(modify_settings, "decorate_callable")

        @modify_settings(LIST_BASED_SETTING={"append": "four"})
        def test_callable():
            self.assertEqual(2, 2)

        spy_decorator.assert_called_once()
        self.assertEqual(spy_decorator.spy_return, test_callable)

    def test_enable_and_disable_accessed(self):
        spy_enable = mock.spy(modify_settings, "enable")
        spy_disable = mock.spy(modify_settings, "disable")

        # TODO: test enable and disable when used as a decorator
        with modify_settings(LIST_BASED_SETTING={"append": "four"}):
            pass

        spy_enable.assert_called_once()
        spy_disable.assert_called_once()


@modify_settings(LIST_BASED_SETTING={"append": "three", "prepend": "zero"})
class AsyncModifySettingsUnitTest(IsolatedAsyncioTestCase):
    @pytest.fixture(autouse=True)
    def make_mocker_available(self, mocker):
        global mock
        mock = mocker
        yield mock
        mock = None

    @modify_settings(LIST_BASED_SETTING={"remove": "two"})
    async def test_modify_after_modify(self):
        self.assertEqual(len(settings.LIST_BASED_SETTING), 3)
        self.assertNotIn("two", settings.LIST_BASED_SETTING)

    async def test_modify_with_context_manager(self):
        self.assertEqual(len(settings.LIST_BASED_SETTING), 4)
        with modify_settings(
            LIST_BASED_SETTING={"append": "four", "prepend": "less than zero"},
        ):
            self.assertEqual(len(settings.LIST_BASED_SETTING), 6)
            self.assertEqual(settings.LIST_BASED_SETTING[0], "less than zero")
            self.assertEqual(settings.LIST_BASED_SETTING[-1], "four")

        self.assertEqual(len(settings.LIST_BASED_SETTING), 4)

    async def test_callable_decorator_accessed(self):
        spy_decorator = mock.spy(modify_settings, "decorate_callable")

        @modify_settings(LIST_BASED_SETTING={"append": "four"})
        async def test_callable():
            self.assertEqual(2, 2)

        spy_decorator.assert_called_once()
        self.assertEqual(spy_decorator.spy_return, test_callable)

    async def test_enable_and_disable_accessed(self):
        spy_enable = mock.spy(modify_settings, "enable")
        spy_disable = mock.spy(modify_settings, "disable")

        # TODO: test enable and disable when used as a decorator
        with modify_settings(LIST_BASED_SETTING={"append": "four"}):
            pass

        spy_enable.assert_called_once()
        spy_disable.assert_called_once()
