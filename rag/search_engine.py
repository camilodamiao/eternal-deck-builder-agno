"""
Search Engine para Eternal Deck Builder
Busca semântica com filtros determinísticos
"""

import chromadb
from chromadb.config import Settings
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import logging
from datetime import datetime
import time
from sentence_transformers import SentenceTransformer

# Imports do projeto
import sys
sys.path.append(str(Path(__file__).parent.parent))

from data.models import Card
from data.sheets_client import get_sheets_client
from config import FACTION_SYMBOLS, MODEL_CONFIGS

# =============================================================================
# 🚨 ÂNCORA: SEARCH_FILTERS - Filtros determinísticos para busca
# Contexto: Permite controle preciso sobre que cartas considerar
# Cuidado: Alguns filtros são pré-busca (ChromaDB) outros pós-busca (Python)
# Dependências: UI passará estes filtros, agentes podem criar programaticamente
# =============================================================================

@dataclass
class SearchFilters:
   """Filtros determinísticos para busca de cartas"""
   
   # Facções
   allowed_factions: Optional[List[str]] = None      # ["Fire", "Time"] 
   max_factions_per_card: Optional[int] = None       # 1-5
   
   # Formato e Raridade  
   format: str = "Throne"                            # "Throne" ou "Expedition"
   max_rarity: Optional[str] = None                  # "Common", "Uncommon", "Rare"
   
   # Arquétipo (para contexto, não filtra diretamente)
   archetype: Optional[str] = None                   # "Aggro", "Control", etc
   
   # Custos
   min_cost: Optional[int] = None
   max_cost: Optional[int] = None
   
   # Tipos
   card_types: Optional[List[str]] = None            # ["Unit", "Spell"]
   unit_types: Optional[List[str]] = None            # ["Valkyrie", "Oni"]
   
   # Cartas específicas
   must_include: Optional[List[str]] = None          # Sempre incluir estas
   must_exclude: Optional[List[str]] = None          # Nunca incluir estas
   
   # Mercado
   include_market: bool = True                       # Incluir merchants/smugglers
   market_access_only: bool = False                  # APENAS merchants

@dataclass 
class SearchResult:
   """Resultado estruturado da busca"""
   cards: List[Card]
   total_found: int
   query: str
   query_interpretation: str
   filters_applied: Optional[SearchFilters]
   search_time: float
   used_chromadb: bool = True

# =============================================================================
# 🚨 ÂNCORA: SEARCH_ENGINE - Motor de busca híbrido
# Contexto: Combina busca semântica (ChromaDB) com filtros determinísticos
# Cuidado: ChromaDB trata palavras independentemente (bag of words)
# Dependências: StrategyScoutAgent e UI usarão este engine
# =============================================================================

