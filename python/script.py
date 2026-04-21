import random
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors

# GENERADOR
class MinesweeperBoardGenerator:
    """Genera un tablero de Buscaminas compatible con MARIE"""
    
    BOARD_SIZE = 16
    TOTAL_CELLS = BOARD_SIZE * BOARD_SIZE  # 256 celdas
    
    # Valores de representación
    MINE = -1
    HIDDEN = 9
    EMPTY = 0
    
    def __init__(self, num_mines, seed=None):
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

# VISUALIZADOR
class MinesweeperVisualizer:
    """Visualiza el tablero de Buscaminas de forma legible"""
    
    SYMBOLS = {
        -1: '*',    # Mina
        0: '.',     # Celda vacía
        1: '1',     # 1 mina vecina
        2: '2',     # 2 minas vecinas
        3: '3',     # 3 minas vecinas
        4: '4',     # 4 minas vecinas
        5: '5',     # 5 minas vecinas
        6: '6',     # 6 minas vecinas
        7: '7',     # 7 minas vecinas
        8: '8',     # 8 minas vecinas
    }
    
    def __init__(self, json_file=None):
        """
        Inicializa el visualizador
        
        Args:
            json_file: Ruta al archivo JSON con datos del tablero
        """
        self.data = None
        self.board = None
        self.board_size = 16
        
        if json_file and os.path.exists(json_file):
            self.load_from_json(json_file)
    
    def load_from_json(self, filepath):
        """Carga datos del tablero desde JSON"""
        with open(filepath, 'r') as f:
            self.data = json.load(f)
        
        self.board = self.data.get('board', [])
        self.board_size = self.data.get('board_size', 16)
    
    def print_board(self):
        """Imprime el tablero completo como guía de referencia"""
        if not self.board:
            print("Error: No hay datos de tablero cargados")
            return
        
        print("\nTablero Buscaminas - Guía completa:")
        print("(* = mina, . = vacío, 1-8 = cantidad de minas adyacentes)\n")
        
        # Encabezado con números de columna
        print("    ", end="")
        for col in range(self.board_size):
            print(f"{col:2d} ", end="")
        print()
        
        # Línea separadora
        print("   +" + "--+" * self.board_size)
        
        # Filas del tablero
        for row in range(self.board_size):
            print(f"{row:2d} |", end="")
            for col in range(self.board_size):
                value = self.board[row][col]
                symbol = self.SYMBOLS.get(value, '?')
                print(f"{symbol:2} ", end="")
            print("|")
        
        # Línea separadora inferior
        print("   +" + "--+" * self.board_size)
        
        # Encabezado inferior
        print("    ", end="")
        for col in range(self.board_size):
            print(f"{col:2d} ", end="")
        print()

    def show_board_graphic(self, save_path=None):
        """
        Muestra el tablero gráficamente con matplotlib
        Usa colores del display MARIE
        
        Args:
            save_path: Si se proporciona, guarda la imagen en lugar de mostrarla
        """
        if not self.board:
            print("Error: No hay datos de tablero cargados")
            return
        
        # Convertir tablero 2D a array numpy para matplotlib
        board_array = np.array(self.board)
        
        # Paleta para que la visualizacion de Python coincida con MARIE.
        marie_colors = {
            'Color0': '#C8C8C8',  # 0: Light Grey (abierta)
            'Color1': '#0000FF',  # 1: Blue
            'Color2': '#00AA00',  # 2: Green
            'Color3': '#FF0000',  # 3: Red
            'Color4': '#00008B',  # 4: Dark Blue
            'Color5': '#800000',  # 5: Dark Red
            'Color6': '#00B8B8',  # 6: Cyan
            'Color7': '#800080',  # 7: Violet
            'Color8': '#FFFFFF',  # 8: White
        }
        
        # Colores
        cmap = colors.ListedColormap([
            marie_colors['Color0'],  # 0: vacío - Light Grey
            marie_colors['Color1'],  # 1: Blue
            marie_colors['Color2'],  # 2: Green
            marie_colors['Color3'],  # 3: Red
            marie_colors['Color4'],  # 4: Dark Blue
            marie_colors['Color5'],  # 5: Dark Red
            marie_colors['Color6'],  # 6: Cyan
            marie_colors['Color7'],  # 7: Violet
            marie_colors['Color8'],  # 8: White
            '#000000',               # 9 (-1): Mina - Negro
        ])
        
        # Crear normalización de colores
        board_normalized = board_array.copy().astype(float)
        board_normalized[board_normalized == -1] = 9  # Minas al índice 9
        
        norm = colors.BoundaryNorm(np.arange(-0.5, 10.5, 1), cmap.N)
        
        # Crear figura
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Mostrar imagen
        im = ax.imshow(board_normalized, cmap=cmap, norm=norm)
        
        # Configurar grid
        ax.set_xticks(np.arange(-0.5, self.board_size, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, self.board_size, 1), minor=True)
        ax.grid(which='minor', color='black', linestyle='-', linewidth=1)
        
        # Etiquetas principales
        ax.set_xticks(np.arange(0, self.board_size, 1))
        ax.set_yticks(np.arange(0, self.board_size, 1))
        ax.set_xticklabels(np.arange(1, self.board_size + 1, 1))
        ax.set_yticklabels(np.arange(1, self.board_size + 1, 1))
        
        # Añadir valores en las celdas
        for i in range(self.board_size):
            for j in range(self.board_size):
                value = self.board[i][j]
                if value == -1:
                    text = 'M'
                elif value == 0:
                    text = ''
                else:
                    text = str(value)
                
                # Texto blanco si está en celda oscura
                text_color = 'white' if value in [-1, 5, 6, 4] else 'black'
                ax.text(j, i, text, ha='center', va='center', 
                       color=text_color, fontsize=8, fontweight='bold')
        
        ax.set_title('Tablero Buscaminas 16x16 - MARIE Colors', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # Guardar o mostrar
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"✓ Imagen guardada en: {save_path}")
            plt.close()
        else:
            plt.show()



