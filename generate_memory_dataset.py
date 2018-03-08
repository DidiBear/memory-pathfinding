import gym
import gym_pathfinding

from gym_pathfinding.games.gridworld import generate_grid, MOUVEMENT
from gym_pathfinding.envs.partially_observable_env import partial_grid
from astar import astar
from tqdm import tqdm
import numpy as np
import operator
import itertools

class DatasetGenerator():
    
    def __init__(self, grid_type="free", observable_depth=2, timesteps=10, partial_type=None):
        """
        Arguments
        ---------
        grid_type : the type of grid ("free", "obstacle", "maze")
        observable_depth : the number of visible cell around the start
        partial_type : "total", "at-start", "flickering", 
        """
        self.grid_type = grid_type
        self.observable_depth = observable_depth
        self.timesteps = timesteps

    def generate_dataset(self, size, shape, *, timesteps = 10):
        """
        Arguments
        ---------
        size : number of episodes generated
        shape : the grid shape

        Return
        ------
        return episodes, a list of tuple (images, labels)

        each episode contains a list of :
        image : (m, n, 2) grid with state and goal on the 3rd axis
            state = (m, n) grid with 1 (wall), 0 (free) and -1 (unseen) ;
            goal = (m, n) grid with 10 at goal position
        label : the action made
        """
        episodes = []
        for _ in tqdm(range(size)):
            grid, start, goal = generate_grid(shape, grid_type=self.grid_type)
            path, action_planning = compute_action_planning(grid, start, goal)

            goal_grid = create_goal_grid(grid.shape, goal)

            episode = self.generate_episode_totally_partial(grid, goal_grid, action_planning, path)

            images, labels = zip(*episode)

            episodes.append((images, labels))
        return episodes

    def generate_episode_totally_partial(self, grid, goal_grid, action_planning, path):
        for timestep in range(self.timesteps):
            # at the end, pad the episode with the last action
            if (timestep < len(action_planning)): 
                action = action_planning[timestep]
                position = path[timestep]
                
                _partial_grid = partial_grid(grid, position, self.observable_depth)
                _partial_grid = grid_with_start(_partial_grid, position)

                image = np.stack([_partial_grid, goal_grid], axis=2)
            
            yield image, action

    def generate_episode_flickering_partial(self, grid, goal_grid, action_planning, path):
        for timestep in range(self.timesteps):
            # at the end, pad the episode with the last action
            if (timestep < len(action_planning)): 
                action = action_planning[timestep]
                position = path[timestep]
                
                _partial_grid = partial_grid(grid, position, self.observable_depth)
                _partial_grid = grid_with_start(_partial_grid, position)

                image = np.stack([_partial_grid, goal_grid], axis=2)
            
            yield image, action


# reversed MOUVEMENT dict
ACTION = {mouvement: action for action, mouvement in dict(enumerate(MOUVEMENT)).items()}

def compute_action_planning(grid, start, goal):
    path = astar(grid, start, goal)

    action_planning = []
    for i in range(len(path) - 1):
        pos = path[i]
        next_pos = path[i+1]
        
        # mouvement = (-1, 0), (1, 0), (0, -1), (0, 1)
        mouvement = tuple(map(operator.sub, next_pos, pos))

        action_planning.append(ACTION[mouvement])
        
    return path, action_planning


def create_goal_grid(shape, goal):
    goal_grid = np.zeros(shape, dtype=np.int8)
    goal_grid[goal] = 10
    return goal_grid

def grid_with_start(grid, start_position):
    _grid = np.array(grid, copy=True)
    _grid[start_position] = 2
    return _grid



def main():
    import joblib
    import argparse

    parser = argparse.ArgumentParser(description='Generate data, list of (images, labels)')
    parser.add_argument('--out', '-o', type=str, default='./data/dataset.pkl', help='Path to save the dataset')
    parser.add_argument('--size', '-s', type=int, default=10000, help='Number of example')
    parser.add_argument('--shape', type=int, default=[9, 9], nargs=2, help='Shape of the grid (e.g. --shape 9 9)')
    parser.add_argument('--grid_type', type=str, default='free', help='Type of grid : "free", "obstacle" or "maze"')
    parser.add_argument('--timesteps', type=int, default=10, help='Number of timestep per episode (constant for all, no matter what happened)')
    args = parser.parse_args()

    generator = DatasetGenerator(
        grid_type=args.grid_type, 
        observable_depth=2,
        partial_type=None
    )

    dataset = generator.generate_dataset(1, (5, 5), timesteps=10)

    # dataset = generate_dataset(args.size, args.shape, 
    #     grid_type=args.grid_type, 
    #     observable_depth=2,
    #     partial_type=None
    # )

    # print("Saving data into {}".format(args.out))
    # joblib.dump(dataset, args.out)
    print("Done")

if __name__ == "__main__":
    main()
