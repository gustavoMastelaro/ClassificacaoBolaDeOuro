import os
import pandas as pd

# Definindo o caminho padrao para o arquivo CSV na pasta data/ na raiz do projeto
DEFAULT_CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "ranking_jogadores.csv")
)

# Definicao dos novos campos/colunas curtos do dataset (conforme solicitado pelo usuario)
CSV_COLUMNS = [
    "Jogador",
    "NºGols",
    "NºAssist",
    "RankingFIFA",
    "Títulos",
    "ValorMercado",
    "NotaMédia",
    "CleanSheet",
    "MOTM",
    "Pontuação"
]

# Mapeamento para suportar nomes antigos ou alternativos de campos para compatibilidade
KEY_MAPPING = {
    "jogador": "Jogador",
    "nome do jogador": "Jogador",
    "n. de gols": "NºGols",
    "n° de gols": "NºGols",
    "nºgols": "NºGols",
    "n. de assistencias": "NºAssist",
    "n° de assistências": "NºAssist",
    "nºassist": "NºAssist",
    "ranking fifa": "RankingFIFA",
    "rankingfifa": "RankingFIFA",
    "conquista de titulos na temporada": "Títulos",
    "conquista de títulos na temporada": "Títulos",
    "títulos": "Títulos",
    "titulos": "Títulos",
    "valor de mercado": "ValorMercado",
    "valormercado": "ValorMercado",
    "nota media de desempenho": "NotaMédia",
    "nota média de desempenho": "NotaMédia",
    "notamédia": "NotaMédia",
    "notamedia": "NotaMédia",
    "clean sheet": "CleanSheet",
    "cleansheet": "CleanSheet",
    "motm": "MOTM",
    "pontuacao": "Pontuação",
    "pontuação": "Pontuação"
}

def parse_valor_mercado(val) -> float:
    """
    Remove o 'M' temporariamente e converte o valor de mercado para float numerico.
    """
    if pd.isna(val):
        return 0.0
    val_str = str(val).strip().upper()
    if val_str.endswith("M"):
        try:
            # Remove o 'M' e multiplica por 1 milhao
            return float(val_str[:-1]) * 1000000.0
        except ValueError:
            return 0.0
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def format_valor_mercado(val) -> str:
    """
    Formata o valor numerico para o formato simplificado com 'M' (ex: 180M).
    """
    try:
        num = float(val)
        return f"{int(num / 1000000)}M"
    except (ValueError, TypeError):
        # Se ja for uma string formatada (ex: '180M'), retorna ela mesma
        val_str = str(val).strip()
        if val_str.upper().endswith("M"):
            return val_str
        return val_str

