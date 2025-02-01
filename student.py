"""Example client."""
import asyncio
import getpass
import json
import os

#+: bibliotecas adicionadas:
from collections import deque, defaultdict
import math
import websockets

FOOD = 2
SUPERFOOD = 3
EMPTY = 0
WALL = 1
BODY = 4
FOOD_COST = -2
SUPERFOOD_COST = -1
EMPTY_COST = 1
WALL_COST = float("inf")#999
BODY_COST = float("inf")#998
SIGHT_POWER = 30
FADING_SIGHT_POWER = 0.5
HEAD_POWER = 200
FADING_HEAD_POWER = 5

EXPLORE_POS_SPACE = 6 
EXPLORE_POWER = 128 #(24/3 * 48/3)
FADING_EXPLORE_POWER = 1

LAST_PATH_POWER = 5
LAST_PATH_EQ = 'division' # 'addition' 'multiplication' 'subtraction' 'division'

MAP_CELL_SIZE = 5

SEARCH_TYPE = 'informed'#'informed_chd'#'informed' #'breadth''depth''uniform''greedy''a*''informed' 'informed_chd' 'informed_mul'
SEARCH_IMPROVE = False
SEARCH_LIMIT = None
SEARCH_HEURISTIC = 'manhattan' # 'manhattan' 'euclidean' 'chebyshev'
DOMAIN_CHUNCK_SIZE = 10 #?: para evitar pesquisas muito grandes
CHUNKS_ON = True

# quando locked_goal_on == True:
#   quando numa pesquisa (com um ou varios goals) chega a um dos goals:
#       guarda esse goal como locked_goal e so faz pesquisa para esse goal
#       enquanto domain.head != locked_goal vai continuar com o mesmo locked_goal
#           caso contrario locked_goal = None
LOCKED_GOAL_ON = True 

FLOOD_COST = 5
ARROUND_BODY_COST = 500

