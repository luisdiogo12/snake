#'body': [[8, 17], [7, 17], [6, 17], [5, 17]]
state1 = {'sight': {'5': {'17': 4}, 
          '6': {'15': 0, '16': 0, '17': 4, '18': 0, '19': 0}, 
          '7': {'15': 0, '16': 0, '17': 4, '18': 0, '19': 0}, 
          '8': {'14': 0, '15': 0, '16': 0, '17': 4, '18': 0, '19': 0, '20': 0}, 
          '9': {'15': 0, '16': 0, '17': 0, '18': 0, '19': 0}, 
          '10': {'15': 0, '16': 0, '17': 0, '18': 0, '19': 0}, 
          '11': {'17': 0}}, }
state2 = {'sight': {  
          '0': {'15': 0, '16': 0, '17': 4, '18': 0, '19': 0}, 
          '1': {'14': 0, '15': 0, '16': 0, '17': 4, '18': 0, '19': 0, '20': 0}, 
          '2': {'15': 0, '16': 0, '17': 0, '18': 0, '19': 0}, 
          '3': {'15': 0, '16': 0, '17': 0, '18': 0, '19': 0}, 
          '4': {'17': 0}, 
          '46': {'17': 4},
          '47': {'15': 0, '16': 0, '17': 4, '18': 0, '19': 0}}}
# 'snakes': [{'body': [[0, 11], [1, 11], [2, 11], [3, 11], [4, 11], [5, 11]],
state3 = {'sight': {
    			'0': {'10': 0, '11': 4, '12': 0, '13': 0, '14': 0, '8': 0, '9': 0},
                '1': {'10': 0, '11': 4, '12': 0, '13': 0, '9': 0},
                '2': {'10': 0, '11': 4, '12': 0, '13': 0, '9': 0},
                '3': {'11': 4},
                '45': {'11': 0},
                '46': {'10': 0, '11': 0, '12': 0, '13': 0, '9': 0},
                '47': {'10': 0, '11': 0, '12': 0, '13': 0, '9': 0}}}
state = {'body': [[12, 23], [12, 0], [12, 1]], 
         'sight': {'9': {'23': 0}, 
                   '10': {'21': 0, '22': 0, '23': 0, '0': 0, '1': 0}, 
                   '11': {'21': 0, '22': 0, '23': 0, '0': 0, '1': 0}, 
                   '12': {'20': 0, '21': 0, '22': 0, '23': 4, '0': 4, '1': 4, '2': 0}, 
                   '13': {'21': 0, '22': 0, '23': 0, '0': 0, '1': 0}, 
                   '14': {'21': 0, '22': 0, '23': 0, '0': 0, '1': 0}, 
                   '15': {'23': 0}}}
s_range = 3
max_key_y = max(state['sight'], key=lambda k: len(state['sight'][k]))
print("max_key_y: ", max_key_y)
new_key_x = list(state['sight'][max_key_y].keys())[s_range]
print("new_key_x: ", new_key_x)

if state['sight'][max_key_y][new_key_x] != 4:
    print("error", state['sight'][max_key_y][new_key_x])
    
key_y = list(state['sight'].keys())[s_range]
key_x = list(state['sight'][key_y].keys())[s_range]
print("key_y: ", key_y)
print("key_x: ", key_x)
