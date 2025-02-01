import json
from student_tree_search import *
from collections import deque,defaultdict

RESET = "\033[0m"
RED   = "\033[91m"
GREEN = "\033[92m"
BLUE  = "\033[94m"
CYAN  = "\033[96m"
MAGENTA = "\033[95m"
YELLOW  = "\033[93m"
GREY  = "\033[90m"

WALL_VALUE = 1
GOAL_VALUE = 0
def print_mapa_colorido(distancias, dead_ends=None , intersecoes = None):
    """
    Imprime a matriz 'distancias' em cores degradê.
      - -1 (obstáculo) em vermelho
      - None (não alcançado) em cinza
      - 0..maxDist em degradê de verde (0) a vermelho (maxDist)
    """
    
    # Identifica valores numéricos (>= 0) para saber min e max
    valores_dist = [dist for row in distancias for dist in row 
                    if (dist is not None and dist >= 0)]
    
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
    
    dead_end_list = []
    if dead_ends is not None:
        has_dead_end = False
        for dead_end in dead_ends:
            dead_end_list.append(dead_end[0])
    
    for i in range(n_linhas):
        linha_str = ""
        for j in range(n_colunas):
            val = distancias[i][j]
            
            if dead_ends is not None:
                has_dead_end = False
                for dead_end in dead_end_list:
                    #print("dead_end: ",dead_end[0], "[i,j]: ",[i,j])
                    if [i,j] == dead_end:
                        #print("[i,j] in dead_end")
                        if [i,j] in intersecoes:
                            linha_str += MAGENTA + " X " + RESET
                        else:
                            linha_str += RED + " X " + RESET
                        has_dead_end = True
                        break
                if has_dead_end:
                    continue
            if intersecoes is not None and [i,j] in intersecoes:
                linha_str += BLUE + " X " + RESET
                continue
            
            # 1) Obstáculo (val = -1)
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
def find_deadEndsPahts(mapa,goal):
    """
    Retorna uma lista de coordenadas (linha, coluna) que representam
    caminhos/células sem saída no mapa, ou seja, células transitáveis
    que não conseguem chegar ao 'goal'.
    
    Parâmetros:
    -----------
    mapa : list[list[int]]
        Matriz representando o mapa. Valores 1 ou 5 serão tratados
        como transitáveis (onde podemos andar).
    goal : list[int]
        Coordenada do objetivo no formato [linha, coluna].
    
    Retorna:
    --------
    dead_ends : list[(int,int)]
        Lista de tuplas (linha, coluna) que são caminhos sem saída.
    """

    # Dimensões do mapa
    rows = len(mapa)
    cols = len(mapa[0]) if rows > 0 else 0

    # Coordenada do goal
    goal_row, goal_col = goal

    # Verifica se o goal está dentro dos limites e se é transitável
    if not (0 <= goal_row < rows and 0 <= goal_col < cols):
        raise ValueError("Coordenada do goal está fora dos limites do mapa.")
    if mapa[goal_row][goal_col] not in [1, 5]:
        # Se a célula de goal não for transitável, não há caminho
        # (todos os nós transitáveis serão considerados sem saída).
        # Você pode retornar todos os nós transitáveis ou apenas uma lista vazia.
        return [
            (r, c) for r in range(rows) for c in range(cols)
            if mapa[r][c] in [1, 5]
        ]

    # Fila para BFS e conjunto de visitados
    queue = deque()
    visited = set()

    # Inicializa a BFS a partir do goal
    queue.append((goal_row, goal_col))
    visited.add((goal_row, goal_col))

    # Direções possíveis (4-connected)
    directions = [(1,0), (-1,0), (0,1), (0,-1)]

    # Executa BFS
    while queue:
        x, y = queue.popleft()
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            # Verifica se (nx, ny) está dentro do mapa e é transitável
            if 0 <= nx < rows and 0 <= ny < cols:
                if mapa[nx][ny] in [1, 5] and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))

    # Todas as células transitáveis que não foram visitadas são caminhos sem saída
    dead_ends = []
    for r in range(rows):
        for c in range(cols):
            if mapa[r][c] in [1, 5] and (r, c) not in visited:
                dead_ends.append([r, c])

    return dead_ends

