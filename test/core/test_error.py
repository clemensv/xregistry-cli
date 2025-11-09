"""Test the error() Jinja extension."""
import os
import sys
import jinja2
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root))

from xregistry.generator.jinja_extensions import JinjaExtensions, TemplateError


def test_error_with_message():
    """Test that error() raises TemplateError with the correct message."""
    env = jinja2.Environment(extensions=[JinjaExtensions.ErrorExtension])
    template = "Processing data... {% error 'Invalid configuration detected' %}"
    
    with pytest.raises(TemplateError) as exc_info:
        env.from_string(template).render()
    
    assert str(exc_info.value) == "Invalid configuration detected"


def test_error_with_variable():
    """Test that error() works with variables."""
    env = jinja2.Environment(extensions=[JinjaExtensions.ErrorExtension])
    template = "{% set reason = 'Missing required field: name' %}{% error reason %}"
    
    with pytest.raises(TemplateError) as exc_info:
        env.from_string(template).render()
    
    assert str(exc_info.value) == "Missing required field: name"


def test_error_with_expression():
    """Test that error() works with expressions."""
    env = jinja2.Environment(extensions=[JinjaExtensions.ErrorExtension])
    template = "{% error 'Value ' + value + ' is not supported' %}"
    
    with pytest.raises(TemplateError) as exc_info:
        env.from_string(template).render(value="foo")
    
    assert str(exc_info.value) == "Value foo is not supported"


def test_error_stops_rendering():
    """Test that error() stops template rendering."""
    env = jinja2.Environment(extensions=[JinjaExtensions.ErrorExtension])
    template = "Start{% error 'Stop here' %}This should not render"
    
    with pytest.raises(TemplateError):
        result = env.from_string(template).render()
        # If we get here, error() didn't stop rendering
        assert False, "error() should have stopped rendering"


def test_conditional_error():
    """Test that error() can be used conditionally."""
    env = jinja2.Environment(extensions=[JinjaExtensions.ErrorExtension])
    template = "{% if invalid %}{% error 'Validation failed' %}{% endif %}Success"
    
    # Should raise error when condition is true
    with pytest.raises(TemplateError) as exc_info:
        env.from_string(template).render(invalid=True)
    assert str(exc_info.value) == "Validation failed"
    
    # Should succeed when condition is false
    result = env.from_string(template).render(invalid=False)
    assert result == "Success"
