from collections import defaultdict

# Exemplo de sets de tuplos (y, x):
set1 = {(1, 2), (3, 4), (5, 6), (7, 4)}  # x=2, 4, 6
set2 = {(8, 4), (9, 6), (10, 7)}         # x=4, 6, 7

# Agrupar tuplos por x em cada set:
def group_by_x(tuples_set):
    grouped = defaultdict(list)
    for y, x in tuples_set:
        grouped[x].append((y, x))
    return grouped

group1 = group_by_x(set1)  # Exemplo: {2: [(1, 2)], 4: [(3,4), (7,4)], ...}
group2 = group_by_x(set2)  # Exemplo: {4: [(8,4)], 6: [(9,6)], ...}

# Encontrar x comuns:
common_x = set(group1.keys()) & set(group2.keys())  # {4, 6}

# Coletar todos os tuplos com x comuns:
resultado = []
resultado_set = set()
for x in common_x:
    
    resultado.extend(group1[x] + group2[x])
    resultado_set.update(group1[x] + group2[x])

print(resultado)
print(resultado_set)