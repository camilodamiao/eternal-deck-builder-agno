"""
Eternal Card Game Synergies Knowledge Base
Foca em COMO mecânicas interagem, sem exemplos específicos de cartas.
Deixa a IA descobrir quais cartas usar baseado nas mecânicas.
"""

from typing import Dict, List, Tuple, Any

# =============================================================================
# 🚨 ÂNCORA: DETAILED_SYNERGIES - Sinergias mecânicas profundas
# Contexto: Explica COMO skills interagem, não QUAIS cartas usar
# Cuidado: Focar em mecânicas puras, sem mencionar cartas específicas
# Dependências: StrategyScout usa para entender interações
# =============================================================================

DETAILED_SYNERGIES = {
    "deadly_quickdraw_combo": {
        "skills": ["Deadly", "Quickdraw"],
        "strength": 5,
        "mechanics": "Quando mesma unidade tem ambas: mata qualquer blocker (Deadly) sem receber dano de volta (Quickdraw)",
        "requirements": "Precisa dar ambas skills para mesma unidade via weapons, spells ou habilidades",
        "strategic_value": "Remoção perfeita que sobrevive ao combate",
        "limitations": "Só funciona se unidade for bloqueada por uma unidade com menos health que o ataque da unidade com Deadly, Quickdraw e Deadly não protegem contra Killer"
    },
    
    "lifesteal_bolster_engine": {
        "skills": ["Lifesteal", "Bolster"],
        "strength": 5,
        "mechanics": "Cada ponto de dano com Lifesteal gera ganho de vida, que triggera todas unidades com Bolster",
        "requirements": "Unidades com Bolster em jogo + fonte consistente de Lifesteal",
        "strategic_value": "Snowball de stats enquanto ganha vida",
        "limitations": "Vulnerável a remoção em massa ou silence nas peças chave"
    },
    
    "echo_destiny_value": {
        "skills": ["Echo", "Destiny"],
        "strength": 4,
        "mechanics": "Destiny joga carta grátis quando comprada, Echo dá cópia. Resultado: 2 cartas grátis",
        "requirements": "Formas de dar Destiny para cartas com Echo ou vice-versa",
        "strategic_value": "Explosão de tempo e vantagem de cartas",
        "limitations": "Destiny não triggera na cópia do Echo se adicionado depois"
    },
    
    "warcry_weapon_scaling": {
        "skills": ["Warcry", "Weapon-matters"],
        "strength": 4,
        "mechanics": "Warcry buffa próxima weapon ou unidade do deck, estratégias de weapons se beneficiam de weapons buffadas",
        "requirements": "Densidade alta de weapons no deck + unidades com Warcry",
        "strategic_value": "Weapons ficam progressivamente mais fortes",
        "limitations": "Precisa densidade correta de ambos tipos de carta"
    },
    
    "overwhelm_double_damage_burst": {
        "skills": ["Overwhelm", "Double Damage"],
        "strength": 5,
        "mechanics": "Double Damage duplica TODO dano, Overwhelm passa excesso para o jogador",
        "requirements": "Unidade grande com ambas skills ou formas de dar ambas",
        "strategic_value": "Dano massivo ao jogador mesmo com blockers pequenos",
        "limitations": "Múltiplos blockers dividem o dano"
    },
    
    "flying_aegis_finisher": {
        "skills": ["Flying", "Aegis"],
        "strength": 4,
        "mechanics": "Flying evita maioria dos blockers, Aegis protege de primeira remoção",
        "requirements": "Unidade que justifique proteção dupla",
        "strategic_value": "Ameaça resiliente e evasiva",
        "limitations": "Ainda morre para segundo removal ou Killer"
    },
    
    "charge_warcry_tempo": {
        "skills": ["Charge", "Warcry"],
        "strength": 3,
        "mechanics": "Charge ataca imediatamente, triggerando Warcry no mesmo turno jogado",
        "requirements": "Unidades baratas com ambas skills",
        "strategic_value": "Pressão imediata + setup futuro",
        "limitations": "Unidades com Charge tendem a ser pequenas"
    },
    
    "unblockable_infiltrate_guaranteed": {
        "skills": ["Unblockable", "Infiltrate"],
        "strength": 3,
        "mechanics": "Unblockable não pode ser defendido, garantindo trigger de Infiltrate",
        "requirements": "Unidades com Infiltrate poderoso para justificar",
        "strategic_value": "Infiltrate effects garantidos",
        "limitations": "Board wipes ainda pegam unidades Unblockable",
    },
    
    "taunt_deadly_trap": {
        "skills": ["Taunt", "Deadly"],
        "strength": 3,
        "mechanics": "Taunt força bloqueio, Deadly mata qualquer unidade que sofrer dano",
        "requirements": "Formas de dar Taunt para unidades com Deadly",
        "strategic_value": "Força trades desfavoráveis para oponente",
        "limitations": "Se houve mais de um defensor, inimigo pode escolher com qual unidade defender",
    },

    "killer_deadly_trap": {
        "skills": ["Killer", "Deadly"],
        "strength": 5,
        "mechanics": "Killer esolhe qual unidade atacar diretamente, Deadly mata qualquer unidade que sofrer dano",
        "requirements": "Formas de dar Killer para unidades com Deadly",
        "strategic_value": "Força trades desfavoráveis para oponente",
        "limitations": "Ambush pode ser usado para evitar o ataque, mas não impede a remoção da unidade. Vulnerável a silence e transform effects",
    },

        "entomb_sacrifice": {
        "skills": ["Entomb"],
        "strength": 4,
        "mechanics": "Entomb ativa efeito quando carta morre, permitindo sacrificar unidades para ativar efeitos poderosos",
        "requirements": "Formas de sacrificar unidades com entomb",
        "strategic_value": "ativar efeitos poderosos sem custo adicional",
        "limitations": "Vulnerável a remoção em massa ou silence nas peças chave",
    }
}

