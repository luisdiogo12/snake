from colorama import Fore, Style, Back
import math
MAP_CELL_SIZE = 1


map_size = [48,24]
foods = [[23,12]]
DOMAIN_CHUNCK_SIZE = 5
map_limits = [[map_size[0]-1,map_size[1]-1],[0,0]]
chunk_size = 5
traverse = False
heads = [[3,2],[3,21],[44,2],[44,21],[24,2],[24,21],[3,12],[44,12]]#,[24,12]]
test_cases = [
    # State [3, 2]
    [
           # Limite [[8,7], [0,0]]
            [[0, 0], [4, 3], [9, 8]],    # Borda, Dentro, Fora
            # Limite [[47,7], [46,0]]
            [[46, 0], [46, 3], [48, 8]],  
            # Limite [[8,23], [0,21]]
            [[0, 21], [4, 22], [9, 24]],  
            # Limite [[47,23], [46,21]]
            [[46, 21], [46, 22], [48, 24]]  
        
    ],
    
    # State [3, 21]
    [
        # Limite [[8,23], [0,16]]
        [[0, 16], [4, 19], [9, 24]],    
        # Limite [[8,2], [0,0]]
        [[0, 0], [4, 1], [9, 8]],       
        # Limite [[47,23], [46,16]]
        [[46, 16], [46, 19], [48, 24]],  
        # Limite [[47,2], [46,0]]
        [[46, 0], [46, 1], [48, 8]]      
    ],
    
    # State [44, 2]
    [
        # Limite [[47,7], [39,0]]
        [[39, 0], [43, 3], [48, 8]],    
        # Limite [[1,7], [0,0]]
        [[0, 0], [0, 3], [2, 8]],       
        # Limite [[47,23], [39,21]]
        [[39, 21], [43, 22], [48, 24]],  
        # Limite [[1,23], [0,21]]
        [[0, 21], [0, 22], [2, 24]]     
    ],
    
    # State [44, 21]
    [
        # Limite [[47,23], [39,16]]
        [[39, 16], [43, 19], [48, 24]],  
        # Limite [[1,23], [0,16]]
        [[0, 16], [0, 19], [2, 24]],     
        # Limite [[47,2], [39,0]]
        [[39, 0], [43, 1], [48, 8]],     
        # Limite [[1,2], [0,0]]
        [[0, 0], [0, 1], [2, 8]]        
    ],
    
    # State [24, 2]
    [
        # Limite [[29,7], [19,0]]
        [[19, 0], [24, 3], [30, 8]],    
        # Limite [[29,23], [19,21]]
        [[19, 21], [24, 22], [30, 24]]  
    ],
    
    # State [24, 21]
    [
        # Limite [[29,23], [19,16]]
        [[19, 16], [24, 19], [30, 24]],  
        # Limite [[29,2], [19,0]]
        [[19, 0], [24, 1], [30, 8]]      
    ],
    
    # State [3, 12]
    [
        # Limite [[8,17], [0,7]]
        [[0, 7], [4, 12], [9, 24]],      
        # Limite [[47,17], [46,7]]
        [[46, 7], [46, 12], [48, 24]]    
    ],
    
    # State [44, 12]
    [
        # Limite [[47,17], [39,7]]
        [[39, 7], [43, 12], [48, 24]],   
        # Limite [[1,17], [0,7]]
        [[0, 7], [0, 12], [2, 24]]       
    ]
]

""" traverse = False
heads = [[24,12],[10,10],[3,3]]
test_cases = [[[[29,10],[5,5]]],[[[5,5],[29,10]]],[[[0,0],[8,5],[10,12]]]] """

def print_map(arr):
    if arr is not None:
        for x in range(map_size[1]):
            row = []
            for y in range(map_size[0]):
                value = 0
                size1 = math.floor((MAP_CELL_SIZE-len(str(value)))/2)
                size2 = MAP_CELL_SIZE - size1 - len(str(value))
                colored_value = size1 * " "+f"{Style.RESET_ALL}{value}"+size2 * " "
                #print([y,x])
                if [y,x] in arr:
                    colored_value = size1 * " "+f"{Back.CYAN}{1}{Style.RESET_ALL}"+size2 * " "
                row.append(colored_value)
            print(" ".join(row))
