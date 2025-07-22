"""
Eternal Card Game Skills Knowledge Base
Contém todas as skills (battle e outras) com suas descrições,
sinergias e metadados para o sistema RAG.
"""

from typing import Dict, List, Tuple, Any
from enum import IntEnum

# =============================================================================
# 🚨 ÂNCORA: SKILL_ENUMS - Enums para categorização de skills
# Contexto: Define níveis de poder e complexidade para ajudar IA
# Cuidado: Valores são subjetivos mas baseados no meta competitivo
# Dependências: Usado pelo StrategyScout para priorizar cartas
# =============================================================================

class PowerLevel(IntEnum):
    WEAK = 1           # Raramente usado competitivamente
    BELOW_AVERAGE = 2  # Situacional
    AVERAGE = 3        # Sólido mas não excepcional
    STRONG = 4         # Frequente em decks competitivos
    VERY_STRONG = 5    # Define o meta

class Complexity(IntEnum):
    SIMPLE = 1      # Efeito direto e óbvio
    MODERATE = 2    # Requer algum timing ou setup
    COMPLEX = 3     # Múltiplas decisões ou interações complexas

# Type hint para consistência
SkillData = Dict[str, Any]

# =============================================================================
# 🚨 ÂNCORA: BATTLE_SKILLS - Skills que afetam combate
# Contexto: Skills que só funcionam em unidades em jogo
# Cuidado: Descrições são oficiais do jogo, não alterar
# Dependências: ChromaDB embeddings, StrategyScout, DeckCrafter
# =============================================================================

