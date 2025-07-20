"""
Setup do Knowledge Base com ChromaDB
Cria embeddings para cards, mechanics e discoveries
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import logging
from tqdm import tqdm
from datetime import datetime
import json
from pathlib import Path
import sys
import os
import shutil
from typing import List, Dict, Any, Optional
import hashlib
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Adiciona root do projeto ao path
sys.path.append(str(Path(__file__).parent.parent))

from data.sheets_client import get_sheets_client
from data.models import Card
from knowledge.eternal_skills import ALL_SKILLS, SKILL_SYNERGIES
from knowledge.eternal_synergies import DETAILED_SYNERGIES, MECHANICAL_PACKAGES

# =============================================================================
# 🚨 ÂNCORA: LOGGING_SETUP - Configuração de logs em arquivo
# Contexto: Logs salvos em data/logs/ com rotação diária
# Cuidado: Cria pasta se não existir
# Dependências: Todos os módulos usam este logger
# =============================================================================

# Setup logging
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f"knowledge_setup_{datetime.now():%Y%m%d}.log", encoding='utf-8'),
        logging.StreamHandler()  # Também mostra no console
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# 🚨 ÂNCORA: CHECKPOINT_SYSTEM - Sistema de checkpoint para retomar
# Contexto: Salva progresso a cada N items processados
# Cuidado: Formato JSON deve ser mantido compatível
# Dependências: Auto-recovery depende deste formato
# =============================================================================

class CheckpointManager:
    """Gerencia checkpoints para retomar processamento"""
    
    def __init__(self, checkpoint_path: str = "data/chromadb/.setup_progress"):
        self.checkpoint_path = Path(checkpoint_path)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        
    def save(self, data: Dict[str, Any]):
        """Salva checkpoint atomicamente"""
        temp_path = self.checkpoint_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        # Move atomicamente para evitar corrupção
        temp_path.replace(self.checkpoint_path)
        
    def load(self) -> Optional[Dict[str, Any]]:
        """Carrega checkpoint se existir"""
        if self.checkpoint_path.exists():
            try:
                with open(self.checkpoint_path) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar checkpoint: {e}")
        return None
        
    def clear(self):
        """Remove checkpoint após conclusão"""
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()

# =============================================================================
# 🚨 ÂNCORA: EMBEDDING_OPTIMIZATION - Criação otimizada de embeddings
# Contexto: Embeddings ricos para melhor descoberta de sinergias
# Cuidado: Formato afeta qualidade da busca semântica
# Dependências: search_engine.py espera este formato
# =============================================================================

class EmbeddingOptimizer:
    """Cria embeddings otimizados para descoberta de sinergias"""
    
    @staticmethod
    def create_card_embedding_text(card: Card) -> str:
        """
        Cria texto rico para embedding de carta
        Inclui triggers, effects e keywords para melhor matching
        """
        # Extrai componentes mecânicos
        triggers = EmbeddingOptimizer._extract_triggers(card.card_text)
        effects = EmbeddingOptimizer._extract_effects(card.card_text)
        keywords = EmbeddingOptimizer._extract_keywords(card.card_text)
        
        # Formata influência de forma searchable
        influence_text = card.influence.replace("{", "").replace("}", " influence ")
        
        # Cria embedding text rico
        embedding_text = f"""
{card.name} {card.type} {card.cost} cost {influence_text}
Card Text: {card.card_text}
Triggers: {' '.join(triggers)}
Effects: {' '.join(effects)}
Keywords: {' '.join(keywords)}
Stats: {f"{card.attack}/{card.health}" if card.is_unit else ""}
Rarity: {card.rarity}
""".strip()
        
        return embedding_text
    
    @staticmethod
    def _extract_triggers(text: str) -> List[str]:
        """Extrai palavras que indicam triggers"""
        trigger_words = ["when", "whenever", "at the", "if", "after", "before"]
        found = []
        text_lower = text.lower()
        for trigger in trigger_words:
            if trigger in text_lower:
                found.append(trigger)
        return found
    
    @staticmethod
    def _extract_effects(text: str) -> List[str]:
        """Extrai tipos de efeitos"""
        effect_words = ["draw", "deal", "gain", "create", "destroy", "kill", 
                       "return", "reduce", "increase", "give", "get", "play"]
        found = []
        text_lower = text.lower()
        for effect in effect_words:
            if effect in text_lower:
                found.append(effect)
        return found
    
    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """Extrai keywords importantes"""
        # Adiciona skills conhecidas se mencionadas
        keywords = []
        text_lower = text.lower()
        
        for skill in ALL_SKILLS.keys():
            if skill.lower() in text_lower:
                keywords.append(skill)
                
        # Adiciona outros termos importantes
        important_terms = ["market", "void", "spell", "unit", "weapon", "relic",
                          "power", "influence", "exhaust", "ready", "attack", "block"]
        for term in important_terms:
            if term in text_lower:
                keywords.append(term)
                
        return keywords

# =============================================================================
# 🚨 ÂNCORA: KNOWLEDGE_BASE_SETUP - Classe principal de setup
# Contexto: Gerencia criação e atualização de todas as collections
# Cuidado: Ordem de criação importa (cards primeiro)
# Dependências: Agentes esperam estas collections existirem
# =============================================================================

class KnowledgeBaseSetup:
    """Setup e gerenciamento do Knowledge Base com ChromaDB"""
    
    def __init__(self, test_mode: bool = False, batch_size: int = 100):
        """
        Args:
            test_mode: Se True, processa apenas 50 cartas para teste
            batch_size: Tamanho do batch para processamento
        """
        self.test_mode = test_mode
        self.batch_size = batch_size
        self.checkpoint = CheckpointManager()
        self.optimizer = EmbeddingOptimizer()
        
        logger.info(f"🚀 Iniciando Knowledge Base Setup (test_mode={test_mode})")
        
        # Carrega modelo de embeddings
        self.embedding_model = self._load_embedding_model()
        
        # Setup ChromaDB
        self.chroma_client = self._setup_chromadb()
        
        # Cliente do Sheets
        self.sheets_client = None
        
    def _load_embedding_model(self) -> SentenceTransformer:
        """Carrega modelo de embeddings com retry e cache"""
        model_name = "sentence-transformers/all-mpnet-base-v2"
        cache_dir = Path("data/models")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📦 Carregando modelo de embeddings: {model_name}")
        
        try:
            model = SentenceTransformer(model_name, cache_folder=str(cache_dir))
            logger.info(f"✅ Modelo carregado: {model.get_sentence_embedding_dimension()} dimensões")
            return model
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            raise
            
    def _setup_chromadb(self) -> chromadb.Client:
        """Configura ChromaDB com persistência e backup"""
        persist_dir = Path("data/chromadb")
        persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup se existir
        if (persist_dir / "chroma.sqlite3").exists():
            self._backup_chromadb()
        
        logger.info(f"🗄️ Configurando ChromaDB em: {persist_dir}")
        
        client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(
                anonymized_telemetry=False,
                persist_directory=str(persist_dir)
            )
        )
        
        return client
    
    def _backup_chromadb(self):
        """Cria backup do ChromaDB existente"""
        backup_dir = Path("data/chromadb_backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"backup_{timestamp}"
        
        logger.info(f"💾 Criando backup em: {backup_path}")
        shutil.copytree("data/chromadb", backup_path, dirs_exist_ok=True)
    
    # =============================================================================
    # 🚨 ÂNCORA: COLLECTION_SETUP - Criação das 3 collections
    # Contexto: Cada collection tem propósito específico
    # Cuidado: IDs devem ser únicos e determinísticos
    # Dependências: Agentes buscam por estes nomes exatos
    # =============================================================================
    
    def setup_all_collections(self):
        """Setup completo das 3 collections com recovery"""
        start_time = datetime.now()
        logger.info("🏗️ Iniciando setup completo do Knowledge Base")
        
        # Verifica checkpoint
        checkpoint_data = self.checkpoint.load()
        if checkpoint_data:
            logger.info(f"📊 Checkpoint encontrado: {checkpoint_data.get('status')}")
            
        try:
            # 1. Collection de cartas
            self._setup_cards_collection(checkpoint_data)
            
            # 2. Collection de mecânicas
            self._setup_mechanics_collection(checkpoint_data)
            
            # 3. Collection de descobertas
            self._setup_discoveries_collection(checkpoint_data)
            
            # Limpa checkpoint após sucesso
            self.checkpoint.clear()
            
            elapsed = datetime.now() - start_time
            logger.info(f"✅ Setup completo em {elapsed.total_seconds():.1f} segundos")
            
            # Mostra estatísticas
            self._show_statistics()
            
        except Exception as e:
            logger.error(f"❌ Erro durante setup: {e}")
            logger.info("💡 Execute novamente para continuar de onde parou")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    def _setup_cards_collection(self, checkpoint_data: Optional[Dict] = None):
        """Configura collection de cartas com retry"""
        collection_name = "eternal_cards"
        
        # Verifica se já está completo
        if checkpoint_data and checkpoint_data.get(f"{collection_name}_complete"):
            logger.info(f"✅ {collection_name} já está completo")
            return
            
        logger.info(f"📚 Configurando collection: {collection_name}")
        
        # Conecta ao Sheets
        if not self.sheets_client:
            self.sheets_client = get_sheets_client()
            
        # Carrega cartas
        all_cards = self.sheets_client.get_all_cards()
        if self.test_mode:
            all_cards = all_cards[:50]
            logger.info(f"🧪 Modo teste: processando apenas {len(all_cards)} cartas")
        
        # Cria ou pega collection
        try:
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "Todas as cartas do Eternal Card Game"}
            )
            logger.info(f"✨ Collection '{collection_name}' criada")
        except Exception:
            collection = self.chroma_client.get_collection(collection_name)
            logger.info(f"📂 Collection '{collection_name}' já existe")
        
        # Processa em batches
        start_idx = checkpoint_data.get(f"{collection_name}_processed", 0) if checkpoint_data else 0
        
        for i in tqdm(range(start_idx, len(all_cards), self.batch_size), 
                     desc="Processando cartas", 
                     initial=start_idx//self.batch_size):
            batch_cards = all_cards[i:i + self.batch_size]
            
            # Prepara dados do batch
            ids = []
            embeddings = []
            metadatas = []
            documents = []
            
            for card in batch_cards:
                # ID determinístico baseado no nome
                card_id = hashlib.md5(card.name.encode()).hexdigest()
                ids.append(card_id)
                
                # Texto para embedding
                embedding_text = self.optimizer.create_card_embedding_text(card)
                documents.append(embedding_text)
                
                # Metadata
                metadata = {
                    "name": card.name,
                    "cost": card.cost,
                    "influence": card.influence,
                    "type": card.type,
                    "rarity": card.rarity,
                    "set_number": card.set_number,
                    "eternal_id": card.eternal_id or "",
                    "attack": card.attack or -1,
                    "health": card.health or -1,
                    "is_unit": card.is_unit,
                    "is_power": card.is_power,
                    "is_spell": card.is_spell,
                    "can_access_market": card.can_access_market
                }
                metadatas.append(metadata)
            
            # Cria embeddings
            embeddings = self.embedding_model.encode(documents, show_progress_bar=False)
            
            # Adiciona ao ChromaDB
            collection.add(
                ids=ids,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                documents=documents
            )
            
            # Salva checkpoint
            self.checkpoint.save({
                "status": "processing_cards",
                f"{collection_name}_processed": i + len(batch_cards),
                f"{collection_name}_total": len(all_cards),
                "timestamp": datetime.now().isoformat()
            })
        
        # Marca como completo
        checkpoint_final = self.checkpoint.load() or {}
        checkpoint_final[f"{collection_name}_complete"] = True
        self.checkpoint.save(checkpoint_final)
        
        logger.info(f"✅ {len(all_cards)} cartas processadas com sucesso")
    
    def _setup_mechanics_collection(self, checkpoint_data: Optional[Dict] = None):
        """Configura collection de mecânicas e sinergias"""
        collection_name = "eternal_mechanics"
        
        # Verifica se já está completo
        if checkpoint_data and checkpoint_data.get(f"{collection_name}_complete"):
            logger.info(f"✅ {collection_name} já está completo")
            return
            
        logger.info(f"🔧 Configurando collection: {collection_name}")
        
        # Cria ou pega collection
        try:
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "Skills e sinergias do Eternal"}
            )
            logger.info(f"✨ Collection '{collection_name}' criada")
        except Exception:
            collection = self.chroma_client.get_collection(collection_name)
            logger.info(f"📂 Collection '{collection_name}' já existe")
        
        # Processa skills
        logger.info("⚙️ Processando skills...")
        skill_ids = []
        skill_embeddings = []
        skill_metadatas = []
        skill_documents = []
        
        for skill_name, skill_data in ALL_SKILLS.items():
            # ID único
            skill_id = f"skill_{hashlib.md5(skill_name.encode()).hexdigest()[:8]}"
            skill_ids.append(skill_id)
            
            # Texto para embedding
            embedding_text = f"""
{skill_name} Skill
Description: {skill_data['description']}
Synergies: {', '.join(skill_data['synergies'])}
Counters: {', '.join(skill_data['counters'])}
Archetypes: {', '.join(skill_data['archetypes'])}
Strategic Role: {', '.join(skill_data['deck_role'])}
{skill_data['embed_text']}
""".strip()
            skill_documents.append(embedding_text)
            
            # Metadata
            metadata = {
                "type": "skill",
                "name": skill_name,
                "power_level": skill_data['power_level'],
                "complexity": skill_data['complexity'],
                "archetypes": ",".join(skill_data['archetypes'])
            }
            skill_metadatas.append(metadata)
        
        # Processa sinergias de skills (SKILL_SYNERGIES)
        logger.info("🔗 Processando sinergias de skills...")
        
        for (skill1, skill2), synergy_data in SKILL_SYNERGIES.items():
            # ID único
            synergy_id = f"skillsyn_{hashlib.md5(f'{skill1}_{skill2}'.encode()).hexdigest()[:8]}"
            skill_ids.append(synergy_id)
            
            # Texto para embedding
            embedding_text = f"""
{skill1} + {skill2} Skill Synergy
Skills: {skill1}, {skill2}
How it works: {synergy_data['description']}
Strength: {synergy_data['strength']}/5
Examples: {', '.join(synergy_data.get('examples', []))}
""".strip()
            skill_documents.append(embedding_text)
            
            # Metadata
            metadata = {
                "type": "skill_synergy",
                "name": f"{skill1}_{skill2}",
                "strength": synergy_data['strength'],
                "skills": f"{skill1},{skill2}"
            }
            skill_metadatas.append(metadata)
        
        # Processa sinergias detalhadas
        logger.info("🔗 Processando sinergias...")
        
        for synergy_name, synergy_data in DETAILED_SYNERGIES.items():
            # ID único
            synergy_id = f"synergy_{hashlib.md5(synergy_name.encode()).hexdigest()[:8]}"
            skill_ids.append(synergy_id)
            
            # Texto para embedding
            embedding_text = f"""
{synergy_name} Synergy
Skills: {', '.join(synergy_data['skills'])}
How it works: {synergy_data['mechanics']}
Requirements: {synergy_data['requirements']}
Strategic value: {synergy_data['strategic_value']}
Limitations: {synergy_data['limitations']}
Strength: {synergy_data['strength']}/5
""".strip()
            skill_documents.append(embedding_text)
            
            # Metadata
            metadata = {
                "type": "synergy",
                "name": synergy_name,
                "strength": synergy_data['strength'],
                "skills": ",".join(synergy_data['skills'])
            }
            skill_metadatas.append(metadata)
        
        # Processa packages mecânicos
        for package_name, package_data in MECHANICAL_PACKAGES.items():
            # ID único
            package_id = f"package_{hashlib.md5(package_name.encode()).hexdigest()[:8]}"
            skill_ids.append(package_id)
            
            # Texto para embedding
            embedding_text = f"""
{package_name} Package
Core mechanics: {', '.join(package_data['core_mechanics'])}
Support mechanics: {', '.join(package_data['support_mechanics'])}
Description: {package_data['synergy_description']}
Win condition: {package_data['win_condition']}
Weaknesses: {', '.join(package_data['weaknesses'])}
""".strip()
            skill_documents.append(embedding_text)
            
            # Metadata
            metadata = {
                "type": "package",
                "name": package_name,
                "core_mechanics": ",".join(package_data['core_mechanics'])
            }
            skill_metadatas.append(metadata)
        
        # Cria embeddings e adiciona
        if skill_documents:
            embeddings = self.embedding_model.encode(skill_documents, show_progress_bar=True)
            
            collection.add(
                ids=skill_ids,
                embeddings=embeddings.tolist(),
                metadatas=skill_metadatas,
                documents=skill_documents
            )
        
        # Marca como completo
        checkpoint_final = self.checkpoint.load() or {}
        checkpoint_final[f"{collection_name}_complete"] = True
        self.checkpoint.save(checkpoint_final)
        
        logger.info(f"✅ {len(skill_ids)} mecânicas processadas com sucesso")
    
    def _setup_discoveries_collection(self, checkpoint_data: Optional[Dict] = None):
        """Configura collection de descobertas (inicialmente vazia)"""
        collection_name = "discovered_synergies"
        
        # Verifica se já está completo
        if checkpoint_data and checkpoint_data.get(f"{collection_name}_complete"):
            logger.info(f"✅ {collection_name} já está completo")
            return
            
        logger.info(f"🔍 Configurando collection: {collection_name}")
        
        # Cria collection vazia para descobertas futuras
        try:
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={
                    "description": "Sinergias descobertas pela IA",
                    "created_at": datetime.now().isoformat()
                }
            )
            logger.info(f"✨ Collection '{collection_name}' criada (vazia, será populada durante uso)")
        except Exception:
            collection = self.chroma_client.get_collection(collection_name)
            logger.info(f"📂 Collection '{collection_name}' já existe")
        
        # Marca como completo
        checkpoint_final = self.checkpoint.load() or {}
        checkpoint_final[f"{collection_name}_complete"] = True
        self.checkpoint.save(checkpoint_final)
    
    def _show_statistics(self):
        """Mostra estatísticas das collections"""
        logger.info("\n📊 Estatísticas do Knowledge Base:")
        
        collections = ["eternal_cards", "eternal_mechanics", "discovered_synergies"]
        
        for coll_name in collections:
            try:
                collection = self.chroma_client.get_collection(coll_name)
                count = collection.count()
                logger.info(f"  • {coll_name}: {count} items")
            except Exception as e:
                logger.info(f"  • {coll_name}: não encontrada ({e})")
    
    # =============================================================================
    # 🚨 ÂNCORA: TEST_FUNCTIONS - Funções para testar busca semântica
    # Contexto: Permite validar que embeddings funcionam corretamente
    # Cuidado: Usa mesma lógica que search_engine.py usará
    # Dependências: Testes devem passar antes de usar em produção
    # =============================================================================
    
    def test_search(self, query: str, collection_name: str = "eternal_cards", n_results: int = 5):
        """
        Testa busca semântica em uma collection
        
        Args:
            query: Texto da busca
            collection_name: Nome da collection
            n_results: Número de resultados
        """
        logger.info(f"\n🔍 Testando busca: '{query}' em {collection_name}")
        
        try:
            collection = self.chroma_client.get_collection(collection_name)
            
            # Cria embedding da query
            query_embedding = self.embedding_model.encode([query])
            
            # Busca
            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=n_results
            )
            
            # Mostra resultados
            logger.info(f"\n📋 Top {n_results} resultados:")
            
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0], 
                results['metadatas'][0],
                results['distances'][0]
            )):
                logger.info(f"\n{i+1}. {metadata.get('name', 'Unknown')}")
                logger.info(f"   Distância: {distance:.4f}")
                logger.info(f"   Tipo: {metadata.get('type', 'Unknown')}")
                
                # Mostra preview do documento
                preview = doc[:200] + "..." if len(doc) > 200 else doc
                logger.info(f"   Preview: {preview}")
                
        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            
    def run_test_suite(self):
        """Executa suite de testes para validar setup"""
        logger.info("\n🧪 Executando suite de testes...")
        
        test_queries = [
            # Testes em cards
            ("deadly quickdraw removal", "eternal_cards"),
            ("flying charge aggro", "eternal_cards"),
            ("market access merchant", "eternal_cards"),
            ("void recursion shadow", "eternal_cards"),
            
            # Testes em mechanics
            ("how to counter flying", "eternal_mechanics"),
            ("best aggressive synergies", "eternal_mechanics"),
            ("combo enablers", "eternal_mechanics")
        ]
        
        for query, collection in test_queries:
            self.test_search(query, collection, n_results=3)
            
        logger.info("\n✅ Suite de testes concluída")


# =============================================================================
# 🚨 ÂNCORA: MAIN_EXECUTION - Script principal
# Contexto: Permite executar diretamente para setup inicial
# Cuidado: Em produção será importado, não executado
# Dependências: Agentes importam as classes, não executam main
# =============================================================================

def main():
    """Função principal para setup"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup do Knowledge Base para Eternal Deck Builder")
    parser.add_argument("--test", action="store_true", help="Modo teste (50 cartas)")
    parser.add_argument("--search", type=str, help="Testa busca com query")
    parser.add_argument("--stats", action="store_true", help="Mostra apenas estatísticas")
    parser.add_argument("--reset", action="store_true", help="Reset completo (remove tudo)")
    
    args = parser.parse_args()
    
    if args.reset:
        confirm = input("⚠️  Isso vai APAGAR todo o knowledge base. Confirma? [y/N]: ")
        if confirm.lower() == 'y':
            logger.info("🗑️ Removendo knowledge base...")
            shutil.rmtree("data/chromadb", ignore_errors=True)
            Path("data/chromadb/.setup_progress").unlink(missing_ok=True)
            logger.info("✅ Knowledge base removido")
        return
    
    # Cria instância
    kb = KnowledgeBaseSetup(test_mode=args.test)
    
    if args.stats:
        kb._show_statistics()
    elif args.search:
        kb.test_search(args.search)
    else:
        # Setup completo
        kb.setup_all_collections()
        
        # Executa testes
        if args.test:
            kb.run_test_suite()


if __name__ == "__main__":
    main()