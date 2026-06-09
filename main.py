import os
import pandas as pd
from src.data.manage_dataset import init_csv, add_or_update_player, recalculate_ranking, DEFAULT_CSV_PATH

def main():
    print("=== Inicializando o projeto de previsao do Ballon D'or ===")
    
    # 1. Inicializa o CSV (cria o diretorio e o arquivo se nao existirem)
    init_csv()
    
    # 2. Simula dados de 4 jogadores de destaque para o Ballon D'or
    jogadores_teste = [
        {
            "Nome do Jogador": "Vinicius Junior",
            "N. de Gols": 24,
            "N. de Assistencias": 11,
            "Ranking FIFA": 5,
            "Conquista de titulos na temporada": 3,
            "Valor de mercado": 150000000.0,
            "Nota Media de desempenho": 8.0,
            "Clean Sheet": 0,
            "MOTM": 7
        },
        {
            "Nome do Jogador": "Jude Bellingham",
            "N. de Gols": 23,
            "N. de Assistencias": 13,
            "Ranking FIFA": 4,
            "Conquista de titulos na temporada": 3,
            "Valor de mercado": 180000000.0,
            "Nota Media de desempenho": 7.9,
            "Clean Sheet": 0,
            "MOTM": 6
        },
        {
            "Nome do Jogador": "Kylian Mbappe",
            "N. de Gols": 44,
            "N. de Assistencias": 10,
            "Ranking FIFA": 2,
            "Conquista de titulos na temporada": 2,
            "Valor de mercado": 180000000.0,
            "Nota Media de desempenho": 8.2,
            "Clean Sheet": 0,
            "MOTM": 9
        },
        {
            "Nome do Jogador": "Rodri",
            "N. de Gols": 9,
            "N. de Assistencias": 14,
            "Ranking FIFA": 8,
            "Conquista de titulos na temporada": 4,
            "Valor de mercado": 120000000.0,
            "Nota Media de desempenho": 8.4,
            "Clean Sheet": 0,
            "MOTM": 8
        }
    ]
    
    # 3. Adiciona ou atualiza os jogadores no arquivo CSV
    print("\nAdicionando/Atualizando jogadores...")
    for jogador in jogadores_teste:
        add_or_update_player(jogador)
        
    # 4. Recalcula o ranking explicitamente
    print("\nRecalculando ranking de forma explicita...")
    recalculate_ranking()
    
    # 5. Imprime o ranking final na tela
    print("\n=== RANKING ATUALIZADO DO BALLON D'OR ===")
    if os.path.exists(DEFAULT_CSV_PATH):
        df = pd.read_csv(DEFAULT_CSV_PATH)
        # Selecionando colunas mais relevantes para a visualizacao no terminal
        colunas_exibicao = [
            "Nome do Jogador", 
            "N. de Gols", 
            "N. de Assistencias", 
            "Nota Media de desempenho", 
            "Conquista de titulos na temporada", 
            "MOTM", 
            "Pontuacao"
        ]
        print(df[colunas_exibicao].to_string(index=True))
    else:
        print("Erro: Arquivo CSV de ranking nao foi encontrado.")

if __name__ == "__main__":
    main()