def make_interceptionsGraph(mapa):
    """
    Constrói um grafo em que os nós são as interseções (ou pontas) do labirinto,
    e as arestas ligam nós consecutivos por um corredor.
    
    Parâmetros:
    -----------
    mapa : list[list[int]]
        Matriz representando o mapa, em que 1 são paredes, e 0 ou 5 são transitáveis.
    
    Retorna:
    --------
    dict:
        Dicionário de adjacência. Chaves são tuplas (linha, coluna) representando nós.
        Valores são listas de tuplas ((linha_dest, col_dest), distancia).
    """
    
    # Dimensões
    rows = len(mapa)
    cols = len(mapa[0]) if rows > 0 else 0
    
    def eh_walkable(r, c):
        """Verifica se (r,c) está dentro do mapa e não é parede."""
        return 0 <= r < rows and 0 <= c < cols and mapa[r][c] != 1
    
    # Vizinhos possíveis (4 direções)
    direcoes = [(1,0), (-1,0), (0,1), (0,-1)]
    
    # 1) Identificar nós (interseções ou pontas)
    nos = []
    for r in range(rows):
        for c in range(cols):
            if eh_walkable(r, c):
                # Contar quantos vizinhos são transitáveis
                vizinhos = 0
                for dr, dc in direcoes:
                    nr, nc = r + dr, c + dc
                    if eh_walkable(nr, nc):
                        vizinhos += 1
                # Se número de vizinhos != 2, vira nó
                # (0, 1 ou >=3 vizinhos)
                if vizinhos != 2:
                    nos.append((r, c))
    
    # Transformar 'nos' em conjunto (para busca rápida)
    nos_set = set(nos)
    
    # 2) Montar as arestas do grafo
    # Usaremos um dicionário de listas de adjacência
    grafo = defaultdict(list)
    
    for (r, c) in nos:
        # Para cada nó, vamos explorar em cada direção possível
        for dr, dc in direcoes:
            nr, nc = r + dr, c + dc
            
            # Só iniciamos a exploração se for célula transitável
            if not eh_walkable(nr, nc):
                continue
            
            distancia = 1
            # Posição atual durante o avanço no corredor
            cr, cc = nr, nc
            # Mantemos a direção original para “seguir reto” no corredor
            dir_atual = (dr, dc)
            
            # Enquanto estivermos em células que NÃO sejam nós
            # e que tenham exatamente 2 vizinhos (um corredor),
            # continuamos andando.
            while True:
                if (cr, cc) in nos_set:
                    # Achamos outro nó
                    grafo[(r, c)].append(((cr, cc), distancia))
                    break
                
                # Verifica quantos vizinhos transitáveis a célula atual tem
                vizinhos_corr = 0
                for x, y in direcoes:
                    if eh_walkable(cr + x, cc + y):
                        vizinhos_corr += 1
                
                # Se não for um corredor (ou seja, vizinhos != 2),
                # paramos, pois chegamos a um lugar que deveria ser nó,
                # mas não está em 'nos_set' (pode acontecer se for beco,
                # mas não mapeamos direito — dependendo da lógica).
                # Você pode adaptar conforme a sua necessidade.
                if vizinhos_corr != 2:
                    break
                
                # Continuar andando na mesma direção
                # Próxima célula no corredor
                cr += dir_atual[0]
                cc += dir_atual[1]
                distancia += 1
                
                # Se saímos do mapa ou trombamos em parede, paramos
                if not eh_walkable(cr, cc):
                    break
    
    # Converte para dict simples (se preferir, ou deixa como defaultdict)
    grafo = dict(grafo)
    
    return grafo
    
