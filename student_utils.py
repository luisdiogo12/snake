from colorama import Fore, Style

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