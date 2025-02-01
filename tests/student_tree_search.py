from colorama import Fore, Style, Back
import math
import inspect
#ToDo: fazer pesquisa do menlhor caminho para passar por todas as comidas
#ToDo: ter em conta na pesquisa que por cada passo o corpo muda de posicao
#ToDo: atualizar as funcoes para terem em conta os numeros nos mapas em vez de ser so body e foods
#ToDo: experimentar fazer search_steps
#Valores do mapa:
    # 2->0  - food
    # 3->1  - superfood
    # 0->2  - vazio
    # 1->99 - parede
    # 4->98 - corpo
FOOD = 2
SUPERFOOD = 3
EMPTY = 0
WALL = 1
BODY = 4
FOOD_COST = -2
SUPERFOOD_COST = -1
EMPTY_COST = 1
WALL_COST = 999
BODY_COST = 998
SIGHT_POWER = 30
FADING_SIGHT_POWER = 0.5
MAP_CELL_SIZE = 5
SEARCH_TYPE = 'informed' #'breadth''depth''uniform''greedy''a*''informed'
SEARCH_IMPROVE = False
SEARCH_LIMIT = None
SEARCH_HEURISTIC = 'manhattan' # 'manhattan' 'euclidean' 'chebyshev'
class SearchDomain():
    def __init__(self, map = None, map_size = None, head=None, last_move=[1,0], body = None, bodys = [], foods = [], superfoods = [], walls = [], s_range = 0,traverse = None):
        self.map = map  #[y][x]
        self.map_size = map_size #[y,x]
        self.head = head
        self.last_move = last_move
        self.body = body
        self.bodys = bodys
        self.foods = foods
        self.superfoods = superfoods
        self.walls = walls
        self.s_range = s_range
        self.traverse = traverse
        self.list_sights = [] # [[power, [y,x], [y,x],...], [power, [y,x], [y,x],...],...]
        self.flag_sight = False

    def atualize_domain(self, state, move=None):
        def atualize_map_with_cost(y,x,value):
            if value == EMPTY:
                new_value = EMPTY_COST
            elif value == FOOD:
                new_value = FOOD_COST
            elif value == WALL:
                new_value = WALL_COST
            elif value == SUPERFOOD:
                new_value = SUPERFOOD_COST
            elif value == BODY:
                new_value = BODY_COST
            else:
                new_value = value
            self.map[y][x] = new_value
        def atualize_list_sight(pos):
            #print("self.list_sights: ", self.list_sights)
            if not self.flag_sight: #começo
                list_to_pop = []
                for i in range(len(self.list_sights)): #remover os que ja acabaram e diminuir o power dos que ainda estao a decorrer
                    #print("i: ",i)
                    #print("self.list_sights[i][0]: ", self.list_sights[i][0])
                    if self.list_sights[i][0] <= EMPTY_COST:
                        list_to_pop.append(i)
                    else:
                        self.list_sights[i][0] -= FADING_SIGHT_POWER
                for i in list_to_pop:
                    self.list_sights.pop(i)
                self.list_sights.append([SIGHT_POWER, pos])
                self.flag_sight = True
            elif self.flag_sight: #durante
                self.list_sights[-1].append(pos)
            else:
                print(f"{Fore.RED}ERROR: sem flag válido em add_sight_costs, flag: {self.flag_sight} {Style.RESET_ALL}")
        def add_sight_costs():
            for i in range(len(self.list_sights)):
                power = math.ceil(self.list_sights[i][0])
                for j in range(1, len(self.list_sights[i])):
                    pos = self.list_sights[i][j]
                    if self.map[pos[0]][pos[1]] != WALL_COST and self.map[pos[0]][pos[1]] != BODY_COST and self.map[pos[0]][pos[1]] != FOOD_COST and self.map[pos[0]][pos[1]] != SUPERFOOD_COST:
                        self.map[pos[0]][pos[1]] = power
        # atualizar mapa com state[map]
        if 'map' in state and 'size' in state and 'level' in state:
            self.map_size = state['size']
            self.map = state['map']
            #?: adicionar as comidas dadas inicialmente no mapa
            width, height = self.map_size
            for x in range(height):
                for y in range(width):
                    value = self.map[y][x]
                    if value == FOOD:
                        if [y, x] not in self.foods:
                            self.foods.append([y, x])
                    elif value == WALL:
                        if [y, x] not in self.walls:
                            self.walls.append([y, x])
                    elif value == SUPERFOOD:
                        if [y, x] not in self.superfoods:
                            self.superfoods.append([y, x])
                    elif value == BODY:
                        if [y, x] not in self.bodys:
                            self.bodys.append([y, x])
                    atualize_map_with_cost(y,x,value)
        # atualizar o mapa com state[sight]
        #ToDo: atualizar isto para multiplayer
        if 'players' in state:
            if 'range' in state:
                self.s_range = state['range']
            if 'traverse' in state:
                self.traverse = state['traverse']
            if 'body' in state:
                """ if self.head is None:
                    self.head = state['body'][0]
                #!: tambem podemos tentar idenficar a cabeça pelo sight (é a coordenada do meio)
                #!: estava a tentar dar track da cabeca apartir dos moviemntos mas estava a dar mal
                else:
                    if move is not None:
                        print("move domain: ", move)
                        if self.last_move != move:
                            self.head =  [self.head[0] + move[0] - self.last_move[0], self.head[1] + move[1]- self.last_move[0]]
                            self.last_move = move
                        else:
                            self.head =  [self.head[0] + move[0], self.head[1] + move[1]]
                    else:
                        move = self.last_move
                        print("move domain: ", move)
                        self.head =  [self.head[0] + move[0], self.head[1] + move[1]]
                    self.head = [self.head[0] % (self.map_size[0]), self.head[1] % (self.map_size[1])]
                #!: assim tambem nao da 
                else:
                    move = [state['body'][0][0] - self.head[0], state['body'][0][1] - self.head[1]]
                    print("move domain: ", move)
                    if self.traverse:
                        if move[0] == (self.map_size[0]+1):
                            move[0] = 1
                        elif move[0] == -(self.map_size[0]+1):
                            move[0] == -1
                        if move[1] == (self.map_size[1]+1):
                            move[1] = 1
                        elif move[1] == -(self.map_size[1]+1):
                            move[1] == -1
                    self.head =  [self.head[0] + move[0], self.head[1] + move[1]] """
                #ToDO: otimizar isto de atualizar corpo
                #?: remover do mapa o corpo antigo (quando a cobra cresce, o sight deixa de conseguir fazer isso)
                if self.body is not None:
                    for y, x in self.body:
                        self.map[y][x] = EMPTY_COST
                self.body = state['body']
                #?: adicionar o corpo novo ao mapa
                for y, x in self.body:
                    self.map[y][x] = BODY_COST
            # atualizar o mapa com state[sight]
            if 'sight' in state:
                sight = state['sight']
                self.flag_sight = False
                for y, x_info in sight.items():
                    for x, value in x_info.items():
                        int_y = int(y)
                        int_x = int(x)
                        pos = [int_y, int_x]
                        if self.map is None:
                            self.map = {}
                        self.map[int_y][int_x] = value
                        if value == FOOD: #?: ve food
                            if pos not in self.foods:
                                self.foods.append(pos)
                        if pos in self.foods and value != FOOD:
                            self.foods.remove(pos)
                        if value == SUPERFOOD: #?: ve superfood
                            if pos not in self.superfoods:
                                self.superfoods.append(pos)
                        if pos in self.superfoods and value != SUPERFOOD:
                            self.superfoods.remove(pos)
                        if value == WALL: #?: ve superfood
                            if pos not in self.walls:
                                self.walls.append(pos)
                        if pos in self.walls and value != WALL:
                            self.walls.remove(pos)
                        if value == BODY: #?: ve superfood
                            if pos not in self.bodys:
                                self.bodys.append(pos)
                        if pos in self.bodys and value != BODY:
                            self.bodys.remove(pos)
                        atualize_map_with_cost(int_y,int_x,value)
                        atualize_list_sight(pos)
                add_sight_costs()
                #print("self.list_sights: ", self.list_sights)
                #ToDo: corrigir isto para ter isto em conta:
                # 'snakes': [{'body': [[0, 11], [1, 11], [2, 11], [3, 11], [4, 11], [5, 11]],
                # 'sight': {'0': {'10': 0, '11': 4, '12': 0, '13': 0, '14': 0, '8': 0, '9': 0},
                #       '1': {'10': 0, '11': 4, '12': 0, '13': 0, '9': 0},
                #       '2': {'10': 0, '11': 4, '12': 0, '13': 0, '9': 0},
                #       '3': {'11': 4},
                #       '45': {'11': 0},
                #       '46': {'10': 0, '11': 0, '12': 0, '13': 0, '9': 0},
                #       '47': {'10': 0, '11': 0, '12': 0, '13': 0, '9': 0}},
                max_key_y = max(state['sight'], key=lambda k: max(state['sight'][k].values()))
                new_key_x = list(state['sight'][max_key_y].keys())[self.s_range]
                key_y = list(state['sight'].keys())[self.s_range]
                key_x = list(state['sight'][key_y].keys())[self.s_range]
                old_head = [int(key_y),int(key_x)]
                self.head = [int(max_key_y),int(new_key_x)]
                if self.head != old_head:
                    print(f"{Fore.RED}WARNING: head diferente do esperado em atualize_domain(), head {self.head}, old_head {old_head} (linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                if not self.head in self.body:
                    print(f"{Fore.RED}ERROR:head nao está no corpo em atualize_domain(), head {self.head}, body {self.body} (linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")

    # resultado de uma accao num estado, ou seja, o estado seguinte
    def actions_results(self, state):
        #ToDo: escluir as acoes que levam a choques com paredes e corpo
        actlist = []
        for dx, dy in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
            neighbor_cell = [state[0] + dx, state[1] + dy]
            #print("neighbor_cell: ", neighbor_cell)
            if self.traverse:
                neighbor_cell = [neighbor_cell[0] % (self.map_size[0]), neighbor_cell[1] % (self.map_size[1])]
            elif not (neighbor_cell[0] < self.map_size[0] and neighbor_cell[0] >= 0 and neighbor_cell[1] < self.map_size[1] and neighbor_cell[1] >= 0):
                neighbor_cell = None;
            if neighbor_cell is not None:
                #!: este if ˅ esta redundante mas é para garantir que nao ha erros
                if self.map[neighbor_cell[0]][neighbor_cell[1]] != WALL_COST and self.map[neighbor_cell[0]][neighbor_cell[1]] != BODY_COST and neighbor_cell not in self.body and neighbor_cell not in self.bodys and neighbor_cell not in self.walls :
                    actlist.append(neighbor_cell)
        return actlist 

    # custo de uma accao num estado
    def cost(self, state):
        return self.map[state[0]][state[1]]
    def is_path_clear(self, state, goal_pos):
        #!: nao é uma boa forma para usar na heuristica
        y0, x0 = state
        y1, x1 = goal_pos

        dx = x1 - x0
        dy = y1 - y0

        steps = max(abs(dx), abs(dy))
        if steps == 0:
            return True  # Estado atual é igual à posição do objetivo

        for i in range(1, steps):
            x = x0 + int(round(i * dx / steps))
            y = y0 + int(round(i * dy / steps))
            # Verifica se há parede ou corpo nesta posição
            cell_value = self.map[y][x]
            if cell_value in [1, 2]:  # Supondo que 1 é parede e 2 é corpo
                return False
        return True
    def heuristic1(self, state, goals):
        min_heuristic = float('inf')
        for goal_pos in goals:
            h = abs(goal_pos[0] - state[0]) + abs(goal_pos[1] - state[1])
            if h < min_heuristic:
                min_heuristic = h
        return min_heuristic
    def heuristic2(self, state, goals):
        min_heuristic = float('inf')
        for goal_pos in goals:
            h = abs(goal_pos[0] - state[0]) + abs(goal_pos[1] - state[1])
            if not self.is_path_clear(state, goal_pos):
                h += 10  # Valor de penalidade ajustável
            if h < min_heuristic:
                min_heuristic = h
        return min_heuristic
    def heuristic3(self, state, goals):
        min_heuristic = float('inf')
        for goal_pos in goals:
            h = abs(goal_pos[0] - state[0]) + abs(goal_pos[1] - state[1])
            # Se não houver linha de visão direta, aumenta a heurística
            if not self.line_of_sight(state, goal_pos):
                h *= 2  # Aumenta o custo heurístico
            if h < min_heuristic:
                min_heuristic = h
        return min_heuristic
    def heuristic4(self, state, goals):
        min_heuristic = float('inf')
        for goal_pos in goals:
            h = abs(goal_pos[0] - state[0]) + abs(goal_pos[1] - state[1])
            # Verifica células adjacentes para penalizar proximidade a paredes
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = state[0] + dx, state[1] + dy
                    if self.is_wall(nx, ny):
                        h += 1  # Penalidade por proximidade a uma parede
            if h < min_heuristic:
                min_heuristic = h
        return min_heuristic
    def heuristic5(self, state, goals):
        min_heuristic = float('inf')
        for goal_pos in goals:
            dx = goal_pos[0] - state[0]
            dy = goal_pos[1] - state[1]
            h = (dx ** 2 + dy ** 2) ** 0.5  # Distância euclidiana
            # Adiciona penalidade se houver paredes entre os pontos
            obstacles = self.count_walls_between(state, goal_pos)
            h += obstacles * 5  # Cada obstáculo adiciona uma penalidade
            if h < min_heuristic:
                min_heuristic = h
        return min_heuristic
    def heuristic6(self, state, goals):
        min_heuristic = float('inf')
        for goal_pos in goals:
            # Use um algoritmo rápido para estimar o caminho
            estimated_cost = self.estimate_cost(state, goal_pos)
            if estimated_cost < min_heuristic:
                min_heuristic = estimated_cost
        return min_heuristic
    def heuristic(self, state, goals, heuristic_type = SEARCH_HEURISTIC):
        #ToDo: na heuristica ter em conta se atravessa alguma parede ou corpo-> para fazer isto talvez alterar os valores das celulas em redor às paredes e corpos
        if heuristic_type == 'manhattan':
            return self.heuristic1(state, goals)
        else:
            print(f"{Fore.RED}ERROR: sem heuristica válida em heuristic, heuristic_type: {heuristic_type} (linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")

    # test if the given "goal" is satisfied in "state"
    def satisfies(self, state, goal):
        #print("satisfies:")
        for food_pos in goal:
            #print("state", state)
            #print("food_pos", food_pos)
            if state == food_pos:
                #print("TRUE")
                return True
        return False
    def print_mapa(self, path=None):
        if not self.map_size:
            print("Mapa não inicializado.")
            return
            
        width, height = self.map_size
        print("Tamanho do mapa:", self.map_size)
        print("Traverse:", self.traverse)
        print("Mapa:")
        print("print_mapa paht", path)
        
        # Itera sobre as linhas (y) e colunas (x) para exibir o mapa
        for x in range(height):
            row = []
            for y in range(width):
                # Obtém o valor da posição (x, y) ou 0 se não estiver presente
                value = self.map[y][x]
                size1 = math.floor((MAP_CELL_SIZE-len(str(value)))/2)
                size2 = MAP_CELL_SIZE - size1 - len(str(value))
                if path is not None and [y, x] in path:
                    colored_value = size1 * " "+f"{Back.MAGENTA}{value}{Style.RESET_ALL}"+size2 * " "
                elif value == EMPTY_COST:
                    colored_value = size1 * " "+f"{Style.RESET_ALL}{value}"+size2 * " "
                elif value == WALL_COST:
                    colored_value = size1 * " "+f"{Back.GREEN}{value}{Style.RESET_ALL}"+size2 * " "
                elif value == FOOD_COST:
                    colored_value = size1 * " "+f"{Back.RED}{value}{Style.RESET_ALL}"+size2 * " "
                elif value == SUPERFOOD_COST:
                    colored_value = size1 * " "+f"{Back.YELLOW}{value}{Style.RESET_ALL}"+size2 * " "
                elif value == BODY_COST:
                    colored_value = size1 * " "+f"{Back.BLUE}{value}{Style.RESET_ALL}"+size2 * " "
                elif value > EMPTY_COST and value <= SIGHT_POWER:
                    colored_value = size1 * " "+f"{Fore.CYAN}{value}{Style.RESET_ALL}"+size2 * " "
                else:
                    colored_value = size1 * " "+f"{Style.RESET_ALL}{value}"+size2 * " "

                #row.append(str(value))
                row.append(colored_value)
                """ for i in range(MAP_CELL_SIZE):
                    row.append(" ") """
            # Imprime a linha como uma string separada por espaços
            print(" ".join(row))
        

class SearchProblem:
    def __init__(self, domain, goal):
        self.domain = domain
        self.initial = domain.head
        self.goal = goal
        """ if domain.foods != []:
            self.goal = [domain.foods[0]]
        else:
            self.goal = [] """

    def goal_test(self, state):
        return self.domain.satisfies(state, self.goal)

# Nos de uma arvore de pesquisa
class SearchNode:
    def __init__(self, state, parent, depth, cost, heuristic): 
        self.state = state
        self.parent = parent
        self.depth = depth
        self.cost = cost
        self.heuristic = heuristic

    def __str__(self):
        return "no(" + str(self.state) + "," + str(self.parent) + ")"

    def __repr__(self):
        return str(self)

class SearchTree:
    # construtor
    def __init__(self, problem, strategy = SEARCH_TYPE, improve = SEARCH_IMPROVE, limit = SEARCH_LIMIT, heuristic = SEARCH_HEURISTIC): 
        #print("problem.initial: ", problem.initial)
        #print("problem.goal: ", problem.goal)
        self.problem = problem
        root = SearchNode(problem.initial, None, 0, 0, problem.domain.heuristic(problem.initial, problem.goal, heuristic))
        self.open_nodes = [root]
        self.strategy = strategy
        self.improve = improve
        self.limit = limit
        self.heuristic = heuristic 
        self.solution = None
        self.best_partial_solution = None
        self.length = None
        self.terminals = 0
        self.non_terminals = 0
        self.avg_branching = 0
        self.cost = None
        self.max_cost_nodes = [root]
        self.num_skipped = 0
        self.num_solution = 0
        self.path = None  

    # obter o caminho (sequencia de estados) da raiz ate um no
    def get_path(self, node):
        if node.parent == None:
            return [node.state]
        path = self.get_path(node.parent)
        path += [node.state]
        return(path)
    def verify_path(self, path, line):
        error_list = []
        error = False
        for step in path:
            for wall in self.problem.domain.walls:
                if step == wall:
                    error_list.append(['wall: ',step])
                    error = True
            for body in self.problem.domain.bodys:
                if step == body:
                    error_list.append(['bodys: ',step])
                    error = True
            for body in self.problem.domain.body:
                if step == body:
                    error_list.append(['body: ',step])
                    error = True
        if error:
            print(f"{Fore.RED}WARNING: verify_path = False , error_list: {error_list}, path: {path}(linha {line}){Style.RESET_ALL}")
            return False
        return True
    # procurar a solucao
    def search(self):
        #print("++++++++++++++++++++++++++++++++++++")
        #print("++++++++++++++++++++++++++++++++++++")
        #print("SEARCHING")
        if self.problem.initial == []:
            print(f"{Fore.RED}ERROR: sem problem.initial em SearchTree.search (linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
            return None
        if self.problem.goal == []:
            return None
        while self.open_nodes != []:
            self.terminals = len(self.open_nodes)
            node = self.open_nodes.pop(0)    
            #print("--------------------")        
            #print("node: ", node.state, "heuristic: ", node.heuristic, "cost: ", node.cost)
            if self.problem.goal_test(node.state):
                #print("SOLUTION>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                self.solution = node
                self.num_solution += 1
                self.length = self.solution.depth
                self.cost = node.cost
                if self.non_terminals != 0:
                    self.avg_branching = ((self.terminals + self.non_terminals) - 1) / self.non_terminals
                else:
                    self.avg_branching = 0
                if not self.improve:
                    path = self.get_path(self.solution)
                    self.path = path
                    #ToDo: eliminar a verificacao quando estiver tudo a funcionar bem
                    if self.verify_path(path[1:],inspect.currentframe().f_lineno):
                        return path
                    else:
                        return None
                    return path      
                continue
            if self.solution is not None and (node.cost + node.heuristic) >= self.solution.cost:
                self.num_skipped += 1
                continue  
            # Expansão do Node
            self.non_terminals += 1
            lnewnodes = []
            for newstate in self.problem.domain.actions_results(node.state):
                #print("newstate: ", newstate)
                #print("pre path: ", self.get_path(node))
                #ToDo: eliminar a verificacao quando estiver tudo a funcionar bem
                if not self.verify_path([newstate],inspect.currentframe().f_lineno):
                    continue
                if newstate not in self.get_path(node):
                    newnode = SearchNode(newstate, node, node.depth + 1, node.cost + self.problem.domain.cost(node.state), self.problem.domain.heuristic(newstate, self.problem.goal, self.heuristic))
                    lnewnodes.append(newnode)
                    #print("newnode_heuristic", newnode.heuristic)
                    #print("goal:",self.problem.goal)
                    if node.cost > self.max_cost_nodes[0].cost:
                        self.max_cost_nodes = [node]
                    elif node.cost == self.max_cost_nodes[0].cost:
                        self.max_cost_nodes.append(node)

            if self.limit == None:
                self.add_to_open(lnewnodes)
            else:
                if node.depth < self.limit:
                    self.add_to_open(lnewnodes)
                else:
                    if self.best_partial_solution is None or node.cost < self.best_partial_solution.cost:
                        self.best_partial_solution = node
        if self.improve and self.solution is not None:
            path = self.get_path(self.solution)
            self.path = path
            #ToDo: eliminar a verificacao quando estiver tudo a funcionar bem
            if self.verify_path(path[1:],inspect.currentframe().f_lineno):
                return path
            else:
                return None
            return path
        elif self.best_partial_solution is not None:
            path = self.get_path(self.best_partial_solution)
            self.path = path
            return path
        else:
            return None

    # juntar novos nos a lista de nos abertos de acordo com a estrategia
    def add_to_open(self,lnewnodes):
        if self.strategy == 'breadth':
            self.open_nodes.extend(lnewnodes)
        elif self.strategy == 'depth':
            self.open_nodes[:0] = lnewnodes
        elif self.strategy == 'uniform':
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda node: node.cost)
        elif self.strategy == 'greedy':
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda node: node.heuristic)
        elif self.strategy == 'a*':
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda node: (node.cost + node.heuristic, node.depth))
        elif self.strategy == 'informed':
            self.open_nodes = sorted(lnewnodes, key=lambda node: (node.cost + node.heuristic, node.depth)) + self.open_nodes

    def get_stats(self):
        #print(f"{Fore.BLUE}STRATEGY: {self.strategy}, IMPROVE: {self.improve}, LIMIT: {self.limit}{Style.RESET_ALL}")
        if self.solution != None:
            if self.solution.state in self.problem.goal:
                solution = f"SUCCESS"
            else:
                solution = f"FAIL"
        else:
            solution = f"FAIL"
        if self.cost != None:
            cost = self.cost
        else:
            cost = "None"
        if self.length != None:
            length = self.length
        else:
            length = "None"
        if self.path != None:
            path = self.path
        else:
            path = "None"
        if self.limit != None:
            limit = self.limit
        else:
            limit = "None"
        
        stats = {
            #'Title':f"{self.strategy}, {self.improve}, {self.limit}",
            'Strategy': self.strategy,
            'Improve': self.improve,
            'Limit': limit,
            'Heuristic': self.heuristic,
            'Solution': solution,
            'Terminals': self.terminals,
            'Non-terminals': self.non_terminals,
            'Avg Branching': self.avg_branching,
            'Cost': cost,
            'Length': length,
            'Num Skipped':  self.num_skipped,
            'Num Solutions': self.num_solution,
            'elapsed_time': None,
            'Path': path,
            # Adicione outras estatísticas que desejar
        }
        return stats
    