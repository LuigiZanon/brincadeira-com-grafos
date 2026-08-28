import random
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import Counter


class GridGraph:
    """
    Classe para representar um grafo de grade.
    """

    def __init__(self, N: int, seed: int = None):
        self.N = N
        self.seed = seed
        self.matrix = []
        self.G = None
        self.position = {}

        if self.N < 2:
            raise ValueError("N nao pode ser menor que 2")

        self.nodes_C = []   # Circulos
        self.nodes_S = []   # Quadrados
        self.nodes_T = []   # Triangulos
        
        self._generate_matrix()
        self._generate_graph()

    def _generate_matrix(self) -> None:
        """
        Gera um grafo de grade NxN.
        """
        if self.seed is not None:
            random.seed(self.seed)

        self.matrix = [
            [random.randint(1, 3) for _ in range(self.N)] for _ in range(self.N)
        ]
        
    def _generate_graph(self) -> None:
        """
        Gera um grafo de grade NxN.
        """
        G_base = nx.grid_2d_graph(self.N, self.N)
        self.G = nx.DiGraph(G_base)
        
        self.position = {(x, y): (y, -x) for x, y in self.G.nodes()}
        
        for i in range(self.N):
            for j in range(self.N):
                node = (i,j)
                node_type = self.matrix[i][j]
                
                self.G.nodes[node]['type'] = node_type
                
                if node_type == 1:
                    self.nodes_C.append(node)
                elif node_type == 2:
                    self.nodes_S.append(node)
                elif node_type == 3:
                    self.nodes_T.append(node)

class PathFinder:
    """
    Classe para realizar a busca
    """
    
    def __init__(self, grid_graph: GridGraph):
        self.grid = grid_graph
        self.succeeded_paths = []
        self.failed_paths = []
        
    def _distance(self, node1, node2):
        """
        Calcula a distância entre dois nós
        """
        return max(abs(node1[0] - node2[0]), abs(node1[1] - node2[1]))
    
    def explore(self):
        """
        Inicia a busca
        """
        for circle in self.grid.nodes_C:
            self._search(circle, 2, [circle])
            
    def _search(self, current_node, step, current_path):
        """
        Realiza a busca no grafo
        """
        if step == 2:
            candidate_node = [
                s for s in self.grid.nodes_S if 
                    (s[0] == current_node[0]) or
                    (s[1] == current_node[1]) or
                    (abs(s[0] - current_node[0]) == abs(s[1] - current_node[1]))
                ]
        
        elif step == 3:
            candidate_node = [
                t for t in self.grid.nodes_T if 
                    (t[1] > current_node[1] and t[0] == current_node[0]) or
                    (t[0] > current_node[0] and t[1] == current_node[1])
            ]
        
        elif step == 4:
            candidate_node = [
                s for s in self.grid.nodes_S if
                abs(s[0] - current_node[0]) == abs(s[1] - current_node[1]) and s != current_node
            ]
        
        elif step == 5:
            self.succeeded_paths.append(current_path)
            return
        
        if not candidate_node:
            self.failed_paths.append(current_path)
            return
        
        minimum_dist = min(self._distance(current_node, c) for c in candidate_node)
        closest_node = [c for c in candidate_node if self._distance(current_node, c) == minimum_dist]
        
        for next_node in closest_node:
            self._search(next_node, step + 1, current_path + [next_node])
            
