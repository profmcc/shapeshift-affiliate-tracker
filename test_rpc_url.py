from dotenv import load_dotenv
import os, yaml, re

load_dotenv()
with open('listeners/portals_listener_config.yaml', 'r') as f:
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
config = replace_env(config)
print(config['chains']['ethereum']['rpc_url']) 