import json
from student_tree_search import *
from collections import deque
import math

# Cores para impressão no terminal (ANSI Escape Codes)
RESET = "\033[0m"
RED   = "\033[91m"
GREEN = "\033[92m"
BLUE  = "\033[94m"
CYAN  = "\033[96m"
MAGENTA = "\033[95m"
YELLOW  = "\033[93m"
GREY  = "\033[90m"

WALL_VALUE = 999
GOAL_VALUE = 0
def print_mapa_colorido(distancias):
    """
    Imprime a matriz 'distancias' em cores degradê.
      - -1 (obstáculo) em vermelho
      - None (não alcançado) em cinza
      - 0..maxDist em degradê de verde (0) a vermelho (maxDist)
    """
    
    # Identifica valores numéricos (>= 0) para saber min e max
    valores_dist = [dist for row in distancias for dist in row 
                    if dist is not None and dist != float('inf') and dist >= 0]
    if not valores_dist:
        # Não há nenhuma célula alcançada (ou só obstáculos e None)
        # Apenas imprimimos com as regras definidas.
        max_dist = 0
        min_dist = 0
    else:
        max_dist = max(valores_dist)
        min_dist = min(valores_dist)
    
    n_linhas = len(distancias)
    n_colunas = len(distancias[0])
    
    for i in range(n_linhas):
        linha_str = ""
        for j in range(n_colunas):
            val = distancias[i][j]
            
            # 1) Obstáculo (val = -1)
            if val == float('inf'):
                linha_str += GREY + 'inf' + RESET
                continue
            if val is None:
                linha_str += GREY + " X " + RESET
                continue
            
            # 3) Célula alcançada (val >= 0)
            if max_dist == min_dist:
                # Se todas as distâncias são iguais (ex: 0), tudo da mesma cor
                cor = "\033[38;2;0;255;0m"  # verde
            else:
                ratio = (val - min_dist) / (max_dist - min_dist)
                r = int(255 * ratio)         # 0 -> 255
                g = int(255 * (1 - ratio))   # 255 -> 0
                b = 0
                cor = f"\033[38;2;{r};{g};{b}m"
            
            # Escreve o valor da distância com a cor calculada
            linha_str += f"{cor}{val:2d}{RESET} "
        
        print(linha_str)
    print()

def bfs_floodfill(json_states = 'test_states.json', scene = "scene_0"):
    with open(json_states, 'r') as file:
        all_scenes = json.load(file)
    states = all_scenes[scene]
    state_map = states["0"]
    mapa = state_map["map"]
    #print(mapa)
    #print_mapa_colorido(mapa)
    size = state_map["size"]
    n_col = size[1]
    n_lin = size[0]
    start = [0,0]
    start_lin = start[0]
    start_col = start[1]
    goal = [40,20]
    goal_lin = goal[0]
    goal_col = goal[1]
    
    if not (0 <= start_lin < n_lin and 0 <= start_col < n_col):
        raise ValueError("Coordenadas de start fora do limite do mapa.")
    if not (0 <= goal_lin < n_lin and 0 <= goal_col < n_col):
        raise ValueError("Coordenadas de goal fora do limite do mapa.")
    
    # Se a posição inicial ou final for obstáculo, não há caminho
    if mapa[start_lin][start_col] == 1 or mapa[goal_lin][goal_col] == 1:
        return None, []
    
    # Cria uma matriz de distâncias inicializada com None
    distancias = [[None for _ in range(n_col)] for _ in range(n_lin)]
    distancias[goal_lin][goal_col] = 0
    
    # Matriz (ou dicionário) para guardar os pais (predecessores)
    # para reconstruir o caminho
    pais = [[None for _ in range(n_col)] for _ in range(n_lin)]
    
    # Fila para BFS (armazenando (linha, coluna))
    fila = deque()
    fila.append((goal_lin, goal_col))
    
    # Movimentos possíveis (cima, baixo, esquerda, direita)
    movimentos = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # BFS
    while fila:
        lin_atual, col_atual = fila.popleft()
        
        # Se alcançamos o goal, podemos parar
        """ if (lin_atual, col_atual) == (start_lin, start_col):
            break """
        
        for d_lin, d_col in movimentos:
            lin_viz = lin_atual + d_lin
            col_viz = col_atual + d_col
            # Verifica se está dentro do mapa e se é espaço livre
            if 0 <= lin_viz < n_lin and 0 <= col_viz < n_col:
                if distancias[lin_viz][col_viz] is None:
                    if mapa[lin_viz][col_viz] == 0 :
                        distancias[lin_viz][col_viz] = distancias[lin_atual][col_atual] + 1
                        pais[lin_viz][col_viz] = (lin_atual, col_atual)
                        fila.append((lin_viz, col_viz))
                    else:
                        distancias[lin_viz][col_viz] = float('inf')
                
                    
    # Reconstruir o caminho, se o goal foi alcançado
    path = []
    if distancias[start_lin][start_col] is not None:
        # Caminho existe; reconstrói "de trás pra frente"
        atual = (start_lin, start_col)
        while atual is not None:
            path.append(atual)
            atual = pais[atual[0]][atual[1]]
        #path.reverse()  # Inverte para ficar do start -> goal
    
    return distancias, path

if __name__ == "__main__":
    distancias, caminho = bfs_floodfill()
    print_mapa_colorido(distancias)
    print("Caminho:", caminho)