def main():
    # === GENERAR ===
    """Función principal para generar el tablero"""

    while True:
        raw = input("Ingresa el número de minas (1-255): ").strip()
        try:
            num_mines = int(raw)
        except ValueError:
            print("Entrada inválida. Debe ser un número entero.")
            continue

        if 1 <= num_mines <= 255:
            break

        print("Número fuera de rango. Debe estar entre 1 y 255.")

    generator = MinesweeperBoardGenerator(num_mines=num_mines, seed=None)
    
    # Generar tablero
    board = generator.generate()
    
    # Exportar en diferentes formatos
    project_dir = os.path.dirname(os.path.abspath(__file__))

    # Generar .mas listo para jugar: base_logic + board data al final
    base_logic = os.path.join(project_dir, "..", "marie", "logic.mas")
    out_mas = os.path.join(project_dir, "..", "marie", "buscaminas.mas")
    generator.export_play_minesweeper_mas(base_logic, out_mas)
    
    # Exportar JSON para visualización
    json_file = os.path.join(project_dir, 'board_data.json')
    generator.export_json(json_file)
    
    print(f"\n✓ Tablero generado: {generator.BOARD_SIZE}x{generator.BOARD_SIZE}")
    print(f"  Minas: {generator.num_mines}")
    print(f"  Celdas vacías: {generator.BOARD_SIZE * generator.BOARD_SIZE - generator.num_mines}")
    print(f"\nArchivos generados:")
    print(f"  - marie/logic.mas (abrir en MARIE)")
    print(f"  - board_data.json (para visualizar)")


    # === VISUALIZAR ===
    """Función principal para visualizar el tablero"""
    
    # Buscar archivo JSON generado
    project_dir = os.path.dirname(os.path.abspath(__file__))
    json_file = os.path.join(project_dir, 'board_data.json')
    
    if not os.path.exists(json_file):
        print(f"Error: Archivo {json_file} no encontrado")
        print("Ejecuta primero: python script.py")
        return
    
    # Crear visualizador y mostrar tablero en ventana
    visualizer = MinesweeperVisualizer(json_file)
    print("Mostrando tablero...")
    visualizer.show_board_graphic()


if __name__ == '__main__':
    main()
