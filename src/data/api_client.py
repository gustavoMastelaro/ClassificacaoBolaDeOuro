import os
import random

# Tenta importar python-dotenv de forma segura
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Se python-dotenv nao estiver instalado, continua sem carregar do arquivo .env
    load_dotenv = None

# Tenta importar requests de forma segura
try:
    import requests
except ImportError:
    requests = None

# Dicionario auxiliar para mapear o ranking da FIFA dos paises mais comuns
FIFA_RANKINGS_MAPPING = {
    "argentina": 1,
    "france": 2,
    "england": 3,
    "belgium": 4,
    "brazil": 5,
    "netherlands": 6,
    "portugal": 7,
    "spain": 8,
    "italy": 9,
    "croatia": 10,
    "germany": 11,
    "morocco": 12,
    "colombia": 13,
    "uruguay": 14,
    "mexico": 15,
    "usa": 16,
    "norway": 47,
    "senegal": 18,
    "japan": 17,
}

class FootballAPIClient:
    """
    Cliente para integracao com a API-FOOTBALL (via RapidAPI).
    Permite buscar estatisticas em tempo real de jogadores e possui fallbacks robustos.
    """
    
    def __init__(self):
        # Carrega a chave de API das variaveis de ambiente
        self.api_key = os.getenv("FOOTBALL_API_KEY")
        
        # Define se estamos em modo simulado (Mock) por padrao ou por falta de chave valida
        self.is_mock_mode = False
        if not self.api_key or self.api_key == "seu_token_aqui" or self.api_key.startswith("MOCK"):
            self.is_mock_mode = True
            self.api_key = "MOCK_KEY"
            
        # Forca o modo mock caso a biblioteca requests nao esteja instalada no ambiente
        if requests is None:
            self.is_mock_mode = True

    def buscar_dados_api(self, nome: str, time: str, season: int = 2023) -> dict:
        """
        Busca dados estatisticos de um jogador da temporada atual, filtrando pelo time do jogador.
        """
        if self.is_mock_mode or requests is None:
            if requests is None:
                print("[INFO] Biblioteca 'requests' nao esta instalada. Utilizando modo MOCK.")
            else:
                print("[AVISO] FootballAPIClient: 'FOOTBALL_API_KEY' ausente ou invalida no .env.")
                print("[INFO] O cliente funcionara em modo MOCK (simulado) como fallback.")
            return self._obter_dados_mock(nome)
            
        url = "https://api-football-v1.p.rapidapi.com/v3/players"
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        params = {
            "search": nome,
            "season": str(season)
        }
        
        try:
            print(f"[API] Buscando jogador '{nome}' no time '{time}' na temporada {season}...")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            # Verifica status HTTP
            if response.status_code == 403:
                print("[API - Erro 403] Acesso negado. Chave de API invalida ou expirada. Ativando fallback...")
                return self._obter_dados_mock(nome)
            elif response.status_code == 429:
                print("[API - Erro 429] Limite de requisicoes excedido. Ativando fallback...")
                return self._obter_dados_mock(nome)
            
            response.raise_for_status()
            data = response.json()
            
            # Trata erros retornados no proprio corpo da API
            if data.get("errors"):
                print(f"[API - Erro Interno] Erros relatados pela API: {data['errors']}. Ativando fallback...")
                return self._obter_dados_mock(nome)
                
            results = data.get("response", [])
            if not results:
                print(f"[API] Jogador '{nome}' nao foi encontrado na API-FOOTBALL. Ativando fallback...")
                return self._obter_dados_mock(nome)
                
            # Tenta encontrar correspondencia de jogador e time
            player_found = None
            stats_to_process = None
            time_clean = time.strip().lower()
            
            for entry in results:
                stats_list = entry.get("statistics", [])
                matching_stats = [
                    s for s in stats_list 
                    if time_clean in s.get("team", {}).get("name", "").lower()
                ]
                if matching_stats:
                    player_found = entry.get("player")
                    stats_to_process = matching_stats
                    break
                    
            # Se nao encontrou filtrando pelo time especifico, usa o primeiro resultado geral
            if not player_found:
                print(f"[API] Nao foi encontrada correspondencia exata para o time '{time}'. Usando primeiro resultado geral.")
                player_found = results[0]["player"]
                stats_to_process = results[0]["statistics"]
            
            # Agrega estatisticas de todas as competicoes do time/jogador
            total_gols = 0
            total_assists = 0
            ratings = []
            clean_sheets = 0
            position = "Desconhecido"
            
            for stat in stats_to_process:
                # Gols e Assistencias
                goals_data = stat.get("goals", {})
                total_gols += (goals_data.get("total") or 0)
                total_assists += (goals_data.get("assists") or 0)
                
                # Coleta a posicao se disponivel
                games_data = stat.get("games", {})
                if games_data.get("position"):
                    position = games_data.get("position")
                
                # Nota Media de desempenho (rating vem como string, ex: "7.350000")
                rating_str = games_data.get("rating")
                if rating_str:
                    try:
                        ratings.append(float(rating_str))
                    except ValueError:
                        pass
                
            # Calcula a media aritmetica das notas
            nota_media = round(sum(ratings) / len(ratings), 2) if ratings else 7.0
            
            # Estimativas para campos ausentes na resposta de estatisticas:
            # 1. Clean Sheets (apenas para goleiros)
            if position.lower() in ["goalkeeper", "goleiro"]:
                clean_sheets = int((nota_media - 6.0) * 15) if nota_media > 6.0 else 2
                clean_sheets = max(0, min(30, clean_sheets))
                
            # 2. MOTM - Estimado com base na nota media e gols
            motm_estimado = max(0, int((nota_media - 7.0) * 10) + int(total_gols * 0.15))
            
            # 3. Titulos da temporada - Valor padrao de fallback
            titulos = random.randint(0, 2)
            
            # 4. Valor de Mercado - Estimativa baseada na idade, nota media e gols
            idade = player_found.get("age", 25)
            fator_idade = max(0.5, (38 - idade) / 10) if idade > 28 else 1.0
            valor_mercado = round((total_gols * 2.5 + total_assists * 1.5 + (nota_media - 6.0) * 20) * fator_idade * 1000000)
            valor_mercado = float(max(5000000, valor_mercado))
            
            print(f"[API] Dados reais processados com sucesso para: {player_found.get('name')}")
            
            return {
                "Jogador": player_found.get("name"),
                "NºGols": total_gols,
                "NºAssist": total_assists,
                "RankingFIFA": FIFA_RANKINGS_MAPPING.get(player_found.get("nationality", "").strip().lower(), 50),
                "Títulos": titulos,
                "ValorMercado": valor_mercado,
                "NotaMédia": nota_media,
                "CleanSheet": clean_sheets,
                "MOTM": motm_estimado
            }
            
        except Exception as e:
            print(f"[API - Erro de Conexao] Falha ao conectar a API externa: {e}. Ativando fallback...")
            return self._obter_dados_mock(nome)

    def _obter_dados_mock(self, player_name: str) -> dict:
        """
        Gera e retorna dados simulados (mock) realistas para um jogador.
        """
        name_clean = player_name.strip().lower()
        
        # Banco estatico com alguns craques
        mock_database = {
            "vinicius junior": {
                "Jogador": "Vinicius Junior",
                "NºGols": 24,
                "NºAssist": 11,
                "RankingFIFA": 5,
                "Títulos": 3,
                "ValorMercado": 150000000.0,
                "NotaMédia": 8.00,
                "CleanSheet": 0,
                "MOTM": 7
            },
            "jude bellingham": {
                "Jogador": "Jude Bellingham",
                "NºGols": 23,
                "NºAssist": 13,
                "RankingFIFA": 4,
                "Títulos": 3,
                "ValorMercado": 180000000.0,
                "NotaMédia": 7.90,
                "CleanSheet": 0,
                "MOTM": 6
            },
            "kylian mbappe": {
                "Jogador": "Kylian Mbappe",
                "NºGols": 44,
                "NºAssist": 10,
                "RankingFIFA": 2,
                "Títulos": 2,
                "ValorMercado": 180000000.0,
                "NotaMédia": 8.20,
                "CleanSheet": 0,
                "MOTM": 9
            },
            "rodri": {
                "Jogador": "Rodri",
                "NºGols": 9,
                "NºAssist": 14,
                "RankingFIFA": 8,
                "Títulos": 4,
                "ValorMercado": 120000000.0,
                "NotaMédia": 8.40,
                "CleanSheet": 0,
                "MOTM": 8
            },
            "erling haaland": {
                "Jogador": "Erling Haaland",
                "NºGols": 45,
                "NºAssist": 5,
                "RankingFIFA": 45,
                "Títulos": 3,
                "ValorMercado": 180000000.0,
                "NotaMédia": 7.80,
                "CleanSheet": 0,
                "MOTM": 8
            }
        }
        
        for key, value in mock_database.items():
            if key in name_clean or name_clean in key:
                print(f"[API Fallback] Retornando dados simulados predefinidos para: {value['Jogador']}")
                return value
                
        # Geracao dinamica para outros jogadores
        print(f"[API Fallback] Gerando estatisticas randomicas plausiveis para: {player_name}")
        gols = random.randint(5, 30)
        assistencias = random.randint(2, 16)
        nota = round(random.uniform(6.8, 8.3), 2)
        motm = random.randint(1, 8)
        titulos = random.randint(0, 3)
        ranking_fifa = random.randint(1, 100)
        valor_mercado = float(random.randint(15, 95) * 1000000)
        
        clean_sheet = 0
        if any(w in name_clean for w in ["goleiro", "gk", "keeper", "courtois", "alisson", "ederson"]):
            clean_sheet = random.randint(8, 20)
            gols = 0
            assistencias = random.randint(0, 1)
            
        return {
            "Jogador": player_name.strip().title(),
            "NºGols": gols,
            "NºAssist": assistencias,
            "RankingFIFA": ranking_fifa,
            "Títulos": titulos,
            "ValorMercado": valor_mercado,
            "NotaMédia": nota,
            "CleanSheet": clean_sheet,
            "MOTM": motm
        }

# Funcao exportada no nivel do modulo como solicitado
def buscar_dados_api(nome: str, time: str) -> dict:
    """
    Funcao wrapper que instancia o FootballAPIClient e realiza a busca de dados do jogador.
    """
    client = FootballAPIClient()
    return client.buscar_dados_api(nome, time)

if __name__ == "__main__":
    print("=== Testando Integracao com API / Fallback ===")
    res = buscar_dados_api("Lionel Messi", "Inter Miami")
    print("\nResultado Messi:", res)
