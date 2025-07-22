"""
StrategyScoutAgent - L2 Agent
Analisa estratégia do usuário e busca cartas relevantes
Fusão de análise estratégica + busca semântica
"""

from agno.agent import Agent, RunResponse
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
import asyncio
import logging
from datetime import datetime

# Imports do projeto
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from rag.search_engine import SearchEngine, SearchFilters
from data.models import Card
from config import FACTION_NAMES, FACTION_SYMBOLS
from knowledge.eternal_skills import ALL_SKILLS, get_skills_by_archetype
from knowledge.eternal_synergies import get_package_for_strategy

# =============================================================================
# 🚨 ÂNCORA: STRATEGY_MODELS - Modelos de dados para análise
# Contexto: Estruturas que representam a estratégia interpretada
# Cuidado: Campos devem cobrir todos os aspectos relevantes
# Dependências: DeckCraftingTeam usará estas estruturas
# =============================================================================

@dataclass
class StrategyAnalysis:
   """Resultado da análise de estratégia"""
   # Arquétipo e velocidade
   archetype: str = "midrange"  # aggro/midrange/control/combo
   speed: str = "medium"  # fast/medium/slow
   
   # Facções
   primary_faction: Optional[str] = None
   secondary_factions: List[str] = field(default_factory=list)
   
   # Mecânicas e temas
   key_mechanics: List[str] = field(default_factory=list)  # burn, flying, removal, etc
   tribal_focus: Optional[str] = None  # Valkyrie, Oni, etc
   
   # Cartas específicas
   must_include_cards: List[str] = field(default_factory=list)
   
   # Preferências
   market_preference: bool = True
   preferred_win_conditions: List[str] = field(default_factory=list)
   
   # Análise adicional
   confidence_score: float = 0.8
   interpretation_notes: str = ""

@dataclass
class ScoutResult:
   """Resultado completo do StrategyScout"""
   strategy: StrategyAnalysis
   card_pool: List[Card]
   pool_size: int
   search_metadata: Dict[str, Any]
   execution_time: float

# =============================================================================
# 🚨 ÂNCORA: STRATEGY_PATTERNS - Padrões para detecção de estratégia
# Contexto: Keywords que indicam arquétipos e mecânicas
# Cuidado: Ordem importa - mais específicos primeiro
# Dependências: _detect_patterns() usa estas definições
# =============================================================================

ARCHETYPE_PATTERNS = {
   "aggro": ["aggro", "aggressive", "fast", "rush", "burn", "face", "beatdown", "tempo"],
   "control": ["control", "removal", "board wipe", "slow", "grind", "defensive", "reactive"],
   "midrange": ["midrange", "value", "balanced", "versatile", "flexible"],
   "combo": ["combo", "synergy", "otk", "engine", "infinite", "loop"]
}

FACTION_PATTERNS = {
   "Fire": ["fire", "burn", "torch", "flame", "oni", "grenadin", "gun"],
   "Time": ["time", "ramp", "dinosaur", "sentinel", "sandstorm", "amber"],
   "Justice": ["justice", "armor", "valkyrie", "enforcer", "law", "order"],
   "Primal": ["primal", "spell", "wisdom", "ice", "yeti", "unseen", "lightning"],
   "Shadow": ["shadow", "kill", "death", "void", "reanimator", "stonescar", "umbren"]
}

MECHANIC_PATTERNS = {
   "removal": ["removal", "kill", "destroy", "vanquish", "harsh rule", "board wipe"],
   "card_draw": ["draw", "card advantage", "wisdom", "strategize", "selection"],
   "ramp": ["ramp", "power", "accelerate", "seek power", "influence"],
   "burn": ["burn", "damage", "torch", "flame blast", "direct damage"],
   "flying": ["flying", "flyer", "aerial", "airborne", "wings"],
   "weapons": ["weapon", "relic weapon", "sword", "hammer", "gun"],
   "void": ["void", "graveyard", "recursion", "reanimator", "death"],
   "tribal": ["tribal", "synergy", "lord", "matters"],
   "sacrifice": ["sacrifice", "sac", "combust", "devour"],
   "lifegain": ["lifegain", "life", "heal", "lifesteal"],
   "market": ["market", "merchant", "smuggler", "etchings", "bargain"]
}

# =============================================================================
# 🚨 ÂNCORA: STRATEGY_SCOUT_AGENT - Agente principal L2
# Contexto: Analisa texto livre e retorna pool de cartas
# Cuidado: Não limitar quantidade de cartas retornadas
# Dependências: SearchEngine, Knowledge Base
# =============================================================================