class SearchEngine:
   """Motor de busca híbrido para cartas Eternal"""
   
   def __init__(self, chroma_path: str = "data/chromadb"):
       """Inicializa engine com ChromaDB e cache de cartas"""
       self.logger = logging.getLogger(__name__)
       
       # 🚨 ÂNCORA: CHROMADB_INIT - Conexão com base vetorial
       # Contexto: Usa collections já criadas por setup_knowledge.py
       # Cuidado: Se path não existe, falha gracefully
       # Dependências: setup_knowledge.py deve ter rodado antes
       try:
           self.chroma_client = chromadb.PersistentClient(
               path=chroma_path,
               settings=Settings(anonymized_telemetry=False)
           )
           self.cards_collection = self.chroma_client.get_collection("eternal_cards")
           self.chromadb_available = True
           self.logger.info(f"✅ ChromaDB conectado: {self.cards_collection.count()} cartas")
       except Exception as e:
           self.logger.warning(f"⚠️ ChromaDB não disponível: {e}")
           self.chromadb_available = False
           
       # Modelo de embeddings (só se ChromaDB disponível)
       if self.chromadb_available:
           model_name = "sentence-transformers/all-mpnet-base-v2"
           cache_dir = Path("data/models")
           self.embedding_model = SentenceTransformer(model_name, cache_folder=str(cache_dir))
       
       # 🚨 ÂNCORA: CARD_CACHE - Cache completo em memória
       # Contexto: 4256 cartas = ~1.5MB, vale a pena cachear
       # Cuidado: Singleton do sheets_client já faz cache
       # Dependências: Fallback quando ChromaDB não disponível
       self.sheets_client = get_sheets_client()
       self._load_card_cache()
       
   def _load_card_cache(self):
       """Carrega todas as cartas em memória para acesso rápido"""
       self.all_cards = self.sheets_client.get_all_cards()
       self.cards_by_name = {card.name.lower(): card for card in self.all_cards}
       self.logger.info(f"📚 Cache carregado: {len(self.all_cards)} cartas")
   
   def search(
       self, 
       query: str = "", 
       filters: Optional[SearchFilters] = None,
       n_results: int = 200
   ) -> SearchResult:
       """
       Busca principal com suporte a query vazia (browsing)
       
       Args:
           query: Texto de busca (pode ser vazio)
           filters: Filtros determinísticos
           n_results: Máximo de resultados
           
       Returns:
           SearchResult com cartas encontradas
       """
       start_time = time.time()
       filters = filters or SearchFilters()
       
       # 🚨 ÂNCORA: SEARCH_STRATEGY - Decisão de estratégia
       # Contexto: Query vazia = browsing, query com texto = busca semântica
       # Cuidado: Sem ChromaDB, sempre usa filtros simples
       # Dependências: UI pode chamar sem query para explorar
       
       if not query and not filters.must_include:
           # Browsing mode - apenas filtros
           results = self._browse_with_filters(filters, n_results)
           interpretation = "Browsing com filtros"
           used_chromadb = False
           
       elif self.chromadb_available and query:
           # Busca semântica + filtros
           results = self._semantic_search_with_filters(query, filters, n_results)
           interpretation = f"Busca semântica: '{query}'"
           used_chromadb = True
           
       else:
           # Fallback: busca simples em memória
           results = self._simple_search_with_filters(query, filters, n_results)
           interpretation = f"Busca simples: '{query}'"
           used_chromadb = False
       
       # Garante cartas obrigatórias
       if filters.must_include:
           results = self._ensure_must_include(results, filters.must_include)
           
       # Remove cartas proibidas
       if filters.must_exclude:
           results = self._apply_exclusions(results, filters.must_exclude)
       
       # Limita resultados
       final_results = results[:n_results]
       
       return SearchResult(
           cards=final_results,
           total_found=len(results),
           query=query,
           query_interpretation=interpretation,
           filters_applied=filters,
           search_time=time.time() - start_time,
           used_chromadb=used_chromadb
       )
   
   def _semantic_search_with_filters(
       self, 
       query: str, 
       filters: SearchFilters, 
       n_results: int
   ) -> List[Card]:
       """Busca semântica via ChromaDB com filtros"""
       
       # 🚨 ÂNCORA: CHROMADB_WHERE - Construção de filtros ChromaDB
       # Contexto: Apenas alguns filtros funcionam no where clause
       # Cuidado: ChromaDB tem sintaxe específica para queries
       # Dependências: Documentação ChromaDB para sintaxe
       
       where_clause = {}
       
       # Tipo de carta (ChromaDB suporta)
       if filters.card_types:
           where_clause["type"] = {"$in": filters.card_types}
           
       # Raridade máxima
       if filters.max_rarity:
           rarities = ["Common", "Uncommon", "Rare", "Legendary"]
           max_idx = rarities.index(filters.max_rarity)
           where_clause["rarity"] = {"$in": rarities[:max_idx + 1]}
           
       # Mercado
       if filters.market_access_only:
           where_clause["can_access_market"] = True
       elif not filters.include_market:
           where_clause["can_access_market"] = False
           
       # Buscar mais que o necessário para compensar pós-filtros
       search_multiplier = 3 if filters.allowed_factions else 2
       
       # Embedding da query
       query_embedding = self.embedding_model.encode([query])
       
       # Busca no ChromaDB
       results = self.cards_collection.query(
           query_embeddings=query_embedding.tolist(),
           n_results=min(n_results * search_multiplier, 1000),
           where=where_clause if where_clause else None
       )
       
       # Converter resultados para Cards
       cards = []
       for metadata in results['metadatas'][0]:
           card_name = metadata.get('name')
           if card_name and card_name.lower() in self.cards_by_name:
               cards.append(self.cards_by_name[card_name.lower()])
               
       # Aplicar filtros pós-busca
       return self._apply_post_filters(cards, filters)
   
   def _browse_with_filters(self, filters: SearchFilters, n_results: int) -> List[Card]:
       """Browsing mode - retorna cartas que passam nos filtros"""
       results = self.all_cards.copy()
       return self._apply_post_filters(results, filters)[:n_results]
   
   def _simple_search_with_filters(
       self, 
       query: str, 
       filters: SearchFilters, 
       n_results: int
   ) -> List[Card]:
       """Busca simples por texto quando ChromaDB não disponível"""
       query_lower = query.lower()
       results = []
       
       for card in self.all_cards:
           # Busca no nome e texto
           if (query_lower in card.name.lower() or 
               query_lower in card.card_text.lower()):
               results.append(card)
               
       return self._apply_post_filters(results, filters)
   
   def _apply_post_filters(self, cards: List[Card], filters: SearchFilters) -> List[Card]:
       """
       Aplica filtros complexos após busca
       
       🚨 ÂNCORA: POST_FILTERS - Filtros aplicados em Python
       Contexto: Filtros muito complexos para ChromaDB where clause
       Cuidado: Ordem importa para performance (mais restritivos primeiro)
       Dependências: Cada filtro deve ser independente
       """
       results = cards
       
       # Custo (muito restritivo, aplicar primeiro)
       if filters.min_cost is not None:
           results = [c for c in results if c.cost >= filters.min_cost]
       if filters.max_cost is not None:
           results = [c for c in results if c.cost <= filters.max_cost]
           
       # Unit types
       if filters.unit_types:
           unit_types_lower = [ut.lower() for ut in filters.unit_types]
           results = [
               c for c in results 
               if any(ut.lower() in unit_types_lower for ut in c.unit_types)
           ]
           
       # Facções (complexo por multi-faction)
       if filters.allowed_factions:
           results = self._filter_by_factions(results, filters)
           
       # Formato Expedition
       if filters.format == "Expedition":
           # TODO: Definir EXPEDITION_SETS em config.py
           # Por enquanto, não filtra
           pass
           
       return results
   
   def _filter_by_factions(self, cards: List[Card], filters: SearchFilters) -> List[Card]:
       """Filtra cartas por facções permitidas e número máximo"""
       if not filters.allowed_factions:
           return cards
           
       allowed_symbols = set()
       for faction in filters.allowed_factions:
           symbol = FACTION_SYMBOLS.get(faction)
           if symbol:
               allowed_symbols.add(symbol)
               
       results = []
       for card in cards:
           # Contar facções na carta
           card_factions = set()
           for symbol in FACTION_SYMBOLS.values():
               if symbol in card.influence:
                   card_factions.add(symbol)
                   
           # Verificar se todas as facções da carta são permitidas
           if card_factions.issubset(allowed_symbols):
               # Verificar número máximo de facções
               if not filters.max_factions_per_card or len(card_factions) <= filters.max_factions_per_card:
                   results.append(card)
                   
       return results
   
   def _ensure_must_include(self, results: List[Card], must_include: List[str]) -> List[Card]:
       """Garante que cartas obrigatórias estejam nos resultados"""
       result_names = {c.name.lower() for c in results}
       
       for required_name in must_include:
           required_lower = required_name.lower()
           if required_lower not in result_names and required_lower in self.cards_by_name:
               # Adiciona no início para garantir visibilidade
               results.insert(0, self.cards_by_name[required_lower])
               
       return results
   
   def _apply_exclusions(self, results: List[Card], must_exclude: List[str]) -> List[Card]:
       """Remove cartas proibidas dos resultados"""
       exclude_lower = {name.lower() for name in must_exclude}
       return [c for c in results if c.name.lower() not in exclude_lower]
   
   def get_card_by_name(self, name: str) -> Optional[Card]:
       """Busca carta específica por nome exato"""
       return self.cards_by_name.get(name.lower())
   
   def get_cards_by_names(self, names: List[str]) -> List[Card]:
       """Busca múltiplas cartas por nome"""
       cards = []
       for name in names:
           card = self.get_card_by_name(name)
           if card:
               cards.append(card)
       return cards


