import os
import sys
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root, 'cedisco_codegen'))

import cedisco_codegen
import cedisco_codegen

def test_pascal():
    assert cedisco_codegen.pascal("foo") == "Foo"
    assert cedisco_codegen.pascal("fooBar") == "FooBar"
    assert cedisco_codegen.pascal("foo_bar_baz") == "FooBarBaz"
    assert cedisco_codegen.pascal("fooBarBaz") == "FooBarBaz"
    assert cedisco_codegen.pascal("FooBarBaz") == "FooBarBaz"

def test_snake():
    assert cedisco_codegen.snake("foo") == "foo"
    assert cedisco_codegen.snake("fooBar") == "foo_bar"
    assert cedisco_codegen.snake("FooBarBaz") == "foo_bar_baz"
    assert cedisco_codegen.snake("fooBarBaz") == "foo_bar_baz"
    assert cedisco_codegen.snake("foo_bar_baz") == "foo_bar_baz"

def test_camel():
    assert cedisco_codegen.camel("foo") == "foo"
    assert cedisco_codegen.camel("foo_bar") == "fooBar"
    assert cedisco_codegen.camel("FooBarBaz") == "fooBarBaz"
    assert cedisco_codegen.camel("foo_bar_baz") == "fooBarBaz"
    assert cedisco_codegen.camel("fooBarBaz") == "fooBarBaz"

def test_regex_search():
    assert cedisco_codegen.regex_search("abc123", r"(\d+)")[0] == "123"
    assert len(cedisco_codegen.regex_search("abc", r"(\d+)")) == 0
    assert cedisco_codegen.regex_search("abc123", r"([a-z]+)")[0] == "abc"
    assert cedisco_codegen.regex_search("456abc", r"([a-z]+)")[0] == "abc"

def test_regex_replace():
    assert cedisco_codegen.regex_replace("abc123", r"(\d+)", "456") == "abc456"
    assert cedisco_codegen.regex_replace("abc123", r"([a-z]+)", "456") == "456123"    

def test_strip_invalid_identifier_characters():
    assert cedisco_codegen.strip_invalid_identifier_characters("foo") == "foo"
    assert cedisco_codegen.strip_invalid_identifier_characters("foo_bar") == "foo_bar"
    assert cedisco_codegen.strip_invalid_identifier_characters("$foo") == "_foo"
    assert cedisco_codegen.strip_invalid_identifier_characters("@foo") == "_foo"
    assert cedisco_codegen.strip_invalid_identifier_characters("%foo") == "_foo"

