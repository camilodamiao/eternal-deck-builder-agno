"""
Eternal Deck Builder AI - Interface Principal
Interface funcional com análise de estratégia e seleção de cartas
"""

import streamlit as st
import pandas as pd
import asyncio
from typing import Dict, List, Optional, Tuple
import time
from datetime import datetime

# Imports do projeto
from agents.strategy_scout import StrategyScoutAgent, SearchFilters
from data.models import Card
from config import FACTION_NAMES

# =============================================================================
# 🚨 ÂNCORA: UI_CONFIG - Configuração da interface
# Contexto: Define layout e comportamento padrão da UI
# Cuidado: Mudanças aqui afetam toda experiência do usuário
# Dependências: Streamlit session state e componentes
# =============================================================================

st.set_page_config(
   page_title="Eternal Deck Builder AI",
   page_icon="🎴",
   layout="wide",
   initial_sidebar_state="expanded"
)

# CSS customizado para melhor visualização
st.markdown("""
<style>
   .stDataFrame {
       font-size: 14px;
   }
   .deck-counter {
       font-size: 18px;
       font-weight: bold;
       padding: 10px;
       border-radius: 5px;
   }
   .valid-deck {
       background-color: #d4edda;
       color: #155724;
   }
   .invalid-deck {
       background-color: #f8d7da;
       color: #721c24;
   }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🚨 ÂNCORA: SESSION_STATE - Gerenciamento de estado
# Contexto: Mantém dados entre interações do usuário
# Cuidado: Limpar quando necessário para evitar dados obsoletos
# Dependências: Todos os componentes interativos
# =============================================================================

# Inicializar session state
if 'scout_result' not in st.session_state:
   st.session_state.scout_result = None
if 'card_quantities' not in st.session_state:
   st.session_state.card_quantities = {}
if 'analyzing' not in st.session_state:
   st.session_state.analyzing = False

# Header
st.title("🎴 Eternal Deck Builder AI")
st.markdown("Descreva sua estratégia e encontre as cartas perfeitas para seu deck")

# =============================================================================
# 🚨 ÂNCORA: SCOUT_SINGLETON - Instância única do agente
# Contexto: Evita recriar o agente a cada interação
# Cuidado: Cache pode precisar ser limpo se houver mudanças
# Dependências: StrategyScoutAgent
# =============================================================================

@st.cache_resource
def get_scout_agent():
   """Retorna instância singleton do StrategyScoutAgent"""
   return StrategyScoutAgent()

scout = get_scout_agent()

# =============================================================================
# Sidebar com filtros opcionais
# =============================================================================

with st.sidebar:
   st.header("🎯 Filtros Opcionais")
   st.markdown("Deixe vazio para detecção automática")
   
   # Facções
   allowed_factions = st.multiselect(
       "Facções Permitidas",
       FACTION_NAMES,
       help="Restringe às facções selecionadas"
   )
   
   # Número máximo de facções por carta
   if allowed_factions:
       max_factions_per_card = st.slider(
           "Máx. Facções por Carta",
           min_value=1,
           max_value=len(allowed_factions),
           value=min(2, len(allowed_factions)),
           help="Ex: 2 = permite mono e dual-faction"
       )
   else:
       max_factions_per_card = None
   
   st.divider()
   
   # Formato e Raridade
   game_format = st.radio(
       "Formato",
       ["Throne", "Expedition"],
       index=0
   )
   
   max_rarity = st.selectbox(
       "Raridade Máxima",
       [None, "Common", "Uncommon", "Rare"],
       format_func=lambda x: "Sem limite" if x is None else x
   )
   
   st.divider()
   
   # Custos
   col1, col2 = st.columns(2)
   with col1:
       min_cost = st.number_input("Custo Mín.", min_value=0, max_value=12, value=0)
   with col2:
       max_cost = st.number_input("Custo Máx.", min_value=0, max_value=12, value=12)
   
   if max_cost == 12:
       max_cost = None
   if min_cost == 0:
       min_cost = None
       
   st.divider()
   
   # Tipos de carta
   card_types = st.multiselect(
       "Tipos de Carta",
       ["Unit", "Spell", "Power", "Weapon", "Relic", "Curse"],
       help="Deixe vazio para todos os tipos"
   )
   
   # Mercado
   include_market = st.checkbox("Incluir cartas de mercado", value=True)
   
   st.divider()
   
   # Cartas específicas
   must_include = st.text_area(
       "Cartas Obrigatórias",
       placeholder="Uma por linha\nEx:\nTorch\nHarsh Rule",
       height=100
   )
   
   must_exclude = st.text_area(
       "Cartas Proibidas",
       placeholder="Uma por linha",
       height=100
   )

# =============================================================================
# Interface principal
# =============================================================================

# Input de estratégia
col1, col2 = st.columns([4, 1])

with col1:
   strategy_input = st.text_area(
       "Descreva sua estratégia:",
       placeholder="Ex: Quero um deck aggro de Fire com muito burn damage e unidades rápidas",
       height=100,
       key="strategy_input"
   )

with col2:
   st.write("")  # Spacing
   st.write("")  # Spacing
   analyze_button = st.button(
       "🔍 Analisar", 
       type="primary", 
       use_container_width=True,
       disabled=st.session_state.analyzing
   )

# =============================================================================
# 🚨 ÂNCORA: ANALYZE_STRATEGY - Processo de análise
# Contexto: Chama o StrategyScoutAgent com os filtros
# Cuidado: Operação async, pode demorar alguns segundos
# Dependências: StrategyScoutAgent, SearchFilters
# =============================================================================

async def analyze_strategy(strategy: str, filters: SearchFilters):
   """Executa análise de estratégia de forma assíncrona"""
   result = await scout.analyze_and_scout(strategy, filters)
   return result

if analyze_button and strategy_input:
   st.session_state.analyzing = True
   
   # Criar filtros
   filters = SearchFilters(
       allowed_factions=allowed_factions if allowed_factions else None,
       max_factions_per_card=max_factions_per_card,
       format=game_format,
       max_rarity=max_rarity,
       min_cost=min_cost,
       max_cost=max_cost,
       card_types=card_types if card_types else None,
       must_include=[c.strip() for c in must_include.split('\n') if c.strip()] if must_include else None,
       must_exclude=[c.strip() for c in must_exclude.split('\n') if c.strip()] if must_exclude else None,
       include_market=include_market
   )
   
   # Executar análise
   with st.spinner("🤔 Analisando estratégia e buscando cartas..."):
       # Run async function
       loop = asyncio.new_event_loop()
       asyncio.set_event_loop(loop)
       result = loop.run_until_complete(analyze_strategy(strategy_input, filters))
       
       st.session_state.scout_result = result
       st.session_state.analyzing = False
       
       # Limpar quantidades anteriores
       st.session_state.card_quantities = {}

# =============================================================================
# Exibir resultados
# =============================================================================

if st.session_state.scout_result:
   result = st.session_state.scout_result
   
   # Análise da estratégia
   st.divider()
   
   col1, col2, col3 = st.columns(3)
   
   with col1:
       st.metric("Arquétipo", result.strategy.archetype.capitalize())
       if result.strategy.primary_faction:
           factions = result.strategy.primary_faction
           if result.strategy.secondary_factions:
               factions += f" + {', '.join(result.strategy.secondary_factions)}"
           st.metric("Facções", factions)
   
   with col2:
       st.metric("Cartas Encontradas", result.pool_size)
       st.metric("Tempo de Busca", f"{result.execution_time:.1f}s")
   
   with col3:
       # Contador do deck
       total_cards = sum(st.session_state.card_quantities.values())
       power_cards = sum(
           qty for card, qty in st.session_state.card_quantities.items()
           if any(c.is_power for c in result.card_pool if c.name == card)
       )
       power_ratio = (power_cards / total_cards * 100) if total_cards > 0 else 0
       
       # Validação visual
       is_valid = 75 <= total_cards <= 150 and power_cards >= total_cards / 3
       deck_class = "valid-deck" if is_valid else "invalid-deck"
       
       st.markdown(
           f'<div class="deck-counter {deck_class}">'
           f'Deck: {total_cards}/75 cartas<br>'
           f'{power_cards} powers ({power_ratio:.0f}%)'
           '</div>',
           unsafe_allow_html=True
       )
   
   # Mecânicas identificadas
   if result.strategy.key_mechanics:
       st.info(f"**Mecânicas chave**: {', '.join(result.strategy.key_mechanics)}")
   
   # =============================================================================
   # 🚨 ÂNCORA: CARD_TABLE - Tabela interativa de cartas
   # Contexto: Permite seleção de quantidades e filtragem
   # Cuidado: Performance com muitas cartas (usar paginação se necessário)
   # Dependências: pandas, streamlit-aggrid seria melhor mas adiciona dependência
   # =============================================================================
   
   st.divider()
   
   # Preparar dados para tabela
   def prepare_card_data(cards: List[Card]) -> pd.DataFrame:
       """Converte lista de cartas em DataFrame para exibição"""
       data = []
       for card in cards:
           # Tipo formatado
           card_type = card.type
           if card.is_unit and card.unit_types:
               card_type = f"{card.type} - {' '.join(card.unit_types)}"
           
           # Stats
           stats = ""
           if card.is_unit and card.attack is not None and card.health is not None:
               stats = f"{card.attack}/{card.health}"
           
           # Quantidade atual
           qty = st.session_state.card_quantities.get(card.name, 0)
           
           data.append({
               "Qtd": qty,
               "Nome": card.name,
               "Custo": f"{card.cost}{card.influence}" if card.cost > 0 else card.influence or "0",
               "Tipo": card_type,
               "Stats": stats,
               "Texto": card.card_text[:100] + "..." if len(card.card_text) > 100 else card.card_text,
               "Raridade": card.rarity
           })
       
       return pd.DataFrame(data)
   
   # Controles da tabela
   col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
   
   with col1:
       search_term = st.text_input("🔍 Buscar nas cartas:", placeholder="Digite para filtrar...")
   
   with col2:
       show_selected = st.checkbox("Mostrar apenas selecionadas")
   
   with col3:
       if st.button("🗑️ Limpar Seleção"):
           st.session_state.card_quantities = {}
           st.rerun()
   
   with col4:
       # Export functionality (future)
       st.button("📥 Exportar Deck", disabled=total_cards == 0)
   
   # Filtrar cartas
   filtered_cards = result.card_pool
   
   if search_term:
       search_lower = search_term.lower()
       filtered_cards = [
           c for c in filtered_cards
           if search_lower in c.name.lower() or search_lower in c.card_text.lower()
       ]
   
   if show_selected:
       filtered_cards = [
           c for c in filtered_cards
           if st.session_state.card_quantities.get(c.name, 0) > 0
       ]
   
   # Criar DataFrame
   df = prepare_card_data(filtered_cards)
   
   # =============================================================================
   # 🚨 ÂNCORA: QUANTITY_SELECTOR - Sistema de seleção de quantidades
   # Contexto: Permite selecionar 0-4 cópias respeitando regras
   # Cuidado: Sigils podem ter quantidade ilimitada
   # Dependências: session_state para persistir seleções
   # =============================================================================
   
   # Exibir tabela com seletores de quantidade
   if not df.empty:
       st.write(f"**{len(df)} cartas** ({'filtradas' if search_term or show_selected else 'totais'})")
       
       # Criar colunas para quantidade
       for idx, row in df.iterrows():
           col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.5, 2, 1, 1.5, 0.8, 3, 1, 0.5])
           
           card_name = row['Nome']
           card = next((c for c in result.card_pool if c.name == card_name), None)
           
           with col1:
               # Determinar máximo de cópias
               max_copies = 99 if card and card.is_sigil else 4
               
               # Seletor de quantidade
               new_qty = st.selectbox(
                   "Qtd",
                   options=range(0, max_copies + 1),
                   index=st.session_state.card_quantities.get(card_name, 0),
                   key=f"qty_{card_name}",
                   label_visibility="collapsed"
               )
               
               # Atualizar quantidade
               if new_qty > 0:
                   st.session_state.card_quantities[card_name] = new_qty
               elif card_name in st.session_state.card_quantities:
                   del st.session_state.card_quantities[card_name]
           
           with col2:
               st.write(row['Nome'])
           
           with col3:
               st.write(row['Custo'])
           
           with col4:
               st.write(row['Tipo'])
           
           with col5:
               st.write(row['Stats'])
           
           with col6:
               st.write(row['Texto'])
           
           with col7:
               st.write(row['Raridade'])
           
           with col8:
               # Quick add button
               if st.button("4x", key=f"add4_{card_name}", help="Adicionar 4 cópias"):
                   st.session_state.card_quantities[card_name] = 4
                   st.rerun()
       
       # Estatísticas do pool
       st.divider()
       
       col1, col2, col3 = st.columns(3)
       
       with col1:
           type_counts = df['Tipo'].apply(lambda x: x.split(' - ')[0]).value_counts()
           st.write("**Distribuição por Tipo:**")
           for card_type, count in type_counts.items():
               st.write(f"- {card_type}: {count}")
       
       with col2:
           rarity_counts = df['Raridade'].value_counts()
           st.write("**Distribuição por Raridade:**")
           for rarity, count in rarity_counts.items():
               st.write(f"- {rarity}: {count}")
       
       with col3:
           # Curva de custo
           cost_values = []
           for _, row in df.iterrows():
               cost_str = row['Custo']
               # Extrair número do custo
               try:
                   if cost_str and cost_str[0].isdigit():
                       cost_values.append(int(cost_str[0]))
               except:
                   pass
           
           if cost_values:
               st.write("**Curva de Custo:**")
               cost_dist = pd.Series(cost_values).value_counts().sort_index()
               for cost, count in cost_dist.items():
                   st.write(f"- {cost}: {'█' * min(count, 20)} ({count})")
   
   else:
       st.warning("Nenhuma carta encontrada com os filtros atuais.")

else:
   # Estado inicial
   st.info("👆 Descreva sua estratégia e clique em Analisar para começar!")
   
   # Exemplos
   with st.expander("💡 Exemplos de estratégias"):
       st.markdown("""
       **Aggro Simples:**
       - "Fast Fire aggro deck with burn"
       - "Mono Justice aggro with weapons"
       
       **Tribal:**
       - "Valkyrie tribal deck with Justice/Fire"
       - "Yeti tribal with Primal/Time"
       
       **Control:**
       - "Hard control with board wipes and card draw"
       - "Time/Justice control with big finishers"
       
       **Combo:**
       - "Reanimator combo with Shadow/Time"
       - "Spell combo deck with Primal"
       """)

# Footer
st.divider()
st.caption("Eternal Deck Builder AI - Powered by Agno Framework")

# Debug info (se necessário)
if st.checkbox("🐛 Debug Info", value=False):
   if st.session_state.scout_result:
       st.json({
           "strategy": {
               "archetype": st.session_state.scout_result.strategy.archetype,
               "factions": [st.session_state.scout_result.strategy.primary_faction] + 
                          st.session_state.scout_result.strategy.secondary_factions,
               "mechanics": st.session_state.scout_result.strategy.key_mechanics,
               "tribal": st.session_state.scout_result.strategy.tribal_focus
           },
           "search_metadata": st.session_state.scout_result.search_metadata,
           "selected_cards": st.session_state.card_quantities
       })