class StrategyScoutAgent(Agent):
   """
   L2 Agent - Analisa estratégia e busca cartas
   Usa SearchEngine com filtros inteligentes baseados na análise
   """
   
   name = "StrategyScout"
   model = "gpt-4o-mini"  # Rápido e eficiente para análise
   temperature = 0.3  # Baixa para consistência
   
   instructions = """You are an expert Eternal Card Game strategist. When analyzing user input:

1. ARCHETYPE: Identify if it's aggro, midrange, control, or combo
  - Aggro: Fast damage, low curve, burn, pressure
  - Midrange: Balanced, value trades, versatile
  - Control: Removal, card draw, late game
  - Combo: Specific interactions, engine pieces

2. FACTIONS: Detect primary and secondary factions from:
  - Direct mentions (Fire, Time, Justice, Primal, Shadow)
  - Faction-specific keywords (burn=Fire, ramp=Time, etc)
  - Card names mentioned

3. KEY MECHANICS: Identify important themes like:
  - Removal, card draw, ramp, burn, flying, weapons
  - Tribal synergies (Valkyrie, Oni, Yeti, etc)
  - Special strategies (void, sacrifice, market)

4. SPECIFIC CARDS: Extract any card names mentioned

5. SPEED: Infer deck speed (fast/medium/slow) from archetype

Be thorough but concise. Output as structured data."""
   
   def __init__(self):
       super().__init__()
       self.search_engine = SearchEngine()
       self.logger = logging.getLogger(__name__)
       
   async def analyze_and_scout(
       self, 
       user_input: str,
       additional_filters: Optional[SearchFilters] = None
   ) -> ScoutResult:
       """
       Analisa input do usuário e busca cartas relevantes
       
       Args:
           user_input: Descrição livre da estratégia desejada
           additional_filters: Filtros extras da UI (facções, raridade, etc)
           
       Returns:
           ScoutResult com análise completa e pool de cartas
       """
       start_time = datetime.now()
       
       self.logger.info(f"🔍 Iniciando análise: '{user_input[:100]}...'")
       
       # 1. Análise inicial com detecção de padrões
       strategy = await self._analyze_strategy(user_input)
       
       # 2. Enriquecer com knowledge base
       strategy = self._enrich_with_knowledge(strategy)
       
       # 3. Criar queries de busca baseadas na análise
       search_queries = self._create_search_queries(strategy, user_input)
       
       # 4. Executar buscas (sem limite de quantidade)
       card_pool = await self._execute_searches(search_queries, strategy, additional_filters)
       
       # 5. Organizar e deduplicar
       final_pool = self._organize_card_pool(card_pool, strategy)
       
       execution_time = (datetime.now() - start_time).total_seconds()
       
       self.logger.info(f"✅ Análise completa: {len(final_pool)} cartas em {execution_time:.2f}s")
       
       return ScoutResult(
           strategy=strategy,
           card_pool=final_pool,
           pool_size=len(final_pool),
           search_metadata={
               "queries_executed": len(search_queries),
               "filters_applied": additional_filters,
               "user_input": user_input,
               "unique_cards": len(set(c.name for c in final_pool))
           },
           execution_time=execution_time
       )
   
   async def _analyze_strategy(self, user_input: str) -> StrategyAnalysis:
       """
       Usa IA para analisar o input do usuário
       
       🚨 ÂNCORA: AI_ANALYSIS - Análise via GPT-4
       Contexto: IA entende nuances que regex não pegaria
       Cuidado: Combinar com detecção de padrões para robustez
       Dependências: Modelo deve ter conhecimento de Eternal
       """
       
       # Primeiro, detecção rápida de padrões
       initial_analysis = self._detect_patterns(user_input)
       
       # Prompt estruturado para IA
       analysis_prompt = f"""Analyze this Eternal Card Game deck request:

"{user_input}"

Current pattern detection found:
- Archetype hints: {initial_analysis.archetype}
- Faction hints: {initial_analysis.primary_faction}, {initial_analysis.secondary_factions}
- Mechanics: {initial_analysis.key_mechanics}

Please provide a refined analysis:
1. Confirmed archetype (aggro/midrange/control/combo)
2. Primary faction and secondary factions (if any)
3. Key mechanics and themes
4. Specific cards mentioned (exact names)
5. Preferred win conditions
6. Should use market? (yes/no)

Format as JSON."""

       try:
           # Chamar IA para análise
           response: RunResponse = await self.run(analysis_prompt)
           
           # Parsear resposta e mesclar com análise inicial
           refined_analysis = self._parse_ai_response(response, initial_analysis)
           
           return refined_analysis
           
       except Exception as e:
           self.logger.warning(f"Erro na análise IA: {e}. Usando apenas padrões.")
           return initial_analysis
   
   def _detect_patterns(self, user_input: str) -> StrategyAnalysis:
       """Detecção rápida de padrões via regex/keywords"""
       input_lower = user_input.lower()
       analysis = StrategyAnalysis()
       
       # Detectar arquétipo
       for archetype, patterns in ARCHETYPE_PATTERNS.items():
           if any(pattern in input_lower for pattern in patterns):
               analysis.archetype = archetype
               break
       
       # Detectar facções
       detected_factions = []
       for faction, patterns in FACTION_PATTERNS.items():
           if any(pattern in input_lower for pattern in patterns):
               detected_factions.append(faction)
       
       if detected_factions:
           analysis.primary_faction = detected_factions[0]
           analysis.secondary_factions = detected_factions[1:3]  # Max 2 secundárias
       
       # Detectar mecânicas
       for mechanic, patterns in MECHANIC_PATTERNS.items():
           if any(pattern in input_lower for pattern in patterns):
               analysis.key_mechanics.append(mechanic)
       
       # Detectar tribais
       tribal_keywords = ["valkyrie", "oni", "yeti", "grenadin", "sentinel", "dragon"]
       for tribal in tribal_keywords:
           if tribal in input_lower:
               analysis.tribal_focus = tribal.capitalize()
               if "tribal" not in analysis.key_mechanics:
                   analysis.key_mechanics.append("tribal")
       
       # Inferir velocidade
       if analysis.archetype == "aggro":
           analysis.speed = "fast"
       elif analysis.archetype == "control":
           analysis.speed = "slow"
       else:
           analysis.speed = "medium"
       
       # Market preference
       if "no market" in input_lower or "without market" in input_lower:
           analysis.market_preference = False
       
       return analysis
   
   def _parse_ai_response(self, response: RunResponse, initial: StrategyAnalysis) -> StrategyAnalysis:
       """Parse resposta da IA e mescla com análise inicial"""
       # Por simplicidade, retorna análise inicial melhorada
       # Em produção, parsearia JSON da resposta
       return initial
   
   def _enrich_with_knowledge(self, strategy: StrategyAnalysis) -> StrategyAnalysis:
       """
       Enriquece análise com knowledge base
       
       🚨 ÂNCORA: KNOWLEDGE_ENRICHMENT - Usa base de conhecimento
       Contexto: Skills e sinergias relevantes para o arquétipo
       Cuidado: Não sobrescrever preferências explícitas do usuário
       Dependências: knowledge/eternal_skills.py, eternal_synergies.py
       """
       
       # Adicionar skills relevantes para o arquétipo
       if strategy.archetype:
           relevant_skills = get_skills_by_archetype(strategy.archetype)
           for skill in relevant_skills[:5]:  # Top 5 skills
               skill_lower = skill.lower()
               if skill_lower not in strategy.key_mechanics:
                   strategy.key_mechanics.append(skill_lower)
       
       # Adicionar package sinérgico
       package = get_package_for_strategy(strategy.archetype)
       if package:
           # Adicionar mecânicas do package
           for mechanic in package.get("core_mechanics", []):
               if mechanic not in strategy.key_mechanics:
                   strategy.key_mechanics.append(mechanic)
       
       return strategy
   
   def _create_search_queries(
       self, 
       strategy: StrategyAnalysis,
       original_input: str
   ) -> List[Dict[str, Any]]:
       """
       Cria múltiplas queries de busca baseadas na estratégia
       
       🚨 ÂNCORA: MULTI_QUERY_STRATEGY - Busca em múltiplas passadas
       Contexto: Uma única busca não pega todas as cartas relevantes
       Cuidado: Não duplicar queries, manter diversidade
       Dependências: SearchEngine executará cada query
       """
       queries = []
       
       # 1. Query original do usuário (pode ter nuances)
       queries.append({
           "query": original_input,
           "purpose": "original_input"
       })
       
       # 2. Query por arquétipo + facções
       if strategy.primary_faction:
           archetype_query = f"{strategy.archetype} {strategy.primary_faction}"
           if strategy.secondary_factions:
               archetype_query += f" {' '.join(strategy.secondary_factions)}"
           queries.append({
               "query": archetype_query,
               "purpose": "archetype_faction"
           })
       
       # 3. Queries por mecânicas principais (top 3)
       for mechanic in strategy.key_mechanics[:3]:
           if strategy.primary_faction:
               mechanic_query = f"{mechanic} {strategy.primary_faction}"
           else:
               mechanic_query = mechanic
           queries.append({
               "query": mechanic_query,
               "purpose": f"mechanic_{mechanic}"
           })
       
       # 4. Query tribal se aplicável
       if strategy.tribal_focus:
           queries.append({
               "query": f"{strategy.tribal_focus} tribal synergy",
               "purpose": "tribal_focus"
           })
       
       # 5. Query para win conditions
       if strategy.preferred_win_conditions:
           for win_con in strategy.preferred_win_conditions:
               queries.append({
                   "query": win_con,
                   "purpose": "win_condition"
               })
       
       # 6. Query para cartas essenciais do arquétipo
       if strategy.archetype == "aggro":
           queries.append({"query": "charge haste aggressive one drop", "purpose": "aggro_core"})
       elif strategy.archetype == "control":
           queries.append({"query": "board wipe removal draw", "purpose": "control_core"})
       elif strategy.archetype == "combo":
           queries.append({"query": "combo piece engine", "purpose": "combo_core"})
       
       # Remover duplicatas mantendo ordem
       seen = set()
       unique_queries = []
       for q in queries:
           if q["query"] not in seen:
               seen.add(q["query"])
               unique_queries.append(q)
       
       self.logger.info(f"📝 Criadas {len(unique_queries)} queries únicas")
       return unique_queries
   
   async def _execute_searches(
       self,
       search_queries: List[Dict[str, Any]],
       strategy: StrategyAnalysis,
       additional_filters: Optional[SearchFilters]
   ) -> List[Card]:
       """
       Executa todas as buscas e combina resultados
       
       🚨 ÂNCORA: NO_LIMIT_SEARCH - Sem limite artificial de cartas
       Contexto: DeckBuilder precisa de todas as opções possíveis
       Cuidado: Pode retornar muitas cartas, mas isso é desejado
       Dependências: SearchEngine deve suportar n_results alto
       """
       all_cards = []
       seen_cards = set()  # Para deduplicação
       
       # Criar filtros base da estratégia
       base_filters = self._create_base_filters(strategy, additional_filters)
       
       # Executar cada query
       for query_info in search_queries:
           query = query_info["query"]
           purpose = query_info["purpose"]
           
           self.logger.debug(f"🔍 Executando query [{purpose}]: {query}")
           
           # Buscar SEM LIMITE (ou limite muito alto)
           result = self.search_engine.search(
               query=query,
               filters=base_filters,
               n_results=1000  # Limite alto para não perder cartas
           )
           
           # Adicionar cards únicos
           for card in result.cards:
               if card.name not in seen_cards:
                   seen_cards.add(card.name)
                   all_cards.append(card)
           
           self.logger.debug(f"   → {len(result.cards)} cartas, {len(all_cards)} total único")
       
       # Buscar cartas obrigatórias mencionadas
       if strategy.must_include_cards:
           for card_name in strategy.must_include_cards:
               card = self.search_engine.get_card_by_name(card_name)
               if card and card.name not in seen_cards:
                   all_cards.insert(0, card)  # Adicionar no início
                   seen_cards.add(card.name)
       
       self.logger.info(f"🎯 Total de cartas únicas encontradas: {len(all_cards)}")
       return all_cards
   
   def _create_base_filters(
       self,
       strategy: StrategyAnalysis,
       additional_filters: Optional[SearchFilters]
   ) -> SearchFilters:
       """Cria filtros base combinando estratégia + filtros UI"""
       
       # Começar com filtros da UI ou vazio
       filters = additional_filters or SearchFilters()
       
       # Adicionar facções da estratégia (se não especificado na UI)
       if not filters.allowed_factions and strategy.primary_faction:
           factions = [strategy.primary_faction]
           if strategy.secondary_factions:
               factions.extend(strategy.secondary_factions)
           filters.allowed_factions = factions
       
       # Market preference
       if not strategy.market_preference:
           filters.include_market = False
       
       # Unit types para tribal
       if strategy.tribal_focus and not filters.unit_types:
           filters.unit_types = [strategy.tribal_focus]
       
       # Ajustar custo máximo por arquétipo
       if filters.max_cost is None:
           if strategy.archetype == "aggro":
               filters.max_cost = 5  # Aggro raramente quer cartas caras
           elif strategy.archetype == "control":
               filters.max_cost = 12  # Control pode querer finishers caros
       
       return filters
   
   def _organize_card_pool(self, cards: List[Card], strategy: StrategyAnalysis) -> List[Card]:
       """
       Organiza pool de cartas por relevância
       
       🚨 ÂNCORA: POOL_ORGANIZATION - Ordem importa para DeckBuilder
       Contexto: Cartas mais relevantes primeiro ajudam na construção
       Cuidado: Não remover cartas, apenas reordenar
       Dependências: DeckCraftingTeam espera cartas ordenadas
       """
       
       # Separar por categorias
       must_include = []
       core_cards = []      # Exatamente o que foi pedido
       synergy_cards = []   # Alta sinergia com estratégia
       support_cards = []   # Cartas de suporte
       
       for card in cards:
           # Must include sempre primeiro
           if card.name in strategy.must_include_cards:
               must_include.append(card)
           # Powers são sempre support
           elif card.is_power:
               support_cards.append(card)
           # Classificar por relevância
           else:
               relevance = self._calculate_relevance(card, strategy)
               if relevance >= 0.8:
                   core_cards.append(card)
               elif relevance >= 0.5:
                   synergy_cards.append(card)
               else:
                   support_cards.append(card)
       
       # Combinar na ordem de prioridade
       organized = []
       organized.extend(must_include)
       organized.extend(sorted(core_cards, key=lambda c: c.cost))  # Core por custo
       organized.extend(sorted(synergy_cards, key=lambda c: c.cost))
       organized.extend(sorted(support_cards, key=lambda c: c.cost))
       
       # Remover duplicatas mantendo ordem
       seen = set()
       final_pool = []
       for card in organized:
           if card.name not in seen:
               seen.add(card.name)
               final_pool.append(card)
       
       return final_pool
   
   def _calculate_relevance(self, card: Card, strategy: StrategyAnalysis) -> float:
       """Calcula relevância de uma carta para a estratégia (0-1)"""
       score = 0.5  # Base
       
       # Boost por mecânicas matching
       card_text_lower = card.card_text.lower()
       for mechanic in strategy.key_mechanics:
           if mechanic in card_text_lower:
               score += 0.1
       
       # Boost por tribal match
       if strategy.tribal_focus:
           if strategy.tribal_focus in card.unit_types:
               score += 0.2
       
       # Ajuste por arquétipo
       if strategy.archetype == "aggro" and card.cost <= 3:
           score += 0.1
       elif strategy.archetype == "control" and "draw" in card_text_lower:
           score += 0.1
       
       # Cap em 1.0
       return min(score, 1.0)