def init_csv(file_path: str = DEFAULT_CSV_PATH) -> None:
    """
    Inicializa o arquivo CSV com os cabecalhos corretos se ele ainda nao existir.
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"Diretorio criado: {directory}")

    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=CSV_COLUMNS)
        df.to_csv(file_path, index=False, encoding="utf-8")
        print(f"Arquivo CSV inicializado com sucesso em: {file_path}")
    else:
        # Se o arquivo ja existe mas esta com colunas antigas, recria ou avisa
        # Aqui fazemos a validacao estrutural para migrar se necessario
        try:
            df_existing = pd.read_csv(file_path, nrows=0)
            if list(df_existing.columns) != CSV_COLUMNS:
                # Recria com a nova estrutura para evitar conflitos
                df = pd.DataFrame(columns=CSV_COLUMNS)
                df.to_csv(file_path, index=False, encoding="utf-8")
                print(f"Estrutura antiga detectada. Arquivo CSV recriado com novos cabecalhos em: {file_path}")
        except Exception:
            pass

def add_or_update_player(player_data: dict, file_path: str = DEFAULT_CSV_PATH) -> None:
    """
    Adiciona um novo jogador ou atualiza as informacoes se ele ja existir.
    Mapeia chaves antigas e garante a formatacao com 'M' para o ValorMercado.
    """
    init_csv(file_path)
    df = pd.read_csv(file_path, encoding="utf-8")
    
    # Processa e mapeia os dados recebidos para os novos nomes de coluna
    mapped_data = {}
    
    # Primeiro, resolve o nome do jogador
    player_name = None
    for k, v in player_data.items():
        k_clean = k.strip().lower()
        if KEY_MAPPING.get(k_clean) == "Jogador":
            player_name = str(v).strip()
            break
            
    if not player_name:
        raise ValueError("O dicionario 'player_data' precisa conter o nome do jogador.")
        
    mapped_data["Jogador"] = player_name

    # Inicializa os campos com valores padrao
    for col in CSV_COLUMNS:
        if col != "Jogador":
            mapped_data[col] = 0.0 if col in ["NotaMédia", "Pontuação"] else 0

    # Copia os dados fornecidos aplicando o mapeamento
    for k, v in player_data.items():
        k_clean = k.strip().lower()
        mapped_col = KEY_MAPPING.get(k_clean)
        if mapped_col and mapped_col != "Jogador":
            if mapped_col == "ValorMercado":
                # Converte para numerico primeiro e depois salva no formato com 'M'
                num_val = parse_valor_mercado(v)
                mapped_data[mapped_col] = format_valor_mercado(num_val)
            elif mapped_col in ["NotaMédia", "Pontuação"]:
                mapped_data[mapped_col] = float(v)
            else:
                try:
                    mapped_data[mapped_col] = int(v)
                except ValueError:
                    mapped_data[mapped_col] = 0

    # Verifica se o jogador ja existe
    match_mask = df["Jogador"].str.strip().str.lower() == mapped_data["Jogador"].lower()
    
    if match_mask.any():
        idx = df[match_mask].index[0]
        for col in CSV_COLUMNS:
            df.at[idx, col] = mapped_data[col]
        print(f"Dados do jogador '{mapped_data['Jogador']}' foram atualizados.")
    else:
        new_row = pd.DataFrame([mapped_data])
        if df.empty:
            df = new_row
        else:
            df = pd.concat([df, new_row], ignore_index=True)
        print(f"Jogador '{mapped_data['Jogador']}' adicionado com sucesso.")
        
    df.to_csv(file_path, index=False, encoding="utf-8")
    
    # Recalcula o ranking apos modificacao
    recalculate_ranking(file_path)

def recalculate_ranking(file_path: str = DEFAULT_CSV_PATH) -> None:
    """
    Le o CSV, processa o ValorMercado (removendo o 'M' para computacao) se necessario,
    recalcula a pontuacao heuristica, ordena do melhor para o pior e salva.
    """
    if not os.path.exists(file_path):
        print(f"Erro: O arquivo '{file_path}' nao existe.")
        return
        
    df = pd.read_csv(file_path, encoding="utf-8")
    
    if df.empty:
        print("O arquivo CSV esta vazio.")
        return

    # Garante os tipos de dados
    df["NºGols"] = pd.to_numeric(df["NºGols"], errors="coerce").fillna(0).astype(int)
    df["NºAssist"] = pd.to_numeric(df["NºAssist"], errors="coerce").fillna(0).astype(int)
    df["NotaMédia"] = pd.to_numeric(df["NotaMédia"], errors="coerce").fillna(0.0).astype(float)
    df["MOTM"] = pd.to_numeric(df["MOTM"], errors="coerce").fillna(0).astype(int)
    df["Títulos"] = pd.to_numeric(df["Títulos"], errors="coerce").fillna(0).astype(int)
    df["RankingFIFA"] = pd.to_numeric(df["RankingFIFA"], errors="coerce").fillna(100).astype(int)

    # Tratamento especial do ValorMercado para remocao do 'M' para uso no calculo
    valores_mercado_numericos = df["ValorMercado"].apply(parse_valor_mercado)

    # Formula de pontuacao (incorporando levemente o valor de mercado numerico)
    df["Pontuação"] = (
        df["NºGols"] * 1.0 +
        df["NºAssist"] * 0.8 +
        df["NotaMédia"] * 5.0 +
        df["MOTM"] * 1.5 +
        df["Títulos"] * 3.0 -
        (df["RankingFIFA"] * 0.05) +
        (valores_mercado_numericos / 50000000.0) # Bonus com base no valor de mercado
    )
    
    # Formata de forma limpa as notas finais
    df["Pontuação"] = df["Pontuação"].round(2)
    
    # Ordena da maior pontuacao para a menor
    df_sorted = df.sort_values(by="Pontuação", ascending=False).reset_index(drop=True)
    
    # Salva de volta no CSV
    df_sorted.to_csv(file_path, index=False, encoding="utf-8")
    print("Ranking recalculado e ordenado com sucesso.")

if __name__ == "__main__":
    print("=== Executando Testes Locais do Gerenciador de Dataset ===")
    test_csv = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "ranking_jogadores_teste.csv")
    )
    if os.path.exists(test_csv):
        os.remove(test_csv)
        
    init_csv(test_csv)
    
    p1 = {
        "Jogador": "Messi",
        "NºGols": 20,
        "NºAssist": 10,
        "RankingFIFA": 1,
        "Títulos": 1,
        "ValorMercado": 35000000, # Numerico puro para testar a formatacao automatica com M
        "NotaMédia": 8.0,
        "CleanSheet": 0,
        "MOTM": 5
    }
    
    add_or_update_player(p1, test_csv)
    
    df_test = pd.read_csv(test_csv)
    print("\nVisualizacao do CSV de Teste:")
    print(df_test)
    
    if os.path.exists(test_csv):
        os.remove(test_csv)