def get_new_state_limits_old(state, chunk_limits_cru, chunk_limits, map_limits):
    def get_extensive_state_limits(case,chunked_limits):
        width, height = map_size
        extensive_state_limits = []
        test_extensive_state_limits = []
        for limits in chunked_limits:
            minx = limits[1][1]
            maxx = limits[0][1]
            miny = limits[1][0]
            maxy = limits[0][0]
            for x in range(minx,maxx+1):
                extensive_state_limits.append([miny,x])
                extensive_state_limits.append([maxy,x])
            for y in range(miny+1,maxy):
                extensive_state_limits.append([y,minx])
                extensive_state_limits.append([y,maxx])
        for x in range(height):
            for y in range(width):
                for limits in chunked_limits:
                    if  (((y == limits[0][0] or y == limits[1][0]) 
                        and (x<=limits[0][1] and x>=limits[1][1]) 
                        )or ((x == limits[0][1] or x == limits[1][1]) 
                        and (y<=limits[0][0] and y>=limits[1][0])
                        )):
                        test_extensive_state_limits.append([y,x])
        #print("extensive_state_limits: ",extensive_state_limits)
        #print("test_extensive_state_limits: ",test_extensive_state_limits)
        """ if case == 0:
            return extensive_state_limits
        elif case == 1:
            limits_to_remove = []
            
        elif case == 2:
        elif case == 3:
        elif case == 4:
        elif case == 5:
        elif case == 6:
        elif case == 7:
        elif case == 8: """
                    
    new_state_limits = []
    caso = 0
    # Caso 1: [3,2]
    if (chunk_limits_cru[0][0] <= map_limits[0][0] and
        chunk_limits_cru[0][1] < map_limits[0][1] and
        chunk_limits_cru[1][0] < map_limits[1][0] and
        chunk_limits_cru[1][1] < map_limits[1][1]):
        caso = 1
        new_state_limits = [[[chunk_limits[0][0], chunk_limits[0][1]], [0, 0]], [[map_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], 0]], [[chunk_limits[0][0], map_limits[0][1]], [0, chunk_limits[1][1]]], [[map_limits[0][0], map_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]]]
        #new_state_limits=  [[[chunk_limits[0][0], chunk_limits[0][1]]], [[chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[1][1]]], [[chunk_limits[1][0], chunk_limits[1][1]]]]
    # Caso 2: [3,21]
    elif (chunk_limits_cru[0][0] <= map_limits[0][0] and
          chunk_limits_cru[0][1] > map_limits[0][1] and
          chunk_limits_cru[1][0] < map_limits[1][0] and
          chunk_limits_cru[1][1] >= map_limits[1][1]):
        caso = 2
        new_state_limits = [[[chunk_limits[0][0], map_limits[0][1]], [0, chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[0][1]], [0, 0]], [[map_limits[0][0], map_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[map_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], 0]]]
        #new_state_limits=  [[[chunk_limits[0][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[0][1]]], [[chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[1][0], chunk_limits[0][1]]]]
    # Caso 3: [44,2]
    elif (chunk_limits_cru[0][0] > map_limits[0][0] and
          chunk_limits_cru[0][1] < map_limits[0][1] and
          chunk_limits_cru[1][0] >= map_limits[1][0] and
          chunk_limits_cru[1][1] < map_limits[1][1]):
        caso = 3
        new_state_limits = [[[map_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], 0]], [[chunk_limits[0][0], chunk_limits[0][1]], [0, 0]], [[map_limits[0][0], map_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], map_limits[0][1]], [0, chunk_limits[1][1]]]]
        #new_state_limits=  [[[chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[0][1]]], [[chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[1][1]]]]
    # Caso 4: [44,21]
    elif (chunk_limits_cru[0][0] > map_limits[0][0] and
          chunk_limits_cru[0][1] > map_limits[0][1] and
          chunk_limits_cru[1][0] >= map_limits[1][0] and
          chunk_limits_cru[1][1] >= map_limits[1][1]):
        caso = 4
        new_state_limits = [[[map_limits[0][0], map_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], map_limits[0][1]], [0, chunk_limits[1][1]]], [[map_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], 0]], [[chunk_limits[0][0], chunk_limits[0][1]], [0, 0]]]
        #new_state_limits=  [[[chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[1][1]]], [[chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[0][1]]]]
    # Caso 5: [24,2]
    elif (chunk_limits_cru[0][0] <= map_limits[0][0] and
          chunk_limits_cru[0][1] < map_limits[0][1] and
          chunk_limits_cru[1][0] >= map_limits[1][0] and
          chunk_limits_cru[1][1] < map_limits[1][1]):
        caso = 5
        new_state_limits = [
            [[chunk_limits[0][0], chunk_limits[0][1]], 
             [chunk_limits[1][0], 0]],
            [[chunk_limits[0][0], map_limits[0][1]], 
             [chunk_limits[1][0], chunk_limits[1][1]]]
        ]
        #new_state_limits=  [[[chunk_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[1][1]], [chunk_limits[1][0], chunk_limits[1][1]]]]
    # Caso 6: [24,21]
    elif (chunk_limits_cru[0][0] <= map_limits[0][0] and
          chunk_limits_cru[0][1] > map_limits[0][1] and
          chunk_limits_cru[1][0] >= map_limits[1][0] and
          chunk_limits_cru[1][1] >= map_limits[1][1]):
        caso = 6
        new_state_limits = [
            [[chunk_limits[0][0], map_limits[0][1]], 
             [chunk_limits[1][0], chunk_limits[1][1]]],
            [[chunk_limits[0][0], chunk_limits[0][1]], 
             [chunk_limits[1][0], 0]]
        ]
        #new_state_limits=  [[[chunk_limits[0][0], chunk_limits[1][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], chunk_limits[0][1]]]]
    # Caso 7: [3,12]
    elif (chunk_limits_cru[0][0] <= map_limits[0][0] and
          chunk_limits_cru[0][1] < map_limits[0][1] and
          chunk_limits_cru[1][0] < map_limits[1][0] and
          chunk_limits_cru[1][1] >= map_limits[1][1]):
        caso = 7
        new_state_limits = [
            [[chunk_limits[0][0], chunk_limits[0][1]], 
             [0, chunk_limits[1][1]]],
            [[map_limits[0][0], chunk_limits[0][1]], 
             [chunk_limits[1][0], chunk_limits[1][1]]]
        ]
        #new_state_limits=  [[[chunk_limits[0][0], chunk_limits[0][1]], [chunk_limits[0][0], chunk_limits[1][1]]], [[chunk_limits[1][0], chunk_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]]]
    # Caso 8: [44,12]
    elif (chunk_limits_cru[0][0] > map_limits[0][0] and
          chunk_limits_cru[0][1] < map_limits[0][1] and
          chunk_limits_cru[1][0] >= map_limits[1][0] and
          chunk_limits_cru[1][1] >= map_limits[1][1]):
        caso = 8
        new_state_limits = [
            [[map_limits[0][0], chunk_limits[0][1]], 
             [chunk_limits[1][0], chunk_limits[1][1]]],
            [[chunk_limits[0][0], chunk_limits[0][1]], 
             [0, chunk_limits[1][1]]]
        ]
        #new_state_limits=  [[[chunk_limits[1][0], chunk_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[0][1]], [chunk_limits[0][0], chunk_limits[1][1]]]]
    else:
        caso = 0
        new_state_limits = chunk_limits
    get_extensive_state_limits(caso,new_state_limits)
    return new_state_limits
