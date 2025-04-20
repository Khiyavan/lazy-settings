import pytest

from django import test
from django.conf import global_settings

from lazy_settings.conf import settings
from lazy_settings.test.utils import override_settings, modify_settings


settings.clear()
settings.register(global_settings)
mock = None


@override_settings(LANGUAGE_CODE="fa", NEW_SETTING="new")
class OverrideSettingsDjangoTests(test.SimpleTestCase):
    @pytest.fixture(autouse=True)
    def make_mocker_available(self, mocker):
        global mock
        mock = mocker
        yield mock
        mock = None

    @classmethod
    def setUpClass(cls):
        if cls._overridden_settings:
            cls.enterClassContext(override_settings(**cls._overridden_settings))
        if cls._modified_settings:
            cls.enterClassContext(modify_settings(cls._modified_settings))
        # the below lines needs django settings to be configured, but we don't want that
        # cls._add_databases_failures()
        # cls.addClassCleanup(cls._remove_databases_failures)

    def test_overriden_settings(self):
        self.assertEqual(settings.LANGUAGE_CODE, "fa")
        self.assertEqual(settings.NEW_SETTING, "new")

    @override_settings(LANGUAGE_CODE="de")
    def test_override_after_override(self):
        self.assertEqual(settings.LANGUAGE_CODE, "de")

    def test_override_with_context_manager(self):
        self.assertEqual(settings.LANGUAGE_CODE, "fa")
        with override_settings(LANGUAGE_CODE="en"):
            self.assertEqual(settings.LANGUAGE_CODE, "en")

        self.assertEqual(settings.LANGUAGE_CODE, "fa")

    def test_django_specific_method_is_called(self):
        spy_decorator = mock.spy(override_settings, "django_save_options")

        @override_settings(A_SETTING="a")
        class TestClass(test.SimpleTestCase):
            def test_something(self):
                self.assertEqual(2, 2)

        spy_decorator.assert_called_once()


@modify_settings(ADMINS={"append": [("john doe", "john@email.com")]})
class ModifySettingsDjangoTests(test.SimpleTestCase):
    @pytest.fixture(autouse=True)
    def make_mocker_available(self, mocker):
        global mock
        mock = mocker
        yield mock
        mock = None

    @classmethod
    def setUpClass(cls):
        if cls._overridden_settings:
            cls.enterClassContext(override_settings(**cls._overridden_settings))
        if cls._modified_settings:
            cls.enterClassContext(modify_settings(cls._modified_settings))
        # the below lines needs django settings to be configured, but we don't want that
        # cls._add_databases_failures()
        # cls.addClassCleanup(cls._remove_databases_failures)

    def test_overriden_settings(self):
        self.assertEqual(settings.ADMINS, [("john doe", "john@email.com")])

    @modify_settings(ADMINS={"append": [("jane doe", "jane@email.com")]})
    def test_override_after_override(self):
        self.assertEqual(len(settings.ADMINS), 2)
        self.assertEqual(settings.ADMINS[1], ("jane doe", "jane@email.com"))

    def test_override_with_context_manager(self):
        self.assertEqual(settings.ADMINS, [("john doe", "john@email.com")])

        with modify_settings(ADMINS={"prepend": [("me", "me@email.com")]}):
            self.assertEqual(len(settings.ADMINS), 2)
            self.assertEqual(settings.ADMINS[0], ("me", "me@email.com"))

        self.assertEqual(len(settings.ADMINS), 1)

    def test_django_specific_method_is_called(self):
        spy_decorator = mock.spy(modify_settings, "django_save_options")

        @modify_settings(ADMIN={"append": [("hi", "hi@email.com")]})
        class TestClass(test.SimpleTestCase):
            def test_something(self):
                self.assertEqual(2, 2)

        spy_decorator.assert_called_once()
