import random
import os


class MinesweeperBoardGenerator:
    """Genera un tablero de Buscaminas compatible con MARIE"""
    
    BOARD_SIZE = 16
    TOTAL_CELLS = BOARD_SIZE * BOARD_SIZE  # 256 celdas
    DEFAULT_MINES = 10
    
    # Valores de representación
    MINE = -1
    HIDDEN = 9
    EMPTY = 0
    
    def __init__(self, num_mines=DEFAULT_MINES, seed=None):
        """
        Inicializa el generador de tablero
        
        Args:
            num_mines: Número de minas a colocar
            seed: Semilla para reproducibilidad (None para aleatorio)

        """
        if seed is not None:
            random.seed(seed)
        
        self.num_mines = min(num_mines, self.TOTAL_CELLS - 1)  # Al menos 1 celda sin mina
        self.board = [[self.EMPTY for _ in range(self.BOARD_SIZE)] for _ in range(self.BOARD_SIZE)]
        self.solution_board = [[self.HIDDEN for _ in range(self.BOARD_SIZE)] for _ in range(self.BOARD_SIZE)]
        self.mines_positions = set() # Set para evitar duplicados
        
    def place_mines(self):
        """Coloca minas aleatoriamente en el tablero"""
        positions = []
        while len(positions) < self.num_mines:
            row = random.randint(0, self.BOARD_SIZE - 1)
            col = random.randint(0, self.BOARD_SIZE - 1)
            pos = (row, col)
            
            if pos not in self.mines_positions:
                self.mines_positions.add(pos)
                self.board[row][col] = self.MINE
                positions.append(pos)
        
        return positions
    
    def calculate_neighbors(self):
        """Calcula el número de minas vecinas para cada celda sin minas"""
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                if self.board[row][col] != self.MINE:
                    count = self._count_adjacent_mines(row, col)
                    self.board[row][col] = count
    
    def _count_adjacent_mines(self, row, col):
        """Cuenta minas adyacentes a una celda"""
        mine_count = 0
        # Revisar los 8 vecinos 
        # (arriba, mismo nivel, abajo) x (izquierda, mismo, derecha)
        for row_offset in [-1, 0, 1]:
            for col_offset in [-1, 0, 1]:
                # Salta la celda central q es la casilla
                if row_offset == 0 and col_offset == 0:
                    continue
                    
                neighbor_row = row + row_offset
                neighbor_col = col + col_offset
                
                # Verificar que el vecino esté dentro del tablero
                if 0 <= neighbor_row < self.BOARD_SIZE and 0 <= neighbor_col < self.BOARD_SIZE:
                    if self.board[neighbor_row][neighbor_col] == self.MINE:
                        mine_count += 1
        
        return mine_count
    
    def generate(self):
        """Genera el tablero completo"""
        self.place_mines()
        self.calculate_neighbors()
        return self.board
    
    def get_marie_memory_block(self):
        """
        Genera el bloque de memoria en formato compatible con MARIE
        Estructura: 256 valores consecutivos (16x16) en orden fila-por-fila
        
        Returns:
            Tupla (address_start, data_block) donde data_block es lista de valores
        """
        memory_block = []
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                value = self.board[row][col]
                # Convertir a representación compatible con MARIE
                if value == self.MINE:
                    marie_value = -1  # Mina representada como -1
                elif value == self.EMPTY:
                    marie_value = 0
                else:  # Número de minas vecinas (1-8)
                    marie_value = value
                
                memory_block.append(marie_value)
        
        return (100, memory_block)  # Comienza en dirección 100 (típico en MARIE)
    
    def export_to_marie_txt(self, filename):
        """
        Exporta el tablero en formato texto para copiar y pegar en MARIE
        Solo genera valores decimales, sin ORG ni comentarios
        """
        address_start, memory_block = self.get_marie_memory_block()
        
        with open(filename, 'w') as f:
            # Cada fila
            f.write(f"SafeCellsLeft, DEC {256 - self.num_mines}\n")
            f.write(f"TotalMines, DEC {self.num_mines}\n")
            for row in range(self.BOARD_SIZE):
                f.write(f"/ Row {row}\n")
                
                # Cada columna en la fila
                for col in range(self.BOARD_SIZE):
                    idx = row * self.BOARD_SIZE + col
                    value = memory_block[idx]
                    f.write(f"        Dec {value}\n")
        
        print(f"✓ Datos exportados a: {filename}")

    def render_board_data_mas(self):
        """
        Renderiza el bloque de datos del tablero como líneas MARIE (.mas).
        Se diseña para ser pegado al final de `base_logic.mas` bajo "BOARD DATA".
        """
        _address_start, memory_block = self.get_marie_memory_block()

        lines = []
        lines.append(f"SafeCellsLeft, DEC {256 - self.num_mines}")
        lines.append(f"TotalMines, DEC {self.num_mines}")
        for row in range(self.BOARD_SIZE):
            lines.append(f"/ Row {row + 1}")
            for col in range(self.BOARD_SIZE):
                idx = row * self.BOARD_SIZE + col
                value = memory_block[idx]
                lines.append(f"        DEC {value}")
        return "\n".join(lines) + "\n"

    def export_play_minesweeper_mas(self, base_logic_path, output_path):
        """
        Crea un archivo .mas listo para ensamblar, combinando:
        - el contenido de `base_logic.mas`
        - el tablero generado (append al final)
        """
        with open(base_logic_path, "r") as f:
            base = f.read()

        if base and not base.endswith("\n"):
            base += "\n"

        combined = base + self.render_board_data_mas()
        with open(output_path, "w") as f:
            f.write(combined)

        print(f"✓ Archivo MARIE generado: {output_path}")
    
    def export_json(self, filename):
        """Exporta el tablero en formato JSON para visualización"""
        import json
        
        data = {
            'board_size': self.BOARD_SIZE,
            'num_mines': self.num_mines,
            'mines_positions': list(self.mines_positions),
            'board': self.board,
            'metadata': {
                'empty_cells': self.BOARD_SIZE * self.BOARD_SIZE - self.num_mines,
                'total_cells': self.TOTAL_CELLS
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Datos JSON exportados a: {filename}")


def main():
    """Función principal para generar el tablero"""
    
    # Crear generador (usa DEFAULT_MINES por defecto)
    generator = MinesweeperBoardGenerator(seed=None)
    
    # Generar tablero
    board = generator.generate()
    
    # Exportar en diferentes formatos
    project_dir = os.path.dirname(os.path.abspath(__file__))

    # Generar .mas listo para jugar: base_logic + board data al final
    base_logic = os.path.join(project_dir, "..", "marie", "base_logic.mas")
    out_mas = os.path.join(project_dir, "..", "marie", "play_minesweeper.mas")
    generator.export_play_minesweeper_mas(base_logic, out_mas)
    
    # Exportar JSON para visualización
    json_file = os.path.join(project_dir, 'board_data.json')
    generator.export_json(json_file)
    
    print(f"\n✓ Tablero generado: {generator.BOARD_SIZE}x{generator.BOARD_SIZE}")
    print(f"  Minas: {generator.num_mines}")
    print(f"  Celdas vacías: {generator.BOARD_SIZE * generator.BOARD_SIZE - generator.num_mines}")
    print(f"\nArchivos generados:")
    print(f"  - marie/play_minesweeper.mas (abrir en MARIE)")
    print(f"  - board_data.json (para visualizar)")


if __name__ == '__main__':
    main()