def get_new_state_limits(state, chunk_limits_cru, chunk_limits, map_limits):
    print("chunk_limits_cru: ",chunk_limits_cru)
    print("chunk_limits: ",chunk_limits)
    def get_extensive_state_limits(case,chunked_limits):
        extensive_state_limits = []
        extensive_state_limits_set = set()
        print("chunked_limits: ",chunked_limits)
        colors = []
        if case == 0 or case == 9:
            for x in range(chunked_limits[0][1][1],  chunked_limits[0][0][1]+1):   
                extensive_state_limits.append([chunked_limits[0][0][0],x])
                extensive_state_limits_set.add((chunked_limits[0][0][0],x))
                extensive_state_limits.append([chunked_limits[0][1][0],x])
                extensive_state_limits_set.add((chunked_limits[0][1][0],x))
            for y in range(chunked_limits[0][1][0],  chunked_limits[0][0][0]):   
                extensive_state_limits.append([y,chunked_limits[0][0][1]])
                extensive_state_limits_set.add((y,chunked_limits[0][0][1]))
                extensive_state_limits.append([y,chunked_limits[0][1][1]]) 
                extensive_state_limits_set.add((y,chunked_limits[0][1][1]))    
        if case == 1 or case == 2 or case == 3 or case == 4:
            #1º valores y maiores primeiro , 2º valores x maiores primeiro 
            for y in range(chunked_limits[0][0][0],  map_limits[0][0]+1): # certo
                extensive_state_limits.append([y,chunked_limits[0][0][1]])
                extensive_state_limits_set.add((y,chunked_limits[0][0][1]))
                extensive_state_limits.append([y,chunked_limits[0][1][1]])
                extensive_state_limits_set.add((y,chunked_limits[0][1][1]))
            for y in range(map_limits[1][0], chunked_limits[1][1][0]+1):
                extensive_state_limits.append([y,chunked_limits[1][0][1]])
                extensive_state_limits_set.add((y,chunked_limits[1][0][1]))
                extensive_state_limits.append([y,chunked_limits[1][1][1]])
                extensive_state_limits_set.add((y,chunked_limits[1][1][1]))
            
            for x in range(chunked_limits[0][0][1],  map_limits[0][1]+1):
                extensive_state_limits.append([chunked_limits[0][0][0],x])
                extensive_state_limits_set.add((chunked_limits[0][0][0],x))
                extensive_state_limits.append([chunked_limits[1][1][0],x])
                extensive_state_limits_set.add((chunked_limits[1][1][0],x))
            for x in range(map_limits[1][1], chunked_limits[0][1][1]+1):
                extensive_state_limits.append([chunked_limits[0][1][0],x])
                extensive_state_limits_set.add((chunked_limits[0][1][0],x))
                extensive_state_limits.append([chunked_limits[1][1][0],x])
                extensive_state_limits_set.add((chunked_limits[1][1][0],x))
        elif case == 5 or case == 6:
            for y in range(chunked_limits[0][0][0],  map_limits[0][0]+1):
                extensive_state_limits.append([y,chunked_limits[0][0][1]])
                extensive_state_limits_set.add((y,chunked_limits[0][0][1]))
                extensive_state_limits.append([y,chunked_limits[0][1][1]])
                extensive_state_limits_set.add((y,chunked_limits[0][1][1]))
            for y in range(map_limits[1][0], chunked_limits[1][1][0]+1):
                extensive_state_limits.append([y,chunked_limits[1][0][1]])
                extensive_state_limits_set.add((y,chunked_limits[1][0][1]))
                extensive_state_limits.append([y,chunked_limits[1][1][1]])
                extensive_state_limits_set.add((y,chunked_limits[1][1][1]))
            
            for x in range(chunked_limits[0][1][1],  chunked_limits[0][0][1]+1):
                extensive_state_limits.append([chunked_limits[0][0][0],x])
                extensive_state_limits_set.add((chunked_limits[0][0][0],x))
                extensive_state_limits.append([chunked_limits[1][0][0],x])
                extensive_state_limits_set.add((chunked_limits[1][0][0],x))
        elif case == 7 or case == 8:
            for y in range(chunked_limits[1][1][0],  chunked_limits[0][0][0]+1):
                extensive_state_limits.append([y,chunked_limits[0][0][1]])
                extensive_state_limits_set.add((y,chunked_limits[0][0][1]))
                extensive_state_limits.append([y,chunked_limits[0][1][1]])
                extensive_state_limits_set.add((y,chunked_limits[0][1][1]))
            
            for x in range(chunked_limits[0][0][1],  map_limits[0][1]+1):
                extensive_state_limits.append([chunked_limits[0][0][0],x])
                extensive_state_limits_set.add((chunked_limits[0][0][0],x))
                extensive_state_limits.append([chunked_limits[1][1][0],x])
                extensive_state_limits_set.add((chunked_limits[1][1][0],x))
            for x in range(map_limits[1][1], chunked_limits[0][1][1]+1):
                extensive_state_limits.append([chunked_limits[0][1][0],x])
                extensive_state_limits_set.add((chunked_limits[0][1][0],x))
                extensive_state_limits.append([chunked_limits[1][1][0],x])
                extensive_state_limits_set.add((chunked_limits[1][1][0],x))
        print("extensive_state_limits: ",extensive_state_limits)
        print("extensive_state_limits_set: ",extensive_state_limits_set)
        return extensive_state_limits

    new_state_limits = []
    caso = 0
    # Caso 1: [3,2]
    if len(chunk_limits) == 1:
        caso = 0
        new_state_limits = chunk_limits
    elif len(chunk_limits) == 2:
        if (chunk_limits_cru[0][0] <= map_limits[0][0] and
            chunk_limits_cru[0][1] < map_limits[0][1] and
            chunk_limits_cru[1][0] < map_limits[1][0] and
            chunk_limits_cru[1][1] < map_limits[1][1]):
            caso = 1
            #new_state_limits = [[[chunk_limits[0][0], chunk_limits[0][1]], [0, 0]], [[map_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], 0]], [[chunk_limits[0][0], map_limits[0][1]], [0, chunk_limits[1][1]]], [[map_limits[0][0], map_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]]]
            #new_state_limits=  [[[chunk_limits[0][0], chunk_limits[0][1]]], [[chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[1][1]]], [[chunk_limits[1][0], chunk_limits[1][1]]]]
            new_state_limits=  [[[chunk_limits[1][0], chunk_limits[1][1]], [chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[1][1]], [chunk_limits[0][0], chunk_limits[0][1]]]]    # Caso 2: [3,21]
        
        # Caso 2: [3,21]
        elif (chunk_limits_cru[0][0] <= map_limits[0][0] and
            chunk_limits_cru[0][1] > map_limits[0][1] and
            chunk_limits_cru[1][0] < map_limits[1][0] and
            chunk_limits_cru[1][1] >= map_limits[1][1]):
            caso = 2
            #new_state_limits = [[[chunk_limits[0][0], map_limits[0][1]], [0, chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[0][1]], [0, 0]], [[map_limits[0][0], map_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[map_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], 0]]]
            #new_state_limits=  [[[chunk_limits[0][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[0][1]]], [[chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[1][0], chunk_limits[0][1]]]]
            new_state_limits=  [[[chunk_limits[1][0], chunk_limits[1][1]], [chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[1][1]], [chunk_limits[0][0], chunk_limits[0][1]]]]    
        # Caso 3: [44,2]
        elif (chunk_limits_cru[0][0] > map_limits[0][0] and
            chunk_limits_cru[0][1] < map_limits[0][1] and
            chunk_limits_cru[1][0] >= map_limits[1][0] and
            chunk_limits_cru[1][1] < map_limits[1][1]):
            caso = 3
            #new_state_limits = [[[map_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], 0]], [[chunk_limits[0][0], chunk_limits[0][1]], [0, 0]], [[map_limits[0][0], map_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], map_limits[0][1]], [0, chunk_limits[1][1]]]]
            #new_state_limits=  [[[chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[0][1]]], [[chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[1][1]]]]
            new_state_limits=  [[[chunk_limits[1][0], chunk_limits[1][1]], [chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[1][1]], [chunk_limits[0][0], chunk_limits[0][1]]]]    
        # Caso 4: [44,21]
        elif (chunk_limits_cru[0][0] > map_limits[0][0] and
            chunk_limits_cru[0][1] > map_limits[0][1] and
            chunk_limits_cru[1][0] >= map_limits[1][0] and
            chunk_limits_cru[1][1] >= map_limits[1][1]):
            caso = 4
            #new_state_limits = [[[map_limits[0][0], map_limits[0][1]], [chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], map_limits[0][1]], [0, chunk_limits[1][1]]], [[map_limits[0][0], chunk_limits[0][1]], [chunk_limits[1][0], 0]], [[chunk_limits[0][0], chunk_limits[0][1]], [0, 0]]]
            #new_state_limits=  [[[chunk_limits[1][0], chunk_limits[1][1]]], [[chunk_limits[0][0], chunk_limits[1][1]]], [[chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[0][1]]]]
            new_state_limits=  [[[chunk_limits[1][0], chunk_limits[1][1]], [chunk_limits[1][0], chunk_limits[0][1]]], [[chunk_limits[0][0], chunk_limits[1][1]], [chunk_limits[0][0], chunk_limits[0][1]]]]    
        # Caso 5: [24,2]
        elif (chunk_limits_cru[0][0] <= map_limits[0][0] and
            chunk_limits_cru[0][1] < map_limits[0][1] and
            chunk_limits_cru[1][0] >= map_limits[1][0] and
            chunk_limits_cru[1][1] < map_limits[1][1]):
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
        elif (chunk_limits_cru[0][0] <= map_limits[0][0] and
            chunk_limits_cru[0][1] > map_limits[0][1] and
            chunk_limits_cru[1][0] >= map_limits[1][0] and
            chunk_limits_cru[1][1] >= map_limits[1][1]):
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
        elif (chunk_limits_cru[0][0] <= map_limits[0][0] and
            chunk_limits_cru[0][1] < map_limits[0][1] and
            chunk_limits_cru[1][0] < map_limits[1][0] and
            chunk_limits_cru[1][1] >= map_limits[1][1]):
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
        elif (chunk_limits_cru[0][0] > map_limits[0][0] and
            chunk_limits_cru[0][1] < map_limits[0][1] and
            chunk_limits_cru[1][0] >= map_limits[1][0] and
            chunk_limits_cru[1][1] >= map_limits[1][1]):
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
            new_state_limits = chunk_limits
    else:
        print("ERROR len(chunk_limits) != de 1 ou 2")
    extensive_new_state_limits = get_extensive_state_limits(caso,new_state_limits)
    print_map(extensive_new_state_limits)
    return new_state_limits

