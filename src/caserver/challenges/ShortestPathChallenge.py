from .BaseChallengeGenerator import BaseChallengeGenerator
import random
import coinslib
import heapq
from .Challenge import Challenge


class PriorityQueue:
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]


class Grid:
    def __init__(self, grid_size):
        self.grid_size = grid_size
        self.walls = []
        self.weights = {}

    def in_range(self, pos):
        (row, col) = pos
        return 0 <= row <= self.grid_size and 0 <= col <= self.grid_size

    def walkable(self, pos):
        return pos not in self.walls

    def neighbors(self, pos):
        (row, col) = pos
        results = [ (row+1, col), (row-1, col), (row, col+1), (row, col-1)]
        if (row + col) % 2 == 0:
            results.reverse()

        results = filter(self.in_range, results)
        results = filter(self.walkable, results)
        return results

    def cost(self, from_node, to_node):
        return self.weights.get(to_node, 1)


def dijkstra_search(grid, start_pos, end_pos):
    frontier = PriorityQueue()
    frontier.put(start_pos, 0)

    came_from = {start_pos: None}
    cost_so_far = {start_pos: 0}

    while not frontier.empty():
        current = frontier.get()

        if current == end_pos:
            break

        for next in grid.neighbors(current):
            new_cost = cost_so_far[current] + grid.cost(current, next)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost
                frontier.put(next, priority)
                came_from[next] = current

    return came_from, cost_so_far


def reconstruct_path(came_from, start_pos, end_pos):
    current = end_pos
    path = [current]

    while current != start_pos:
        current = came_from[current]
        path.append(current)

    path.append(start_pos)
    path.reverse()

    fixed_path = []

    for coord in path:
        if len(fixed_path) == 0:
            fixed_path.append(coord)
        else:
            if fixed_path[-1] != coord:
                fixed_path.append(coord)

    return fixed_path


class ShortestPathChallenge(BaseChallengeGenerator):
    def __init__(self, config_file):
        BaseChallengeGenerator.__init__(self, 'shortest_path', config_file)
        self.debug_output = False
        self.read_parameters()

    def read_parameters(self):
        self.config_file.read_file()
        self.parameters["grid_size"] = self.config_file.get_int('shortest_path.grid_size', 25)
        self.parameters["nb_blockers"] = self.config_file.get_int('shortest_path.nb_blockers', 80)
        self.debug_output = self.config_file.get_bool('shortest_path.debug_output', False)
        self.read_nonce_limit()

    def save_grid(self, grid, start_pos, end_pos, nonce, path):
        fp = open('grid_{0}.txt'.format(nonce), 'w')

        for row in range(self.parameters["grid_size"]):
            line = ""
            for col in range(self.parameters["grid_size"]):
                if (row, col) in grid.walls:
                    line += "x "
                elif (row, col) == start_pos:
                    line += "s "
                elif (row, col) == end_pos:
                    line += "e "
                elif (row, col) in path:
                    line += "p "
                else:
                    line += "  "

            fp.write(line + "\n")

        fp.close()

    def generate(self, previous_hash):
        self.read_parameters()
        solution = None
        while True:
            nonce = random.randint(self.nonce_min, self.nonce_max)
            print("Generating {0} problem nonce = {1}".format(self.problem_name, nonce))
            try:
                solution = self.generate_solution(previous_hash, nonce)
                break
            except Exception as e:
                print("No solution exists with nonce = {0}".format(nonce))

        return solution

    def generate_solution(self, previous_hash, nonce):
        solution_string = ""

        grid = Grid(self.parameters["grid_size"])
        seed_hash = self.generate_seed_hash(previous_hash, nonce)
        # seed is the last solution hash suffix, else it's 0
        prng = coinslib.MT64(coinslib.seed_from_hash(seed_hash))

        for i in range(self.parameters["grid_size"]):
            # placing extremity walls
            grid.walls.append((i, 0))
            grid.walls.append((i, self.parameters["grid_size"] - 1))

            if i > 0 and i < (self.parameters["grid_size"] - 1):
                grid.walls.append((0, i))
                grid.walls.append((self.parameters["grid_size"] - 1, i))

        start_pos = (prng.extract_number() % self.parameters["grid_size"], prng.extract_number() % self.parameters["grid_size"])
        while start_pos in grid.walls:
            start_pos = (prng.extract_number() % self.parameters["grid_size"], prng.extract_number() % self.parameters["grid_size"])

        end_pos = (prng.extract_number() % self.parameters["grid_size"], prng.extract_number() % self.parameters["grid_size"])
        while end_pos in grid.walls:
            end_pos = (prng.extract_number() % self.parameters["grid_size"], prng.extract_number() % self.parameters["grid_size"])

        # placing walls
        for i in range(self.parameters["nb_blockers"]):
            # wall pos (row, col)
            block_pos = (prng.extract_number() % self.parameters["grid_size"], prng.extract_number() % self.parameters["grid_size"])
            if block_pos != start_pos and block_pos != end_pos:
                grid.walls.append(block_pos)

        path = []
        came_from, cost_so_far = dijkstra_search(grid, start_pos, end_pos)
        path = reconstruct_path(came_from, start_pos, end_pos)

        for coord in path:
            solution_string += "{0}{1}".format(coord[0], coord[1])

        if self.debug_output:
            self.save_grid(grid, start_pos, end_pos, nonce, path)

        hash = self.generate_hash(solution_string)
        return Challenge(self.problem_name, nonce, solution_string, hash, self.parameters)
