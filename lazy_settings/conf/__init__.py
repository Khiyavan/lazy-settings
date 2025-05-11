"""
Settings and configuration for Django.

Read values from the module specified by the DJANGO_SETTINGS_MODULE environment
variable, and then from django.conf.global_settings; see the global_settings.py
for a list of all possible variables.
"""

import importlib
import os
from types import ModuleType
from typing import Any, Self

from lazy_settings.conf.utils import locate_pyproject
from lazy_settings.exceptions import ImproperlyConfigured
from lazy_settings.utils.functional import LazyObject, empty

try:
    import rtoml
except ImportError:
    rtoml = None  # type: ignore[assignment]
    try:
        import tomli as tomllib
    except ImportError:
        import tomllib  # type: ignore[no-redef]


ENVIRONMENT_VARIABLE = "SETTINGS_MODULE"


class SettingsReference(str):
    """
    String subclass which references a current settings value. It's treated as
    the value in memory but serializes to a settings.NAME attribute reference.
    """

    def __new__(self, value: Any, setting_name: str) -> Self:
        return str.__new__(self, value)

    def __init__(self, value: str, setting_name: str) -> None:
        self.setting_name = setting_name


class LazySettings(LazyObject["Settings | UserSettingsHolder"]):
    """
    A lazy proxy for either global Django settings or a custom settings object.
    The user can manually configure settings prior to using them. Otherwise,
    Django uses the settings module pointed to by DJANGO_SETTINGS_MODULE.
    """

    def _parse_toml(self) -> str | None:
        if pyproject := locate_pyproject():
            # rtoml can't use the `b` option if `open()`, and tomllib can handle a Path object,
            # so we support them like this for now
            if rtoml:
                config: dict[str, Any] = rtoml.load(pyproject)
            else:
                with pyproject.open("rb") as f:
                    config = tomllib.load(f)

            settings_module: str | None = config.get("lazy-settings", {}).get(
                "SETTINGS_MODULE"
            )
        return settings_module

    def _setup(self, name: str | None = None) -> None:
        """
        Load the settings module pointed to by the environment variable or pyproject.toml. This
        is used the first time settings are needed, if the user hasn't
        configured settings manually.
        """
        settings_module: str | None = os.environ.get(ENVIRONMENT_VARIABLE)
        if not settings_module:
            settings_module = self._parse_toml()

        if not settings_module:
            desc = ("setting %s" % name) if name else "settings"
            raise ImproperlyConfigured(
                "Requested %s, but settings are not configured. "
                "You must either define the environment variable %s "
                "or call settings.configure() before accessing settings."
                % (desc, ENVIRONMENT_VARIABLE)
            )

        self._wrapped = Settings(settings_module)

    def __repr__(self) -> str:
        # Hardcode the class name as otherwise it yields 'Settings'.
        if self._wrapped is empty:
            return "<LazySettings [Unevaluated]>"
        return '<LazySettings "%(settings_module)s">' % {
            "settings_module": self._wrapped.SETTINGS_MODULE,  # type: ignore[attr-defined]
        }

    def __getattr__(self, name: str) -> Any:
        """Return the value of a setting and cache it in self.__dict__."""
        if (_wrapped := self._wrapped) is empty:
            self._setup(name)
            _wrapped = self._wrapped
        val = getattr(_wrapped, name)

        self.__dict__[name] = val
        return val

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Set the value of setting. Clear all cached values if _wrapped changes
        (@override_settings does this) or clear single values when set.
        """
        if name == "_wrapped":
            self.__dict__.clear()
        else:
            self.__dict__.pop(name, None)
        super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        """Delete a setting and clear it from cache if needed."""
        super().__delattr__(name)
        self.__dict__.pop(name, None)

    def __iter__(self):
        if self._wrapped is empty:
            raise ImproperlyConfigured(
                "settings are not configured. "
                "You must either define the environment variable %s "
                "or call settings.configure() before accessing settings."
                % (ENVIRONMENT_VARIABLE)
            )
        for setting in self._wrapped:
            yield setting

    def configure(self, **options) -> None:
        """
        Called to manually configure the settings.
        """
        if not self.configured:
            raise RuntimeError("Settings already configured.")
        holder = UserSettingsHolder()
        for name, value in options.items():
            if not name.isupper():
                raise TypeError("Setting %r must be uppercase." % name)
            setattr(holder, name, value)
        self._wrapped = holder

    @property
    def configured(self) -> bool:
        """Return True if the settings have already been configured."""
        return self._wrapped is not empty

    def register(self, settings_module: ModuleType) -> None:
        if self._wrapped is empty:
            self._setup()
        self._wrapped.register(settings_module)  # type: ignore[attr-defined]

    def clear(self) -> None:
        if self._wrapped is empty:
            return
        self._wrapped.clear()  # type: ignore[attr-defined]


class Settings:
    def __init__(self, settings_module: str):
        # store the settings module in case someone later cares
        self.SETTINGS_MODULE = settings_module

        mod = importlib.import_module(self.SETTINGS_MODULE)

        self._explicit_settings = set()
        for setting in dir(mod):
            if setting.isupper():
                setting_value = getattr(mod, setting)

                setattr(self, setting, setting_value)
                self._explicit_settings.add(setting)

    def __repr__(self) -> str:
        return '<%(cls)s "%(settings_module)s">' % {
            "cls": self.__class__.__name__,
            "settings_module": self.SETTINGS_MODULE,
        }

    def __iter__(self):
        for setting in dir(self):
            if setting.isupper():
                yield setting

    def is_overridden(self, setting: str) -> bool:
        return setting in self._explicit_settings

    def register(self, settings_module: ModuleType) -> None:
        for setting in dir(settings_module):
            if setting.isupper() and setting not in self:
                setattr(self, setting, getattr(settings_module, setting))

    def clear(self) -> None:
        for attr in self:
            if attr.isupper():
                delattr(self, attr)


class UserSettingsHolder:
    """Holder for user configured settings."""

    # SETTINGS_MODULE doesn't make much sense in the manually configured
    # (standalone) case.
    SETTINGS_MODULE: None = None

    def __init__(self, settings=None):
        self.__dict__["_deleted"] = set()

        # if settings is None, it won't have any upper case attribute
        for setting in dir(settings):
            if setting not in self and setting.isupper():
                setattr(self, setting, getattr(settings, setting))

    def __getattr__(self, name: str) -> Any:
        if not name.isupper() or name in self._deleted:
            raise AttributeError

        return getattr(self, name)

    def __setattr__(self, name: str, value: Any) -> None:
        self._deleted.discard(name)
        super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        self._deleted.add(name)
        if hasattr(self, name):
            super().__delattr__(name)

    def __dir__(self) -> list:
        return sorted(
            s
            for s in [
                *self.__dict__,
            ]
            if s not in self._deleted
        )

    def __repr__(self):
        return "<%(cls)s>" % {
            "cls": self.__class__.__name__,
        }

    def __iter__(self):
        for setting in dir(self):
            if setting.isupper():
                yield setting

    def register(self, settings_module: ModuleType | Settings) -> None:
        for setting in dir(settings_module):
            if setting.isupper() and setting not in dir(self):
                setattr(self, setting, getattr(settings_module, setting))

    def clear(self):
        for attr in dir(self):
            if attr.isupper():
                delattr(self, attr)

    def is_overridden(self, setting: str) -> bool:
        deleted = setting in self._deleted
        set_locally = setting in self.__dict__
        return deleted or set_locally


settings = LazySettings()
