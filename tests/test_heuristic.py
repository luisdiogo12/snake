class TestHeuristic:
    def __init__(self, map_size):
        self.map_size = map_size
    
    def heuristic(self, state, goals):
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

# Testes
def run_tests():
    tester = TestHeuristic(map_size=[48, 24])
    
    # Caso 1: Distância direta é menor
    state = (10, 10)
    goals = [(15, 15)]
    print(tester.heuristic(state, goals))  # Deve retornar 10 (5+5)

    # Caso 2: Wrap-around no eixo x
    state = (0, 10)
    goals = [(47, 10)]
    print(tester.heuristic(state, goals))  # Deve retornar 1 (min(47, 1) + 0)

    # Caso 3: Wrap-around no eixo y
    state = (10, 0)
    goals = [(10, 23)]
    print(tester.heuristic(state, goals))  # Deve retornar 1 (0 + min(23, 1))

    # Caso 4: Múltiplos goals com wrap
    state = (47, 23)
    goals = [(0, 0), (45, 22)]
    print(tester.heuristic(state, goals))  # Deve retornar 3 (min(2,46) + min(1,23))

    # Caso 5: Estado e goal coincidem
    state = (30, 20)
    goals = [(30, 20)]
    print(tester.heuristic(state, goals))  # Deve retornar 0

    # Caso 6: Wrap em ambos os eixos
    state = (1, 1)
    goals = [(47, 23)]
    print(tester.heuristic(state, goals))  # Deve retornar 4 (min(2,46)=2 + min(22,2)=2)

if __name__ == "__main__":
    run_tests()