BATTLE_SKILLS: Dict[str, SkillData] = {
    # A
    "Aegis": {
        "description": "Protected from one enemy spell or effect (but not from battle damage)",
        "synergies": ["voltron strategies", "key units", "finishers", "relic weapons"],
        "counters": ["killer", "transform effects", "silence", "relic removal"],
        "archetypes": ["midrange", "control", "voltron"],
        "embed_text": "Aegis protection shield spell immunity hexproof protective barrier defense against removal one-time protection",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "uncommon_plus",
        "deck_role": ["protection", "finisher"],
        "combo_potential": 3
    },
    
    # B
    "Berserk": {
        "description": "When this attacks, you may give it Reckless to attack a second time this turn. Can only be used once",
        "synergies": ["weapon buffs", "combat tricks", "overwhelm", "lifesteal", "pump spells"],
        "counters": ["stun", "permafrost", "deadly blockers", "fast removal"],
        "archetypes": ["aggro", "midrange", "weapons"],
        "embed_text": "Berserk double attack twice aggressive combat multiple strikes reckless fury two attacks extra damage",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.MODERATE,
        "rarity_trend": "uncommon_plus",
        "deck_role": ["damage", "pressure"],
        "combo_potential": 4
    },
    
    # C
    "Charge": {
        "description": "Can attack the turn it is played",
        "synergies": ["aggro", "surprise attacks", "combat tricks", "weapons", "pump spells"],
        "counters": ["ambush units", "fast removal", "permafrost"],
        "archetypes": ["aggro", "burn", "tempo"],
        "embed_text": "Charge immediate attack haste rush aggressive tempo surprise damage fast pressure no summoning sickness",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "common",
        "deck_role": ["pressure", "finisher", "tempo"],
        "combo_potential": 3
    },
    
    # D
    "Deadly": {
        "description": "Kills any unit it damages",
        "synergies": ["quickdraw", "small units", "ping damage", "killer", "taunt"],
        "counters": ["aegis", "go-wide strategies", "flying", "overwhelm"],
        "archetypes": ["control", "midrange", "removal"],
        "embed_text": "Deadly deathtouch instant kill removal efficient trades destroy damage lethal poison assassin",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "common",
        "deck_role": ["removal", "defense"],
        "combo_potential": 4
    },
    
    "Decay": {
        "description": "Permanently reduces the strength and health of units and relic weapons it damages",
        "synergies": ["ping damage", "multi-hit", "relic weapons"],
        "counters": ["deadly", "overwhelm", "go-wide"],
        "archetypes": ["control", "grind"],
        "embed_text": "Decay permanent reduction debuff weaken shrink stats lower attack health lasting effect",
        "power_level": PowerLevel.BELOW_AVERAGE,
        "complexity": Complexity.MODERATE,
        "rarity_trend": "rare_plus",
        "deck_role": ["control", "value"],
        "combo_potential": 2
    },
    
    "Double Damage": {
        "description": "Deals double damage",
        "synergies": ["overwhelm", "pump spells", "berserk", "killer", "relic weapons"],
        "counters": ["chump blockers", "deadly", "permafrost"],
        "archetypes": ["aggro", "combo", "burn"],
        "embed_text": "Double damage twice multiplier burst high damage amplify power overwhelming force",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "rare_plus",
        "deck_role": ["finisher", "burst"],
        "combo_potential": 5
    },
    
    # E
    "Endurance": {
        "description": "Readies at the end of your turn, can't be stunned, and can't be exhausted except to pay costs",
        "synergies": ["tap abilities", "multiple blocks", "killer"],
        "counters": ["silence", "transform", "hard removal"],
        "archetypes": ["control", "midrange"],
        "embed_text": "Endurance ready untap vigilance stun immunity no exhaustion multiple uses defensive",
        "power_level": PowerLevel.AVERAGE,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "uncommon_plus",
        "deck_role": ["defense", "utility"],
        "combo_potential": 3
    },
    
    "Exalted": {
        "description": "When this unit dies, play a weapon with its stats and battle skills on one of your units",
        "synergies": ["sacrifice effects", "weapon synergies", "revenge"],
        "counters": ["silence", "transform", "void hate"],
        "archetypes": ["midrange", "weapons", "value"],
        "embed_text": "Exalted death trigger weapon creation inheritance stats transfer battle skills lasting value",
        "power_level": PowerLevel.AVERAGE,
        "complexity": Complexity.MODERATE,
        "rarity_trend": "rare_plus",
        "deck_role": ["value", "resilience"],
        "combo_potential": 3
    },
    
    # F
    "Flying": {
        "description": "Can only be blocked by other units with flying",
        "synergies": ["weapons", "pump spells", "aegis", "combat tricks"],
        "counters": ["reach units", "flying blockers", "sandstorm titan", "removal"],
        "archetypes": ["aggro", "midrange", "control finishers"],
        "embed_text": "Flying evasion aerial airborne unblockable bypass ground units wings flight soar",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "common",
        "deck_role": ["evasion", "finisher"],
        "combo_potential": 3
    },
    
    # K
    "Killer": {
        "description": "May be exhausted one time to attack any enemy unit",
        "synergies": ["deadly", "pump spells", "endurance", "summon effects"],
        "counters": ["aegis", "ambush blockers", "fast removal"],
        "archetypes": ["control", "removal", "midrange"],
        "embed_text": "Killer targeted removal fight destroy unit direct attack assassinate execute",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.MODERATE,
        "rarity_trend": "uncommon_plus",
        "deck_role": ["removal", "utility"],
        "combo_potential": 4
    },
    
    # L
    "Lifesteal": {
        "description": "When this deals damage, you gain that much health",
        "synergies": ["bolster", "berserk", "double damage", "overwhelm", "pump spells"],
        "counters": ["face aegis", "stun", "permafrost"],
        "archetypes": ["midrange", "control", "lifegain"],
        "embed_text": "Lifesteal healing drain life gain health vampire sustain recovery lifelink",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "common",
        "deck_role": ["sustain", "stabilization"],
        "combo_potential": 5
    },
    
    # N
    "Nomad": {
        "description": "This unit has Flying on your turn and +X/+X on the enemy turn",
        "synergies": ["combat tricks", "weapons", "pump spells"],
        "counters": ["removal on your turn", "stun effects"],
        "archetypes": ["tempo", "midrange"],
        "embed_text": "Nomad flying shifting stats defensive offensive mode change adaptation versatile",
        "power_level": PowerLevel.AVERAGE,
        "complexity": Complexity.MODERATE,
        "rarity_trend": "rare",
        "deck_role": ["versatile", "tempo"],
        "combo_potential": 2
    },
    
    # O
    "Overwhelm": {
        "description": "When this hits an enemy unit, leftover damage is dealt to the enemy player or site",
        "synergies": ["pump spells", "double damage", "berserk", "killer"],
        "counters": ["high health blockers", "deadly", "multiple blockers"],
        "archetypes": ["aggro", "midrange", "finisher"],
        "embed_text": "Overwhelm trample excess damage breakthrough pierce through blockers face damage",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "uncommon_plus",
        "deck_role": ["pressure", "finisher"],
        "combo_potential": 4
    },
    
    # Q
    "Quickdraw": {
        "description": "When this kills a blocking unit, the blocker doesn't deal damage back",
        "synergies": ["deadly", "high attack", "pump spells", "weapons"],
        "counters": ["overwhelm", "unblockable", "aegis"],
        "archetypes": ["aggro", "midrange"],
        "embed_text": "Quickdraw first strike fast damage priority speed quick reflexes",
        "power_level": PowerLevel.AVERAGE,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "common",
        "deck_role": ["combat advantage"],
        "combo_potential": 5
    },
    
    # R
    "Reckless": {
        "description": "This must attack",
        "synergies": ["high stats", "lifesteal", "overwhelm"],
        "counters": ["deadly blockers", "combat tricks", "stun"],
        "archetypes": ["aggro"],
        "embed_text": "Reckless forced attack must attack aggressive downside berserker fury",
        "power_level": PowerLevel.WEAK,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "common",
        "deck_role": ["aggression"],
        "combo_potential": 2
    },
    
    "Regen": {
        "description": "The first time a unit with Regen is dealt damage, prevent it",
        "synergies": ["revenge", "exalted", "weapons", "aegis"],
        "counters": ["double damage", "overwhelm", "killer"],
        "archetypes": ["midrange", "control"],
        "embed_text": "Regen regeneration heal damage prevention shield protection resilience recovery",
        "power_level": PowerLevel.AVERAGE,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "uncommon_plus",
        "deck_role": ["resilience"],
        "combo_potential": 3
    },
    
    "Revenge": {
        "description": "The first time this is killed, give it Destiny and put it into the top ten cards of your deck",
        "synergies": ["warcry", "exalted", "sacrifice effects", "infiltrate"],
        "counters": ["silence", "transform", "void hate"],
        "archetypes": ["midrange", "value", "grind"],
        "embed_text": "Revenge resurrect return destiny comeback value recursion second chance rebirth",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.MODERATE,
        "rarity_trend": "rare",
        "deck_role": ["value", "recursion"],
        "combo_potential": 4
    },
    
    # T
    "Taunt": {
        "description": "This unit must be blocked if possible",
        "synergies": ["deadly", "high health", "regen", "combat tricks"],
        "counters": ["killer", "flying", "removal"],
        "archetypes": ["control", "midrange"],
        "embed_text": "Taunt forced block provoke challenge guardian defender protection",
        "power_level": PowerLevel.AVERAGE,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "uncommon",
        "deck_role": ["protection", "control"],
        "combo_potential": 3
    },
    
    # U
    "Unblockable": {
        "description": "Cannot be blocked",
        "synergies": ["weapons", "pump spells", "infiltrate", "combat tricks"],
        "counters": ["face aegis", "armor", "lifesteal blockers"],
        "archetypes": ["aggro", "combo"],
        "embed_text": "Unblockable evasion unstoppable bypass guaranteed damage shadow sneak stealth",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "rare",
        "deck_role": ["finisher", "inevitability"],
        "combo_potential": 3
    },
    
    # V
    "Valor": {
        "description": "This unit gets +1/+1 this turn for each unit that blocks it",
        "synergies": ["overwhelm", "taunt", "multi-attack", "combat tricks"],
        "counters": ["single blockers", "deadly", "removal"],
        "archetypes": ["aggro", "combat"],
        "embed_text": "Valor courage strength in numbers growing power multi-block punishment brave",
        "power_level": PowerLevel.BELOW_AVERAGE,
        "complexity": Complexity.MODERATE,
        "rarity_trend": "uncommon",
        "deck_role": ["combat trick"],
        "combo_potential": 2
    },
    
    # W
    "Warcry": {
        "description": "When this attacks, the top unit or weapon of your deck gets +1/+1",
        "synergies": ["weapons", "echo units", "revenge", "charge units"],
        "counters": ["face aegis on weapons", "control decks"],
        "archetypes": ["aggro", "midrange", "weapons"],
        "embed_text": "Warcry buff pump deck manipulation top card enhancement battle cry strengthen",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "common",
        "deck_role": ["value", "aggression"],
        "combo_potential": 4
    }
}

