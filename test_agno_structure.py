# test_agno_structure.py
import agno.agent
import agno

print("=== agno.agent ===")
print(dir(agno.agent))

# Procurar por RunResponse
for module_name in ['models', 'response', 'types', 'core']:
    try:
        module = __import__(f'agno.{module_name}', fromlist=[''])
        print(f"\n=== agno.{module_name} ===")
        print(dir(module))
    except ImportError:
        print(f"\n✗ agno.{module_name} não existe")