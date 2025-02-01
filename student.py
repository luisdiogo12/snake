"""Example client."""
import asyncio
import getpass
import json
import os

#+: bibliotecas adicionadas:
from collections import deque

#!: eliminar no final:
from student_tree_search import *
from student_utils import *
from colorama import Fore, Style
import inspect
import math
from tests.state_recorder import StateRecorder 
import argparse
from rich.console import Console
from rich.text import Text
from time import monotonic

import websockets

#ToDo: no final, quando nao houverem erros, remover as confirmações de erros pq estao so a ocupar tempo, remover tambem coisas redundantes
#ToDo: por pesos no mapa para a cobra preferir trajetos nao explorados para obter mais informacao
#ToDo: comer frutas especiais ate ter as melhores skills
#ToDo: prevensao que a pesquisa demore demasiado tempo
#ToDo: talvez implementar ruido no mapa, para nao haverem loops de paths
#ToDo: talvez fazer com que os custos de onde paths foram definidas, sejam menores no mapa, ou entao que sejam usadas na heuristica ou custo para terem um valor menor, para as proximas paths serem mais rapidamente calculadas e terem preferencia em manter a path para nao entrar em loops
#ToDo: verificar se o trasverse esta a ser bem atualizado, é que no state aparece True em vez de true que o python usa
#ToDo. fazer pesquisa por secções do mapa ou por profundidade, para nao ter de calcular o mapa todo
#Todo: durante a pesquisa, fazer um domain simulado a simular o movimento da cobra para ter isso em conta
#Todo: adaptar para multiplayer

#!: eliminar no final
parser = argparse.ArgumentParser()
parser.add_argument("--name", help="nome do player", default="ibon")
args = parser.parse_args()
recorder = StateRecorder(args.name);

domain = SearchDomain()
""" move = None """
def is_opposite_key(last_key, new_key):
    #print("last_key: ", last_key)
    opposites = {"w": "s", "s": "w", "a": "d", "d": "a"}
    return opposites[last_key] == new_key