class GraphVisualizer:
    """
    Controla a renderização visual do grafo, plotando os nós estáticos 
    e animando a adição das arestas conforme os caminhos encontrados.
    """
    def __init__(self, grid_graph, path_finder):
        self.grid = grid_graph
        self.paths = path_finder.succeeded_paths + path_finder.failed_paths
        
        success_ends = [p[-1] for p in path_finder.succeeded_paths]
        
        self.most_visited_success_node = None
        if success_ends:
            self.most_visited_success_node = Counter(success_ends).most_common(1)[0][0]

        self.succeed_nodes = list(set(success_ends))
        if self.most_visited_success_node in self.succeed_nodes:
            self.succeed_nodes.remove(self.most_visited_success_node)
            
        self.failed_nodes = list(set([p[-1] for p in path_finder.failed_paths]))
        
        N = self.grid.N
        self.figsize = max(10, N * 1.0)
        self.node_size = max(100, 3600 / N)
        self.edge_width = max(2, 12 / N)
        self.arrow_width = max(2, 120 / N)
        self.X_size = self.node_size * 3.5
        self.star_size = self.node_size * 4
        
        self.fig, self.ax = plt.subplots(figsize=(self.figsize, self.figsize))
        self.edges_sequence = self._prepare_animation_sequence()

    def _prepare_animation_sequence(self) -> list:
        """Processa todos os caminhos para gerar uma sequência linear de arestas para a animação."""
        sequence = []
        for path in self.paths:
            for i in range(len(path) - 1):
                aresta = (path[i], path[i+1])
                if i == 0:
                    color, rad = "green", 0.2
                elif i == 1:
                    color, rad = (0.4,0.4,0.4), 0.25
                else:
                    color, rad = "blue", 0.18
                    
                sequence.append((aresta, color, rad))
        return sequence

    def _draw_base_nodes(self) -> None:
        """Plota os nós e suas formas/cores iniciais."""
        self.ax.clear()
        self.ax.axis("off")
        
        nx.draw_networkx_nodes(self.grid.G, pos=self.grid.position, nodelist=self.grid.nodes_C, node_color="green", node_size=self.node_size, node_shape="o", ax=self.ax)
        nx.draw_networkx_nodes(self.grid.G, pos=self.grid.position, nodelist=self.grid.nodes_S, node_color="black", node_size=self.node_size, node_shape="s", ax=self.ax)
        nx.draw_networkx_nodes(self.grid.G, pos=self.grid.position, nodelist=self.grid.nodes_T, node_color="blue", node_size=self.node_size, node_shape="^", ax=self.ax)
        
        if self.failed_nodes:
            nx.draw_networkx_nodes(self.grid.G, pos=self.grid.position, nodelist=self.failed_nodes, node_color="red", node_size=self.X_size, node_shape="x", linewidths=3, ax=self.ax)
            
        if self.succeed_nodes:
            nx.draw_networkx_nodes(self.grid.G, pos=self.grid.position, nodelist=self.succeed_nodes, node_color="gold", node_size=self.star_size, node_shape="*", ax=self.ax)
            
        if self.most_visited_success_node:
            nx.draw_networkx_nodes(self.grid.G, pos=self.grid.position, nodelist=[self.most_visited_success_node], node_color="purple", node_size=self.star_size, node_shape="*", ax=self.ax)

    def _update_frame(self, frame: int):
        """Função chamada a cada frame da animação. O frame 0 desenha o mapa base."""
        if frame == 0:
            self._draw_base_nodes()
            return

        aresta, color, rad = self.edges_sequence[frame - 1]
        nx.draw_networkx_edges(
            self.grid.G,
            pos=self.grid.position,
            edgelist=[aresta],
            edge_color=color,
            width=self.edge_width,
            arrows=True,
            arrowsize=self.arrow_width,
            connectionstyle=f'arc3,rad={rad}',
            alpha=0.5,
            ax=self.ax,
        )

    def animate_and_show(self, interval_ms: int = 5) -> None:
        """Inicia e exibe a animação do algoritmo de busca."""
        total_frames = len(self.edges_sequence) + 1
        
        self.ani = FuncAnimation(
            self.fig, 
            self._update_frame, 
            frames=total_frames, 
            interval=interval_ms, 
            repeat=False
        )
        
        plt.show()

    def show_static(self) -> None:
        """Exibe o grafo completo imediatamente, sem animação."""
        self._draw_base_nodes()
        
        for aresta, color, rad in self.edges_sequence:
            nx.draw_networkx_edges(
                self.grid.G,
                pos=self.grid.position,
                edgelist=[aresta],
                edge_color=color,
                width=self.edge_width,
                arrows=True,
                arrowsize=self.arrow_width,
                node_size=self.node_size,
                connectionstyle=f'arc3,rad={rad}',
                alpha=0.5,
                ax=self.ax,
            )
            
        plt.show()
        
        
grafo = GridGraph(10, 10)

buscador = PathFinder(grafo)
buscador.explore()

visualizador = GraphVisualizer(grafo, buscador)
visualizador.show_static()