# =============================================================================
# 🚨 ÂNCORA: MECHANICAL_PACKAGES - Grupos de mecânicas que funcionam juntas
# Contexto: Padrões de mecânicas, não cartas específicas
# Cuidado: Descrever interações, não listar cartas
# Dependências: DeckCrafter identifica esses padrões
# =============================================================================

MECHANICAL_PACKAGES = {
    "aggressive_burn": {
        "core_mechanics": ["direct damage spells", "charge units", "overwhelm"],
        "support_mechanics": ["cost reduction", "spell damage amplification"],
        "synergy_description": "Combina dano direto com pressão de unidades rápidas",
        "win_condition": "Reduzir vida do oponente a zero rapidamente",
        "weaknesses": ["lifesteal", "armor gain", "defensive units"]
    },
    
    "go_wide_tokens": {
        "core_mechanics": ["token generation", "unit buffs", "mass pump effects"],
        "support_mechanics": ["sacrifice synergies", "death triggers"],
        "synergy_description": "Cria muitas unidades pequenas e as transforma em ameaças",
        "win_condition": "Overwhelm com quantidade de ameaças",
        "weaknesses": ["board wipes", "harsh rule effects"]
    },
    
    "weapons_matter": {
        "core_mechanics": ["weapon generation", "weapon buffs", "warcry"],
        "support_mechanics": ["unit protection", "weapon recursion"],
        "synergy_description": "Foca em buffar e reutilizar weapons para value",
        "win_condition": "Criar weapons massivas ou gerar vantagem incremental",
        "weaknesses": ["weapon removal", "unit removal"]
    },
    
    "void_recursion": {
        "core_mechanics": ["self-mill", "void interaction", "reanimation"],
        "support_mechanics": ["entomb effects", "death triggers", "sacrifice"],
        "synergy_description": "Usa void como segunda mão, reciclando recursos",
        "win_condition": "Vantagem de recursos através de recursão",
        "weaknesses": ["void hate", "silence effects", "transform removal"]
    },
    
    "spell_combo": {
        "core_mechanics": ["spell cost reduction", "spell copying", "card draw"],
        "support_mechanics": ["spell damage", "fast spells"],
        "synergy_description": "Encadeia múltiplos spells para efeito explosivo",
        "win_condition": "Combo de spells para dano ou vantagem massiva",
        "weaknesses": ["negate effects", "face aegis", "aggressive pressure"]
    },
    
    "ramp_fatties": {
        "core_mechanics": ["power acceleration", "cost reduction", "big units"],
        "support_mechanics": ["card selection", "protection spells"],
        "synergy_description": "Acelera para jogar ameaças grandes antes do oponente",
        "win_condition": "Dominar com unidades que oponente não consegue lidar",
        "weaknesses": ["aggressive starts", "hard removal", "transform effects"]
    }
}