def get_command(move):
    #!: n percebo pq que o servidor le os comandos ao contrario
    if move[0] == 1 and move[1] == 0:	    #>
        return "d"#"w"
    elif move[0] == -1 and move[1] == 0:	#<
        return "a"#"s"
    elif move[0] == 0 and move[1] == 1:	    #˅
        return "s"#"d"
    elif move[0] == 0 and move[1] == -1:    #^
        return "w"#"a"
    else:
        print(f"{Fore.RED}ERROR: sem move válido em comando, move: {move}  (linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
        return ""
    
flag_head_reached_mapcenter = False
def wander():
    global flag_head_reached_mapcenter
    #ToDo: experimentar com posicoes random, tendo em conta o state['range']
    print(f"{Back.GREEN}>>>WANDER{Style.RESET_ALL}")
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
        print(f"{Fore.RED}ERROR: em student.wander, alguma coisa mal com as flags (linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
    
    print("explore_positions: ", explore_positions)
    problem = SearchProblem(domain, explore_positions)
    path = SearchTree(problem).search()
    domain.print_mapa(path)
    if path != None:
        if len(path) != 1: # ou seja chegou ao destino, em principio nao é preciso pq o dominio lida com isto automaticamente       
            return path[1]
        else:
            print(f"{Fore.RED}ERROR: em student.wander, path apenas com 1 posicao (linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}ERROR: em student.wander, path é None (linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
    return None

# enquanto for != None e pq ainda nao chegou la
# resentar para none tambem quando sao encontradas frutas
last_explore_position = None 

def find_next_explore_position():
    """
    Procura a posicao de domain.possible_explore_positions mais proxima de domain.head que tenha o menor power em domain.explored_positions
    Pesquisa breath-first
    """
    start_ns = monotonic()
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
        visited_norm_heads = set() #!: penso que nao precisa de ser set visto que so sao adicionadas posicoes novas, mas set usa hash e é mais rapido
        closest_explore_positions = []
        test_closest_explore_positions = []
        next_explore_position = None
        bfs_depth = 0 #?: para evitar uma pesquisa muito extensiva
        MAX_BFS_DEPTH = 100
        #ToDo: esta pesquisa nao esta a ter em conta trasverse = True
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
                                    print(f"{Fore.CYAN}bfs found next_explore_position: {next_explore_position}, com custo: {explored_position[0]} {Style.RESET_ALL}" )
                                    #closest_explore_positions.append(explored_position)
                                    test_closest_explore_positions.append(explored_position)
                                    print(f"break ,explored_position[0]: {explored_position[0]},linha {inspect.currentframe().f_lineno}")
                                    break
                                else:
                                    closest_explore_positions.append(explored_position)
                            if next_explore_position != None:
                                print(f"break linha {inspect.currentframe().f_lineno}")
                                break
                    if tuple(new_norm_head) not in visited_norm_heads:
                        queue.append(new_norm_head)
                if next_explore_position != None:
                    print(f"break linha {inspect.currentframe().f_lineno}")
                    break
            if next_explore_position != None:
                print(f"break linha {inspect.currentframe().f_lineno}")
                break
            if bfs_depth >= MAX_BFS_DEPTH:
                print(f"break, bfs_depth: {bfs_depth}, linha {inspect.currentframe().f_lineno}")
                break
    #?: encontrar a posicao com menor power(que nao foi visitada a mais tempo)
    if next_explore_position == None:
        smallest_power = float("inf")
        for closest_explore_position in closest_explore_positions:
            if closest_explore_position[0] < smallest_power:
                smallest_power = closest_explore_position[0]
                next_explore_position = closest_explore_position[1]
    end_ns = monotonic()
    elapsed_ns = end_ns - start_ns
    print(f"{Fore.BLUE}TIME: explore: elapsed_ns: {elapsed_ns}(linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
    start_ns = monotonic()
    if needs_new_explore_position:
        print("closest_explore_positions: ", closest_explore_positions)
        print("test_closest_explore_positions: ", test_closest_explore_positions)
    return next_explore_position

def explore():
    global last_explore_position
    print(f"{Back.GREEN}>>>EXPLORE{Style.RESET_ALL}")
    while True:
        next_explore_position = find_next_explore_position()
        if next_explore_position == None:
            print(f"{Fore.RED}ERROR: em student.explore, next_explore_position é None (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
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
                        print(f"{Fore.YELLOW}WARNING: next_explore_position {next_explore_position} in domain.flood_deadends (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
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
                        print(f"{Fore.YELLOW}WARNING: next_explore_position {next_explore_position} in domain.flood_deadends (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
    if next_explore_position == None:
        return None
    start_ns = monotonic()
    problem = SearchProblem(domain, [next_explore_position])
    search_tree = SearchTree(problem)
    path = search_tree.search()
    print(f"{Fore.CYAN}search states: {search_tree.stats} {Style.RESET_ALL}" )
    end_ns = monotonic()
    elapsed_ns = end_ns - start_ns
    print(f"{Fore.BLUE}TIME: explore-search: elapsed_ns: {elapsed_ns}(linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
    start_ns = monotonic()
    domain.print_mapa(path)
    end_ns = monotonic()
    elapsed_ns = end_ns - start_ns
    print(f"{Fore.BLUE}TIME: explore-print_map: elapsed_ns: {elapsed_ns}(linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
    start_ns = monotonic()
    if path != None:
        if len(path) != 1: # ou seja chegou ao destino, em principio nao é preciso pq o dominio lida com isto automaticamente       
            last_explore_position = next_explore_position
            return path[1]
        else:
            print(f"{Fore.RED}ERROR: path apenas com 1 posicao (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}ERROR: path == None (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
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
            all_start_ns = monotonic()
            start_ns = monotonic()
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game update, this must be called timely or your game will get out of sync with the server
                print("-----------------------------------------------------")
                print(state)
                
                recorder.record_state(state) #!: eliminar no final
                
                key = ""
                #food_info = state['food']
                #body_info = state['body'] #?: a cabeça é a primeira posição
                """ if move is None:
                    print("move for domain: None")
                else:
                    print("move for domain: ", move) """
                start_ns = monotonic()
                domain.atualize_domain(state)
                problem_goals = domain.foods
                for problem_goal in problem_goals:
                    if tuple(problem_goal) in domain.flood_deadends:
                        problem_goals.remove(problem_goal)
                        print(f"{Fore.YELLOW}WARNING: em student.agent_loop, problem_goal: {problem_goal} in domain.flood_deadends (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                #!: elinimar no final(para testar traverse): 
                #domain.traverse = False
                
                problem = SearchProblem(domain, domain.foods)
                end_ns = monotonic()
                elapsed_ns = end_ns - start_ns
                print(f"{Fore.BLUE}TIME: atualizar domain: elapsed_ns: {elapsed_ns}(linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                start_ns = monotonic()
                print("domain.foods: ", domain.foods)
                print("domain.foods + domain.superfoods: ", domain.foods + domain.superfoods)
                # apenas para ver o mapa
                if 'map' in state and 'size' in state and 'level' in state:
                    start_ns = monotonic()
                    domain.print_mapa()
                    end_ns = monotonic()
                    elapsed_ns = end_ns - start_ns
                    print(f"{Fore.BLUE}TIME: print mapa: elapsed_ns: {elapsed_ns}(linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                    start_ns = monotonic()
                elif domain.foods != []:
                    start_ns = monotonic()
                    last_explore_position = None #+: resetar explore()
                    #print("body: ", state['body'])
                    search_tree = SearchTree(problem)
                    path = search_tree.search()
                    end_ns = monotonic()
                    elapsed_ns = end_ns - start_ns
                    print(f"{Fore.BLUE}TIME: achar path: elapsed_ns: {elapsed_ns}(linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                    start_ns = monotonic()
                    domain.print_mapa(path = path)
                    end_ns = monotonic()
                    elapsed_ns = end_ns - start_ns
                    print(f"{Fore.BLUE}TIME: printar mapa: elapsed_ns: {elapsed_ns}(linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                    start_ns = monotonic()
                    #print("domain.foods: ",domain.foods)
                    #print("domain.walls: ",domain.walls)
                    #print("domain.bodys: ",domain.bodys)
                    print(f"{Fore.CYAN}search states: {search_tree.stats} {Style.RESET_ALL}" )
                    print("full path: ", path)
                    if path != None:
                        if len(path) != 1: # ou seja chegou ao destino, em principio nao é preciso pq o dominio lida com isto automaticamente       
                            next_position = path[1]
                            move = get_move(domain, next_position)
                            key = get_command(move)
                        else:
                            print(f"{Fore.YELLOW}WARNING: em student.agent_loop, path apenas com 1 posicao, a food devia desaparecer do domain aintes de ser feita a pesquisa (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}WARNING: path == None apesar de domain.foods != [] (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                        if domain.foods != []:
                            print(f"{Fore.YELLOW}WARNING: em student.agent_loop, path deu None mas existem foods (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                        #next_position = wander()
                        next_position = explore()
                        if next_position != None:
                            move = get_move(domain, next_position)
                            key = get_command(move)
                        else:
                            print(f"{Fore.RED}WARNING: next_position == None (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                else:
                    #next_position = wander()
                    next_position = explore()
                    if next_position != None:
                        move = get_move(domain, next_position)
                        key = get_command(move)
                print("key: ", key)
                print("last_key: ", last_key)
                if (key == "" and 'map' not in state):
                    print(f"{Fore.RED}ERROR: key vazia (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                elif last_key != "" and is_opposite_key(last_key, key):
                    print(f"{Fore.RED}ERROR: , key oposta à anterior , last_key: {last_key}, key: {key} (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                
                #!: idealmente nao seria preciso
                if (key == "" and 'map' not in state) or (last_key != "" and is_opposite_key(last_key, key)):
                    print(f"{Fore.YELLOW}WARNING: , key corrected (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                    head = domain.head
                    actlist = domain.actions_results(head) 
                    if actlist == []:
                        print(f"{Fore.RED}ERROR: actlist vazia, head: {head} (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                    print("actlist: ", actlist)
                    possible_moves = []
                    #!: eliminar, apenas para verificacao de erros
                    for act in actlist:
                        if act in domain.head:
                            print(f"{Fore.RED}ERROR: act: {act} in domain.head: {domain.head} (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                        if act in domain.body:
                            print(f"{Fore.RED}ERROR: act: {act} in domain.body: {domain.body} (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                        if act in domain.bodys:
                            print(f"{Fore.RED}ERROR: act: {act} in domain.bodys: (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                        if tuple(act) in domain.walls:
                            print(f"{Fore.RED}ERROR: act: {act} in domain.walls: (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                        if domain.map[act[0]][act[1]] == WALL_COST:
                            print(f"{Fore.RED}ERROR: act: {act} with map_cost: {domain.map[act[0]][act[1]]} (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                        if domain.map[act[0]][act[1]] == BODY_COST:
                            print(f"{Fore.RED}ERROR: act: {act} with map_cost: {domain.map[act[0]][act[1]]} (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                    #+: verificar as coordenadas à volta 
                    for act in actlist:         
                        actlist2 = domain.actions_results(act)
                        if actlist2 != []: #+: significa que a proxima posicao (act) tem pelo menos uma outra proxima posicao possivel (act2)
                            possible_moves.append(act)    
                        #!: eliminar, apenas para verificacao de erros
                        for act2 in actlist2:
                            if act2 in domain.head:
                                print(f"{Fore.RED}ERROR: act: {act2} in domain.head: {domain.head} (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                            if act2 in domain.body:
                                print(f"{Fore.RED}ERROR: act: {act2} in domain.body: {domain.body} (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                            if act2 in domain.bodys:
                                print(f"{Fore.RED}ERROR: act: {act2} in domain.bodys: (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                            if tuple(act2) in domain.walls:
                                print(f"{Fore.RED}ERROR: act: {act2} in domain.walls: (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                            if domain.map[act2[0]][act2[1]] == WALL_COST:
                                print(f"{Fore.RED}ERROR: act: {act2} with map_cost: {domain.map[act2[0]][act2[1]]} (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                            if domain.map[act2[0]][act2[1]] == BODY_COST:
                                print(f"{Fore.RED}ERROR: act: {act2} with map_cost: {domain.map[act2[0]][act2[1]]} (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                    if possible_moves == []:
                        print(f"{Fore.RED}ERROR: possible_moves vazia (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                    keys = []
                    for possible_move in possible_moves:
                        move = get_move(domain, possible_move)
                        key = get_command(move)
                        if not is_opposite_key(last_key, key):
                            keys.append(key)
                    if keys == []:
                        print(f"{Fore.RED}ERROR: keys vazia (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                    else:
                        key = keys[0]
                        print("key_corrected: ", key)

                if (key == "" and 'map' not in state):
                    print(f"{Fore.RED}ERROR: key_corrected vazia (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                elif last_key != "" and is_opposite_key(last_key, key):
                    print(f"{Fore.RED}ERROR: , key_corrected oposta à anterior , last_key: {last_key}, key: {key} (arquivo {inspect.getfile(inspect.currentframe())},linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
                
                last_key = key
                end_ns = monotonic()
                elapsed_ns = end_ns - all_start_ns
                print(f"{Fore.BLUE}TIME: Total: elapsed_ns: {elapsed_ns}(linha {inspect.currentframe().f_lineno}){Style.RESET_ALL}")
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
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", args.name))