# =============================================================================
# Teste rápido se executado diretamente
# =============================================================================

if __name__ == "__main__":
   logging.basicConfig(level=logging.INFO)
   
   print("🧪 Testando SearchEngine...")
   
   engine = SearchEngine()
   
   # Teste 1: Busca simples
   print("\n1️⃣ Busca simples: 'torch'")
   result = engine.search("torch", n_results=5)
   print(f"Encontradas: {result.total_found} cartas")
   for card in result.cards[:3]:
       print(f"  - {card.name} | {card.cost}{card.influence}")
       
   # Teste 2: Busca com filtros
   print("\n2️⃣ Busca com filtros: Fire units até 3 de custo")
   filters = SearchFilters(
       allowed_factions=["Fire"],
       card_types=["Unit"],
       max_cost=3
   )
   result = engine.search("", filters=filters, n_results=10)
   print(f"Encontradas: {result.total_found} cartas")
   for card in result.cards[:5]:
       print(f"  - {card.name} | {card.cost}{card.influence} | {card.type}")
       
   # Teste 3: Must include/exclude
   print("\n3️⃣ Teste must include/exclude")
   filters = SearchFilters(
       must_include=["Torch", "Permafrost"],
       must_exclude=["Harsh Rule"]
   )
   result = engine.search("removal", filters=filters, n_results=10)
   print(f"Encontradas: {result.total_found} cartas")
   print("Primeiras 5:")
   for card in result.cards[:5]:
       print(f"  - {card.name}")