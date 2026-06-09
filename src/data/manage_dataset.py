import os
import pandas as pd

# Definindo o caminho padrão para o arquivo CSV na pasta data/ na raiz do projeto
DEFAULT_CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "ranking_jogadores.csv")
)

# Definição dos campos/colunas do dataset
CSV_COLUMNS = [
    "Nome do Jogador",
    "N° de Gols",
    "N° de Assistências",
    "Ranking FIFA",
    "Conquista de títulos na temporada",
    "Valor de mercado",
    "Nota Média de desempenho",
    "Clean Sheet",
    "MOTM",
    "Pontuação"  # Coluna adicional para registrar a pontuação heurística calculada
]

def init_csv(file_path: str = DEFAULT_CSV_PATH) -> None:
    """
    Inicializa o arquivo CSV com os cabeçalhos corretos se ele ainda não existir.
    Garante também que a pasta de destino (ex: data/) seja criada.
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"Diretório criado: {directory}")

    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=CSV_COLUMNS)
        df.to_csv(file_path, index=False, encoding="utf-8")
        print(f"Arquivo CSV inicializado com sucesso em: {file_path}")
    else:
        print(f"O arquivo CSV já existe em: {file_path}")

def add_or_update_player(player_data: dict, file_path: str = DEFAULT_CSV_PATH) -> None:
    """
    Adiciona um novo jogador ou atualiza as informações se ele já existir (busca por 'Nome do Jogador').
    
    player_data deve ser um dicionário contendo as chaves correspondentes aos campos do CSV.
    Campos não fornecidos serão preenchidos com valores padrão (0 ou 0.0).
    """
    # Garante que o arquivo CSV esteja inicializado
    init_csv(file_path)
    
    # Lê o CSV existente
    df = pd.read_csv(file_path, encoding="utf-8")
    
    # Valida se o 'Nome do Jogador' foi fornecido
    player_name = player_data.get("Nome do Jogador")
    if not player_name:
        raise ValueError("O dicionário 'player_data' precisa conter a chave 'Nome do Jogador'.")

    # Normaliza e limpa os dados de entrada usando os campos padrão
    cleaned_data = {}
    for col in CSV_COLUMNS:
        if col == "Nome do Jogador":
            cleaned_data[col] = str(player_name).strip()
        elif col == "Pontuação":
            # A pontuação será calculada/recalculada dinamicamente, iniciamos com 0
            cleaned_data[col] = float(player_data.get(col, 0.0))
        elif col in ["Valor de mercado", "Nota Média de desempenho"]:
            cleaned_data[col] = float(player_data.get(col, 0.0))
        else:
            # Demais campos são numéricos inteiros (Gols, Assistências, Títulos, Clean Sheet, MOTM, etc.)
            cleaned_data[col] = int(player_data.get(col, 0))

    # Verifica se o jogador já existe no dataframe
    match_mask = df["Nome do Jogador"].str.strip().str.lower() == cleaned_data["Nome do Jogador"].lower()
    
    if match_mask.any():
        # Atualiza a linha existente
        idx = df[match_mask].index[0]
        for col in CSV_COLUMNS:
            df.at[idx, col] = cleaned_data[col]
        print(f"Dados do jogador '{cleaned_data['Nome do Jogador']}' foram atualizados.")
    else:
        # Adiciona uma nova linha
        new_row = pd.DataFrame([cleaned_data])
        if df.empty:
            df = new_row
        else:
            df = pd.concat([df, new_row], ignore_index=True)
        print(f"Jogador '{cleaned_data['Nome do Jogador']}' adicionado com sucesso.")
        
    # Salva as alterações de volta no CSV
    df.to_csv(file_path, index=False, encoding="utf-8")
    
    # Recalcula o ranking de forma automática após inserção/atualização
    recalculate_ranking(file_path)

def recalculate_ranking(file_path: str = DEFAULT_CSV_PATH) -> None:
    """
    Lê o CSV, recalcula a pontuação de cada jogador com base em uma pontuação heurística,
    ordena os jogadores do melhor para o pior e salva o arquivo novamente.
    
    Heurística simples provisória:
    Pontuação = Gols + Assistências + (Nota Média de desempenho * 5) + MOTM + (Títulos * 2) - (Ranking FIFA * 0.1)
    """
    if not os.path.exists(file_path):
        print(f"Erro: O arquivo '{file_path}' não existe. Inicialize-o primeiro.")
        return
        
    df = pd.read_csv(file_path, encoding="utf-8")
    
    if df.empty:
        print("O arquivo CSV está vazio. Nenhum ranking a recalcular.")
        return

    # Garante que os tipos estão corretos antes de fazer o cálculo matemático
    df["N° de Gols"] = pd.to_numeric(df["N° de Gols"], errors="coerce").fillna(0).astype(int)
    df["N° de Assistências"] = pd.to_numeric(df["N° de Assistências"], errors="coerce").fillna(0).astype(int)
    df["Nota Média de desempenho"] = pd.to_numeric(df["Nota Média de desempenho"], errors="coerce").fillna(0.0).astype(float)
    df["MOTM"] = pd.to_numeric(df["MOTM"], errors="coerce").fillna(0).astype(int)
    df["Conquista de títulos na temporada"] = pd.to_numeric(df["Conquista de títulos na temporada"], errors="coerce").fillna(0).astype(int)
    df["Ranking FIFA"] = pd.to_numeric(df["Ranking FIFA"], errors="coerce").fillna(100).astype(int)

    # Fórmula provisória de pontuação
    # Valorizamos gols, assistências, prêmios MOTM, títulos conquistados e a consistência da nota média.
    # Penalizamos de forma sutil se o Ranking FIFA da seleção nacional for muito baixo (pior/maior número).
    df["Pontuação"] = (
        df["N° de Gols"] * 1.0 +
        df["N° de Assistências"] * 0.8 +
        df["Nota Média de desempenho"] * 5.0 +
        df["MOTM"] * 1.5 +
        df["Conquista de títulos na temporada"] * 3.0 -
        (df["Ranking FIFA"] * 0.05)
    )
    
    # Ordena da maior pontuação para a menor
    df_sorted = df.sort_values(by="Pontuação", ascending=False).reset_index(drop=True)
    
    # Salva de volta no CSV
    df_sorted.to_csv(file_path, index=False, encoding="utf-8")
    print("Ranking recalculado e ordenado com sucesso.")

if __name__ == "__main__":
    # Teste simples para validação do script
    print("Iniciando teste do gerenciador de dataset...")
    
    # Caminho do CSV de teste
    test_csv = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "ranking_jogadores_teste.csv")
    )
    
    # Remove arquivo de teste anterior se existir
    if os.path.exists(test_csv):
        os.remove(test_csv)
        
    init_csv(test_csv)
    
    # Jogador 1
    player1 = {
        "Nome do Jogador": "Lionel Messi",
        "N° de Gols": 28,
        "N° de Assistências": 15,
        "Ranking FIFA": 1,
        "Conquista de títulos na temporada": 2,
        "Valor de mercado": 35000000,
        "Nota Média de desempenho": 8.1,
        "Clean Sheet": 0,
        "MOTM": 10
    }
    
    # Jogador 2
    player2 = {
        "Nome do Jogador": "Erling Haaland",
        "N° de Gols": 45,
        "N° de Assistências": 5,
        "Ranking FIFA": 45,
        "Conquista de títulos na temporada": 3,
        "Valor de mercado": 180000000,
        "Nota Média de desempenho": 7.8,
        "Clean Sheet": 0,
        "MOTM": 8
    }
    
    # Adicionando/Atualizando jogadores no arquivo de teste
    add_or_update_player(player1, test_csv)
    add_or_update_player(player2, test_csv)
    
    # Lendo o resultado do teste
    df_test = pd.read_csv(test_csv)
    print("\nConteúdo final do CSV de Teste:")
    print(df_test[["Nome do Jogador", "N° de Gols", "Nota Média de desempenho", "Pontuação"]])
    
    # Limpeza do arquivo de teste
    if os.path.exists(test_csv):
        os.remove(test_csv)
        print("\nArquivo de teste limpo.")