#!: por no self.map_limits
map_limits = [[map_size[0]-1,map_size[1]-1],[0,0]]
def satisfie(selfhead, state, goal):
    for food_pos in goal:
        #print("food_pos", food_pos)
        if state == food_pos:
            return True
    chunk_limits_teleport = [[selfhead[0]+DOMAIN_CHUNCK_SIZE,selfhead[1]+DOMAIN_CHUNCK_SIZE],[selfhead[0]-DOMAIN_CHUNCK_SIZE,selfhead[1]-DOMAIN_CHUNCK_SIZE]]
    if traverse:
        chunk_limits = [[(selfhead[0]+DOMAIN_CHUNCK_SIZE)% map_size[0],(selfhead[1]+DOMAIN_CHUNCK_SIZE)% map_size[1]],[(selfhead[0]-DOMAIN_CHUNCK_SIZE)% map_size[0],(selfhead[1]-DOMAIN_CHUNCK_SIZE)% map_size[1]]]
        #print("chunk_limits_teleport: ", chunk_limits_teleport)
        #print("chunk_limits: ", chunk_limits)
        #print("map_limits: ", map_limits)
        chunked_limits = get_new_state_limits(selfhead, chunk_limits_teleport, chunk_limits, map_limits)
        #result = get_new_state_limits(state, chunk_limits_cru, chunk_limits, map_limits)
    else:
        chunked_limits = [[[max(0, min(limit, map_size[i] - 1)) for i, limit in enumerate(chunk)]for chunk in chunk_limits_teleport]]
        print("chunked_limits: ", chunked_limits)
        get_new_state_limits(selfhead, chunk_limits_teleport, chunked_limits, map_limits)
        """ chunked_limits = []
        for goal in test_goals:
            if goal[0] > chunk_limits[0][0]:
                goal[0] = chunk_limits[0][0]
            elif goal[0] < chunk_limits[1][0]:
                goal[0] = chunk_limits[1][0]
            if goal[1] > chunk_limits[0][1]:
                goal[1] = chunk_limits[0][1]
            elif goal[1] < chunk_limits[1][1]:
                goal[1] = chunk_limits[1][1]
            chunked_limits.append(goal) """
    print("chunked_limits: ", chunked_limits)
    """ for limits in chunked_limits:
        if ((state[0] == limits[0][0] or state[0] == limits[1][0]) and (state[1]>=limits[0][1] or state[1]>=limits[1][1])) or ((state[1] == limits[0][1] or state[1] == limits[1][1]) and (state[0]>=limits[0][0] or state[0]>=limits[1][0])):
            return True """
    return False
