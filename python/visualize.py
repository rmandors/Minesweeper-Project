import json
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors


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
        
        # Colores MARIE del display (convertidos de RGB565 a RGB)
        # Fórmula RGB565: R = (hex >> 11) << 3, G = ((hex >> 5) & 0x3F) << 2, B = (hex & 0x1F) << 3
        marie_colors = {
            'Color0': '#C88CC0',  # 6318 - Light Grey
            'Color1': '#0000FF',  # Blue puro
            'Color2': '#008000',  # Green puro
            'Color3': '#FF0000',  # Red puro
            'Color4': '#00008B',  # Dark Blue
            'Color5': '#800000',  # Dark Red
            'Color6': '#008080',  # Teal/Dark Cyan
            'Color7': '#800080',  # 4010 - Violet
            'Color8': '#F8FCF8',  # 7FFF - White
        }
        
        # Crear mapa de colores: 0=vacío(grey), 1-8=colores progresivos, -1=negro(mina)
        cmap = colors.ListedColormap([
            marie_colors['Color0'],  # 0: vacío - Light Grey
            marie_colors['Color1'],  # 1: Blue
            marie_colors['Color2'],  # 2: Green
            marie_colors['Color3'],  # 3: Cyan
            marie_colors['Color4'],  # 4: Dark Blue
            marie_colors['Color5'],  # 5: Dark Red
            marie_colors['Color6'],  # 6: Violet
            marie_colors['Color7'],  # 7: White
            marie_colors['Color8'],  # 8: Red
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
    """Función principal para visualizar el tablero"""
    
    # Buscar archivo JSON generado
    project_dir = os.path.dirname(os.path.abspath(__file__))
    json_file = os.path.join(project_dir, 'board_data.json')
    
    if not os.path.exists(json_file):
        print(f"Error: Archivo {json_file} no encontrado")
        print("Ejecuta primero: python generate_board.py")
        return
    
    # Crear visualizador y mostrar tablero en ventana
    visualizer = MinesweeperVisualizer(json_file)
    print("Mostrando tablero...")
    visualizer.show_board_graphic()


if __name__ == '__main__':
    main()