def find_deadEnds(mapa, start = [0,0]):
    """
    encontra os dead ends do mapa e a direcao que tem de seguir para sair
    o return = [[coordenadas do dead end],[direcao que tem de seguir para sair]]
    """
    rows = len(mapa)
    cols = len(mapa[0]) if rows > 0 else 0
    # Fila para BFS e conjunto de visitados
    queue = deque()
    visited = set()
    dead_ends = []
    start_row, start_col = start
    

    # Direções possíveis (4-connected)
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    for x in range(rows):
        for y in range(cols):
            num_conections = 0
            connections_directions = []
            for dx, dy in directions:
                if mapa[x][y] == 1:
                    break
                nx, ny = x + dx, y + dy
                if 0 <= nx < rows and 0 <= ny < cols: # Verifica se (nx, ny) está dentro do mapa
                    if mapa[nx][ny] == 0:
                        num_conections += 1
                        connections_directions.append([dx,dy])
            if num_conections == 1:
                dead_ends.append([[x,y],connections_directions[0]])
    return dead_ends

def find_interceptions(mapa,start = [0,0]):
    """
    encontra as interseções do mapa
    interseções são pontos onde o mapa tem mais de 2 conexões
    sao expluidos porntos onde o mapa tem mais de 2 conexões, mas que diagonalmente nao tem parece, sao interpretados como livres
    PROBLEMA: nao considera intersecoes como (intersecao marcada com valores 5):
    [[0,0,1,0,1],
     [0,0,1,0,1],
     [1,1,5,5,1],
     [0,0,5,5,0],
     [1,1,1,0,1]]
    """
    rows = len(mapa)
    cols = len(mapa[0]) if rows > 0 else 0
    # Fila para BFS e conjunto de visitados
    queue = deque()
    visited = set()
    interceptions = []
    start_row, start_col = start
    

    # Direções possíveis (4-connected)
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    free_directions = [(1,1),(-1,-1),(1,-1),(-1,1)]
    #submapas considerados intersecoes
    submap_endoftunel   = [[[1,1,1],
                            [0,0,0],
                            [0,1,1]],
                           [[0,1,1],
                            [0,0,0],
                            [1,1,1]],
                           [[0,1,1],
                            [0,0,0],
                            [0,1,1]],
                           
                           [[1,1,1],
                            [0,0,1],
                            [0,1,1]],
                           [[0,1,1],
                            [0,0,1],
                            [1,1,1]],
                           [[0,1,1],
                            [0,0,1],
                            [0,1,1]],
                           
                           
                           [[1,1,1],
                            [0,0,0],
                            [1,1,0]],
                           [[1,1,0],
                            [0,0,0],
                            [1,1,1]],
                           [[1,1,0],
                            [0,0,0],
                            [1,1,0]],
                           
                           [[1,1,1],
                            [0,0,0],
                            [1,1,0]],
                           [[1,1,0],
                            [0,0,0],
                            [1,1,1]],
                           [[1,1,0],
                            [0,0,0],
                            [1,1,0]],
                           
                           [[1,0,0],
                            [1,0,1],
                            [1,0,1]],
                           [[1,0,0],
                            [1,0,1],
                            [1,0,1]],
                           [[0,0,0],
                            [1,0,1],
                            [1,0,1]],
                           
                           [[1,0,0],
                            [1,0,1],
                            [1,1,1]],
                           [[1,0,0],
                            [1,0,1],
                            [1,1,1]],
                           [[0,0,0],
                            [1,0,1],
                            [1,1,1]],
                           
                           
                           [[1,0,1],
                            [1,0,1],
                            [0,0,0]],
                           [[1,0,1],
                            [1,0,1],
                            [1,0,0]],
                           [[1,0,1],
                            [1,0,1],
                            [0,0,1]],
                           
                           [[1,1,1],
                            [1,0,1],
                            [0,0,0]],
                           [[1,1,1],
                            [1,0,1],
                            [1,0,0]],
                           [[1,1,1],
                            [1,0,1],
                            [0,0,1]]]
    """                    [[0,0,0],
                            [0,0,0],
                            [0,0,0]],               """
    for x in range(rows):
        for y in range(cols):
            num_conections = 0
            if mapa[x][y] == 1:
                    break
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < rows and 0 <= ny < cols: # Verifica se (nx, ny) está dentro do mapa
                    if mapa[nx][ny] == 0:
                        num_conections += 1
            if num_conections >= 1:
                free = False
                prov_map = [[0,0,0],[0,0,0],[0,0,0]]
                for dx, dy in free_directions:
                    nx, ny = x + dx, y + dy
                    subx, suby = 1 + dx, 1 + dy
                    print("x,y:",(x,y)," nx,ny:",(nx,ny), "subx,suby:",(subx,suby))
                    if 0 <= nx < rows and 0 <= ny < cols:
                        if mapa[nx][ny] == 0 and num_conections > 2:
                            free = True
                            break
                        else:
                            prov_map[subx][suby] = mapa[nx][ny]
                            if num_conections <= 2:
                                free = True
                    else:
                        prov_map[subx][suby] = 1
                        free = True
                for linha in prov_map:
                    print(linha)
                print()
                if not free:
                    interceptions.append([x,y])
                if prov_map in submap_endoftunel:
                    interceptions.append([x,y])
    return interceptions