for i,head in  enumerate(heads):
    print(f"{Fore.BLUE}head: {head}{Style.RESET_ALL}")
    state_cases = test_cases[i]
    for j, states in enumerate(state_cases):
        for k, state in enumerate(states):
            print(f"state: {state}")
            sat = satisfie(head, state, foods)
            if sat:
                print(f"{Fore.GREEN}sat: {sat}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}sat: {sat}{Style.RESET_ALL}")

print("------------\n------------")    
#sat = satisfie(state, foods)
#print("sat: ", sat)
""" chunk_limits_cru = [[state[0]+DOMAIN_CHUNCK_SIZE,state[1]+DOMAIN_CHUNCK_SIZE],[state[0]-DOMAIN_CHUNCK_SIZE,state[1]-DOMAIN_CHUNCK_SIZE]]
print("chunk_limits_cru: ", chunk_limits_cru)
test_goals = [[23,12],[0,23],[10,11],[42,23]]
if traverse:
    chunk_limits = [[(state[0]+DOMAIN_CHUNCK_SIZE)% map_size[0],(state[1]+DOMAIN_CHUNCK_SIZE)% map_size[1]],[(state[0]-DOMAIN_CHUNCK_SIZE)% map_size[0],(state[1]-DOMAIN_CHUNCK_SIZE)% map_size[1]]]
    map_limits = [[map_size[0]-1,map_size[1]-1],[0,0]]
    chunked_test_goals = get_new_state_limits(state, chunk_limits_cru, chunk_limits, map_limits)
else:
    chunk_limits = [[state[0]+DOMAIN_CHUNCK_SIZE,state[1]+DOMAIN_CHUNCK_SIZE],[state[0]-DOMAIN_CHUNCK_SIZE,state[1]-DOMAIN_CHUNCK_SIZE]]
    chunk_limits = [[max(0, min(limit, map_size[i] - 1)) for i, limit in enumerate(chunk)]for chunk in chunk_limits]
    chunked_test_goals = []
    for goal in test_goals:
        if goal[0] > chunk_limits[0][0]:
            goal[0] = chunk_limits[0][0]
        elif goal[0] < chunk_limits[1][0]:
            goal[0] = chunk_limits[1][0]
        if goal[1] > chunk_limits[0][1]:
            goal[1] = chunk_limits[0][1]
        elif goal[1] < chunk_limits[1][1]:
            goal[1] = chunk_limits[1][1]
        chunked_test_goals.append(goal)
            
        
print("chunk_limits: ", chunk_limits)
print("chunked_test_goals: ", chunked_test_goals)

print("---") """
""" map_size = [9,8]
map_limits = [[map_size[0]-1,map_size[1]-1],[0,0]]
chunk_size = 3
states = [[2,1],[2,6],[7,2],[7,5],[4,0],[1,3],[7,4],[4,5]]
limits =[[[[5,4],[0,0]],[[8,4],[8,0]],[[5,7],[0,6]]],
         [[[5,7],[0,3]],[[5,1],[0,0]],[[8,7],[8,0]]],
         [[[8,5],[4,0]],[[1,5],[0,0]],[[8,7],[4,7]]],
         [[[8,7],[4,2]],[[1,7],[1,2]],[[8,0],[4,0]]],
         [[[7,3],[1,0]],[[7,7],[1,5]]],
         [[[1,6],[0,0]],[[8,6],[7,0]]],
         [[[1,7],[0,1]],[[8,7],[7,1]]],
         [[[7,0],[1,0]],[[7,1],[1,2]]],] """
