import os
import random
import requests
from dotenv import load_dotenv

# Carrega as variaveis de ambiente a partir de um arquivo .env se ele existir na raiz
load_dotenv()

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
        # Carrega a chave de API das variaveis de ambiente (.env)
        self.api_key = os.getenv("FOOTBALL_API_KEY")
        
        # Define se estamos em modo simulado (Mock) por padrao ou por falta de chave valida
        self.is_mock_mode = False
        if not self.api_key or self.api_key == "seu_token_aqui" or self.api_key.startswith("MOCK"):
            print("[AVISO] FootballAPIClient: 'FOOTBALL_API_KEY' ausente ou invalida no .env.")
            print("[INFO] O cliente funcionarera em modo MOCK (simulado) como fallback.")
            self.is_mock_mode = True
            self.api_key = "MOCK_KEY"
        else:
            print(f"[API] Chave de API carregada com sucesso: {self.api_key[:5]}... (ocultada)")

    def buscar_estatisticas_jogador(self, nome_jogador: str, season: int = 2023) -> dict:
        """
        Faz uma requisicao HTTP real para a API-FOOTBALL buscando dados do jogador.
        Caso ocorra algum erro (limite de requests, falha de rede ou chave invalida),
        o metodo aciona automaticamente o fallback para retornar dados mockados coerentes.
        """
        if self.is_mock_mode:
            return self._obter_dados_mock(nome_jogador)
            
        url = "https://api-football-v1.p.rapidapi.com/v3/players"
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        params = {
            "search": nome_jogador,
            "season": str(season)
        }
        
        try:
            print(f"[API] Enviando requisicao para API-FOOTBALL buscando por: '{nome_jogador}' na temporada {season}...")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            # Verifica status HTTP
            if response.status_code == 403:
                print("[API - Erro 403] Acesso negado. Chave de API invalida ou expirada. Ativando fallback...")
                return self._obter_dados_mock(nome_jogador)
            elif response.status_code == 429:
                print("[API - Erro 429] Limite de requisicoes excedido. Ativando fallback...")
                return self._obter_dados_mock(nome_jogador)
            
            response.raise_for_status()
            data = response.json()
            
            # Trata erros retornados no proprio corpo da API (comum na API-FOOTBALL)
            if data.get("errors"):
                print(f"[API - Erro Interno] Erros relatados pela API: {data['errors']}. Ativando fallback...")
                return self._obter_dados_mock(nome_jogador)
                
            results = data.get("response", [])
            if not results:
                print(f"[API] Jogador '{nome_jogador}' nao foi encontrado na API-FOOTBALL. Ativando fallback...")
                return self._obter_dados_mock(nome_jogador)
                
            # Processa o primeiro jogador retornado (match mais proximo)
            player_info = results[0]["player"]
            stats_list = results[0]["statistics"]
            
            # Agrega estatisticas de todas as competicoes/times da temporada
            total_gols = 0
            total_assists = 0
            ratings = []
            clean_sheets = 0
            
            nationality = player_info.get("nationality", "").strip().lower()
            ranking_fifa = FIFA_RANKINGS_MAPPING.get(nationality, 50)
            
            # Identifica posicao
            position = "Desconhecido"
            
            for stat in stats_list:
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
            
            # Estimativas para campos ausentes na resposta direta de estatisticas da API de Jogadores:
            # 1. Clean Sheets (apenas para goleiros)
            if position.lower() in ["goalkeeper", "goleiro"]:
                clean_sheets = int((nota_media - 6.0) * 15) if nota_media > 6.0 else 2
                clean_sheets = max(0, min(30, clean_sheets))
                
            # 2. MOTM - Estimado com base na nota media e gols
            motm_estimado = max(0, int((nota_media - 7.0) * 10) + int(total_gols * 0.15))
            
            # 3. Titulos da temporada - Valor padrao de fallback
            titulos = random.randint(0, 2)
            
            # 4. Valor de Mercado - Estimativa baseada na idade, nota media e gols
            idade = player_info.get("age", 25)
            fator_idade = max(0.5, (38 - idade) / 10) if idade > 28 else 1.0
            valor_mercado = round((total_gols * 2.5 + total_assists * 1.5 + (nota_media - 6.0) * 20) * fator_idade * 1000000)
            valor_mercado = float(max(5000000, valor_mercado))
            
            print(f"[API] Dados reais processados com sucesso para: {player_info.get('name')}")
            
            return {
                "Jogador": player_info.get("name"),
                "NºGols": total_gols,
                "NºAssist": total_assists,
                "RankingFIFA": ranking_fifa,
                "Títulos": titulos,
                "ValorMercado": valor_mercado,
                "NotaMédia": nota_media,
                "CleanSheet": clean_sheets,
                "MOTM": motm_estimado
            }
            
        except Exception as e:
            print(f"[API - Erro de Conexao] Falha ao conectar a API externa: {e}. Ativando fallback...")
            return self._obter_dados_mock(nome_jogador)

    def _obter_dados_mock(self, player_name: str) -> dict:
        """
        Gera e retorna dados simulados (mock) realistas para um jogador.
        Usado quando nao ha chave de API ativa ou ocorre erro na requisicao externa.
        """
        name_clean = player_name.strip().lower()
        
        # Banco estatico com alguns craques usando cabecalhos corretos
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

    # Alias para compatibilidade caso outro script ainda chame get_player_stats
    def get_player_stats(self, player_name: str) -> dict:
        return self.buscar_estatisticas_jogador(player_name)

if __name__ == "__main__":
    print("=== Testando Integracao com API / Fallback ===")
    client = FootballAPIClient()
    stats = client.buscar_estatisticas_jogador("Lionel Messi")
    print("\nEstatisticas Lionel Messi:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
