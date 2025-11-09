"""Integration test for error() extension in template renderer."""
import os
import sys
import tempfile
import jinja2

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root))

from xregistry.generator.jinja_extensions import JinjaExtensions, TemplateError
import pytest


def test_error_extension_registered():
    """Test that error() extension can be registered in Jinja environment."""
    # Create environment with all three extensions (like template_renderer does)
    env = jinja2.Environment(extensions=[
        JinjaExtensions.ExitExtension, 
        JinjaExtensions.TimeExtension, 
        JinjaExtensions.ErrorExtension
    ])
    
    # Verify ErrorExtension is in the environment (extensions dict uses full class path)
    extension_names = [ext.split('.')[-1] for ext in env.extensions.keys()]
    assert 'ErrorExtension' in extension_names
    assert 'ExitExtension' in extension_names
    assert 'TimeExtension' in extension_names
    
    # Test that the error extension works correctly
    template = env.from_string("Before\n{% error 'Custom error message' %}\nAfter")
    with pytest.raises(TemplateError) as exc_info:
        template.render()
    
    assert str(exc_info.value) == "Custom error message"


def test_error_with_all_extensions():
    """Test that error() works alongside other extensions."""
    env = jinja2.Environment(extensions=[
        JinjaExtensions.ExitExtension, 
        JinjaExtensions.TimeExtension, 
        JinjaExtensions.ErrorExtension
    ])
    
    # Test time extension works
    template = env.from_string("Time: {% time %}")
    result = template.render()
    assert "Time: " in result
    assert "Z" in result  # ISO format timestamp
    
    # Test error extension works
    template = env.from_string("{% if fail %}{% error 'Failed' %}{% endif %}OK")
    with pytest.raises(TemplateError):
        template.render(fail=True)
    
    # Test success case
    result = template.render(fail=False)
    assert result == "OK"