# =============================================================================
# 🚨 ÂNCORA: ANTI_SYNERGIES - Mecânicas que conflitam
# Contexto: Combinações que se atrapalham mutuamente
# Cuidado: Explicar POR QUE não funcionam juntas
# Dependências: Validator avisa sobre conflitos
# =============================================================================

ANTI_SYNERGIES = {
    "infiltrate_taunt": {
        "mechanics": ["Infiltrate", "Taunt"],
        "conflict": "Taunt força bloqueio, impedindo que unidade com Infiltrate conecte com jogador inimigo",
        "severity": "high"
    },
    
    "warcry_spell_heavy": {
        "mechanics": ["Warcry", "Spell-based strategy"],
        "conflict": "Warcry só buffa units/weapons. Em deck sem muitos desses, skill é desperdiçada",
        "severity": "high"
    },
    
    "reckless_control": {
        "mechanics": ["Reckless", "Control strategy"],
        "conflict": "Reckless força ataques, incompatível com estratégia defensiva de control",
        "severity": "medium"
    },
    
    "echo_market": {
        "mechanics": ["Echo", "Market cards"],
        "conflict": "Cartas de Market são únicas (1 cópia), Echo não tem valor",
        "severity": "high"
    },
    
    "destiny_expensive": {
        "mechanics": ["Destiny", "High cost cards"],
        "conflict": "Destiny joga grátis mas cartas caras são ruins early game quando Destiny triggera",
        "severity": "medium"
    },
    
    "aegis_sacrifice": {
        "mechanics": ["Aegis", "Self-sacrifice strategies"],
        "conflict": "Aegis protege unidade que você quer sacrificar, atrapalhando o plano",
        "severity": "low"
    }
}

# =============================================================================
# 🚨 ÂNCORA: TEMPO_CONSIDERATIONS - Como velocidade afeta sinergias
# Contexto: Algumas sinergias precisam de tempo, outras precisam ser rápidas
# Cuidado: Considerar curva de mana e velocidade do meta
# Dependências: StrategyScout usa para avaliar viabilidade
# =============================================================================

TEMPO_CONSIDERATIONS = {
    "fast_synergies": {
        "description": "Sinergias que funcionam melhor em decks rápidos",
        "examples": [
            "Charge + Warcry: Valor imediato",
            "Burn + Overwhelm: Pressão rápida",
            "Echo + Cheap units: Flood the board"
        ],
        "mana_curve": "Peak at 1-3 cost",
        "critical_turn": "Turns 1-5"
    },
    
    "slow_synergies": {
        "description": "Sinergias que precisam setup ou tempo",
        "examples": [
            "Bolster engines: Precisa peças em jogo",
            "Void recursion: Precisa encher void primeiro",
            "Weapon scaling: Valor incremental"
        ],
        "mana_curve": "Balanced, with late game",
        "critical_turn": "Turns 5+"
    },
    
    "flexible_synergies": {
        "description": "Funcionam em qualquer velocidade",
        "examples": [
            "Flying + Aegis: Sempre bom",
            "Deadly + Quickdraw: Sempre eficiente",
            "Lifesteal: Útil early ou late"
        ],
        "mana_curve": "Adaptable",
        "critical_turn": "All game"
    }
}

# =============================================================================
# 🚨 ÂNCORA: SYNERGY_CATEGORIES - Tipos de sinergia para busca
# Contexto: Agrupa sinergias por tipo de efeito
# Cuidado: Uma sinergia pode estar em múltiplas categorias
# Dependências: RAG usa para busca semântica
# =============================================================================

