import os
import sys
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root))

from ceregistry.generate_code import *


def test_pascal():
    assert pascal("foo") == "Foo"
    assert pascal("fooBar") == "FooBar"
    assert pascal("foo_bar_baz") == "FooBarBaz"
    assert pascal("fooBarBaz") == "FooBarBaz"
    assert pascal("FooBarBaz") == "FooBarBaz"

def test_snake():
    assert snake("foo") == "foo"
    assert snake("fooBar") == "foo_bar"
    assert snake("FooBarBaz") == "foo_bar_baz"
    assert snake("fooBarBaz") == "foo_bar_baz"
    assert snake("foo_bar_baz") == "foo_bar_baz"

def test_camel():
    assert camel("foo") == "foo"
    assert camel("foo_bar") == "fooBar"
    assert camel("FooBarBaz") == "fooBarBaz"
    assert camel("foo_bar_baz") == "fooBarBaz"
    assert camel("fooBarBaz") == "fooBarBaz"

def test_regex_search():
    assert regex_search("abc123", r"(\d+)")[0] == "123"
    assert len(regex_search("abc", r"(\d+)")) == 0
    assert regex_search("abc123", r"([a-z]+)")[0] == "abc"
    assert regex_search("456abc", r"([a-z]+)")[0] == "abc"

def test_regex_replace():
    assert regex_replace("abc123", r"(\d+)", "456") == "abc456"
    assert regex_replace("abc123", r"([a-z]+)", "456") == "456123"    

def test_strip_invalid_identifier_characters():
    assert strip_invalid_identifier_characters("foo") == "foo"
    assert strip_invalid_identifier_characters("foo_bar") == "foo_bar"
    assert strip_invalid_identifier_characters("$foo") == "_foo"
    assert strip_invalid_identifier_characters("@foo") == "_foo"
    assert strip_invalid_identifier_characters("%foo") == "_foo"