# =============================================================================
# Teste do agente
# =============================================================================

if __name__ == "__main__":
   import asyncio
   
   async def test_scout():
       """Testa o StrategyScoutAgent"""
       logging.basicConfig(level=logging.INFO)
       
       scout = StrategyScoutAgent()
       
       # Teste 1: Aggro simples
       print("\n🔥 Teste 1: Fire Aggro")
       result = await scout.analyze_and_scout("I want a fast fire aggro deck with burn damage")
       print(f"Arquétipo: {result.strategy.archetype}")
       print(f"Facção: {result.strategy.primary_faction}")
       print(f"Cartas encontradas: {result.pool_size}")
       print(f"Top 5 cartas: {[c.name for c in result.card_pool[:5]]}")
       
       # Teste 2: Tribal
       print("\n⚔️ Teste 2: Valkyrie Tribal")
       result = await scout.analyze_and_scout("Justice valkyrie tribal deck with weapons")
       print(f"Tribal: {result.strategy.tribal_focus}")
       print(f"Cartas encontradas: {result.pool_size}")
       
       # Teste 3: Control complexo
       print("\n🌊 Teste 3: Control Multi-faction")
       result = await scout.analyze_and_scout(
           "I need a control deck with Harsh Rule, card draw and big finishers. "
           "Thinking Time/Justice/Primal for maximum control options."
       )
       print(f"Facções: {result.strategy.primary_faction} + {result.strategy.secondary_factions}")
       print(f"Must include: {result.strategy.must_include_cards}")
       print(f"Cartas encontradas: {result.pool_size}")
   
   # Executar testes
   asyncio.run(test_scout())