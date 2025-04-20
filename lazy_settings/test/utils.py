from functools import wraps
from inspect import iscoroutinefunction
from unittest import TestCase

from lazy_settings.conf import UserSettingsHolder, settings

try:
    import pytest
except ImportError:
    pass


class TestContextDecorator:
    """
    A base class that can either be used as a context manager during tests
    or as a test function or unittest.TestCase subclass decorator to perform
    temporary alterations.

    `attr_name`: attribute assigned the return value of enable() if used as
                 a class decorator.

    `kwarg_name`: keyword argument passing the return value of enable() if
                  used as a function decorator.
    """

    def __init__(self, attr_name=None, kwarg_name=None):
        self.attr_name = attr_name
        self.kwarg_name = kwarg_name

    def enable(self):
        raise NotImplementedError

    def disable(self):
        raise NotImplementedError

    def __enter__(self):
        return self.enable()

    def __exit__(self, exc_type, exc_value, traceback):
        self.disable()

    def decorate_class(self, cls):
        if issubclass(cls, TestCase):
            decorated_setUp = cls.setUp

            def setUp(inner_self):
                context = self.enable()
                inner_self.addCleanup(self.disable)
                if self.attr_name:
                    setattr(inner_self, self.attr_name, context)
                decorated_setUp(inner_self)

            cls.setUp = setUp

        else:

            @pytest.fixture(autouse=True)
            def settings_fixture(inner_self):
                context = self.enable()
                if self.attr_name:
                    setattr(inner_self, self.attr_name, context)

                yield context
                self.disable()

            cls.settings_fixture = settings_fixture

        return cls

    def decorate_callable(self, func):
        if iscoroutinefunction(func):
            # If the inner function is an async function, we must execute async
            # as well so that the `with` statement executes at the right time.
            @wraps(func)
            async def inner(*args, **kwargs):
                with self as context:
                    if self.kwarg_name:
                        kwargs[self.kwarg_name] = context
                    return await func(*args, **kwargs)

        else:

            @wraps(func)
            def inner(*args, **kwargs):
                with self as context:
                    if self.kwarg_name:
                        kwargs[self.kwarg_name] = context
                    return func(*args, **kwargs)

        return inner

    def __call__(self, decorated):
        if isinstance(decorated, type):
            return self.decorate_class(decorated)
        elif callable(decorated):
            return self.decorate_callable(decorated)
        raise TypeError("Cannot decorate object of type %s" % type(decorated))


class override_settings(TestContextDecorator):
    """
    Act as either a decorator or a context manager. If it's a decorator, take a
    function and return a wrapped function. If it's a contextmanager, use it
    with the ``with`` statement. In either event, entering/exiting are called
    before and after, respectively, the function/block is executed.
    """

    enable_exception = None

    def __init__(self, **kwargs):
        self.options = kwargs
        super().__init__()

    def enable(self):
        override = UserSettingsHolder(settings._wrapped)
        for key, new_value in self.options.items():
            setattr(override, key, new_value)

        self.wrapped = settings._wrapped
        settings._wrapped = override

    def disable(self):
        settings._wrapped = self.wrapped
        del self.wrapped
        responses = []

        if self.enable_exception is not None:
            exc = self.enable_exception
            self.enable_exception = None
            raise exc
        for _, response in responses:
            if isinstance(response, Exception):
                raise response

    def django_save_options(self, test_func):
        if test_func._overridden_settings is None:
            test_func._overridden_settings = self.options
        else:
            # Duplicate dict to prevent subclasses from altering their parent.
            test_func._overridden_settings = {
                **test_func._overridden_settings,
                **self.options,
            }

    def decorate_class(self, cls):
        try:
            from django.test import SimpleTestCase

            if issubclass(cls, SimpleTestCase):
                self.django_save_options(cls)
                return cls
        except ImportError:
            pass

        return super().decorate_class(cls)


class modify_settings(override_settings):
    """
    Like override_settings, but makes it possible to append, prepend, or remove
    items instead of redefining the entire list.
    """

    def __init__(self, *args, **kwargs):
        if args:
            # Hack used when instantiating from SimpleTestCase.setUpClass.
            assert not kwargs
            self.operations = args[0]
        else:
            assert not args
            self.operations = list(kwargs.items())
        super().__init__()

    def django_save_options(self, test_func):
        if test_func._modified_settings is None:
            test_func._modified_settings = self.operations
        else:
            # Duplicate list to prevent subclasses from altering their parent.
            test_func._modified_settings = (
                list(test_func._modified_settings) + self.operations
            )

    def enable(self):
        self.options = {}
        for name, operations in self.operations:
            try:
                # When called from SimpleTestCase.setUpClass, values may be
                # overridden several times; cumulate changes.
                value = self.options[name]
            except KeyError:
                value = list(getattr(settings, name, []))
            for action, items in operations.items():
                # items may be a single value or an iterable.
                if isinstance(items, str):
                    items = [items]
                if action == "append":
                    value += [item for item in items if item not in value]
                elif action == "prepend":
                    value = [item for item in items if item not in value] + value
                elif action == "remove":
                    value = [item for item in value if item not in items]
                else:
                    raise ValueError("Unsupported action: %s" % action)
            self.options[name] = value
        super().enable()
