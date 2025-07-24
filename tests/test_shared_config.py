import os
import tempfile
import pytest
from shared.config import load_yaml_config

def test_load_yaml_config_env_substitution(monkeypatch):
    monkeypatch.setenv('TEST_ENV_VAR', 'env_value')
    yaml_content = '''
    foo: bar
    env: ${TEST_ENV_VAR}
    nested:
      key: ${TEST_ENV_VAR}
    '''
    with tempfile.NamedTemporaryFile('w+', delete=False) as f:
        f.write(yaml_content)
        f.flush()
        config = load_yaml_config(f.name)
    assert config['foo'] == 'bar'
    assert config['env'] == 'env_value'
    assert config['nested']['key'] == 'env_value' 