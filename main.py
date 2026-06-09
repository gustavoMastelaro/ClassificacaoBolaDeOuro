import os
import pandas as pd
from src.data.manage_dataset import init_csv, add_or_update_player, recalculate_ranking, DEFAULT_CSV_PATH
from src.data.api_client import buscar_dados_api

def main():
    # Garante a inicializacao do arquivo de dados antes de iniciar o loop
    init_csv()
    
    while True:
        print("\nMENU BALLON D'OR")
        print("[1] Visualizar o Top 10 Atual")
        print("[2] Adicionar/Atualizar Jogador via API")
        print("[3] Sair do Programa")
        
        opcao = input("Escolha uma opcao: ").strip()
        
        if opcao == "1":
            print("\nTOP 10 JOGADORES ATUAIS")
            if os.path.exists(DEFAULT_CSV_PATH):
                df = pd.read_csv(DEFAULT_CSV_PATH)
                if df.empty:
                    print("Nenhum jogador cadastrado no sistema ate o momento.")
                else:
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
                    # Exibe no maximo os 10 primeiros colocados
                    print(df[colunas_exibicao].head(10).to_string(index=True))
            else:
                print("[Aviso] O arquivo de dados nao foi encontrado. Adicione um jogador para inicializa-lo.")
                
        elif opcao == "2":
            print("\nAdicionar/Atualizar Jogador via API")
            nome = input("Nome do Jogador: ").strip()
            time = input("Time Atual do Jogador: ").strip()
            
            if not nome or not time:
                print("[Erro] O nome do jogador e o time sao obrigatorios.")
                continue
                
            try:
                # Busca as estatisticas do jogador usando a API / Mock
                print(f"Buscando dados na API para '{nome}' do '{time}'...")
                player_data = buscar_dados_api(nome, time)
                
                if player_data and player_data.get("Jogador"):
                    # Exibe um resumo amigavel dos dados obtidos
                    print("\n--- Dados Encontrados ---")
                    print(f"  Jogador: {player_data['Jogador']}")
                    print(f"  Gols: {player_data['NºGols']}")
                    print(f"  Assistencias: {player_data['NºAssist']}")
                    print(f"  Nota Media: {player_data['NotaMédia']}")
                    print(f"  MOTM: {player_data['MOTM']}")
                    print(f"  Titulos: {player_data['Títulos']}")
                    
                    # Salva no CSV e recalcula o ranking
                    add_or_update_player(player_data)
                    print(f"\n[Sucesso] Jogador '{player_data['Jogador']}' atualizado com dados da API!")
                else:
                    print(f"[Erro] Jogador '{nome}' nao foi encontrado ou nao possui dados validos.")
            except Exception as e:
                print(f"[Erro] Falha ao processar dados via API: {e}")
                
        elif opcao == "3":
            print("\nEncerrando o programa. Obrigado por utilizar!")
            break
        else:
            print("\n[Erro] Opcao invalida. Por favor, escolha entre [1], [2] ou [3].")

if __name__ == "__main__":
    main()
