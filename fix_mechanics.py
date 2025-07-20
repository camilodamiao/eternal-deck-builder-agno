"""
Script para deletar e recriar a collection eternal_mechanics
Corrige o problema de ter apenas 51 items ao invés de ~63
"""
import chromadb
from pathlib import Path
import json
import sys

print("🔧 Fix Mechanics Collection Script")
print("-" * 50)

# Conecta ao ChromaDB
print("📂 Conectando ao ChromaDB...")
client = chromadb.PersistentClient(path="data/chromadb")

# Lista collections atuais
print("\n📊 Collections atuais:")
for coll in client.list_collections():
    count = coll.count()
    print(f"  • {coll.name}: {count} items")

# Confirma antes de deletar
response = input("\n⚠️  Deletar 'eternal_mechanics' collection? [y/N]: ")
if response.lower() != 'y':
    print("❌ Cancelado pelo usuário")
    sys.exit(0)

# Deleta APENAS mechanics
try:
    client.delete_collection("eternal_mechanics")
    print("✅ Collection eternal_mechanics deletada com sucesso")
except Exception as e:
    print(f"❌ Erro ao deletar: {e}")
    sys.exit(1)

# Cria checkpoint falso para forçar reprocessamento APENAS de mechanics
checkpoint_path = Path("data/chromadb/.setup_progress")
checkpoint_data = {
    "eternal_cards_complete": True,  # Não reprocessar cards
    "eternal_mechanics_complete": False,  # REPROCESSAR mechanics
    "discovered_synergies_complete": True,  # Não reprocessar discoveries
    "status": "processing_mechanics"
}

print("\n📝 Criando checkpoint para reprocessar apenas mechanics...")
checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
with open(checkpoint_path, 'w') as f:
    json.dump(checkpoint_data, f, indent=2)

print("✅ Checkpoint criado")
print("\n📌 Próximos passos:")
print("1. Execute: python -m rag.setup_knowledge")
print("2. Apenas eternal_mechanics será reprocessada")
print("3. Deve resultar em ~63 items (37 skills + 12 skill synergies + 14 outros)")
print("\n⏱️  Tempo estimado: 1-2 minutos")