def find_pathDeadEnds(mapa):
    dead_ends = find_deadEnds(mapa)
    print("dead_ends: ",dead_ends)
    interceptions = find_interceptions(mapa)
    print("interceptions: ",interceptions)
    print_mapa_colorido(mapa, dead_ends, interceptions)
    rows = len(mapa)
    cols = len(mapa[0]) if rows > 0 else 0
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    dead_end_interceptions = []
    new_map = mapa.copy()
    for dead_end_inf in dead_ends:
        dead_end = dead_end_inf[0]
        direction = dead_end_inf[1]
        current = dead_end
        print("dead_end: ",dead_end)
        while True:
            #print_mapa_colorido(new_map)
            if current in interceptions:
                print("TRUE")
                dead_end_interceptions.append([dead_end,current])
                new_map[current[0]][current[1]] = 1
                break
            else:
                current = [current[0]+direction[0],current[1]+direction[1]]
                
    print_mapa_colorido(new_map)
            
            
       
            
            

if __name__ == "__main__":
    size = [10,15]
    mapa = [[0,0,0,0,0,0,0,1,0,0,0],
            [0,0,0,0,1,1,1,1,0,0,0],
            [0,0,0,0,1,0,1,0,0,0,0],
            [0,0,0,0,1,0,1,0,0,0,0],
            [0,0,0,0,1,0,1,0,0,0,0],
            [0,0,1,1,1,0,1,1,1,1,1],
            [0,0,0,0,0,0,0,0,0,0,0],
            [0,0,1,0,1,0,1,1,1,1,1],
            [0,0,1,0,1,0,1,0,0,0,0],
            [0,0,1,0,1,0,1,0,0,0,0],
            [0,0,1,0,1,1,1,0,0,0,0],
            [0,0,0,0,1,0,1,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0],]
    goals = [[9,14],[6,0],[6,2],[4,2],[10,8]]
    dead_ends_paths = find_deadEndsPahts(mapa,[14,9])
    """ for cell in dead_ends:
        print(cell) """
    #print_mapa_colorido(mapa, dead_ends_paths)
    grafo = make_interceptionsGraph(mapa)
    # Exibindo o grafo de interseções
    """ for no, adj in grafo.items():
        print(f"Nó {no} se conecta a:")
        for (dest, dist) in adj:
            print(f"  -> {dest} (distância = {dist})")
        print() """
    dead_ends = find_deadEnds(mapa)
    interceptions = find_interceptions(mapa)
    print_mapa_colorido(mapa, dead_ends, interceptions)
    find_pathDeadEnds(mapa)