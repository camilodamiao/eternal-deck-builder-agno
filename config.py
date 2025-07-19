"""
Configuração central do Eternal Deck Builder Agno
Todas as configurações, regras e constantes do projeto
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# =============================================================================
# 🚨 ÂNCORA: ENV_VARS - Variáveis de ambiente e credenciais
# Contexto: Todas as credenciais vêm do .env para segurança
# Cuidado: Nunca fazer hardcode de API keys aqui
# Dependências: .env file, Google Sheets API, OpenAI API
# =============================================================================

# API Keys e Credenciais
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
GOOGLE_SHEETS_ID: Optional[str] = os.getenv("GOOGLE_SHEETS_ID", "1n9r5BUClyw1aj0S7Vbtam_5xgaQtRM0xYs4KIkJdTVc")
GOOGLE_SHEETS_CREDENTIALS_PATH: Optional[str] = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "./credentials.json")

# =============================================================================
# 🚨 ÂNCORA: VALIDATION - Validação suave de configurações
# Contexto: Avisa sobre configs faltando mas não trava o programa
# Cuidado: Permite testes parciais durante desenvolvimento
# Dependências: Usado por todos os módulos que precisam das APIs
# =============================================================================

def validate_config() -> Dict[str, bool]:
    """Valida configurações e retorna status"""
    status = {
        "openai": bool(OPENAI_API_KEY),
        "sheets_id": bool(GOOGLE_SHEETS_ID),
        "sheets_creds": os.path.exists(GOOGLE_SHEETS_CREDENTIALS_PATH) if GOOGLE_SHEETS_CREDENTIALS_PATH else False
    }
    
    # Avisos amigáveis
    if not status["openai"]:
        print("⚠️  AVISO: OPENAI_API_KEY não encontrada no .env")
        print("   Para usar a IA, adicione: OPENAI_API_KEY=sk-...")
        
    if not status["sheets_creds"]:
        print("⚠️  AVISO: Arquivo de credenciais do Google não encontrado")
        print(f"   Esperado em: {GOOGLE_SHEETS_CREDENTIALS_PATH}")
        
    return status

# Executar validação ao importar
CONFIG_STATUS = validate_config()

# =============================================================================
# 🚨 ÂNCORA: DECK_RULES - Regras fundamentais do Eternal Card Game
# Contexto: Usadas pela IA para gerar decks válidos e pelo validador
# Cuidado: Estas são regras oficiais do jogo, não alterar sem certeza
# Dependências: DeckBuilder agent, Validator, UI constraints
# =============================================================================

DECK_RULES: Dict[str, Any] = {
    "min_cards": 75,
    "max_cards": 150,
    "recommended_cards": 75,  # Para máxima consistência
    "max_copies": 4,  # Por carta (exceto Sigils que são ilimitados)
    "min_power_ratio": 1/3,  # Mínimo 33% do deck deve ser power
    "min_power_cards": 25,  # Para deck de 75 cartas
    
    # Regras de Mercado (Market/Black Market)
    "market": {
        "size": 5,  # Exatamente 5 cartas
        "unique_only": True,  # Não pode repetir cartas
        "access_required": True,  # Precisa de Merchants/Smugglers
        "description": """
        O Mercado (Market) é um conjunto de 5 cartas únicas fora do deck principal.
        Para acessar: precisa de cartas que mencionam 'your market' no texto.
        Estratégia: inclua respostas situacionais e cartas tech no mercado.
        """,
        
        # 🚨 IMPORTANTE: Método de detecção de acesso ao mercado
        "detection_method": """
        1. PRIMEIRO: Buscar cartas com 'your market' no cardtext
        2. DEPOIS: Avaliar o texto completo para confirmar que acessa mercado
        3. CUIDADO: Algumas cartas podem mencionar 'market' sem dar acesso
        4. EXCEÇÕES: Pode haver cartas que acessam mercado sem ter 'your market'
        """,
        
        # Padrões de texto que indicam acesso ao mercado
        "access_patterns": [
            "your market",      # Padrão mais comum (95% dos casos)
            "from your market", # Variação comum
            "in your market",   # Outra variação
        ],
        
        # Exemplos conhecidos (para referência da IA)
        "example_merchants": [
            "Merchants geralmente têm: 'play a sigil from your market'",
            "Smugglers podem ter: 'swap a card from your market'",
            "Etchings: 'play the top card of your market'",
            "Bargain: habilidade que pode acessar mercado"
        ]
    }
}

# =============================================================================
# 🚨 ÂNCORA: FACTIONS - Sistema de facções e influência
# Contexto: Define as 5 facções e seus símbolos para parsing
# Cuidado: Símbolos devem corresponder exatamente ao formato da planilha
# Dependências: Card parser, Deck builder, UI filters
# =============================================================================

FACTIONS: Dict[str, Dict[str, str]] = {
    "Fire": {
        "symbol": "{F}",
        "name": "Fire",
        "style": "Aggro, burn, weapons",
        "color": "#FF4444"
    },
    "Time": {
        "symbol": "{T}", 
        "name": "Time",
        "style": "Ramp, big units, value",
        "color": "#FFD700"
    },
    "Justice": {
        "symbol": "{J}",
        "name": "Justice",
        "style": "Control, armor, order",
        "color": "#4169E1"
    },
    "Primal": {
        "symbol": "{P}",
        "name": "Primal",
        "style": "Spells, flying, card draw",
        "color": "#00CED1"
    },
    "Shadow": {
        "symbol": "{S}",
        "name": "Shadow",
        "style": "Removal, void, sacrifice",
        "color": "#8B008B"
    }
}

# Lista simplificada para UI
FACTION_NAMES: list = list(FACTIONS.keys())
FACTION_SYMBOLS: Dict[str, str] = {k: v["symbol"] for k, v in FACTIONS.items()}

# =============================================================================
# 🚨 ÂNCORA: MODEL_CONFIGS - Configurações dos modelos de IA
# Contexto: Define capacidades e limitações de cada modelo
# Cuidado: o3/o3-mini não suportam temperature/stop parameters
# Dependências: Agent creation, LLM initialization, cost calculation
# =============================================================================

MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    "o3": {
        "name": "O3 (Raciocínio Avançado)",
        "model_id": "o3",
        "supports_temperature": False,  # Importante: o3 não aceita
        "supports_stop": False,         # Importante: o3 não aceita
        "supports_tools": True,
        "max_tokens": 4096,
        "cost_per_1k_input": 0.015,
        "cost_per_1k_output": 0.060,
        "description": "Melhor para raciocínio complexo e estratégias elaboradas"
    },
    "o3-mini": {
        "name": "O3 Mini (Raciocínio Rápido)",
        "model_id": "o3-mini", 
        "supports_temperature": False,
        "supports_stop": False,
        "supports_tools": True,
        "max_tokens": 4096,
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.012,
        "description": "Raciocínio rápido, bom custo-benefício"
    },
    "gpt-4.1": {
        "name": "GPT-4.1 (Versão Estável)",
        "model_id": "gpt-4-0125-preview",  # ID real da API
        "supports_temperature": True,
        "supports_stop": True,
        "supports_tools": True,
        "max_tokens": 4096,
        "cost_per_1k_input": 0.010,
        "cost_per_1k_output": 0.030,
        "description": "Modelo equilibrado e confiável"
    },
    "gpt-4.1-mini": {
        "name": "GPT-4.1 Mini (Econômico)",
        "model_id": "gpt-4-1106-preview",  # ID real da API
        "supports_temperature": True,
        "supports_stop": True,
        "supports_tools": True,
        "max_tokens": 4096,
        "cost_per_1k_input": 0.001,
        "cost_per_1k_output": 0.002,
        "description": "Rápido e econômico para tarefas simples"
    }
}

# Lista simplificada para UI
MODEL_OPTIONS: list = list(MODEL_CONFIGS.keys())

# =============================================================================
# 🚨 ÂNCORA: GAME_CONSTANTS - Outras constantes do jogo
# Contexto: Valores que raramente mudam mas são importantes
# Cuidado: Verificar com as regras oficiais antes de alterar
# Dependências: Deck validation, UI limits
# =============================================================================

# Tipos de carta válidos
CARD_TYPES: list = ["Unit", "Spell", "Power", "Weapon", "Relic", "Curse"]

# Raridades
RARITIES: list = ["Common", "Uncommon", "Rare", "Legendary"]

# Formatos de jogo suportados
GAME_FORMATS: Dict[str, str] = {
    "Throne": "Todas as cartas legais",
    "Expedition": "Apenas cartas dos sets mais recentes"
}

# =============================================================================
# 🚨 ÂNCORA: UI_CONSTANTS - Configurações da interface
# Contexto: Valores padrão para a UI Streamlit
# Cuidado: Afetam a experiência do usuário
# Dependências: Streamlit app.py
# =============================================================================

UI_CONFIG: Dict[str, Any] = {
    "page_title": "Eternal Deck Builder - Agno",
    "page_icon": "🎴",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    
    # Limites da UI
    "max_strategy_length": 500,
    "max_required_cards": 10,
    "max_banned_cards": 20,
    
    # Mensagens padrão
    "strategy_placeholder": "Ex: Aggressive Fire deck with burn damage and fast units",
    "no_strategy_error": "Please describe your deck strategy!",
    "generation_success": "✅ Deck generated successfully!",
    "validation_success": "✅ Deck is valid and ready to play!"
}

# =============================================================================
# Função helper para debug
# =============================================================================

def print_config_status():
    """Imprime status da configuração (útil para debug)"""
    print("\n=== Eternal Deck Builder Config Status ===")
    print(f"✓ OpenAI API: {'Configured' if CONFIG_STATUS['openai'] else 'Missing'}")
    print(f"✓ Google Sheets ID: {'Configured' if CONFIG_STATUS['sheets_id'] else 'Missing'}")
    print(f"✓ Google Credentials: {'Found' if CONFIG_STATUS['sheets_creds'] else 'Missing'}")
    print(f"✓ Available Models: {len(MODEL_CONFIGS)}")
    print(f"✓ Factions: {len(FACTIONS)}")
    print("==========================================\n")

# Executar ao importar com flag de debug
if os.getenv("DEBUG_CONFIG", "").lower() == "true":
    print_config_status()
    