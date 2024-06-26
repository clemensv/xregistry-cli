import os
import sys
import pytest

from xregistry.generator.jinja_filters import JinjaFilters

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root))

from xregistry.commands.generate_code import *

def test_pascal():
    jf = JinjaFilters()
    assert jf.pascal("foo") == "Foo"
    assert jf.pascal("fooBar") == "FooBar"
    assert jf.pascal("foo_bar_baz") == "FooBarBaz"
    assert jf.pascal("fooBarBaz") == "FooBarBaz"
    assert jf.pascal("FooBarBaz") == "FooBarBaz"

def test_snake():
    jf = JinjaFilters()
    assert jf.snake("foo") == "foo"
    assert jf.snake("fooBar") == "foo_bar"
    assert jf.snake("FooBarBaz") == "foo_bar_baz"
    assert jf.snake("fooBarBaz") == "foo_bar_baz"
    assert jf.snake("foo_bar_baz") == "foo_bar_baz"

def test_camel():
    jf = JinjaFilters()
    assert jf.camel("foo") == "foo"
    assert jf.camel("foo_bar") == "fooBar"
    assert jf.camel("FooBarBaz") == "fooBarBaz"
    assert jf.camel("foo_bar_baz") == "fooBarBaz"
    assert jf.camel("fooBarBaz") == "fooBarBaz"

def test_regex_search():
    jf = JinjaFilters()
    assert jf.regex_search("abc123", r"(\d+)")[0] == "123"
    assert len(jf.regex_search("abc", r"(\d+)")) == 0
    assert jf.regex_search("abc123", r"([a-z]+)")[0] == "abc"
    assert jf.regex_search("456abc", r"([a-z]+)")[0] == "abc"

def test_regex_replace():
    jf = JinjaFilters()
    assert jf.regex_replace("abc123", r"(\d+)", "456") == "abc456"
    assert jf.regex_replace("abc123", r"([a-z]+)", "456") == "456123"    

def test_strip_invalid_identifier_characters():
    jf = JinjaFilters()
    assert jf.strip_invalid_identifier_characters("foo") == "foo"
    assert jf.strip_invalid_identifier_characters("foo_bar") == "foo_bar"
    assert jf.strip_invalid_identifier_characters("$foo") == "_foo"
    assert jf.strip_invalid_identifier_characters("@foo") == "_foo"
    assert jf.strip_invalid_identifier_characters("%foo") == "_foo"