# =============================================================================
# 🚨 ÂNCORA: OTHER_SKILLS - Skills não relacionadas a combate
# Contexto: Skills que afetam como/quando cartas são jogadas
# Cuidado: Algumas aparecem em spells (Echo) outras só em units (Ambush)
# Dependências: ChromaDB embeddings, StrategyScout, DeckCrafter
# =============================================================================

OTHER_SKILLS: Dict[str, SkillData] = {
    # A
    "Ambush": {
        "description": "Can be played to block an enemy attack or at the end of their turn",
        "synergies": ["instant speed tricks", "killer units", "summon effects", "combat tricks"],
        "counters": ["torch after blocks", "sweepers", "harsh rule"],
        "archetypes": ["tempo", "control", "tricks"],
        "embed_text": "Ambush instant speed flash surprise blocker defensive trick end of turn unexpected",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.MODERATE,
        "rarity_trend": "uncommon_plus",
        "deck_role": ["defense", "tempo"],
        "combo_potential": 4
    },
    
    # B
    "Bond": {
        "description": "When played, you may exhaust another unit of the same type to reduce this card's cost by the exhausted unit's power",
        "synergies": ["tribal decks", "go-wide strategies", "token generators"],
        "counters": ["removal heavy", "board wipes"],
        "archetypes": ["tribal", "aggro", "tempo"],
        "embed_text": "Bond cost reduction tribal synergy exhaust creature type discount cheap",
        "power_level": PowerLevel.AVERAGE,
        "complexity": Complexity.MODERATE,
        "rarity_trend": "common",
        "deck_role": ["cost reduction", "tempo"],
        "combo_potential": 3
    },
    
    # D
    "Destiny": {
        "description": "Automatically play when drawn, then draw another card",
        "synergies": ["echo", "revenge", "card draw", "warcry buffs"],
        "counters": ["hand size limit", "counterspells"],
        "archetypes": ["combo", "value", "tempo"],
        "embed_text": "Destiny free play automatic draw card advantage tempo surprise value",
        "power_level": PowerLevel.VERY_STRONG,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "rare_plus",
        "deck_role": ["tempo", "value"],
        "combo_potential": 5
    },
    
    # E
    "Echo": {
        "description": "Get an additional copy when drawn",
        "synergies": ["cost reduction", "warcry", "destiny", "card draw"],
        "counters": ["hand size limit", "discard"],
        "archetypes": ["value", "combo", "control"],
        "embed_text": "Echo duplicate copy card advantage value two for one clone repeat",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "uncommon_plus",
        "deck_role": ["value", "card advantage"],
        "combo_potential": 4
    },
    
    # I
    "Imbue": {
        "description": "When you play a unit with Imbue, you may stun one of your other units and keep it stunned. As long as it's stunned, this unit gets its stats",
        "synergies": ["summon effects", "infiltrate units", "sacrifice synergies"],
        "counters": ["removal", "silence", "board wipes"],
        "archetypes": ["combo", "midrange"],
        "embed_text": "Imbue power steal stats transfer stun lock sacrifice enhance absorb",
        "power_level": PowerLevel.BELOW_AVERAGE,
        "complexity": Complexity.COMPLEX,
        "rarity_trend": "rare",
        "deck_role": ["power boost", "combo"],
        "combo_potential": 3
    },
    
    "Inscribe": {
        "description": "This card can be played as a depleted Sigil",
        "synergies": ["power consistency", "influence fixing", "late game value"],
        "counters": ["aggro pressure", "face damage"],
        "archetypes": ["control", "midrange", "3+ colors"],
        "embed_text": "Inscribe flexibility power sigil modal choice consistency fixing",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.MODERATE,
        "rarity_trend": "uncommon_plus",
        "deck_role": ["flexibility", "consistency"],
        "combo_potential": 2
    },
    
    # P
    "Pledge": {
        "description": "On your first turn, a card with Pledge can be played as a Sigil",
        "synergies": ["mulligan decisions", "power consistency", "aggro curves"],
        "counters": ["late game irrelevance"],
        "archetypes": ["aggro", "all decks"],
        "embed_text": "Pledge first turn sigil power consistency early game flexibility",
        "power_level": PowerLevel.AVERAGE,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "common",
        "deck_role": ["consistency"],
        "combo_potential": 1
    },
    
    # S

    "Shift": {
        "description": "Units with Shift may be played Shifted for their Shift cost. Shifted units can't attack, block, or be selected by any cards. Their passive abilities still function, and they can still be affected by global effects. Units remain Shifted for three turns, then emerge ready and gain Unblockable for the turn",
        "synergies": [
            "passive abilities",      # Continuam funcionando
            "global buffs",          # "+1/+1 to all units" ainda aplica
            "setup strategies",      # 3 turnos para preparar
            "surprise attacks",      # Emerge com Unblockable
            "cost reduction",        # Shift cost geralmente menor
            "protection timing",     # Dodge removal específico
            "combat tricks"          # Emerge no momento certo
        ],
        "counters": [
            "harsh rule",           # Mata mesmo Shifted
            "sack the city",       # Afeta todas unidades
            "end of days",         # Board wipe global
            "setback",             # Retorna mesmo Shifted
            "passage of eons",     # Transform all units
            "board stalls",        # 3 turnos sem blocker
            "aggro pressure"       # Tempo perdido
        ],
        "archetypes": ["control", "midrange", "tempo", "combo"],
        "embed_text": "shift shifted emerge phase out untargetable hexproof protection three turns 3 turns alternate cost cheaper deploy early dodge removal setup attacker unblockable timing temporary immunity phasing vanish reappear",
        "power_level": PowerLevel.STRONG,    # 4
        "complexity": Complexity.COMPLEX,     # 3
        "rarity_trend": "rare_plus",
        "deck_role": ["protection", "tempo", "alternate cost", "setup"],
        "combo_potential": 4
    },

    "Stealth": {
        "description": "This unit is played hidden. It is revealed when it deals or takes damage, is affected by an enemy effect, or has anything played directly on it",
        "synergies": ["infiltrate", "weapons", "combat tricks", "surprise attacks"],
        "counters": ["board wipes", "relic weapons"],
        "archetypes": ["tempo", "aggro", "tricks"],
        "embed_text": "Stealth hidden invisible concealed surprise infiltrate sneak undetected",
        "power_level": PowerLevel.AVERAGE,
        "complexity": Complexity.MODERATE,
        "rarity_trend": "rare",
        "deck_role": ["surprise", "protection"],
        "combo_potential": 3
    },
    
    "Swift": {
        "description": "This spell doesn't give your opponent a chance to respond and can't be negated",
        "synergies": ["combo protection", "guaranteed effects", "burn"],
        "counters": ["face aegis", "prevention effects"],
        "archetypes": ["combo", "burn", "control"],
        "embed_text": "Swift uncounterable guaranteed instant no response unstoppable certain",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "rare_plus",
        "deck_role": ["reliability", "combo"],
        "combo_potential": 3
    },
    
    # U
    "Unleash": {
        "description": "When you play this card, create and draw a copy of it. Discard it at the end of the turn. The copy's cost can't be reduced",
        "synergies": ["spell damage", "combo pieces", "burst"],
        "counters": ["hand size limit", "counterspells"],
        "archetypes": ["combo", "burn"],
        "embed_text": "Unleash copy temporary burst double cast amplify spell duplicate",
        "power_level": PowerLevel.AVERAGE,
        "complexity": Complexity.MODERATE,
        "rarity_trend": "rare",
        "deck_role": ["burst", "combo"],
        "combo_potential": 4
    },
    
    # V
    "Versatile": {
        "description": "This can be played as either a relic weapon or unit weapon",
        "synergies": ["weapon matters", "empty board", "flexibility"],
        "counters": ["weapon removal", "unit removal"],
        "archetypes": ["weapons", "midrange"],
        "embed_text": "Versatile flexible choice modal weapon relic unit adaptable option",
        "power_level": PowerLevel.AVERAGE,
        "complexity": Complexity.MODERATE,
        "rarity_trend": "rare",
        "deck_role": ["flexibility"],
        "combo_potential": 2
    },
    
    "Voidbound": {
        "description": "This card can't leave the void",
        "synergies": ["void recursion", "entomb effects", "reanimator"],
        "counters": ["silence in void", "void hate"],
        "archetypes": ["reanimator", "void"],
        "embed_text": "Voidbound stuck permanent void graveyard locked eternal rest",
        "power_level": PowerLevel.WEAK,
        "complexity": Complexity.SIMPLE,
        "rarity_trend": "rare",
        "deck_role": ["void strategy"],
        "combo_potential": 2
    },
    
    # W
    "Warp": {
        "description": "You can play this from the top of your deck",
        "synergies": ["scout", "deck manipulation", "card advantage"],
        "counters": ["face aegis for spells", "counterspells"],
        "archetypes": ["control", "value"],
        "embed_text": "Warp top deck play library cast deck access immediate value",
        "power_level": PowerLevel.STRONG,
        "complexity": Complexity.MODERATE,
        "rarity_trend": "rare",
        "deck_role": ["value", "card advantage"],
        "combo_potential": 3
    }
}

