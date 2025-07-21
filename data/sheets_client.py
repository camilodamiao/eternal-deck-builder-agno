"""
Cliente para conexão com Google Sheets
Lê e cacheia cartas do Eternal Card Game
"""
import gspread
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging
from datetime import datetime

from data.models import Card
from config import GOOGLE_SHEETS_ID, GOOGLE_SHEETS_CREDENTIALS_PATH, CONFIG_STATUS

# Configurar logging
logger = logging.getLogger(__name__)

# =============================================================================
# 🚨 ÂNCORA: SHEETS_AUTH - Autenticação via Service Account
# Contexto: Usa arquivo JSON de credenciais do Google Cloud Console
# Cuidado: Arquivo deve ter permissão de leitura na planilha
# Dependências: config.py define o caminho do arquivo
# =============================================================================

class GoogleSheetsClient:
    """
    Cliente para ler cartas do Google Sheets
    Implementa cache completo em memória para performance
    """
    
    def __init__(self):
        """Inicializa cliente e prepara cache"""
        self._gc = None  # Cliente gspread
        self._sheet = None  # Worksheet ativa
        
        # 🚨 ÂNCORA: CACHE_STRATEGY - Cache completo por simplicidade
        # Contexto: 8000 cartas = ~10MB, aceitável para app desktop
        # Cuidado: Se escalar para 50k+ cartas, implementar cache parcial
        # Dependências: RAG precisará acesso rápido a todas as cartas
        self._cards_cache: List[Card] = []
        self._cache_loaded: bool = False
        self._load_time: Optional[datetime] = None
        
    def connect(self) -> bool:
        """
        Conecta ao Google Sheets
        Retorna True se sucesso, False se falhar
        """
        if not CONFIG_STATUS['sheets_creds']:
            logger.error(f"Credenciais não encontradas em: {GOOGLE_SHEETS_CREDENTIALS_PATH}")
            return False
            
        try:
            # Autenticar com service account
            self._gc = gspread.service_account(filename=GOOGLE_SHEETS_CREDENTIALS_PATH)
            
            # Abrir planilha por ID
            spreadsheet = self._gc.open_by_key(GOOGLE_SHEETS_ID)
            
            # Pegar primeira aba (geralmente onde estão os dados)
            self._sheet = spreadsheet.sheet1
            
            logger.info(f"✅ Conectado ao Google Sheets: {spreadsheet.title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {str(e)}")
            return False
    
    # =============================================================================
    # 🚨 ÂNCORA: FIELD_MAPPING - Mapeamento colunas planilha → modelo Card
    # Contexto: Nomes das colunas devem corresponder exatamente
    # Cuidado: CardText e DeckBuildable são nomes específicos da planilha
    # Dependências: models.py espera estes campos no formato correto
    # =============================================================================
    
    def _parse_card_row(self, row: Dict[str, Any]) -> Optional[Card]:
        """
        Converte uma linha da planilha em objeto Card
        Retorna None se a carta não for deck buildable
        """
        # Filtrar cartas não utilizáveis em decks
        if row.get('DeckBuildable', '').upper() != 'TRUE':
            return None
            
        # Campos obrigatórios - validar presença
        if not row.get('Name'):
            return None
            
        try:
            # 🚨 ÂNCORA: UNIT_TYPES_PARSING - Parse dos 3 campos de tipo
            # Contexto: UnitType/0, UnitType/1, UnitType/2 podem estar vazios
            # Cuidado: Remover espaços e valores vazios
            # Dependências: models.py espera List[str]
            unit_types = []
            for i in range(3):
                unit_type_field = f'UnitType/{i}'
                if unit_type_field in row and row[unit_type_field]:
                    type_value = str(row[unit_type_field]).strip()
                    if type_value and type_value.lower() != 'nan':
                        unit_types.append(type_value)
            
            # Mapear campos com tratamento de vazios
            card_data = {
                # Obrigatórios
                'name': row['Name'].strip(),
                'cost': int(row.get('Cost', 0)),
                'type': row.get('Type', 'Unknown').strip(),
                'card_text': row.get('CardText', '').strip(),
                'rarity': row.get('Rarity', 'Common').strip(),
                'deck_buildable': True,  # Já filtrado acima
                
                # Influência - manter formato original
                'influence': row.get('Influence', '').strip(),
                
                # IDs para exportação
                'set_number': str(row.get('SetNumber', '')).strip(),
                'eternal_id': str(row.get('EternalID', '')).strip(),
                
                # 🚨 ÂNCORA: SET_NAME_PARSING - Nome do set
                # Contexto: Importante para filtros de formato (Expedition)
                # Cuidado: Pode estar vazio em cartas antigas
                # Dependências: Usado em filtros futuros
                'set_name': row.get('SetName', '').strip() or None,
                
                # Novos campos
                'unit_types': unit_types,  # Lista processada acima
                
                # Opcionais - converter vazios em None
                'attack': int(row['Attack']) if row.get('Attack') and str(row['Attack']).isdigit() else None,
                'health': int(row['Health']) if row.get('Health') and str(row['Health']).isdigit() else None,
                
                # URL da imagem se disponível
                'image_url': row.get('ImageUrl', '').strip() or None,
            }
            
            return Card(**card_data)
            
        except Exception as e:
            logger.warning(f"⚠️  Erro ao parsear carta {row.get('Name', 'Unknown')}: {str(e)}")
            return None
    
    def _load_all_cards(self) -> bool:
        """
        Carrega todas as cartas do Sheets para o cache
        Retorna True se sucesso
        """
        if not self._sheet:
            if not self.connect():
                return False
                
        try:
            logger.info("📊 Carregando cartas do Google Sheets...")
            
            # Pegar todos os registros como lista de dicionários
            # get_all_records() já usa a primeira linha como headers
            all_records = self._sheet.get_all_records()  # type: ignore
            
            logger.info(f"📄 Total de linhas na planilha: {len(all_records)}")
            
            # Parsear cada linha
            cards_loaded = 0
            for row in all_records:
                card = self._parse_card_row(row)
                if card:
                    self._cards_cache.append(card)
                    cards_loaded += 1
                    
            self._cache_loaded = True
            self._load_time = datetime.now()
            
            logger.info(f"✅ {cards_loaded} cartas carregadas no cache")
            logger.info(f"📊 Memória aproximada: {cards_loaded * 350 / 1024:.1f} KB")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar cartas: {str(e)}")
            return False
    
    def get_all_cards(self) -> List[Card]:
        """
        Retorna todas as cartas do cache
        Carrega do Sheets se ainda não carregado
        """
        if not self._cache_loaded:
            self._load_all_cards()
            
        return self._cards_cache.copy()  # Retorna cópia para evitar mutação
    
    def search_cards(
        self,
        name: Optional[str] = None,
        card_type: Optional[str] = None,
        cost_max: Optional[int] = None,
        factions: Optional[List[str]] = None,
        rarity: Optional[str] = None,
        text_contains: Optional[str] = None
    ) -> List[Card]:
        """
        Busca cartas com filtros
        Usa cache em memória para performance
        """
        if not self._cache_loaded:
            self._load_all_cards()
            
        results = self._cards_cache
        
        # Aplicar filtros sequencialmente
        if name:
            name_lower = name.lower()
            results = [c for c in results if name_lower in c.name.lower()]
            
        if card_type:
            type_lower = card_type.lower()
            results = [c for c in results if type_lower == c.type.lower()]
            
        if cost_max is not None:
            results = [c for c in results if c.cost <= cost_max]
            
        if factions:
            # Carta deve ter pelo menos uma das facções solicitadas
            faction_symbols = {
                'Fire': '{F}',
                'Time': '{T}',
                'Justice': '{J}',
                'Primal': '{P}',
                'Shadow': '{S}'
            }
            
            symbols_to_check = [faction_symbols.get(f, f) for f in factions]
            results = [
                c for c in results 
                if any(symbol in c.influence for symbol in symbols_to_check)
            ]
            
        if rarity:
            rarity_lower = rarity.lower()
            results = [c for c in results if rarity_lower == c.rarity.lower()]
            
        if text_contains:
            text_lower = text_contains.lower()
            results = [c for c in results if text_lower in c.card_text.lower()]
            
        return results
    
    def get_card_by_name(self, name: str) -> Optional[Card]:
        """
        Busca uma carta específica por nome exato
        Retorna None se não encontrar
        """
        if not self._cache_loaded:
            self._load_all_cards()
            
        name_lower = name.lower()
        for card in self._cards_cache:
            if card.name.lower() == name_lower:
                return card
                
        return None
    
    def get_market_access_cards(self) -> List[Card]:
        """
        Retorna todas as cartas que podem acessar o mercado
        Usa a propriedade can_access_market do modelo
        """
        if not self._cache_loaded:
            self._load_all_cards()
            
        return [c for c in self._cards_cache if c.can_access_market]
    
    def get_cards_by_unit_type(self, unit_type: str) -> List[Card]:
        """
        Retorna todas as cartas de um tipo tribal específico
        Ex: get_cards_by_unit_type("Valkyrie")
        """
        if not self._cache_loaded:
            self._load_all_cards()
        
        unit_type_lower = unit_type.lower()
        return [
            card for card in self._cards_cache 
            if any(ut.lower() == unit_type_lower for ut in card.unit_types)
        ]

    def get_cards_by_set(self, set_name: str) -> List[Card]:
        """
        Retorna todas as cartas de um set específico
        Ex: get_cards_by_set("Dark Frontier")
        """
        if not self._cache_loaded:
            self._load_all_cards()
        
        set_name_lower = set_name.lower()
        return [
            card for card in self._cards_cache 
            if card.set_name and card.set_name.lower() == set_name_lower
        ]
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o cache"""
        return {
            'loaded': self._cache_loaded,
            'card_count': len(self._cards_cache),
            'load_time': self._load_time.isoformat() if self._load_time else None,
            'memory_kb': len(self._cards_cache) * 350 / 1024 if self._cache_loaded else 0
        }


# =============================================================================
# Singleton global para reutilizar conexão
# =============================================================================

_client_instance: Optional[GoogleSheetsClient] = None

def get_sheets_client() -> GoogleSheetsClient:
    """
    Retorna instância singleton do cliente
    Garante que só existe uma conexão/cache
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = GoogleSheetsClient()
    return _client_instance


