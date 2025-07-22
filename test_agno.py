# test_agno.py - arquivo de teste rápido
import agno
print("Agno version:", agno.__version__ if hasattr(agno, '__version__') else "Unknown")
print("Available in agno:", dir(agno))

# Tentar importações comuns
try:
    from agno import Agent
    print("✓ Agent importado com sucesso")
except ImportError as e:
    print("✗ Agent não encontrado:", e)

try:
    from agno.agent import Agent
    print("✓ Agent encontrado em agno.agent")
except ImportError as e:
    print("✗ Agent não em agno.agent:", e)

try:
    from agno import Assistant
    print("✓ Assistant encontrado")
except ImportError as e:
    print("✗ Assistant não encontrado:", e)