# =============================================================================
# 🚨 ÂNCORA: SKILL_CATEGORIES - Agrupamento de skills por função
# Contexto: Ajuda IA entender papéis das skills no deck
# Cuidado: Uma skill pode estar em múltiplas categorias
# Dependências: StrategyScout usa para filtrar por estratégia
# =============================================================================

SKILL_CATEGORIES = {
    "evasion": ["Flying", "Unblockable", "Stealth"],
    "protection": ["Aegis", "Regen", "Endurance", "Stealth"],
    "removal": ["Deadly", "Killer", "Decay"],
    "combat_advantage": ["Deadly", "Quickdraw", "Double Damage", "Berserk", "Overwhelm"],
    "value_generation": ["Echo", "Destiny", "Revenge", "Warcry", "Exalted", "Warp"],
    "tribal_synergy": ["Bond", "Imbue"],
    "resource_advantage": ["Lifesteal", "Inscribe", "Pledge"],
    "tempo": ["Charge", "Ambush", "Warp", "Destiny"],
    "aggro_tools": ["Charge", "Overwhelm", "Warcry", "Berserk", "Quickdraw"],
    "control_tools": ["Deadly", "Killer", "Endurance", "Taunt", "Ambush"],
    "finishers": ["Unblockable", "Flying", "Double Damage", "Overwhelm", "Aegis"],
    "flexibility": ["Versatile", "Inscribe", "Pledge", "Nomad"]
}