class SearchDomain(): 
    def __init__(self, map = None, map_size = None, head=None, last_move=[1,0], body = None, bodys = [], foods = [], superfoods = [], walls = set(), s_range = 0,traverse = None,chunks_on=CHUNKS_ON, chunk_size = DOMAIN_CHUNCK_SIZE, explore_pos_space = EXPLORE_POS_SPACE, locked_goal_on = LOCKED_GOAL_ON, last_path_power = LAST_PATH_POWER, last_path_eq = LAST_PATH_EQ):
        self.heuristics = ["manhattan"]
        self.map = map  #[y][x]
        self.map_size = map_size #[y,x]
        self.map_limits = None
        self.map_floodfill = None
        self.path_floodfill = None 
        self.floodfill_max = None #para print
        self.floodfill_min = None #para print
        self.use_floodfill_just_for_deadends = False
        self.floodfill_calc_path = False # so calcula se self.use_floodfill_just_for_deadends = True
        self.flood_deadends = set()
        self.head = head
        self.last_move = last_move
        self.body = body
        self.bodys = bodys
        self.foods = foods
        self.superfoods = superfoods
        self.walls = walls # set()
        self.s_range = s_range
        self.traverse = traverse
        self.list_sights = [] # [[power, [y,x], [y,x],...], [power, [y,x], [y,x],...],...]
        self.flag_sight = False # para assinalar que esta no comeco de uma nova [power, [y,x], [y,x],...], logo a primeira coisa a adicionar é o power
        self.list_heads = [] # [[power, [y,x]], [power, [y,x]],...] # para marcar pesos de onde a cobra passou para evitar loops
        self.head_sight = False
        self.chunks_on = chunks_on
        self.chunk_size = chunk_size
        self.current_head_chunk = None
        self.chunked_limits = None # set of limits of the chunks ((y,x),(y,x),...)
        self.chunk_limits_teleport = None
        self.really_satisfies = None # por causa dos chunks, para ver se realmente chegou ao objetivo 
        self.wander = False # para o domain saber quando deve fazer as operacoes relacionadas 
        #?: explorar os pontos que estar na possible_explore_positions e com o power (proveniente de explored_positions)
        self.explore_pos_space = explore_pos_space
        self.all_explore_positions = []
        self.possible_explore_positions = [] # baseado em self.all_explore_positions mas retirando os casos tendo em conta o state
        self.explored_positions = [] #[[power, [y,x]], [power, [y,x]],...] # para marcar as posicoes ja exploradas e vao desaparecendo
        
        self.locked_goal_on = locked_goal_on
        self.locked_goal = None
        #+: tem em conta a path anterior no calculo do custo, se a path pertencer a pesquisa atual
        self.last_path_on = True
        self.last_path = None # para ter em conta no calculo do custo
        self.last_path_power = last_path_power
        self.last_path_eq = last_path_eq
        self.arround_obj= set()
    
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
                        if self.list_sights[i][0] <= EMPTY_COST:
                            list_to_pop.append(i)
                for i in list_to_pop:
                    self.list_sights.pop(i)
                self.list_sights.append([SIGHT_POWER, pos])
                self.flag_sight = True
            elif self.flag_sight: #durante
                self.list_sights[-1].append(pos)
        def add_sight_costs():#+: adiciona os custos ao mapa
            for i in range(len(self.list_sights)):
                power = math.ceil(self.list_sights[i][0])
                for j in range(1, len(self.list_sights[i])):
                    pos = self.list_sights[i][j]
                    if self.map[pos[0]][pos[1]] != WALL_COST and self.map[pos[0]][pos[1]] != BODY_COST and self.map[pos[0]][pos[1]] != FOOD_COST and self.map[pos[0]][pos[1]] != SUPERFOOD_COST:
                        self.map[pos[0]][pos[1]] = power
        def atualize_list_head(pos):
            if not self.flag_head: #começo
                list_to_pop = []
                for i in range(len(self.list_heads)): #remover os que ja acabaram e diminuir o power dos que ainda estao a decorrer
                    #print("i: ",i)
                    #print("self.list_heads[i][0]: ", self.list_heads[i][0])
                    if self.list_heads[i][0] <= EMPTY_COST:
                        list_to_pop.append(i)
                    else:
                        self.list_heads[i][0] -= FADING_HEAD_POWER
                for i in list_to_pop:
                    self.list_heads.pop(i)
                self.list_heads.append([HEAD_POWER, pos])
                self.flag_head = True
            elif self.flag_head: #durante
                self.list_heads[-1].append(pos)
        def add_head_costs(): #+: adiciona os custos ao mapa
            for i in range(len(self.list_heads)):
                power = math.ceil(self.list_heads[i][0])
                for j in range(1, len(self.list_heads[i])):
                    pos = self.list_heads[i][j]
                    if self.map[pos[0]][pos[1]] != WALL_COST and self.map[pos[0]][pos[1]] != BODY_COST and self.map[pos[0]][pos[1]] != FOOD_COST and self.map[pos[0]][pos[1]] != SUPERFOOD_COST:
                        self.map[pos[0]][pos[1]] = power
        def initAdd_explored_positions(pos):
            self.explored_positions.append([0,pos])
            
        #+: atualiza os custos das posicoes exploradas, trata do caso da pos nao pertencer a lista
        def atualize_explored_positions(pos_list): #?: tem que ser uma lista de posicoes pq se atualizar a cada posicao inserida do sight entao por cada iteracao vai decrementar o power o numero de posicoes sight que existe
            for i in range(len(self.explored_positions)): #remover os que ja acabaram e diminuir o power dos que ainda estao a decorrer
                #print("i: ",i)
                #print("self.explored_positions[i][0]: ", self.explored_positions[i][0])
                if self.explored_positions[i][1] in pos_list: #?: atualiza o custo da posicao que foi recentemente explorada
                    self.explored_positions[i][0] = EXPLORE_POWER
                #!: este elif parece redundante mas para prevenir deixa estar
                elif self.explored_positions[i][0] <= EMPTY_COST: #?: reseta o custo das posicoes que ja foram exploradas a muito tempo
                    self.explored_positions[i][0] = 0
                else:
                    self.explored_positions[i][0] -= FADING_EXPLORE_POWER #?: diminui o custo das posicoes que fora exploradas
                    if self.explored_positions[i][0] <= EMPTY_COST: #?: reseta caso o custo seja menor que 0, ou seja, exploradas a muito tempo
                        self.explored_positions[i][0] = 0
        # atualizar mapa com state[map]
        #+: Na primeira iteracao com o state: popular o self.map com pesos, adicionar self.all_explore_positions tendo em conta o mapa
        if 'map' in state and 'size' in state and 'level' in state:
            self.map_size = state['size']
            self.map = state['map']
            width, height = self.map_size
            for x in range(height):
                for y in range(width):
                    value = self.map[y][x]
                    pos = [y,x]
                    tpos = (y,x)
                    if value == WALL:
                        if tpos not in self.walls:
                            self.walls.add(tpos)
                    elif value == BODY:
                        if pos not in self.bodys:
                            self.bodys.append(pos)
                    elif value == FOOD:
                        if pos not in self.foods:
                            self.foods.append(pos)
                    elif value == SUPERFOOD:
                        if pos not in self.superfoods:
                            self.superfoods.append(pos)
                    if pos not in self.bodys and tpos not in self.walls:
                        if (y % self.explore_pos_space == 1) and (x % self.explore_pos_space == 1):
                            self.all_explore_positions.append(pos)
                            initAdd_explored_positions(pos)
                    atualize_map_with_cost(y,x,value)
            self.map_limits = [[self.map_size[0]-1,self.map_size[1]-1],[0,0]]
            print("all_explore_positions: ", self.all_explore_positions)
        # atualizar o mapa com state[sight]

        if 'players' in state:
            self.arround_obj = set()
            if 'range' in state:
                self.s_range = state['range']
            if 'traverse' in state:
                self.traverse = state['traverse']
            if 'body' in state:
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
                self.bodys = [] # resetar porque podem-se mover
                sight_pos = []
                for y, x_info in sight.items():
                    for x, value in x_info.items():
                        int_y = int(y)
                        int_x = int(x)
                        pos = [int_y, int_x]
                        tpos = (int_y, int_x)
                        sight_pos.append(pos)
                        if self.map is None:
                            self.map = {}
                        self.map[int_y][int_x] = value
                        if value == FOOD: #?: atualiza self.foods, nao precisa de retirar da lista 
                            if pos not in self.foods:
                                self.foods.append(pos)
                        if pos in self.foods and value != FOOD:
                            self.foods.remove(pos)
                        if value == SUPERFOOD: #?: ve superfood
                            if pos not in self.superfoods:
                                self.superfoods.append(pos)
                        if pos in self.superfoods and value != SUPERFOOD:
                            self.superfoods.remove(pos)
                        
                        if value == BODY: #?:
                            if pos not in self.bodys:
                                self.bodys.append(pos)
                        if pos in self.bodys and value != BODY:
                            self.bodys.remove(pos)
                        atualize_map_with_cost(int_y,int_x,value)
                        atualize_list_sight(pos)
                atualize_explored_positions(sight_pos)
                add_sight_costs()
                max_key_y = max(state['sight'], key=lambda k: len(state['sight'][k]))
                new_key_x = list(state['sight'][max_key_y].keys())[self.s_range]
                # old head:
                #key_y = list(state['sight'].keys())[self.s_range]
                #key_x = list(state['sight'][key_y].keys())[self.s_range]
                #old_head = [int(key_y),int(key_x)]
                #self.head = [int(max_key_y),int(new_key_x)]
                self.head = [int(max_key_y),int(new_key_x)]
                self.flag_head = False
                atualize_list_head(self.head)
                add_head_costs()
                #print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>head: ", self.head)
                if state['sight'][max_key_y][new_key_x] != 4:
                    print(f"ERROR: no sight a cabeça nao esta com o valor de body (4) , head: {self.head}, state['sight'][max_key_y][new_key_x]: {state['sight'][max_key_y][new_key_x]})")
                if not self.head in self.body:
                    print(f"ERROR:head nao está no corpo em atualize_domain(), head {self.head}, body {self.body} ")
            #+: para atualizar o self.new_explored_positions
            possible_explore_positions = []
            #print("self.all_explore_positions", self.all_explore_positions)
            for explore_position in self.all_explore_positions:
                if (explore_position not in self.body) and (explore_position not in self.bodys) and (tuple(explore_position) not in self.walls):
                    possible_explore_positions.append(explore_position)
                    #print("explore_position", explore_position)
            #print("possible_explore_positions: ",possible_explore_positions)
            self.possible_explore_positions = possible_explore_positions
            
            self.map_floodfill = None
            self.path_floodfill = None
            self.flood_deadends = set()
            if self.use_floodfill_just_for_deadends:
                self.bfs_floodfill([0,0],self.map_limits[0])
            else:
                self.flood_fill(self.head, self.foods)
            
            for bp in self.body:
                for dx, dy in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
                    neighbor_cell = [bp[0] + dy, bp[1] + dx]
                    #print("neighbor_cell: ", neighbor_cell)
                    if self.traverse:
                        neighbor_cell = [neighbor_cell[0] % (self.map_size[0]), neighbor_cell[1] % (self.map_size[1])]
                    elif not (neighbor_cell[0] < self.map_size[0] and neighbor_cell[0] >= 0 and neighbor_cell[1] < self.map_size[1] and neighbor_cell[1] >= 0):
                        neighbor_cell = None;
                    for dx, dy in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
                        close_to_head = [self.head[0] + dy, self.head[1] + dx]
                        if neighbor_cell == close_to_head:
                            neighbor_cell = None;
                    if neighbor_cell is not None:
                        self.arround_obj.add(tuple(neighbor_cell))
            for bp in self.bodys:
                for dx, dy in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
                    neighbor_cell = [bp[0] + dy, bp[1] + dx]
                    #print("neighbor_cell: ", neighbor_cell)
                    if self.traverse:
                        neighbor_cell = [neighbor_cell[0] % (self.map_size[0]), neighbor_cell[1] % (self.map_size[1])]
                    elif not (neighbor_cell[0] < self.map_size[0] and neighbor_cell[0] >= 0 and neighbor_cell[1] < self.map_size[1] and neighbor_cell[1] >= 0):
                        neighbor_cell = None;
                    for dx, dy in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
                        close_to_head = [self.head[0] + dy, self.head[1] + dx]
                        if neighbor_cell == close_to_head:
                            neighbor_cell = None;
                    if neighbor_cell is not None:
                        self.arround_obj.add(tuple(neighbor_cell))
            

        for wall_pos in self.walls:
            self.map[wall_pos[0]][wall_pos[1]] = WALL_COST
        for wp in self.walls:
            for dx, dy in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
                neighbor_cell = [wp[0] + dy, wp[1] + dx]
                #print("neighbor_cell: ", neighbor_cell)
                if self.traverse:
                    neighbor_cell = [neighbor_cell[0] % (self.map_size[0]), neighbor_cell[1] % (self.map_size[1])]
                elif not (neighbor_cell[0] < self.map_size[0] and neighbor_cell[0] >= 0 and neighbor_cell[1] < self.map_size[1] and neighbor_cell[1] >= 0):
                    neighbor_cell = None;
                if neighbor_cell is not None:
                    self.arround_obj.add(tuple(neighbor_cell))
           
        
    # resultado de uma accao num estado, ou seja, o estado seguinte
    def actions_results(self, state):
        actlist = []
        if state[1] > self.map_size[1]-1:
            print(f"ERROR: state tem a ordem contraria , state: {state} ")
        for dx, dy in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
            neighbor_cell = [state[0] + dy, state[1] + dx]
            #print("neighbor_cell: ", neighbor_cell)
            if self.traverse:
                neighbor_cell = [neighbor_cell[0] % (self.map_size[0]), neighbor_cell[1] % (self.map_size[1])]
            elif not (neighbor_cell[0] < self.map_size[0] and neighbor_cell[0] >= 0 and neighbor_cell[1] < self.map_size[1] and neighbor_cell[1] >= 0):
                neighbor_cell = None;
            if neighbor_cell is not None:
                if self.map[neighbor_cell[0]][neighbor_cell[1]] != WALL_COST and self.map[neighbor_cell[0]][neighbor_cell[1]] != BODY_COST and neighbor_cell not in self.body and neighbor_cell not in self.bodys and tuple(neighbor_cell) not in self.walls :
                    if self.map_floodfill is not None:
                        if self.map_floodfill[neighbor_cell[0]][neighbor_cell[1]] is not None:
                            actlist.append(neighbor_cell)
                    else:
                        actlist.append(neighbor_cell)
        return actlist 

    # custo de uma accao num estado
    def cost(self, state, goals=None):
        def floodfill_cost(cost,state):
            #print("cost: ", cost)
            if not self.use_floodfill_just_for_deadends and cost != float("inf"):   
                if self.map_floodfill is not None:
                    f_cost = self.map_floodfill[state[0]][state[1]]
                    #print("f_cost: ", f_cost)
                    if (f_cost is None) or ((state[0],state[1]) in self.flood_deadends):
                        cost = float("inf")
                    else:
                        cost += f_cost
                else:
                    if (state[0],state[1]) in self.flood_deadends:
                        cost = float("inf")
                    print(f"ERROR: sem map_floodfill válido em cost, state: {state} ")
            if self.use_floodfill_just_for_deadends and cost != float("inf"):
                if self.map_floodfill is not None:
                    f_cost = self.map_floodfill[state[0]][state[1]]
                    if f_cost is None or ((state[0],state[1]) in self.flood_deadends):
                        cost = float("inf")
                else:
                    if (state[0],state[1]) in self.flood_deadends:
                        cost = float("inf")
                    print(f"ERROR: sem map_floodfill válido em cost, state: {state} ")
            return cost
        def last_path_cost(cost,state,goals):
            #print(cost)
            if self.last_path_on and self.last_path is not None and goals is not None and len(goals) > 0 and cost != float("inf"):
                #print("inside")
                flag_goal_in_last_path = False
                for goal in goals:
                    if goal in self.last_path:
                        flag_goal_in_last_path = True
                        break
                if ((state in self.last_path) and flag_goal_in_last_path):
                    if self.last_path_eq == 'addition':
                        cost += self.last_path_power
                    elif self.last_path_eq == 'multiplication':
                        cost *= self.last_path_power
                    elif self.last_path_eq == 'subtraction':
                        cost -= self.last_path_power
                    elif self.last_path_eq == 'division':
                        cost /= self.last_path_power
                    else:
                        print(f"ERROR: sem last_path_eq válido em cost, last_path_eq: {self.last_path_eq} ")
                #print(flag_goal_in_last_path)
            #print(cost)
            return cost
        def arround_body_cost(cost,state):
            if tuple(state) in self.arround_obj:
                cost += ARROUND_BODY_COST
            return cost
        cost = self.map[state[0]][state[1]]
        #print("cost: ", cost)
        if (state in self.body or state  in self.bodys or tuple(state) in self.walls):
            cost = float("inf")    
        else:

            cost = floodfill_cost(cost,state)
            cost = last_path_cost(cost,state,goals)
            #cost = floodfill_cost(cost,state)
            cost = arround_body_cost(cost,state)
         
        return cost
    def is_path_clear(self, state, goal_pos):
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
        if self.traverse:
            min_heuristic = float('inf')
            width, height = self.map_size
            for goal_pos in goals:
                dx = abs(state[0] - goal_pos[0])
                dx = min(dx, width - dx)
                dy = abs(state[1] - goal_pos[1])
                dy = min(dy, height - dy)
                h = dx + dy
                if h < min_heuristic:
                    min_heuristic = h
            return min_heuristic
        else:
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
        if heuristic_type == self.heuristics[0]:
            return self.heuristic1(state, goals)
        else:
            print(f"ERROR: sem heuristica válida em heuristic, heuristic_type: {heuristic_type} ()")

    def atualize_chunked_limits(self):
        def get_chunked_limits(chunk_limits_teleport, chunk_limits, map_limits):
            print("chunk_limits_teleport: ",chunk_limits_teleport)
            print("chunk_limits: ",chunk_limits)
            def get_extensive_state_limits(case,new_state_limits):
                print("case: ",case)
                extensive_state_limits_set = set()
                print("new_state_limits: ",new_state_limits)
                print("case: ",case)
                if case == 0 or case == 9:
                    for x in range(new_state_limits[0][1][1],  new_state_limits[0][0][1]+1):
                        """ if (new_state_limits[0][0][0] == map_limits[0][0] ) and  ( new_state_limits[0][0][1] == map_limits[0][1]): # y  max e x max
                            continue
                        if (new_state_limits[0][1][0] == map_limits[0][0] ) and  ( new_state_limits[0][0][1] == map_limits[0][1]): # y  min e x max
                            continue
                        if (new_state_limits[0][1][0] == map_limits[0][0] ) and  ( new_state_limits[0][1][1] == map_limits[0][1]): # y  min e x min
                            continue
                        if (new_state_limits[0][0][0] == map_limits[0][0] ) and  ( new_state_limits[0][1][1] == map_limits[0][1]): # y  max e x min
                            continue """
                        if (new_state_limits[0][0][0] == map_limits[0][0] ):  
                            if (x != new_state_limits[0][1][1] and x != new_state_limits[0][0][1]):
                                extensive_state_limits_set.add((new_state_limits[0][1][0],x))
                                continue
                        if ( new_state_limits[0][1][0] == map_limits[1][0]): 
                            if (x != new_state_limits[0][1][1] and x != new_state_limits[0][0][1]):
                                extensive_state_limits_set.add((new_state_limits[0][0][0],x))
                                continue
                        extensive_state_limits_set.add((new_state_limits[0][0][0],x))
                        extensive_state_limits_set.add((new_state_limits[0][1][0],x))
                    for y in range(new_state_limits[0][1][0],  new_state_limits[0][0][0]):
                        """ if (new_state_limits[0][0][0] == map_limits[0][0] ) and  ( new_state_limits[0][0][1] == map_limits[0][1]): # y  max e x max
                            continue
                        if (new_state_limits[0][1][0] == map_limits[0][0] ) and  ( new_state_limits[0][0][1] == map_limits[0][1]): # y  min e x max
                            continue
                        if (new_state_limits[0][1][0] == map_limits[0][0] ) and  ( new_state_limits[0][1][1] == map_limits[0][1]): # y  min e x min
                            continue
                        if (new_state_limits[0][0][0] == map_limits[0][0] ) and  ( new_state_limits[0][1][1] == map_limits[0][1]): # y  max e x min
                            continue """
                        if (new_state_limits[0][0][1] == map_limits[0][1] ):
                            if (y != new_state_limits[0][1][0] and y != new_state_limits[0][0][0]):
                                extensive_state_limits_set.add((y,new_state_limits[0][1][1]))  
                                continue   
                        if ( new_state_limits[0][1][1] == map_limits[1][1]):
                            if (y != new_state_limits[0][1][0] and y != new_state_limits[0][0][0]):
                                extensive_state_limits_set.add((y,new_state_limits[0][0][1]))
                                continue
                        extensive_state_limits_set.add((y,new_state_limits[0][0][1]))
                        extensive_state_limits_set.add((y,new_state_limits[0][1][1]))    
                    if tuple(map_limits[0]) in extensive_state_limits_set:
                        extensive_state_limits_set.remove(tuple(map_limits[0]))
                    if tuple(map_limits[1]) in extensive_state_limits_set:
                        extensive_state_limits_set.remove(tuple(map_limits[1]))
                    if (map_limits[0][0],map_limits[1][1]) in extensive_state_limits_set:
                        extensive_state_limits_set.remove((map_limits[0][0],map_limits[1][1]))
                    if (map_limits[1][0],map_limits[0][1]) in extensive_state_limits_set:
                        extensive_state_limits_set.remove((map_limits[1][0],map_limits[0][1]))
                if case == 1 or case == 2 or case == 3 or case == 4:
                    #1º valores y maiores primeiro , 2º valores x maiores primeiro 
                    for y in range(new_state_limits[0][0][0],  map_limits[0][0]+1): # certo
                        extensive_state_limits_set.add((y,new_state_limits[0][0][1]))
                        extensive_state_limits_set.add((y,new_state_limits[0][1][1]))
                    for y in range(map_limits[1][0], new_state_limits[1][1][0]+1):
                        extensive_state_limits_set.add((y,new_state_limits[1][0][1]))
                        extensive_state_limits_set.add((y,new_state_limits[1][1][1]))
                    
                    for x in range(new_state_limits[0][0][1],  map_limits[0][1]+1):
                        extensive_state_limits_set.add((new_state_limits[0][0][0],x))
                        extensive_state_limits_set.add((new_state_limits[1][1][0],x))
                    for x in range(map_limits[1][1], new_state_limits[0][1][1]+1):
                        extensive_state_limits_set.add((new_state_limits[0][1][0],x))
                        extensive_state_limits_set.add((new_state_limits[1][1][0],x))
                elif case == 7 or case == 8:
                    for y in range(new_state_limits[0][0][0],  map_limits[0][0]+1):
                        extensive_state_limits_set.add((y,new_state_limits[0][0][1]))
                        extensive_state_limits_set.add((y,new_state_limits[0][1][1]))
                    for y in range(map_limits[1][0], new_state_limits[1][1][0]+1):
                        extensive_state_limits_set.add((y,new_state_limits[1][0][1]))
                        extensive_state_limits_set.add((y,new_state_limits[1][1][1]))
                    
                    for x in range(new_state_limits[0][1][1],  new_state_limits[0][0][1]+1):
                        extensive_state_limits_set.add((new_state_limits[0][0][0],x))
                        extensive_state_limits_set.add((new_state_limits[1][0][0],x))
                elif case == 5 or case == 6:
                    for y in range(new_state_limits[1][1][0],  new_state_limits[0][0][0]+1):
                        extensive_state_limits_set.add((y,new_state_limits[0][0][1]))
                        extensive_state_limits_set.add((y,new_state_limits[0][1][1]))
                    
                    for x in range(new_state_limits[0][0][1],  map_limits[0][1]+1):
                        extensive_state_limits_set.add((new_state_limits[0][0][0],x))
                        extensive_state_limits_set.add((new_state_limits[1][1][0],x))
                    for x in range(map_limits[1][1], new_state_limits[0][1][1]+1):
                        extensive_state_limits_set.add((new_state_limits[0][1][0],x))
                        extensive_state_limits_set.add((new_state_limits[1][1][0],x))
                print("extensive_state_limits_set: ",extensive_state_limits_set)
                return extensive_state_limits_set

            new_state_limits = []
            caso = 0
            # Caso 1: [3,2]
            if len(chunk_limits) == 1:
                caso = 0
                new_state_limits = chunk_limits
                #print(f"WARNING: ... , case = 0,  chunk_limits: {chunk_limits} , new_state_limits: {new_state_limits} , chunk_limits_teleport: {chunk_limits_teleport} ")
            elif len(chunk_limits) == 2:
                if (chunk_limits_teleport[0][0] <= map_limits[0][0] and
                    chunk_limits_teleport[0][1] < map_limits[0][1] and
                    chunk_limits_teleport[1][0] < map_limits[1][0] and
                    chunk_limits_teleport[1][1] < map_limits[1][1]):
                    caso = 1
                    #new_state_limits = [[[chunk_limits[0][0], chunk_limits[0][1]], [0, 0]], [[map_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], 0]], [[chunk_limits[0][0], map_limits[0][1]], [0, chunk_limits[1][1]]], [[map_limits[0][0], map_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]]]
                    #new_state_limits=  [[[chunk_limits[0][0], chunk_limits[0][1]]], [[chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[1][1]]], [[chunk_limits[1][0], chunk_limits[1][1]]]]
                    new_state_limits=  [[[chunk_limits[1][0], chunk_limits[1][1]], [chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[1][1]], [chunk_limits[0][0], chunk_limits[0][1]]]]    # Caso 2: [3,21]
                
                # Caso 2: [3,21]
                elif (chunk_limits_teleport[0][0] <= map_limits[0][0] and
                    chunk_limits_teleport[0][1] > map_limits[0][1] and
                    chunk_limits_teleport[1][0] < map_limits[1][0] and
                    chunk_limits_teleport[1][1] >= map_limits[1][1]):
                    caso = 2
                    #new_state_limits = [[[chunk_limits[0][0], map_limits[0][1]], [0, chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[0][1]], [0, 0]], [[map_limits[0][0], map_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[map_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], 0]]]
                    #new_state_limits=  [[[chunk_limits[0][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[0][1]]], [[chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[1][0], chunk_limits[0][1]]]]
                    new_state_limits=  [[[chunk_limits[1][0], chunk_limits[1][1]], [chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[1][1]], [chunk_limits[0][0], chunk_limits[0][1]]]]    
                # Caso 3: [44,2]
                elif (chunk_limits_teleport[0][0] > map_limits[0][0] and
                    chunk_limits_teleport[0][1] < map_limits[0][1] and
                    chunk_limits_teleport[1][0] >= map_limits[1][0] and
                    chunk_limits_teleport[1][1] < map_limits[1][1]):
                    caso = 3
                    #new_state_limits = [[[map_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], 0]], [[chunk_limits[0][0], chunk_limits[0][1]], [0, 0]], [[map_limits[0][0], map_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], map_limits[0][1]], [0, chunk_limits[1][1]]]]
                    #new_state_limits=  [[[chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[0][1]]], [[chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[1][1]]]]
                    new_state_limits=  [[[chunk_limits[1][0], chunk_limits[1][1]], [chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[1][1]], [chunk_limits[0][0], chunk_limits[0][1]]]]    
                # Caso 4: [44,21]
                elif (chunk_limits_teleport[0][0] > map_limits[0][0] and
                    chunk_limits_teleport[0][1] > map_limits[0][1] and
                    chunk_limits_teleport[1][0] >= map_limits[1][0] and
                    chunk_limits_teleport[1][1] >= map_limits[1][1]):
                    caso = 4
                    #new_state_limits = [[[map_limits[0][0], map_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], map_limits[0][1]], [0, chunk_limits[1][1]]], [[map_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], 0]], [[chunk_limits[0][0], chunk_limits[0][1]], [0, 0]]]
                    #new_state_limits=  [[[chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[1][1]]], [[chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[0][1]]]]
                    new_state_limits=  [[[chunk_limits[1][0], chunk_limits[1][1]], [chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[1][1]], [chunk_limits[0][0], chunk_limits[0][1]]]]    
                # Caso 5: [24,2]
                elif (chunk_limits_teleport[0][0] <= map_limits[0][0] and
                    chunk_limits_teleport[0][1] < map_limits[0][1] and
                    chunk_limits_teleport[1][0] >= map_limits[1][0] and
                    chunk_limits_teleport[1][1] < map_limits[1][1]):
                    """ new_state_limits = [
                        [[chunk_limits[0][0], chunk_limits[0][1]], 
                        [chunk_limits[1][0], 0]],
                        [[chunk_limits[0][0], map_limits[0][1]], 
                        [chunk_limits[1][0], chunk_limits[1][1]]]
                    ] """
                    caso = 5
                    #new_state_limits=  [[[chunk_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[1][1]], [chunk_limits[1][0], chunk_limits[1][1]]]]
                    new_state_limits=  [[[chunk_limits[0][0], chunk_limits[1][1]], [chunk_limits[0][0], chunk_limits[0][1]]], [[chunk_limits[1][0], chunk_limits[1][1]], [chunk_limits[1][0], chunk_limits[0][1]]]]    
                # Caso 6: [24,21]
                elif (chunk_limits_teleport[0][0] <= map_limits[0][0] and
                    chunk_limits_teleport[0][1] > map_limits[0][1] and
                    chunk_limits_teleport[1][0] >= map_limits[1][0] and
                    chunk_limits_teleport[1][1] >= map_limits[1][1]):
                    """ new_state_limits = [
                        [[chunk_limits[0][0], map_limits[0][1]], 
                        [chunk_limits[1][0], chunk_limits[1][1]]],
                        [[chunk_limits[0][0], chunk_limits[0][1]], 
                        [chunk_limits[1][0], 0]]
                    ] """
                    caso = 6
                    #new_state_limits=  [[[chunk_limits[0][0], chunk_limits[1][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], chunk_limits[0][1]]]]
                    new_state_limits=  [[[chunk_limits[0][0], chunk_limits[1][1]], [chunk_limits[0][0], chunk_limits[0][1]]], [[chunk_limits[1][0], chunk_limits[1][1]], [chunk_limits[1][0], chunk_limits[0][1]]]]    
                # caso 7: [3,12]
                elif (chunk_limits_teleport[0][0] <= map_limits[0][0] and
                    chunk_limits_teleport[0][1] < map_limits[0][1] and
                    chunk_limits_teleport[1][0] < map_limits[1][0] and
                    chunk_limits_teleport[1][1] >= map_limits[1][1]):
                    """ new_state_limits = [
                        [[chunk_limits[0][0], chunk_limits[0][1]], 
                        [0, chunk_limits[1][1]]],
                        [[map_limits[0][0], chunk_limits[0][1]], 
                        [chunk_limits[1][0], chunk_limits[1][1]]]
                    ] """
                    caso = 7
                    #new_state_limits=  [[[chunk_limits[0][0], chunk_limits[0][1]], [chunk_limits[0][0], chunk_limits[1][1]]], [[chunk_limits[1][0], chunk_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]]]
                    new_state_limits=  [[[chunk_limits[1][0], chunk_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[0][1]], [chunk_limits[0][0], chunk_limits[1][1]]]]    
                # Caso 8: [44,12]
                elif (chunk_limits_teleport[0][0] > map_limits[0][0] and
                    chunk_limits_teleport[0][1] < map_limits[0][1] and
                    chunk_limits_teleport[1][0] >= map_limits[1][0] and
                    chunk_limits_teleport[1][1] >= map_limits[1][1]):
                    """ new_state_limits = [
                        [[map_limits[0][0], chunk_limits[0][1]], 
                        [chunk_limits[1][0], chunk_limits[1][1]]],
                        [[chunk_limits[0][0], chunk_limits[0][1]], 
                        [0, chunk_limits[1][1]]]
                    ] """
                    caso = 8
                    #new_state_limits=  [[[chunk_limits[1][0], chunk_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[0][1]], [chunk_limits[0][0], chunk_limits[1][1]]]]
                    new_state_limits=  [[[chunk_limits[1][0], chunk_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[0][1]], [chunk_limits[0][0], chunk_limits[1][1]]]]    
                else:
                    caso = 9
                    new_state_limits = [chunk_limits]
                    #print(f"WARNING: ... , case = 9,  chunk_limits: {chunk_limits} , new_state_limits: {new_state_limits} , chunk_limits_teleport: {chunk_limits_teleport} ")
            else:
                print("ERROR len(chunk_limits) != de 1 ou 2")
            extensive_new_state_limits = get_extensive_state_limits(caso,new_state_limits)
            return extensive_new_state_limits
        new_head = False
        if self.current_head_chunk == None:
            new_head = True
        elif self.head != self.current_head_chunk:
            new_head = True
        if new_head:
            #print("self.current_head_chunk, self.head :", self.current_head_chunk,self.head)
            #print("new_head: ",new_head)
            self.current_head_chunk = self.head
            chunk_limits_teleport = [[self.head[0]+self.chunk_size,self.head[1]+self.chunk_size],[self.head[0]-self.chunk_size,self.head[1]-self.chunk_size]]
            self.chunk_limits_teleport = chunk_limits_teleport
            if self.traverse:
                chunk_limits = [[(self.head[0]+self.chunk_size)% self.map_size[0],(self.head[1]+self.chunk_size)% self.map_size[1]],[(self.head[0]-self.chunk_size)% self.map_size[0],(self.head[1]-self.chunk_size)% self.map_size[1]]]
                #print("chunk_limits_teleport: ", chunk_limits_teleport)
                #print("chunk_limits: ", chunk_limits)
                #print("map_limits: ", map_limits)
                chunked_limits = get_chunked_limits(chunk_limits_teleport, chunk_limits, self.map_limits)
                #result = get_new_chunked_limits(state, chunk_limits_teleport, chunk_limits, map_limits)
            else:
                chunk_limits = [[[max(0, min(limit, self.map_size[i] - 1)) for i, limit in enumerate(chunk)]for chunk in chunk_limits_teleport]]
                chunked_limits = get_chunked_limits(chunk_limits_teleport, chunk_limits, self.map_limits)
            self.chunked_limits = chunked_limits
            print("chunk_limits_teleport: ", chunk_limits_teleport)
            print("chunked_limits: ", chunked_limits)
            return chunked_limits    
        else:
            return self.chunked_limits    
    # test if the given "goal" is satisfied in "state"
    def satisfies(self, state, goals):
        self.really_satisfies = False
        for goal_pos in goals:
            #print("food_pos", food_pos)
            if state == goal_pos:
                self.really_satisfies = True
                return True
        if self.chunks_on:
            self.atualize_chunked_limits()
            #print("state: ", state)
            #+: caso o goal esteja no limite do chunk:
            """ is_one_goal_in_chunk = False
            for goal_pos in goals:
                if goal_pos in self.chunked_limits:
                    if state == goal_pos:
                        is_one_goal_in_chunk = True
                    else:
                        is_one_goal_in_chunk =  False
            if is_one_goal_in_chunk:
                self.really_satisfies = True
                return True """
            
            if tuple(state) in self.chunked_limits:
                return True
        return False

    def bfs_floodfill(self,start,end,flood_cost = FLOOD_COST):
        #print("bfs_floodfill end: ",end)
        counter_dead_end = 0
        if not (0 <= start[0] < self.map_size[0] and 0 <= start[1] < self.map_size[1]):
            print("ValueError(Coordenadas de start fora do limite do mapa.)")
            raise ValueError("Coordenadas de start fora do limite do mapa.")
        if not (0 <= end[0] < self.map_size[0] and 0 <= end[1] < self.map_size[1]):
            print("ValueError(Coordenadas de goal fora do limite do mapa.)")
            raise ValueError("Coordenadas de goal fora do limite do mapa.")
        
        # Se a posição inicial ou final for obstáculo, não há caminho
        if (self.map[start[0]][start[1]] != WALL_COST and self.map[start[0]][start[1]] != BODY_COST and start not in self.body and start not in self.bodys and tuple(start) not in self.walls): 
            return None, [], set(), True
        
        # Cria uma matriz de distâncias inicializada com None
        distancias = [[None for _ in range(self.map_size[1])] for _ in range(self.map_size[0])]
        distancias[end[0]][end[1]] = 0
        
        # Matriz (ou dicionário) para guardar os pais (predecessores)
        # para reconstruir o caminho
        pais = [[None for _ in range(self.map_size[1])] for _ in range(self.map_size[0])]
        
        # Fila para BFS (armazenando (linha, coluna))
        fila = deque()
        fila.append((end[0], end[1]))
        
        # Movimentos possíveis (cima, baixo, esquerda, direita)
        movimentos = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        search_start = None
        search_start_cost = float('inf')
        flag_found_parent = False
        search_start_list = []
        search_start_list_costs = []
        
        all_searched_positions = set()
        # BFS
        """ def h(state,goal):
            min_heuristic = float('inf')
            h = abs(goal[0] - state[0]) + abs(goal[1] - state[1])
            if h < min_heuristic:
                min_heuristic = h
            return min_heuristic """
        while fila:
            lin_atual, col_atual = fila.popleft()
            
            # Se alcançamos o goal, podemos parar
            """ if (lin_atual, col_atual) == (start[0], start[1]):
                break """
            if [lin_atual,col_atual] == start:
                    flag_found_parent = True
                    
            for d_lin, d_col in movimentos:
                lin_viz = lin_atual + d_lin
                col_viz = col_atual + d_col
                # Verifica se está dentro do self.map e se é espaço livre
                if 0 <= lin_viz < self.map_size[0] and 0 <= col_viz < self.map_size[1]:
                    if distancias[lin_viz][col_viz] is None:
                        if (self.map[lin_viz][col_viz] != WALL_COST and self.map[lin_viz][col_viz] != BODY_COST and [lin_viz,col_viz] not in self.body and [lin_viz,col_viz] not in self.bodys and tuple([lin_viz,col_viz]) not in self.walls): 
                            distancias[lin_viz][col_viz] = distancias[lin_atual][col_atual] + flood_cost
                            pais[lin_viz][col_viz] = (lin_atual, col_atual)
                            all_searched_positions.add((lin_viz, col_viz))
                            fila.append((lin_viz, col_viz))
                            counter_dead_end += 1
                            if flag_found_parent:
                                search_start_list.append([lin_viz, col_viz])
                                search_start_list_costs.append(distancias[lin_viz][col_viz])
                            v_f = distancias[lin_viz][col_viz]
                            if self.floodfill_max is None:
                                self.floodfill_max = v_f
                            elif v_f > self.floodfill_max:
                                self.floodfill_max = v_f
                            if self.floodfill_min is None:
                                self.floodfill_min = v_f
                            elif v_f < self.floodfill_min:
                                self.floodfill_min = v_f

                    
                        
        # Reconstruir o caminho, se o goal foi alcançado
        path = []
        if not self.use_floodfill_just_for_deadends and self.floodfill_calc_path:
            #print("search_start_list", search_start_list)
            for i,s in enumerate(search_start_list):
                if search_start_list_costs[i] < search_start_cost:
                    search_start = s
                    search_start_cost = search_start_list_costs[i]
            if distancias[search_start[0]][search_start[1]] is not None: 
                # Caminho existe; reconstrói "de trás pra frente"
                atual = (search_start[0], search_start[1])
                #print("atual: ",atual)
                while atual is not None:
                    path.append(atual)
                    atual = pais[atual[0]][atual[1]]
                #path.reverse()  # Inverte para ficar do start -> goal
                #print("path_floodfill0: ",path)
            #print("path_floodfill0: ",path)
        is_dead_end = False
        if counter_dead_end <= 100:
            is_dead_end = True
            self.flood_deadends.update(all_searched_positions)
            print(f"WARNING: found deadend in goal {end} ")
            return distancias, [], all_searched_positions, is_dead_end
        self.map_floodfill = distancias
        #self.print_map_floodfill(distancias)
        #print("path_floodfill0: ",path)
        #print("start: ", start)
        return distancias, path, all_searched_positions, is_dead_end
    def fuse_floodfill(self,distancias_finais, distancias):
        if distancias_finais == None:
            return distancias
        n_linhas = len(distancias)
        n_colunas = len(distancias[0])
        for i in range(n_linhas):
            for j in range(n_colunas):
                if distancias_finais[i][j] is None:
                    if distancias[i][j] is not None:
                        print(f"ERROR:  distancias_finais[{i}][{j}] is None and distancias[{i}][{j}] is not None ")
                else:
                    if distancias[i][j] is None:
                        print(f"ERROR:  distancias[{i}][{j}] is None and distancias_finais[{i}][{j}] is not None ")
                if distancias_finais[i][j] is not None:
                    distancias_finais[i][j] += distancias[i][j]
                    v_f = distancias_finais[i][j]
                    if self.floodfill_max is None:
                        self.floodfill_max = v_f
                    elif v_f > self.floodfill_max:
                        self.floodfill_max = v_f
                    if self.floodfill_min is None:
                        self.floodfill_min = v_f
                    elif v_f < self.floodfill_min:
                        self.floodfill_min = v_f
        return distancias_finais
    def flood_fill(self, start, goals):
        #print("floof_fill goals: ",goals)
        def group_by_x(tuples_set):
            grouped = defaultdict(list)
            for y, x in tuples_set:
                grouped[x].append((y, x))
            return grouped
        def group_by_y(tuples_set):
            grouped = defaultdict(list)
            for y, x in tuples_set:
                grouped[y].append((y, x))
            return grouped
        if goals is None or goals == []:
            print(f"WARNING:  goals is None or goals = [] ")
            return None, []
        flood_cost = FLOOD_COST // len(goals)
        path = ()
        len_path = float('inf')
        distancias_finais = None
        n_deadends = 0
        dead_ends_list = []
        if flood_cost == 0:
            flood_cost = 1
        for goal in goals:
            #print("floof_fill goal: ",goal)
            distancias, path, all_searched_positions, is_dead_end = self.bfs_floodfill( start, goal, flood_cost)
            if path != []:
                if len(path) < len_path:
                    len_path = len(path)
                    self.path_floodfill = path
            if distancias is not None and not is_dead_end:
                distancias_finais = self.fuse_floodfill(distancias_finais, distancias)
            if is_dead_end:
                print(f"WARNING: found deadend in goal {goal} ")
                dead_ends_list.append([all_searched_positions])
                n_deadends += 1
        #print("distancias_finais:")
        #print(distancias_finais)
        #self.print_map_floodfill(distancias_finais)
        self.map_floodfill = distancias_finais
        self.path_floodfill = path
        #print("path_floodfill: ",path)
        #+: corrige os flood_deadends para quando traverse
        if self.traverse:
            all_limit_deadends = set()
            limit_deadends_xmin = set()
            limit_deadends_xmax = set()
            limit_deadends_ymin = set()
            limit_deadends_ymax = set()
            for x in range(self.map_size[0]):
                for dead_end in dead_ends_list:
                    if (0,x) in dead_end:
                        limit_deadends_ymin.add((0,x))
                        all_limit_deadends.add((0,x))
                    if (self.map_size[1]-1,x) in dead_end:
                        limit_deadends_ymax.add((self.map_size[1]-1,x))
                        all_limit_deadends
            for y in range(self.map_size[1]):
                for dead_end in dead_ends_list:
                    if (y,0) in dead_end:
                        limit_deadends_xmin.add((y,0))
                        all_limit_deadends.add((y,0))
                    if (y,self.map_size[0]-1) in dead_end:
                        limit_deadends_xmax.add((y,self.map_size[0]-1))
                        all_limit_deadends.add((y,self.map_size[0]-1))
            if all_limit_deadends != set(): # pelo menos 1 pode nao ser deadend
                if n_deadends == 1: # nenhum é deadend
                    self.flood_deadends = set()
                if limit_deadends_xmin != set() and limit_deadends_xmax != set():
                    to_remove = set()
                    g_xmin = group_by_x(limit_deadends_xmin)
                    g_xmax = group_by_x(limit_deadends_xmax)
                    comon_x = set(g_xmin.keys()) & set(g_xmax.keys())
                    for c in comon_x:
                        to_remove.update(g_xmin[c] + g_xmax[c])     
                    for d in dead_ends_list:
                        for r in to_remove:
                            if r in d:
                                self.flood_deadends.difference_update(r)      
                else:
                    self.flood_deadends.difference_update(limit_deadends_xmin)
                    self.flood_deadends.difference_update(limit_deadends_xmax)
                if limit_deadends_ymin != set() and limit_deadends_ymax != set():
                    to_remove = set()
                    g_ymin = group_by_y(limit_deadends_ymin)
                    g_ymax = group_by_y(limit_deadends_ymax)
                    comon_y = set(g_ymin.keys()) & set(g_ymax.keys())
                    for c in comon_y:
                        to_remove.update(g_ymin[c] + g_ymax[c])     
                    for d in dead_ends_list:
                        for r in to_remove:
                            if r in d:
                                self.flood_deadends.difference_update(r)
                else:
                    self.flood_deadends.difference_update(limit_deadends_ymin)
                    self.flood_deadends.difference_update(limit_deadends_ymax)
                
        return distancias_finais, path
        