# =============================================================================
# Teste rápido se executado diretamente
# =============================================================================

if __name__ == "__main__":
    # Configurar logging para debug
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testando GoogleSheetsClient...")
    
    client = get_sheets_client()
    
    # Testar conexão
    if client.connect():
        # Carregar cartas
        cards = client.get_all_cards()
        print(f"\n✅ Total de cartas: {len(cards)}")
        
        # Mostrar algumas cartas de exemplo
        if cards:
            print("\n📋 Primeiras 3 cartas:")
            for card in cards[:3]:
                print(f"  - {card.name} | {card.cost}{card.influence} | {card.type}")
                
        # Testar busca
        fire_cards = client.search_cards(factions=['Fire'], cost_max=3)
        print(f"\n🔥 Cartas Fire com custo ≤ 3: {len(fire_cards)}")
        
        # Testar merchants
        merchants = client.get_market_access_cards()
        print(f"\n🏪 Cartas que acessam mercado: {len(merchants)}")
        if merchants:
            print(f"   Exemplo: {merchants[0].name}")
            
        # Info do cache
        cache_info = client.get_cache_info()
        print(f"\n💾 Cache: {cache_info['memory_kb']:.1f} KB")

        # Testar tribal
        valkyries = client.get_cards_by_unit_type("Valkyrie")
        print(f"\n⚔️ Valkyries encontradas: {len(valkyries)}")
        if valkyries:
            print(f"   Exemplo: {valkyries[0].name} - {valkyries[0].unit_types}")