# =============================================================================
# 🚨 ÂNCORA: SKILL_SYNERGIES - Combinações poderosas conhecidas
# Contexto: Além das sinergias óbvias (Deadly+Quickdraw)
# Cuidado: Força da sinergia é subjetiva mas baseada no meta
# Dependências: DeckCrafter usa para identificar packages
# =============================================================================

SKILL_SYNERGIES = {
    # Sinergias Tier 1 (Muito Fortes)
    ("Deadly", "Quickdraw"): {
        "strength": 5,
        "description": "Kills attackers before taking damage, perfect defense",
        "examples": ["Scorpion Wasp", "Desert Marshal with weapons"]
    },
    ("Lifesteal", "Berserk"): {
        "strength": 5,
        "description": "Double the healing with two attacks",
        "examples": ["Moldermuck", "Lifesteal weapon on Berserk unit"]
    },
    ("Overwhelm", "Double Damage"): {
        "strength": 5,
        "description": "Massive face damage potential through blockers",
        "examples": ["Carnosaur", "Flameblast"]
    },
    
    # Sinergias Tier 2 (Fortes)
    ("Warcry", "Revenge"): {
        "strength": 4,
        "description": "Buffs the revenge copy when it returns",
        "examples": ["Ripknife Assassin"]
    },
    ("Echo", "Destiny"): {
        "strength": 4,
        "description": "Two free units when drawn",
        "examples": ["Twinning Ritual on Destiny units"]
    },
    ("Flying", "Aegis"): {
        "strength": 4,
        "description": "Evasive threat protected from removal",
        "examples": ["Silverwing Familiar", "Hooru Fliers"]
    },
    ("Killer", "Deadly"): {
        "strength": 4,
        "description": "Instant removal for any unit",
        "examples": ["Deathstrike", "Deadly unit with Xenan Initiation"]
    },
    
    # Sinergias Tier 3 (Moderadas)
    ("Taunt", "Deadly"): {
        "strength": 3,
        "description": "Forces unfavorable blocks",
        "examples": ["Deadly unit with Taunt relic"]
    },
    ("Regen", "Revenge"): {
        "strength": 3,
        "description": "Harder to kill the first time for revenge value",
        "examples": ["Revenge units with combat tricks"]
    },
    ("Charge", "Warcry"): {
        "strength": 3,
        "description": "Immediate attack triggers warcry",
        "examples": ["Oni Ronin", "Rakano aggro package"]
    },
    ("Endurance", "Killer"): {
        "strength": 3,
        "description": "Kill every turn without losing blocker",
        "examples": ["Sandstorm Titan with Killer"]
    }
}