map_size = [48,24]
map_limits = [[map_size[0]-1,map_size[1]-1],[0,0]]
chunk_size = 5
states = [[3,2],[3,21],[44,2],[44,21],[24,2],[24,21],[3,12],[44,12]]
limits =[[[[8,7],[0,0]],[[47,7],[46,0]],[[8,23],[0,21]],[[47,23],[46,21]]],
         [[[8,23],[0,16]],[[8,2],[0,0]],[[47,23],[46,16]],[[47,2],[46,0]]],
         [[[47,7],[39,0]],[[1,7],[0,0]],[[47,23],[39,21]], [[1,23],[0,21]]],
         [[[47,23],[39,16]],[[1,23],[0,16]],[[47,2],[39,0]], [[1,2],[0,0]]],
         [[[29,7],[19,0]],[[29,23],[19,21]]],
         [[[29,23],[19,16]],[[29,2],[19,0]]],
         [[[8,17],[0,7]],[[47,17],[46,7]]],
         [[[47,17],[39,7]],[[1,17],[0,7]]],] 
for limit in limits:
    for lim in limit:
        if lim[0][0] < lim[1][0]:
            print("lim[0][0] < lim[1][0]")
            print(lim)
        if lim[0][1] < lim[1][1]:
            print("lim[0][1] < lim[1][1]")
            print(lim)
""" states = []
for y in range(map_size[1]):
    for x in range(map_size[0]):
        states.append([x,y]) """
