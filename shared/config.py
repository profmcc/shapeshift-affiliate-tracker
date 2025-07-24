"""
shared.config

Centralized configuration loader for listeners. Loads .env and YAML config files.

Example usage:
    from shared.config import load_config
    config = load_config('listeners/portals_listener_config.yaml')
"""
import os
import yaml
import re
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, '.env')

# Always load .env from the project root
load_dotenv(ENV_PATH)

def load_yaml_config(config_path):
    """
    Load a YAML config file and substitute ${VAR} with environment variables.
    Args:
        config_path (str): Path to the YAML config file.
    Returns:
        dict: The loaded and environment-substituted config.
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    pattern = re.compile(r'\$\{([^}]+)\}')
    def replace_env(val):
        if isinstance(val, str):
            return pattern.sub(lambda m: os.getenv(m.group(1), m.group(0)), val)
        if isinstance(val, dict):
            return {k: replace_env(v) for k, v in val.items()}
        if isinstance(val, list):
            return [replace_env(v) for v in val]
        return val
    return replace_env(config)

def load_config(config_path):
    """
    Load a YAML config file and substitute ${VAR} with environment variables.
    Alias for load_yaml_config for consistency.
    
    Args:
        config_path (str): Path to the YAML config file.
    Returns:
        dict: The loaded and environment-substituted config.
    """
    return load_yaml_config(config_path) 