# =============================================================================
# 🚨 ÂNCORA: HELPER_FUNCTIONS - Funções úteis para queries
# Contexto: Facilita busca e análise de skills
# Cuidado: Usadas por outros módulos, manter assinaturas
# Dependências: StrategyScout, DeckCrafter
# =============================================================================

def get_skills_by_archetype(archetype: str) -> List[str]:
    """Retorna skills relevantes para um arquétipo"""
    archetype_lower = archetype.lower()
    relevant_skills = []
    
    # Busca em battle skills
    for skill, data in BATTLE_SKILLS.items():
        if archetype_lower in [a.lower() for a in data["archetypes"]]:
            relevant_skills.append(skill)
    
    # Busca em other skills
    for skill, data in OTHER_SKILLS.items():
        if archetype_lower in [a.lower() for a in data["archetypes"]]:
            relevant_skills.append(skill)
            
    return sorted(list(set(relevant_skills)))

def get_skills_by_power_level(min_level: int = 3) -> List[str]:
    """Retorna skills com poder >= min_level"""
    powerful_skills = []
    
    for skill, data in {**BATTLE_SKILLS, **OTHER_SKILLS}.items():
        if data["power_level"] >= min_level:
            powerful_skills.append(skill)
            
    return sorted(powerful_skills)