class SearchProblem:
    def __init__(self, domain, goals):
        self.domain = domain
        self.initial = domain.head
        self.goals = goals
        """ if domain.foods != []:
            self.goals = [domain.foods[0]]
        else:
            self.goals = [] """

    def goal_test(self, state):
        return self.domain.satisfies(state, self.goals)

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
        #print("problem.goals: ", problem.goals)
        self.strategys = ['breadth', 'depth', 'uniform', 'greedy', 'a*', 'informed', 'informed_chd','informed_mul']
        self.problem = problem
        root = SearchNode(problem.initial, None, 0, 0, problem.domain.heuristic(problem.initial, problem.goals, heuristic))
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
        self.stats = {}

    # obter o caminho (sequencia de estados) da raiz ate um no
    def get_path(self, node):
        if node.parent == None:
            return [node.state]
        path = self.get_path(node.parent)
        path += [node.state]
        return(path)
    def verify_path(self, path):
        error_list = []
        error = False
        for step in path:
            if tuple(step) in self.problem.domain.walls:
                error_list.append(['wall: ',step])
                error = True
            """ for wall in self.problem.domain.walls:
                if step == wall:
                    error_list.append(['wall: ',step])
                    error = True """
            for body in self.problem.domain.bodys:
                if step == body:
                    error_list.append(['bodys: ',step])
                    error = True
            for body in self.problem.domain.body:
                if step == body:
                    error_list.append(['body: ',step])
                    error = True
        if error:
            print(f"WARNING: verify_path = False , error_list: {error_list}")
            return False
        return True
    # procurar a solucao
    def search(self):
        #print("++++++++++++++++++++++++++++++++++++")
        #print("++++++++++++++++++++++++++++++++++++")
        #print("SEARCHING")
        if self.problem.initial == []:
            print(f"ERROR: sem problem.initial em SearchTree.search ()")
            self.add_small_stats( new_stat="ERROR1", new_state_value="self.problem.initial == []")
            return None
        if self.problem.goals == []:
            self.add_small_stats( new_stat="WARNING1", new_state_value="self.problem.goals == []")
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
                    if self.verify_path(path[1:]):
                        self.add_small_stats( new_stat="Improve1", new_state_value="false")
                        self.add_small_stats( new_stat="End search reason1", new_state_value="found path")
                        self.problem.domain.last_path = path
                        return path
                    else:
                        self.add_small_stats( new_stat="ERROR2", new_state_value="erro na verificacao do path")
                        return None
                    self.problem.domain.last_path = path
                    return path      
                continue
            if self.solution is not None and (node.cost + node.heuristic) >= self.solution.cost:
                self.num_skipped += 1
                continue  
            # Expansão do Node
            self.non_terminals += 1
            lnewnodes = []
            newstates = self.problem.domain.actions_results(node.state)
            if newstates == []:
                print(f"WARNING: sem newstates ")
            for newstate in newstates:
                #print("newstate: ", newstate)
                #print("pre path: ", self.get_path(node))
                if not self.verify_path([newstate]):
                    continue
                if newstate not in self.get_path(node):
                    newnode = SearchNode(newstate, node, node.depth + 1, node.cost + self.problem.domain.cost(newstate,self.problem.goals), self.problem.domain.heuristic(newstate, self.problem.goals, self.heuristic))
                    lnewnodes.append(newnode)
                    #print("newnode_heuristic", newnode.heuristic)
                    #print("goal:",self.problem.goals)
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
            if self.verify_path(path[1:]):
                self.add_small_stats( new_stat="Improve2", new_state_value="true")
                self.add_small_stats( new_stat="End search reason2", new_state_value="found path")
                self.problem.domain.last_path = path
                return path
            else:
                self.add_small_stats( new_stat="ERROR3", new_state_value="erro na verificacao do path")
                return None
            self.problem.domain.last_path = path
            return path
        elif self.best_partial_solution is not None:
            path = self.get_path(self.best_partial_solution)
            self.path = path
            self.add_small_stats( new_stat="Improve3", new_state_value="false")
            self.add_small_stats( new_stat="End search reason3", new_state_value="found best_partial_solution")
            self.problem.domain.last_path = path
            return path
        else:
            self.add_small_stats( new_stat="ERROR4", new_state_value="found no solution")
            return None

    # juntar novos nos a lista de nos abertos de acordo com a estrategia
    def add_to_open(self,lnewnodes):
        # ['breadth', 'depth', 'uniform', 'greedy', 'a*', 'informed']
        if self.strategy == self.strategys[0]: 
            self.open_nodes.extend(lnewnodes)
        elif self.strategy == self.strategys[1]:
            self.open_nodes[:0] = lnewnodes
        elif self.strategy == self.strategys[2]:
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda node: node.cost)
        elif self.strategy == self.strategys[3]:
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda node: node.heuristic)
        elif self.strategy == self.strategys[4]:
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda node: (node.cost + node.heuristic, node.depth))
        elif self.strategy ==  self.strategys[5]:
            self.open_nodes = sorted(lnewnodes, key=lambda node: ((node.cost//10) + node.heuristic,node.depth)) + self.open_nodes
        elif self.strategy ==  self.strategys[6]:
            self.open_nodes = sorted(lnewnodes, key=lambda node: (node.cost, node.heuristic, node.depth)) + self.open_nodes
        if self.strategy ==  self.strategys[7]:
            self.open_nodes = sorted(lnewnodes, key=lambda node: (node.cost*node.heuristic,node.cost ,node.depth)) + self.open_nodes
    def add_small_stats(self, new_stat=None, new_state_value=None):
        if new_stat is not None and new_state_value is not None:
            self.stats[new_stat] = new_state_value
        if self.problem.domain.really_satisfies == None:
            self.stats["End domain reason"] = "no solution reached"
        elif self.problem.domain.really_satisfies:
            self.stats["End domain reason"] = "reached roal"
        elif not self.problem.domain.really_satisfies:
            self.stats["End domain reason"] = "reached limit"
    
    def get_stats(self):
        #print(f"STRATEGY: {self.strategy}, IMPROVE: {self.improve}, LIMIT: {self.limit}")
        if self.solution != None:
            if self.solution.state in self.problem.goals:
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
    

domain = SearchDomain()
""" move = None """
def get_move(domain, next_position):
    global move
    #print("domain.head",domain.head)
    #print("next_position", next_position)
    move = [next_position[0]-domain.head[0],next_position[1]-domain.head[1]]
    #print("move before",move)
    #print("domain.map_size-1 : [",domain.map_size[0]-1,", ",domain.map_size[1]-1,"]")
    #print("-(domain.map_size-1) : [",-(domain.map_size[0]-1),", ",-(domain.map_size[1]-1),"]")
    #print("traverse: ", domain.traverse)
    # [0,23]->[0,-1]
    if domain.traverse:
        if move[0] == (domain.map_size[0]-1):
            move[0] = -1
        elif move[0] == -(domain.map_size[0]-1):
            move[0] = 1
        if move[1] == (domain.map_size[1]-1):
            move[1] = -1
        elif move[1] == -(domain.map_size[1]-1):
            move[1] = 1
        print("move: ",move)
    return move
def is_opposite_key(last_key, new_key):
    #print("last_key: ", last_key)
    opposites = {"w": "s", "s": "w", "a": "d", "d": "a"}
    return opposites[last_key] == new_key
def get_command(move):
    if move[0] == 1 and move[1] == 0:	    #>
        return "d"#"w"
    elif move[0] == -1 and move[1] == 0:	#<
        return "a"#"s"
    elif move[0] == 0 and move[1] == 1:	    #˅
        return "s"#"d"
    elif move[0] == 0 and move[1] == -1:    #^
        return "w"#"a"
    else:
        print(f"ERROR: sem move válido em comando, move: {move}  ()")
        return ""
    
flag_head_reached_mapcenter = False
def wander():
    global flag_head_reached_mapcenter
    print(f">>>WANDER")
    explore_positions = []
    #?: cria posicoes espacadas de 2*domain.s_range
    """ for x in range(0, domain.map_size[1], 2*domain.s_range):
        for y in range(0, domain.map_size[0], 2*domain.s_range):
            print("x: ", x, "y: ", y)
            # "transladar" as coordenadas
            relative_pos = [(y+domain.head[0])% (domain.map_size[0]),(x+domain.head[1])% (domain.map_size[1])]
            if relative_pos not in domain.body and relative_pos not in domain.head and relative_pos not in domain.walls:
                explore_positions.append(relative_pos) """
    #?: leva a cobra ao centro e depois ir para um dos 4 vertices do mapa
    if domain.head == [23,11] and flag_head_reached_mapcenter == False:
        flag_head_reached_mapcenter = True
        explore_positions = [[47,23],[47,0],[0,23],[0,0]]
    elif domain.head != [23,11] and flag_head_reached_mapcenter == False: 
        explore_positions = [[23,11]]
    elif domain.head != [23,11] and flag_head_reached_mapcenter == True:
        flag_head_reached_mapcenter = False
        explore_positions = [[47,23],[47,0],[0,23],[0,0]]
    elif domain.head == [23,11] and flag_head_reached_mapcenter == True:
        flag_head_reached_mapcenter = True
        explore_positions = [[47,23],[47,0],[0,23],[0,0]]
    else:
        print(f"ERROR: em student.wander, alguma coisa mal com as flags ()")
    
    print("explore_positions: ", explore_positions)
    problem = SearchProblem(domain, explore_positions)
    path = SearchTree(problem).search()
    #domain.print_mapa(path)
    if path != None:
        if len(path) != 1: # ou seja chegou ao destino, em principio nao é preciso pq o dominio lida com isto automaticamente       
            return path[1]
        else:
            print(f"ERROR: em student.wander, path apenas com 1 posicao ()")
    else:
        print(f"ERROR: em student.wander, path é None ()")
    return None

# enquanto for != None e pq ainda nao chegou la
# resentar para none tambem quando sao encontradas frutas
last_explore_position = None 

def find_next_explore_position():
    """
    Procura a posicao de domain.possible_explore_positions mais proxima de domain.head que tenha o menor power em domain.explored_positions
    Pesquisa breath-first
    """
    
    #+: para dar lock numa explore_position ate que seja explorada
    #+: opcao mais eficiente pq para explorar so precisa de estar dentro so sight:
    #+:     - se tornasse o explored_positions em mapa (ou seja, cada posicao normalizada representava o power na posicao nao normalizada) poderia usar o valor no mapa para verificar se ja foi visitada (se o valor == EXPLORE_POWER e pq foi visitada)
    global last_explore_position
    needs_new_explore_position = False
    print("last_explore_position: ", last_explore_position)
    if last_explore_position != None:
        if domain.head == last_explore_position: # se a cobra ja chegou a posicao
            last_explore_position = None
            needs_new_explore_position = True
            print("CHEGOU A LAST_EXPLORE_POSITION")
        else:
            next_explore_position = last_explore_position
    else:
        needs_new_explore_position = True
        print("last_explore_position: ", last_explore_position)
    
    if needs_new_explore_position:
        norm_head = [((domain.head[0] // domain.explore_pos_space)*domain.explore_pos_space)+domain.all_explore_positions[0][0], ((domain.head[1] // domain.explore_pos_space)*domain.explore_pos_space)+domain.all_explore_positions[0][1]]
        #norm_moves = [[domain.all_explore_positions[0][0],domain.explore_pos_space],[domain.all_explore_positions[0][0],-domain.explore_pos_space],[domain.explore_pos_space,domain.all_explore_positions[0][1]],[-domain.explore_pos_space,domain.all_explore_positions[0][1]]]
        norm_moves = [[0,domain.explore_pos_space],[0,-domain.explore_pos_space],[domain.explore_pos_space,0],[-domain.explore_pos_space,0]]
        print("norm_head: ", norm_head)
        print("norm_moves: ", norm_moves)
        queue = [norm_head]
        visited_norm_heads = set()  
        closest_explore_positions = []
        test_closest_explore_positions = []
        next_explore_position = None
        bfs_depth = 0 #?: para evitar uma pesquisa muito extensiva
        MAX_BFS_DEPTH = 100
        while queue: 
            current_pos = queue.pop(0)
            bfs_depth += 1
            if tuple(current_pos) in visited_norm_heads: #?: ignorar posicoes ja visitadas, evitar loops
                continue
            visited_norm_heads.add(tuple(current_pos)) #?: adicionar posicao atual a lista de visitadas
            for norm_move in norm_moves:
                new_norm_head = [norm_head[0]+norm_move[0],norm_head[1]+norm_move[1]]
                print("new_norm_head: ", new_norm_head)
                if 0 <= new_norm_head[0] < domain.map_size[0] and 0 <= new_norm_head[1] < domain.map_size[1]: #?: limitar pesquisa aos limites do mapa
                    print( "new_norm_head inside domain:")
                    #print("new_norm_head: ", new_norm_head)
                    if new_norm_head in domain.possible_explore_positions:
                        print("new_norm_head in possible_explore_positions")
                        for explored_position in domain.explored_positions:
                            if explored_position[1] == new_norm_head:
                                print("new_norm_head in explored_positions")
                                if explored_position[0] == 0:
                                    next_explore_position = explored_position[1]
                                    print(f"bfs found next_explore_position: {next_explore_position}, com custo: {explored_position[0]} " )
                                    #closest_explore_positions.append(explored_position)
                                    test_closest_explore_positions.append(explored_position)
                                    print(f"break ,explored_position[0]: {explored_position[0]},")
                                    break
                                else:
                                    closest_explore_positions.append(explored_position)
                            if next_explore_position != None:
                                print(f"break ")
                                break
                    if tuple(new_norm_head) not in visited_norm_heads:
                        queue.append(new_norm_head)
                if next_explore_position != None:
                    print(f"break ")
                    break
            if next_explore_position != None:
                print(f"break ")
                break
            if bfs_depth >= MAX_BFS_DEPTH:
                print(f"break, bfs_depth: {bfs_depth}, ")
                break
    #?: encontrar a posicao com menor power(que nao foi visitada a mais tempo)
    if next_explore_position == None:
        smallest_power = float("inf")
        for closest_explore_position in closest_explore_positions:
            if closest_explore_position[0] < smallest_power:
                smallest_power = closest_explore_position[0]
                next_explore_position = closest_explore_position[1]
    
    
    
    if needs_new_explore_position:
        print("closest_explore_positions: ", closest_explore_positions)
        print("test_closest_explore_positions: ", test_closest_explore_positions)
    return next_explore_position

def explore():
    global last_explore_position
    print(f">>>EXPLORE")
    while True:
        next_explore_position = find_next_explore_position()
        if next_explore_position == None:
            print(f"ERROR: em student.explore, next_explore_position é None ")
            break
        else:
            print("next_explore_position: ", [next_explore_position])
            #+: atualizar o domain
            if not domain.use_floodfill_just_for_deadends:
                domain.map_floodfill = None
                domain.path_floodfill = None
                domain.flood_deadends = set()
                domain.flood_fill(domain.head,[next_explore_position])
                if tuple(next_explore_position) in domain.flood_deadends:
                        domain.possible_explore_positions.remove(next_explore_position)
                        last_explore_position = None
                        print(f"WARNING: next_explore_position {next_explore_position} in domain.flood_deadends ")
                else:
                    break
            else:
                domain.map_floodfill = None
                domain.path_floodfill = None
                domain.flood_deadends = set()
                domain.flood_fill(domain.head,[next_explore_position])
                if tuple(next_explore_position) in domain.flood_deadends:
                        domain.possible_explore_positions.remove(next_explore_position)
                        last_explore_position = None
                        print(f"WARNING: next_explore_position {next_explore_position} in domain.flood_deadends ")
    if next_explore_position == None:
        return None
    
    problem = SearchProblem(domain, [next_explore_position])
    search_tree = SearchTree(problem)
    path = search_tree.search()
    print(f"search states: {search_tree.stats} " )
    
    
    
    #domain.print_mapa(path)
    
    
    
    if path != None:
        if len(path) != 1: # ou seja chegou ao destino, em principio nao é preciso pq o dominio lida com isto automaticamente       
            last_explore_position = next_explore_position
            return path[1]
        else:
            print(f"ERROR: path apenas com 1 posicao ")
    else:
        print(f"ERROR: path == None ")
    return None
last_key = ""
async def agent_loop(server_address="localhost:8000", agent_name="student"):
    
    global last_key
    global last_explore_position
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        """ global move """ 
        while True:
            
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game update, this must be called timely or your game will get out of sync with the server
                print("-----------------------------------------------------")
                print(state)                
                key = ""
                #food_info = state['food']
                #body_info = state['body'] #?: a cabeça é a primeira posição
                """ if move is None:
                    print("move for domain: None")
                else:
                    print("move for domain: ", move) """
                
                domain.atualize_domain(state)
                problem_goals = domain.foods
                for problem_goal in problem_goals:
                    if tuple(problem_goal) in domain.flood_deadends:
                        problem_goals.remove(problem_goal)
                        print(f"WARNING: em student.agent_loop, problem_goal: {problem_goal} in domain.flood_deadends ")
                
                problem = SearchProblem(domain, domain.foods)
                
                
                
                
                print("domain.foods: ", domain.foods)
                print("domain.foods + domain.superfoods: ", domain.foods + domain.superfoods)
                # apenas para ver o mapa
                if 'map' in state and 'size' in state and 'level' in state:
                    print("ns pq que nao consigo eliminar esta condicao sem que o codigo se escangalhe todo")
                    #domain.print_mapa()
                    
                    
                    
                    
                elif domain.foods != []:
                    
                    last_explore_position = None #+: resetar explore()
                    #print("body: ", state['body'])
                    search_tree = SearchTree(problem)
                    path = search_tree.search()
                    
                    
                    
                    
                    #domain.print_mapa(path = path)
                    
                    
                    
                    #print("domain.foods: ",domain.foods)
                    #print("domain.walls: ",domain.walls)
                    #print("domain.bodys: ",domain.bodys)
                    print(f"search states: {search_tree.stats} " )
                    print("full path: ", path)
                    if path != None:
                        if len(path) != 1: # ou seja chegou ao destino, em principio nao é preciso pq o dominio lida com isto automaticamente       
                            next_position = path[1]
                            move = get_move(domain, next_position)
                            key = get_command(move)
                        else:
                            print(f"WARNING: em student.agent_loop, path apenas com 1 posicao, a food devia desaparecer do domain aintes de ser feita a pesquisa ")
                    else:
                        print(f"WARNING: path == None apesar de domain.foods != [] ")
                        if domain.foods != []:
                            print(f"WARNING: em student.agent_loop, path deu None mas existem foods ")
                        #next_position = wander()
                        next_position = explore()
                        if next_position != None:
                            move = get_move(domain, next_position)
                            key = get_command(move)
                        else:
                            print(f"WARNING: next_position == None ")
                else:
                    #next_position = wander()
                    next_position = explore()
                    if next_position != None:
                        move = get_move(domain, next_position)
                        key = get_command(move)
                print("key: ", key)
                print("last_key: ", last_key)
                if (key == "" and 'map' not in state):
                    print(f"ERROR: key vazia ")
                elif last_key != "" and is_opposite_key(last_key, key):
                    print(f"ERROR: , key oposta à anterior , last_key: {last_key}, key: {key} ")
                
                if (key == "" and 'map' not in state) or (last_key != "" and is_opposite_key(last_key, key)):
                    print(f"WARNING: , key corrected ")
                    head = domain.head
                    actlist = domain.actions_results(head) 
                    if actlist == []:
                        print(f"ERROR: actlist vazia, head: {head} ")
                    print("actlist: ", actlist)
                    possible_moves = []
                    
                    #+: verificar as coordenadas à volta 
                    for act in actlist:         
                        actlist2 = domain.actions_results(act)
                        if actlist2 != []: #+: significa que a proxima posicao (act) tem pelo menos uma outra proxima posicao possivel (act2)
                            possible_moves.append(act)    
                    if possible_moves == []:
                        print(f"ERROR: possible_moves vazia ")
                    keys = []
                    for possible_move in possible_moves:
                        move = get_move(domain, possible_move)
                        key = get_command(move)
                        if not is_opposite_key(last_key, key):
                            keys.append(key)
                    if keys == []:
                        print(f"ERROR: keys vazia ")
                    else:
                        key = keys[0]
                        print("key_corrected: ", key)

                if (key == "" and 'map' not in state):
                    print(f"ERROR: key_corrected vazia ")
                elif last_key != "" and is_opposite_key(last_key, key):
                    print(f"ERROR: , key_corrected oposta à anterior , last_key: {last_key}, key: {key} ")
                
                last_key = key
                
                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )  # send key command to server - you must implement this send in the AI agent
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return



# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))

