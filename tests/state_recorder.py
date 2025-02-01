import json
import os
from datetime import datetime

class StateRecorder:
    def __init__(self, player_name):
        base_path = os.path.dirname(__file__)
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H_%M_%S")
        filename = f"{player_name}_{timestamp}.json"
        self.filename = os.path.join(base_path, filename)
        self.state_counter = 0
        self.states_dict = {}
        
        # Tentar carregar estados existentes
        try:
            with open(self.filename, 'r') as f:
                self.states_dict = json.load(f)
                self.state_counter = max(int(k) for k in self.states_dict.keys()) + 1
        except (FileNotFoundError, ValueError):
            pass

    def record_state(self, state):
        # Adicionar novo estado
        self.states_dict[str(self.state_counter)] = state
        self.state_counter += 1
        
        # Salvar no arquivo
        with open(self.filename, 'w') as f:
            json.dump(self.states_dict, f, indent=2)