def get_synergistic_skills(skill: str) -> List[Tuple[str, int]]:
    """Retorna skills que combinam bem com a skill dada"""
    synergies = []
    
    # Verifica sinergias diretas
    for (skill1, skill2), syn_data in SKILL_SYNERGIES.items():
        if skill == skill1:
            synergies.append((skill2, syn_data["strength"]))
        elif skill == skill2:
            synergies.append((skill1, syn_data["strength"]))
    
    # Verifica sinergias mencionadas nos dados
    skill_data = BATTLE_SKILLS.get(skill) or OTHER_SKILLS.get(skill)
    if skill_data:
        # Adiciona sinergias mencionadas com força média (3)
        for syn in skill_data["synergies"]:
            # Procura skills que correspondem à sinergia mencionada
            for other_skill in {**BATTLE_SKILLS, **OTHER_SKILLS}.keys():
                if other_skill.lower() in syn.lower():
                    synergies.append((other_skill, 3))
    
    # Remove duplicatas e ordena por força
    unique_synergies = {}
    for s, strength in synergies:
        unique_synergies[s] = max(unique_synergies.get(s, 0), strength)
    
    return sorted(unique_synergies.items(), key=lambda x: x[1], reverse=True)

def get_skill_counters(skill: str) -> List[str]:
    """Retorna o que é efetivo contra a skill"""
    skill_data = BATTLE_SKILLS.get(skill) or OTHER_SKILLS.get(skill)
    if skill_data:
        return skill_data["counters"]
    return []

def get_skills_for_role(role: str) -> List[str]:
    """Retorna skills adequadas para um papel específico no deck"""
    role_lower = role.lower()
    relevant_skills = []
    
    for skill, data in {**BATTLE_SKILLS, **OTHER_SKILLS}.items():
        if role_lower in [r.lower() for r in data["deck_role"]]:
            relevant_skills.append(skill)
            
    return sorted(list(set(relevant_skills)))

# Alias úteis para compatibilidade
ALL_SKILLS = {**BATTLE_SKILLS, **OTHER_SKILLS}
COMPETITIVE_SKILLS = get_skills_by_power_level(PowerLevel.STRONG)