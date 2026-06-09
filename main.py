import os
import pandas as pd
from src.data.manage_dataset import init_csv, add_or_update_player, recalculate_ranking, DEFAULT_CSV_PATH

def main():
    print("=== Inicializando o projeto de previsao do Ballon D'or ===")
    
    # 1. Inicializa o CSV (cria o diretorio e o arquivo se nao existirem)
    init_csv()
    
    # 2. Simula dados de 4 jogadores de destaque para o Ballon D'or com os novos cabecalhos curtos
    jogadores_teste = [
        {
            "Jogador": "Vinicius Junior",
            "NºGols": 24,
            "NºAssist": 11,
            "RankingFIFA": 5,
            "Títulos": 3,
            "ValorMercado": 150000000.0, # Passando como numero para a formatacao com M atuar
            "NotaMédia": 8.0,
            "CleanSheet": 0,
            "MOTM": 7
        },
        {
            "Jogador": "Jude Bellingham",
            "NºGols": 23,
            "NºAssist": 13,
            "RankingFIFA": 4,
            "Títulos": 3,
            "ValorMercado": 180000000.0,
            "NotaMédia": 7.9,
            "CleanSheet": 0,
            "MOTM": 6
        },
        {
            "Jogador": "Kylian Mbappe",
            "NºGols": 44,
            "NºAssist": 10,
            "RankingFIFA": 2,
            "Títulos": 2,
            "ValorMercado": 180000000.0,
            "NotaMédia": 8.2,
            "CleanSheet": 0,
            "MOTM": 9
        },
        {
            "Jogador": "Rodri",
            "NºGols": 9,
            "NºAssist": 14,
            "RankingFIFA": 8,
            "Títulos": 4,
            "ValorMercado": 120000000.0,
            "NotaMédia": 8.4,
            "CleanSheet": 0,
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
    
    # 5. Imprime o ranking final na tela de forma organizada
    print("\n=== RANKING ATUALIZADO DO BALLON D'OR ===")
    if os.path.exists(DEFAULT_CSV_PATH):
        df = pd.read_csv(DEFAULT_CSV_PATH)
        # Selecionando colunas com os novos nomes curtos para exibicao
        colunas_exibicao = [
            "Jogador", 
            "NºGols", 
            "NºAssist", 
            "NotaMédia", 
            "Títulos", 
            "ValorMercado", 
            "MOTM", 
            "Pontuação"
        ]
        # Imprime o dataframe formatado
        print(df[colunas_exibicao].to_string(index=True))
    else:
        print("Erro: Arquivo CSV de ranking nao foi encontrado.")

if __name__ == "__main__":
    main()