for i,state in  enumerate(states):
    print("state: ", state)
    chunk_limits_cru = [[state[0]+chunk_size,state[1]+chunk_size],[state[0]-chunk_size,state[1]-chunk_size]]
    print("chunk_limits_cru: ", chunk_limits_cru)
    chunk_limits = [[(state[0]+chunk_size)% map_size[0],(state[1]+chunk_size)% map_size[1]],[(state[0]-chunk_size)% map_size[0],(state[1]-chunk_size)% map_size[1]]]
    print("chunk_limits: ", chunk_limits)
    """ if(chunk_limits[0][0] < chunk_limits[1][0] ):
        if(chunk_limits[0][1] < chunk_limits[1][1]):
            print("My<my Mx<mx")
        else:
            print(f"{Back.BLUE}My<my Mx>mx{Style.RESET_ALL}")
    else:
        if(chunk_limits[0][1] < chunk_limits[1][1]):
            print(f"{Back.BLUE}My>my Mx<mx{Style.RESET_ALL}")
        else:
            print("My>my Mx>mx") """
    if chunk_limits_cru[0][0]>map_limits[0][0]:
        if chunk_limits_cru[0][1]>map_limits[0][1]:
            print(f"{Back.BLUE}chunk_limits_cru[0][0]>map_limits[0][0] chunk_limits_cru[0][1]>map_limits[0][1]{Style.RESET_ALL}")
        else:
            print(f"{Back.BLUE}chunk_limits_cru[0][0]>map_limits[0][0] chunk_limits_cru[0][1]<map_limits[0][1]{Style.RESET_ALL}")
    else:
        if chunk_limits_cru[0][1]>map_limits[0][1]:
            print(f"{Back.BLUE}chunk_limits_cru[0][0]<=map_limits[0][0] chunk_limits_cru[0][1]>map_limits[0][1]{Style.RESET_ALL}")
        else:
            print(f"{Back.BLUE}chunk_limits_cru[0][0]<=map_limits[0][0] chunk_limits_cru[0][1]<map_limits[0][1]{Style.RESET_ALL}")
    if chunk_limits_cru[1][0]<0:
        if chunk_limits_cru[1][1]<0:
            print(f"{Back.BLUE}chunk_limits_cru[1][0]<map_limits[1][0] chunk_limits_cru[1][1]<map_limits[1][1]{Style.RESET_ALL}")
        else:
            print(f"{Back.BLUE}chunk_limits_cru[1][0]<map_limits[1][0] chunk_limits_cru[1][1]>=map_limits[1][1]{Style.RESET_ALL}")
    else:
        if chunk_limits_cru[1][1]<0:
            print(f"{Back.BLUE}chunk_limits_cru[1][0]>=map_limits[1][0] chunk_limits_cru[1][1]<map_limits[1][1]{Style.RESET_ALL}")
        else:
            print(f"{Back.BLUE}chunk_limits_cru[1][0]>=map_limits[1][0] chunk_limits_cru[1][1]>=map_limits[1][1]{Style.RESET_ALL}")
    state_limits = limits[i]
    #print("limits: ", state_limits)
    new_state_limits = []
    for limit in state_limits:
        #print("limit: ",limit)
        new_limit = []
        for m in limit:
            #print("m: ", m)
            new_m = []
            for n in m:
                #print("n: ", n)
                result = ""  # Inicializa a string resultante

                if n == chunk_limits[0][0]:
                    result += "chunk_limits[0][0]"
                if n == chunk_limits[0][1]:
                    result += "chunk_limits[0][1]"
                if n == chunk_limits[1][0]:
                    result += "chunk_limits[1][0]"
                if n == chunk_limits[1][1]:
                    result += "chunk_limits[1][1]"
                if n == map_limits[0][0]:
                    result += "map_limits[0][0]"
                if n == map_limits[0][1]:
                    result += "map_limits[0][1]"
                if n == map_limits[1][0]:
                    result += "map_limits[1][0]"
                if n == map_limits[1][1]:
                    result += "map_limits[1][1]"

                new_m.append(result)
            new_limit.append(new_m)
        new_state_limits.append(new_limit)
    print("new_state_limits: ", new_state_limits)
    print("limits: ", limits[i])
    result = get_new_state_limits(state, chunk_limits_cru, chunk_limits, map_limits)
    print("result: ", result)
    old_result = get_new_state_limits_old(state, chunk_limits_cru, chunk_limits, map_limits)
    print("old_result: ", old_result)
    n_elements = 0
    for limit in result:
        for m in limit:
            n_elements += 1
    
    new_result = []
    for limit in result:
        new_limit = []
        for m in limit:
            new_m = [0,0]
            for i,n in enumerate(m):
                if n != 0 and n != map_limits[0][0] and n != map_limits[0][1]:
                    new_m[i] = n
            new_limit.append(new_m)
        #print("new_limit: ", new_limit)
        if n_elements == 8:
            resultado = []
            max_length = max(len(sub) for sub in new_limit) if new_limit else 0
            # Itera por cada posição de índice nos subarrays
            for i in range(max_length):
                # Coleta elementos de todos os subarrays na posição i
                elementos = []
                for sub in new_limit:
                    if i < len(sub):  # Verifica se o índice existe no subarray
                        elementos.append(sub[i])
                
                # Filtra zeros e adiciona ao resultado
                filtrados = [num for num in elementos if num != 0]
                resultado.extend(filtrados)
            #print("resultado: ", resultado)
        elif n_elements == 4:
            colunas = list(zip(*new_limit))
            novas_colunas = []
            
            for coluna in colunas:
                # Encontra o primeiro valor não-zero na coluna
                substituto = next((num for num in coluna if num != 0), 0)
                # Substitui os zeros pelo substituto encontrado
                nova_coluna = [substituto if num == 0 else num for num in coluna]
                novas_colunas.append(nova_coluna)
            
            # Transpõe de volta para linhas e converte para listas
            resultado = [list(linha) for linha in zip(*novas_colunas)]
        else:
            print("<<<<<<<<<<<<<<<<ERROR>>>>>>>>>>>>>>>>")
            print("n_elements: ", n_elements)
            print("new_limit: ", new_limit)
        new_result.append(resultado)
    print("new_result: ", new_result)
    def organizar_array(arr):
        # Passo 1: "Achatar" o array para obter todos os pares [x, y]
        flattened = [elem for sublist in arr for elem in sublist]
        
        # Passo 2: Agrupar os elementos pelo valor de `x`
        grupos = {}
        for x, y in flattened:
            if x not in grupos:
                grupos[x] = []
            grupos[x].append([x, y])
        
        # Passo 3: Ordenar cada grupo por `y` decrescente
        grupos_ordenados = []
        for x in grupos:
            # Ordena os elementos do grupo por `y` decrescente e `x` decrescente (para desempate)
            grupo = sorted(grupos[x], key=lambda coord: (-coord[1], -coord[0]))
            grupos_ordenados.append(grupo)
        
        # Passo 4: Ordenar os grupos pelo critério principal (maior `y` do grupo) e secundário (maior `x`)
        grupos_ordenados.sort(key=lambda g: (-g[0][1], -g[0][0]))
        
        return grupos_ordenados
    ordered_new_result = organizar_array(new_result)
    print("ordered_new_result: ", ordered_new_result)
    new_state_limits = []
    for limit in ordered_new_result:
        #print("limit: ",limit)
        new_limit = []
        if n_elements == 8:
            limit = [limit]
        for m in limit:
            #print("m: ", m)
            new_m = []
            for n in m:
                #print("n: ", n)
                result = ""  # Inicializa a string resultante

                if n == chunk_limits[0][0]:
                    result += "chunk_limits[0][0]"
                if n == chunk_limits[0][1]:
                    result += "chunk_limits[0][1]"
                if n == chunk_limits[1][0]:
                    result += "chunk_limits[1][0]"
                if n == chunk_limits[1][1]:
                    result += "chunk_limits[1][1]"
                if n == map_limits[0][0]:
                    result += "map_limits[0][0]"
                if n == map_limits[0][1]:
                    result += "map_limits[0][1]"
                if n == map_limits[1][0]:
                    result += "map_limits[1][0]"
                if n == map_limits[1][1]:
                    result += "map_limits[1][1]"

                new_m.append(result)
            new_limit.append(new_m)
        new_state_limits.append(new_limit)
    print("new_state_limits: ", new_state_limits)
                
            
    """ x1, x2 = chunk_limits_cru[0]
    y1, y2 = chunk_limits_cru[1]
    prev_state_limits = []
    if x1 > 0 and x2 > 0:
        if y1 < 0 and y2 < 0:
            prev_state_limits = [[['chunk_limits[0][0]-', 'chunk_limits[0][1]-'], 
                     ['map_limits[1][0]-map_limits[1][1]-', 'map_limits[1][0]-map_limits[1][1]-']],
                    [['chunk_limits[1][0]-map_limits[0][0]-', 'chunk_limits[0][1]-'], 
                     ['chunk_limits[1][0]-map_limits[0][0]-', 'map_limits[1][0]-map_limits[1][1]-']],
                    [['chunk_limits[0][0]-', 'map_limits[0][1]-'], 
                     ['map_limits[1][0]-map_limits[1][1]-', 'chunk_limits[1][1]-']]]
        elif y1 < 0 and y2 > 0:
            prev_state_limits = [[['chunk_limits[0][0]-', 'map_limits[0][1]-'], 
                     ['map_limits[1][0]-map_limits[1][1]-', 'chunk_limits[1][1]-']],
                    [['chunk_limits[0][0]-', 'chunk_limits[0][1]-'], 
                     ['map_limits[1][0]-map_limits[1][1]-', 'map_limits[1][0]-map_limits[1][1]-']],
                    [['chunk_limits[1][0]-map_limits[0][0]-', 'map_limits[0][1]-'], 
                     ['chunk_limits[1][0]-map_limits[0][0]-', 'map_limits[1][0]-map_limits[1][1]-']]]
        elif y1 > 0 and y2 < 0:
            prev_state_limits = [[['map_limits[0][0]-', 'chunk_limits[0][1]-'], 
                     ['chunk_limits[1][0]-', 'map_limits[1][0]-map_limits[1][1]-']],
                    [['chunk_limits[0][0]-', 'chunk_limits[0][1]-'], 
                     ['map_limits[1][0]-map_limits[1][1]-', 'map_limits[1][0]-map_limits[1][1]-']],
                    [['map_limits[0][0]-', 'chunk_limits[1][1]-map_limits[0][1]-'], 
                     ['chunk_limits[1][0]-', 'chunk_limits[1][1]-map_limits[0][1]-']]]
        else:
            prev_state_limits = [[['map_limits[0][0]-', 'map_limits[0][1]-'], 
                     ['chunk_limits[1][0]-', 'chunk_limits[1][1]-']],
                    [['chunk_limits[0][0]-', 'map_limits[0][1]-'], 
                     ['chunk_limits[0][0]-', 'chunk_limits[1][1]-']],
                    [['map_limits[0][0]-', 'chunk_limits[0][1]-map_limits[1][0]-map_limits[1][1]-'], 
                     ['chunk_limits[1][0]-', 'chunk_limits[0][1]-map_limits[1][0]-map_limits[1][1]-']]]
    print("prev_state_limits: ", prev_state_limits) """
    """ if chunk_limits_cru[0][0]<0:
        if chunk_limits_cru[0][1]<0 :
            if chunk_limits_cru[1][0]<0:
                if chunk_limits_cru[1][1]<0:
                else:
            else:
                if chunk_limits_cru[1][1]<0:
                else:
        else:
            if chunk_limits_cru[1][0]<0:
                if chunk_limits_cru[1][1]<0:
                else:
            else:
                if chunk_limits_cru[1][1]<0:
                else:
    else:
        if chunk_limits_cru[0][1]<0:
            if chunk_limits_cru[1][0]<0:
                if chunk_limits_cru[1][1]<0:
                else:
            else:
                if chunk_limits_cru[1][1]<0:
                else:
        else:
            if chunk_limits_cru[1][0]<0:
                if chunk_limits_cru[1][1]<0:
                    new_state_limits:  [[['chunk_limits[0][0]-', 'chunk_limits[0][1]-'], ['map_limits[1][0]-map_limits[1][1]-', 'map_limits[1][0]-map_limits[1][1]-']], [['chunk_limits[1][0]-map_limits[0][0]-', 'chunk_limits[0][1]-'], ['chunk_limits[1][0]-map_limits[0][0]-', 'map_limits[1][0]-map_limits[1][1]-']], [['chunk_limits[0][0]-', 'map_limits[0][1]-'], ['map_limits[1][0]-map_limits[1][1]-', 'chunk_limits[1][1]-']]]
                else:
                    new_state_limits:  [[['chunk_limits[0][0]-', 'map_limits[0][1]-'], ['map_limits[1][0]-map_limits[1][1]-', 'chunk_limits[1][1]-']], [['chunk_limits[0][0]-', 'chunk_limits[0][1]-'], ['map_limits[1][0]-map_limits[1][1]-', 'map_limits[1][0]-map_limits[1][1]-']], [['chunk_limits[1][0]-map_limits[0][0]-', 'map_limits[0][1]-'], ['chunk_limits[1][0]-map_limits[0][0]-', 'map_limits[1][0]-map_limits[1][1]-']]]
            else:
                if chunk_limits_cru[1][1]<0:
                    new_state_limits:  [[['map_limits[0][0]-', 'chunk_limits[0][1]-'], ['chunk_limits[1][0]-', 'map_limits[1][0]-map_limits[1][1]-']], [['chunk_limits[0][0]-', 'chunk_limits[0][1]-'], ['map_limits[1][0]-map_limits[1][1]-', 'map_limits[1][0]-map_limits[1][1]-']], [['map_limits[0][0]-', 'chunk_limits[1][1]-map_limits[0][1]-'], ['chunk_limits[1][0]-', 'chunk_limits[1][1]-map_limits[0][1]-']]]
                else:
                    new_state_limits:  [[['map_limits[0][0]-', 'map_limits[0][1]-'], ['chunk_limits[1][0]-', 'chunk_limits[1][1]-']], [['chunk_limits[0][0]-', 'map_limits[0][1]-'], ['chunk_limits[0][0]-', 'chunk_limits[1][1]-']], [['map_limits[0][0]-', 'chunk_limits[0][1]-map_limits[1][0]-map_limits[1][1]-'], ['chunk_limits[1][0]-', 'chunk_limits[0][1]-map_limits[1][0]-map_limits[1][1]-']]] """
    print("---")

