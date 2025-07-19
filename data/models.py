"""
Modelos de dados para o Eternal Deck Builder
Estruturas principais: Card, DeckCard, Deck
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, computed_field

# =============================================================================
# 🚨 ÂNCORA: CARD_MODEL - Modelo principal de carta
# Contexto: Mapeia campos do Google Sheets, sem validação pesada
# Cuidado: Nomes dos campos devem corresponder às colunas da planilha
# Dependências: GoogleSheetsClient espera estes campos
# =============================================================================

class Card(BaseModel):
    """
    Representa uma carta do Eternal Card Game
    Campos mapeados diretamente da planilha Google Sheets
    """
    # Campos obrigatórios
    name: str = Field(..., description="Nome da carta")
    cost: int = Field(0, description="Custo de power")
    influence: str = Field("", description="Requisitos de influência ex: {F}{F}")
    type: str = Field(..., description="Unit, Spell, Power, Weapon, Relic, Curse")
    card_text: str = Field("", description="Texto completo da carta", alias="CardText")
    rarity: str = Field("Common", description="Common, Uncommon, Rare, Legendary")
    deck_buildable: bool = Field(True, description="Se pode ser usada em decks", alias="DeckBuildable")
    set_number: str = Field("", description="Número do set", alias="SetNumber")
    
    # Campos opcionais (apenas para units/weapons)
    attack: Optional[int] = Field(None, description="Poder de ataque")
    health: Optional[int] = Field(None, description="Vida/Resistência")
    
    # Campos extras úteis
    eternal_id: Optional[str] = Field(None, description="ID único no jogo", alias="EternalID")
    image_url: Optional[str] = Field(None, description="URL da imagem", alias="ImageUrl")
    
    # Configuração do Pydantic
    class Config:
        # Permite usar tanto card_text quanto CardText
        populate_by_name = True
        # Permite campos extras não definidos
        extra = "allow"
    
    # =============================================================================
    # 🚨 ÂNCORA: CARD_PROPERTIES - Propriedades computadas úteis
    # Contexto: Helpers para identificar tipos de carta rapidamente
    # Cuidado: Baseadas no campo 'type', deve corresponder aos tipos do jogo
    # Dependências: Usadas pelo deck builder e validador
    # =============================================================================
    
    @computed_field
    @property
    def is_power(self) -> bool:
        """Verifica se é uma carta de power"""
        return self.type.lower() == "power"
    
    @computed_field
    @property
    def is_unit(self) -> bool:
        """Verifica se é uma unidade"""
        return self.type.lower() == "unit"
    
    @computed_field
    @property
    def is_spell(self) -> bool:
        """Verifica se é uma magia"""
        return self.type.lower() == "spell"
    
    @computed_field
    @property
    def is_sigil(self) -> bool:
        """Verifica se é um Sigil (power básico)"""
        return self.is_power and "sigil" in self.name.lower()
    
    @computed_field
    @property
    def influence_count(self) -> int:
        """Conta quantos símbolos de influência a carta requer"""
        if not self.influence:
            return 0
        return self.influence.count("{")
    
    @computed_field
    @property
    def faction_count(self) -> int:
        """Conta quantas facções diferentes a carta usa"""
        if not self.influence:
            return 0
        factions = set()
        for symbol in ["{F}", "{T}", "{J}", "{P}", "{S}"]:
            if symbol in self.influence:
                factions.add(symbol)
        return len(factions)
    
    # =============================================================================
    # 🚨 ÂNCORA: MARKET_ACCESS - Detecção de acesso ao mercado
    # Contexto: Identifica cartas que podem acessar o mercado
    # Cuidado: Baseado em análise de texto, pode ter falsos positivos
    # Dependências: Usado pelo deck builder para incluir merchants
    # =============================================================================
    
    @computed_field
    @property
    def can_access_market(self) -> bool:
        """
        Detecta se a carta pode acessar o mercado
        Busca por 'your market' no texto da carta
        """
        if not self.card_text:
            return False
        
        text_lower = self.card_text.lower()
        # Padrões comuns que indicam acesso ao mercado
        market_patterns = [
            "your market",
            "from your market", 
            "in your market"
        ]
        
        return any(pattern in text_lower for pattern in market_patterns)
    
    # Métodos úteis
    def format_cost(self) -> str:
        """Formata custo com influência. Ex: 3{F}{F}"""
        return f"{self.cost}{self.influence}" if self.cost > 0 else self.influence
    
    def format_stats(self) -> str:
        """Formata stats para units. Ex: 3/3"""
        if self.is_unit and self.attack is not None and self.health is not None:
            return f"{self.attack}/{self.health}"
        return ""
    
    def format_for_deck(self) -> str:
        """Formata carta para lista de deck. Ex: Torch | 1{F} | Common"""
        parts = [self.name, self.format_cost()]
        
        if self.is_unit:
            stats = self.format_stats()
            if stats:
                parts.append(stats)
                
        parts.append(self.rarity)
        return " | ".join(parts)
    
    def __str__(self) -> str:
        """Representação em string da carta"""
        return self.format_for_deck()


# =============================================================================
# 🚨 ÂNCORA: DECK_CARD - Carta com quantidade no deck
# Contexto: Representa "4x Torch" por exemplo
# Cuidado: Quantidade máxima é 4 (exceto Sigils)
# Dependências: Usado pelo Deck e validador
# =============================================================================

class DeckCard(BaseModel):
    """Representa uma carta e sua quantidade no deck"""
    card: Card
    quantity: int = Field(1, ge=1, le=4, description="Quantidade (1-4)")
    
    def format(self) -> str:
        """Formata para exibição. Ex: 4 Torch (Set1 #8)"""
        return f"{self.quantity} {self.card.name}"
    
    def format_detailed(self) -> str:
        """Formata com detalhes. Ex: 4x Torch | 1{F} | 2 damage | Common"""
        return f"{self.quantity}x {self.card.format_for_deck()}"
    
    def __str__(self) -> str:
        return self.format()


# =============================================================================
# 🚨 ÂNCORA: DECK_MODEL - Modelo de deck completo
# Contexto: Contém main deck + mercado opcional
# Cuidado: Validação mínima aqui, usar DeckValidator para validação completa
# Dependências: DeckBuilder cria isto, Exporter usa para gerar arquivo
# =============================================================================

class Deck(BaseModel):
    """Representa um deck completo do Eternal"""
    name: str = Field("Unnamed Deck", description="Nome do deck")
    description: Optional[str] = Field(None, description="Descrição/estratégia")
    
    # Cartas principais (75-150)
    main_deck: List[DeckCard] = Field(default_factory=list, description="Deck principal")
    
    # Mercado (exatamente 5 cartas únicas)
    market: Optional[List[Card]] = Field(None, description="Cartas do mercado")
    
    # Metadata
    format: str = Field("Throne", description="Formato do jogo")
    archetype: Optional[str] = Field(None, description="Aggro, Control, Midrange, Combo")
    
    # Estatísticas computadas
    @computed_field
    @property
    def total_cards(self) -> int:
        """Total de cartas no main deck"""
        return sum(dc.quantity for dc in self.main_deck)
    
    @computed_field
    @property
    def power_count(self) -> int:
        """Total de power cards"""
        return sum(
            dc.quantity for dc in self.main_deck 
            if dc.card.is_power
        )
    
    @computed_field
    @property
    def unit_count(self) -> int:
        """Total de unidades"""
        return sum(
            dc.quantity for dc in self.main_deck 
            if dc.card.is_unit
        )
    
    @computed_field
    @property
    def spell_count(self) -> int:
        """Total de spells"""
        return sum(
            dc.quantity for dc in self.main_deck 
            if dc.card.is_spell
        )
    
    @computed_field
    @property
    def average_cost(self) -> float:
        """Custo médio das cartas não-power"""
        non_power_cards = [
            (dc.card.cost, dc.quantity) 
            for dc in self.main_deck 
            if not dc.card.is_power
        ]
        
        if not non_power_cards:
            return 0.0
            
        total_cost = sum(cost * qty for cost, qty in non_power_cards)
        total_cards = sum(qty for _, qty in non_power_cards)
        
        return round(total_cost / total_cards, 2) if total_cards > 0 else 0.0
    
    @computed_field
    @property
    def power_ratio(self) -> float:
        """Proporção de powers no deck"""
        if self.total_cards == 0:
            return 0.0
        return round(self.power_count / self.total_cards, 2)
    
    @computed_field
    @property
    def has_market_access(self) -> bool:
        """Verifica se o deck tem cartas que acessam o mercado"""
        return any(
            dc.card.can_access_market 
            for dc in self.main_deck
        )
    
    # Métodos helper
    def get_curve(self) -> Dict[int, int]:
        """Retorna a curva de mana (custo -> quantidade)"""
        curve = {}
        for dc in self.main_deck:
            if not dc.card.is_power:
                cost = dc.card.cost
                curve[cost] = curve.get(cost, 0) + dc.quantity
        return dict(sorted(curve.items()))
    
    def get_factions(self) -> Dict[str, int]:
        """Conta cartas por facção"""
        factions = {}
        faction_symbols = {"{F}": "Fire", "{T}": "Time", "{J}": "Justice", 
                          "{P}": "Primal", "{S}": "Shadow"}
        
        for dc in self.main_deck:
            for symbol, name in faction_symbols.items():
                if symbol in dc.card.influence:
                    factions[name] = factions.get(name, 0) + dc.quantity
                    
        return factions
    
    def format_stats(self) -> str:
        """Formata estatísticas do deck"""
        stats = [
            f"Total: {self.total_cards} cards",
            f"Powers: {self.power_count} ({int(self.power_ratio * 100)}%)",
            f"Units: {self.unit_count}",
            f"Spells: {self.spell_count}",
            f"Avg Cost: {self.average_cost}"
        ]
        
        if self.market:
            stats.append(f"Market: {len(self.market)} cards")
            
        return " | ".join(stats)
    
    def __str__(self) -> str:
        return f"{self.name} - {self.format_stats()}"


# =============================================================================
# 🚨 ÂNCORA: DECK_RESULT - Resultado da geração de deck
# Contexto: Usado para retornar deck + informações adicionais
# Cuidado: Inclui tanto o deck quanto metadata sobre a geração
# Dependências: Retornado pelo DeckBuilder
# =============================================================================

class DeckResult(BaseModel):
    """Resultado completo da geração de deck"""
    deck: Deck
    success: bool = True
    message: Optional[str] = None
    generation_time: Optional[float] = None
    tokens_used: Optional[int] = None
    
    # Informações de debug
    cards_considered: Optional[int] = None
    strategy_analysis: Optional[str] = None
    
    def __str__(self) -> str:
        if self.success:
            return f"✅ {self.deck.name} generated successfully"
        return f"❌ Generation failed: {self.message}"