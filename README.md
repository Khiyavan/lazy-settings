# Lazy Settings
[![codecov](https://codecov.io/gh/khiyavan/lazy-settings/graph/badge.svg?token=UERDWJ9M31)](https://codecov.io/gh/khiyavan/lazy-settings)

this project is a port of django's settings tool, with a few adjustments to work with any project


# Features
* manage user and package settings
* allow manual configuration
* can work with multiple projects via registering (experimental)
* tools for testing


# Usage

this project is a port of django's settings, so most things that you can do with django's setting, you can do here, with a few adjustments.

## for users:
### for a normal use
you need to set `SETTINGS_MODULE`,
value of `SETTINGS_MODULE` is a dotted path to the file
so if your file is in `my_project.settings.py`, you should set the env var as `my_project.settings`

there is two way to set this:

1. environment variable which should point to a python module (file)
all your settings should be defined in this module (or imported in this module)

there are many ways to set an environment variable

you can export it manually, use a library like `environs`, use a tool like `direnv`
or set it via python's `os` module
`os.environ.setdefault("SETTINGS_MODULE", "dir_to_file.settings")`

just be sure the env variable is set before accessing the settings


2. you can use `pyproject.toml` to declare the settings module:

```toml
[lazy-settings]
SETTINGS_MODULE = "some_dir.settings"
```
if env variable is defined, toml will **not** be read.

you can install `rtoml`(rust) or `tomli`(C) to speed up toml parsing, if none of these are installed, `tomllib` from stdlib will be used.
if both `rtoml` and `tomli` are installed, `rtoml` will be used.


#### settings object
you can use the `lazy_settings.conf.settings` object which hold all the settings in your project and packages that use this tool

the interface is like this:
```python
from lazy_settings.conf import settings

# read a settings and check its value
assert settings.MY_SETTINGS == "something"

# alter a setting (you probably shouldn't use this)
settings.MY_SETTINGS = "something else"

# loop over all settings
for setting in settings:
    print(setting)

# check if a setting exists
if getattr(settings, "THAT_SETTINGS"):
    pass
```

### for manual use
to manually configure the settings object, you can look at [django's docs](https://docs.djangoproject.com/en/5.2/topics/settings/#using-settings-without-setting-django-settings-module) since the same logic is used here

note that the register functionality is available here as well, tho, again, it's experimental.

## for package developers
put your projects default settings in a file (or a class)
all settings should be uppercased

then in a place where it's ensured to be read by python, have this code:

```python
from lazy_settings.conf import settings

from my_project import default_settings

settings.register(default_settings)
```

or you can use `getattr`.

note that the register functionality is experimental.


### for testing
`lazy-settings` comes with tools for testing.

these tools are avilable at `lazy_settings.test`.

test tools work with both `pytest` and `unittest`.

when used with pytest, if a class is decorated, a fixture called `settings_fixture` will be added to the class, so don't use the same name to prevent shadowing.

if a class is not a subclass of `unittest.TestCase`, it's considered a pytest test suite, so you can't use class decorators with mixin test classes.


#### override_settings
this can be used as both a context manager and a decorator to override a setting, the change will be reverted once the scope is over.

if used as a class decorator, all tests in class will be effected, if used as a function/method decorator, only that function will be effected

 
example with class test suite:

```python
from lazy_settings.test import override_settings
# pytest
@override_settings(A_SETTING="new value", NEW_SETTING="this wasn't in the file")
class TestOverridentSettings:
    def test_overriden_settings(self):
        assert settings.A_SETTING == "new value"
        assert settings.NEW_SETTING == "this wasn't in the file"


# async pytest        
@override_settings(A_SETTING="new value", NEW_SETTING="this wasn't in the file")
class TestOverridentSettingsAsync:
    @override_settings(A_SETTING="another one")
    async def test_override_after_override(self):
        assert settings.A_SETTING == "another one"



from unittest import TestCase, IsolatedAsyncioTestCase

# unittest
@override_settings(A_SETTING="new value", NEW_SETTING="this wasn't in the file")
class OverridentSettingsUnitTest(TestCase):
    def test_overriden_settings(self):
        self.assertEqual(settings.A_SETTING, "new value")
        self.assertEqual(settings.NEW_SETTING, "this wasn't in the file")
        


# async unittest        
@override_settings(A_SETTING="new value", NEW_SETTING="this wasn't in the file")
class AsyncOverridentSettingsUnitTest(IsolatedAsyncioTestCase):
    @override_settings(A_SETTING="another one")
    async def test_override_after_override(self):
        self.assertEqual(settings.A_SETTING, "another one")
```


example with function decorator:
```python
@override_settings(A_SETTING="something new")
def test_override_settings_function_decorator():
    assert settings.A_SETTING == "something new"


@override_settings(A_SETTING="something new")
async def test_override_settings_async_function_decorator():
    assert settings.A_SETTING == "something new"
```


example with context manager:
```python
def test_override_settings_context_manager_in_function():
    with override_settings(A_SETTING="context!!"):
        assert settings.A_SETTING == "context!!"

    assert settings.A_SETTING == "something"
```



#### modify_settings
modify_settings allows you to run `append`, `prepend` and `remove` so you don't have to re-write the list

this can also be used as both a decorator and a context manager


example as a class decorator
```python
rom lazy_settings.test import modify_settings

# pytest
@modify_settings(LIST_BASED_SETTING={"append": "three", "prepend": "zero"})
class TestModifySettings:
    def test_modified_settings(self):
        assert len(settings.LIST_BASED_SETTING) == 4
        assert settings.LIST_BASED_SETTING[0] == "zero"
        assert settings.LIST_BASED_SETTING[-1] == "three"


# async pytest        
@modify_settings(LIST_BASED_SETTING={"append": "three", "prepend": "zero"})
class TestModifySettingsAsync:
    @modify_settings(LIST_BASED_SETTING={"remove": "two"})
    async def test_modify_after_modify(self):
        assert len(settings.LIST_BASED_SETTING) == 3
        assert "two" not in settings.LIST_BASED_SETTING



from unittest import TestCase, IsolatedAsyncioTestCase        

# unittest        
@modify_settings(LIST_BASED_SETTING={"append": "three", "prepend": "zero"})
class ModifySettingsUnitTest(TestCase):
    def test_modified_settings(self):
        self.assertEqual(len(settings.LIST_BASED_SETTING), 4)
        self.assertEqual(settings.LIST_BASED_SETTING[0], "zero")
        self.assertEqual(settings.LIST_BASED_SETTING[-1], "three")



# async unittest        
@modify_settings(LIST_BASED_SETTING={"append": "three", "prepend": "zero"})
class AsyncModifySettingsUnitTest(IsolatedAsyncioTestCase):
    @modify_settings(LIST_BASED_SETTING={"remove": "two"})
    async def test_modify_after_modify(self):
        self.assertEqual(len(settings.LIST_BASED_SETTING), 3)
        self.assertNotIn("two", settings.LIST_BASED_SETTING)
```

example as function decorator
```python
@modify_settings(LIST_BASED_SETTING={"append": "things", "prepend": "first things"})
def test_modify_settings_fucntion_decorator():
    assert settings.LIST_BASED_SETTING == ["first things", "one", "two", "things"]


@modify_settings(LIST_BASED_SETTING={"append": "things", "prepend": "first things"})
async def test_modify_settings_async_fucntion_decorator():
    assert settings.LIST_BASED_SETTING == ["first things", "one", "two", "things"]
```


example as context manager
```python
def test_modify_settings_context_manager_in_function():
    with modify_settings(
        LIST_BASED_SETTING={"append": "three", "prepend": "zero"},
    ):
        assert settings.LIST_BASED_SETTING == ["zero", "one", "two", "three"]
    assert settings.LIST_BASED_SETTING == ["one", "two"]
```