SYNERGY_CATEGORIES = {
    "damage_amplification": [
        "overwhelm_double_damage_burst",
        "berserk_lifesteal_sustain",
        "charge_warcry_tempo"
    ],
    
    "defensive_synergies": [
        "deadly_quickdraw_combo",
        "flying_aegis_finisher",
        "endurance_killer_control",
        "taunt_deadly_trap"
    ],
    
    "value_generation": [
        "echo_destiny_value",
        "warcry_weapon_scaling",
        "revenge_warcry_recursion",
        "lifesteal_bolster_engine"
    ],
    
    "combo_enablers": [
        "stealth_infiltrate_guaranteed",
        "echo_destiny_value",
        "spell_combo"
    ],
    
    "resource_advantage": [
        "void_recursion",
        "echo_destiny_value",
        "revenge_warcry_recursion"
    ],
    
    "tempo_positive": [
        "charge_warcry_tempo",
        "echo_destiny_value",
        "aggressive_burn"
    ]
}

# =============================================================================
# 🚨 ÂNCORA: HELPER_FUNCTIONS - Funções para análise de sinergias
# Contexto: Facilita avaliação de compatibilidade mecânica
# Cuidado: Usado por outros módulos, manter assinaturas
# Dependências: DeckCrafter, Validator
# =============================================================================

def get_synergies_for_skills(skills: List[str]) -> Dict[str, Any]:
    """Retorna todas sinergias relevantes para lista de skills"""
    relevant_synergies = {}
    
    for syn_name, syn_data in DETAILED_SYNERGIES.items():
        # Verifica se alguma skill está na sinergia
        if any(skill in syn_data["skills"] for skill in skills):
            relevant_synergies[syn_name] = syn_data
            
    return relevant_synergies

def check_anti_synergies(mechanics: List[str]) -> List[Dict[str, Any]]:
    """Verifica se há mecânicas conflitantes"""
    conflicts = []
    
    for anti_name, anti_data in ANTI_SYNERGIES.items():
        conflicting = [m for m in mechanics if m in anti_data["mechanics"]]
        if len(conflicting) >= 2:
            conflicts.append({
                "conflict": anti_name,
                "mechanics": conflicting,
                "reason": anti_data["conflict"],
                "severity": anti_data["severity"]
            })
            
    return conflicts

def get_package_for_strategy(strategy: str) -> Dict[str, Any]:
    """Retorna mechanical package mais adequado para estratégia"""
    strategy_lower = strategy.lower()
    
    # Mapeamento simples de keywords para packages
    keyword_mapping = {
        "aggro": "aggressive_burn",
        "burn": "aggressive_burn", 
        "tokens": "go_wide_tokens",
        "weapons": "weapons_matter",
        "void": "void_recursion",
        "graveyard": "void_recursion",
        "spell": "spell_combo",
        "combo": "spell_combo",
        "ramp": "ramp_fatties",
        "control": "ramp_fatties"  # Control often uses big finishers
    }
    
    for keyword, package_name in keyword_mapping.items():
        if keyword in strategy_lower:
            return MECHANICAL_PACKAGES.get(package_name, {})
            
    return {}

def evaluate_synergy_strength(synergies: List[str]) -> float:
    """Calcula força total de sinergias em uma lista"""
    total_strength = 0
    synergy_count = 0
    
    for syn in DETAILED_SYNERGIES.values():
        if all(skill in synergies for skill in syn["skills"]):
            total_strength += syn["strength"]
            synergy_count += 1
            
    return total_strength / max(synergy_count, 1)

def get_compatible_mechanics(base_mechanic: str) -> List[str]:
    """Retorna mecânicas que funcionam bem com a base"""
    compatible = []
    
    # Busca em sinergias detalhadas
    for syn_data in DETAILED_SYNERGIES.values():
        if base_mechanic in syn_data["skills"]:
            for skill in syn_data["skills"]:
                if skill != base_mechanic:
                    compatible.append(skill)
                    
    # Busca em packages
    for package in MECHANICAL_PACKAGES.values():
        if base_mechanic in package["core_mechanics"]:
            compatible.extend(package["support_mechanics"])
            
    return list(set(compatible))  # Remove duplicatas