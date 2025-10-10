import random
import sys

# Payoff matrix
# payoff[player_action][opponent_action]
payoffMatrix = [
    [3, 0],
    [5, 1],
]

gridSize = 10
steps = 10

if (len(sys.argv) > 1):
    gridSize = int(sys.argv[1])

if (len(sys.argv) > 2):
    steps = int(sys.argv[2])
    
actionGrid = []
rewardGrid = []
workGrid = []
cooperate = 0
defect = 1

# Initialize the grid with random strategies: 'C' or 'D'

def makeShape(size, value):
    grid = []
    for i in range(size):
        row = []
        for j in range(size):
            row.append(value)
        grid.append(row)
    return grid

    
def initializeActionGrid0(size):
    global actionGrid
    for i in range(size):
        for j in range(size):
            if (random.random() < 0.5):
                actionGrid[i][j] = cooperate
            else:
                actionGrid[i][j] = defect

def initializeActionGrid1(size):
    global actionGrid
    for i in range(size):
        for j in range(size):
            if i < size / 2: 
                actionGrid[i][j] = cooperate
            else:
                actionGrid[i][j] = defect

def initializeActionGrid2(size):
    global actionGrid
    for i in range(size):
        for j in range(size):
            if i == j:
                actionGrid[i][j] = defect
            else: 
                actionGrid[i][j] = cooperate

def initializeActionGrid3(size):
    global actionGrid
    for i in range(size):
        for j in range(size):
            actionGrid[i][j] = cooperate

    actionGrid[int (size / 2)][int(size / 2)] = defect

def initializeActionGrid4(size):
    global actionGrid
    for i in range(size):
        for j in range(size):
            actionGrid[i][j] = cooperate

    if (size > 1):
         actionGrid[1][1] = defect
    else:
        actionGrid[0][0] = defect

                
# Get neighbors in north, south, east, west including boundary condition
def getNeighbors(i, j, size):
    neighbors = []
    if (i>0):
        neighbors.append((i-1, j))
    if (i+1<size):
        neighbors.append((i+1, j))
    if (j+1<size):
        neighbors.append((i, j+1))
    if (j>0):
        neighbors.append((i, j-1))
    return neighbors

# Play Prisoner's Dilemma with all neighbors and compute total payoff
def computeReward(i, j):
    action = actionGrid[i][j]
    neighbors = getNeighbors(i, j, gridSize)
    total_reward = 0
    for ni, nj in neighbors:
        neighbor_action = actionGrid[ni][nj]
        total_reward += payoffMatrix[action][neighbor_action]
    return total_reward
# ------------------------------------------------------

from multiprocessing import Pool, Array, cpu_count

G_SIZE = None
G_ACTION = None
G_REWARD = None
G_WORK = None

def idx(i,j,n):
    return i*n+j

def create_shared(size, actionBuf, rewardBuf, workBuf):
    global G_SIZE, G_ACTION, G_REWARD, G_WORK
    G_SIZE = size
    G_ACTION = actionBuf
    G_REWARD = rewardBuf
    G_WORK = workBuf

def reward_chunk(bound):
    start, end = bound
    n = G_SIZE

    for i in range(start, end):
        base = i * n

    for j in range(n):
        a = G_ACTION[base + j]
        total = 0

    for (ni, nj) in getNeighbors(i, j, n):
        total += payoffMatrix[a][G_ACTION[idx(ni, nj, n)]]
        G_REWARD[base + j] = total

def update_chunk(bound):
    start, end = bound
    n = G_SIZE

    for i in range(start, end):
        base = i * n

    for j in range(n):
        best_reward = G_REWARD[base + j]
        best_action = G_ACTION[base + j]

    for (ni, nj) in getNeighbors(i, j, n):
        r = G_REWARD[idx(ni, nj, n)]
        if r > best_reward:
            best_reward = r
            best_action = G_ACTION[idx(ni, nj, n)]
        G_WORK[base + j] = best_action

def split_bounds(nrows, nprocs):
    # Even-ish partition of rows into contiguous blocks
    size = (nrows + nprocs - 1) // nprocs
    bounds = []
    for i in range(nprocs):
        s = i * size
        e = min(nrows, s + size)
        if s < e:
            bounds.append((s, e))

    return bounds

def run_sim_sharedMP(initF = initializeActionGrid3, size=8, steps=10, fName = 'sharedMP.txt'):
    global actionGrid, rewardGrid, workGrid
    actionGrid = makeShape(size, cooperate)
    rewardGrid = makeShape(size, 0)
    workGrid = makeShape(size, cooperate)

    initF(size)

    print(f"{initF.__name__}, size={size}, steps={steps}, fName={fName}")

    total = size * size
    actionSH = Array('i', total, lock=False)
    rewardSH = Array('i', total, lock=False)
    workSH = Array('i', total, lock=False)

    k = 0
    for i in range(size):
        for j in range(size):
            actionSH[k] = actionGrid[i][j]
            k += 1

    nprocs = min(cpu_count(), size) or 1
    bounds = split_bounds(size, nprocs)

    with Pool(processes=nprocs, initializer=create_shared, initargs=(size, actionSH, rewardSH, workSH)) as pool:
        for ss in range(steps):
            pool.map(reward_chunk, bounds)

            pool.map(update_chunk, bounds)

            for q in range(total):
                actionSH[q] = workSH[q]

            coop = 0 
            for q in range(total):
                if actionSH[q] == cooperate:
                    coop += 1
            defectors = total - coop 

            print(f"step {ss}: {coop} cooperates, {defectors} defects")

    with open(fName, "w") as f:
        for i in range(gridSize):
            f.write(f"{i}: {actionGrid[i]}\n")

# ------------------------------------------------------
# Run simulation
def runSimulation(initF = initializeActionGrid3, size=8, steps=10, fName = 'output.txt'):
    global actionGrid
    global rewardGrid
    global workGrid
    global gridSize

    gridSize = size
    actionGrid = makeShape(size, cooperate)
    rewardGrid = makeShape(size, 0)
    workGrid = makeShape(size, cooperate)

    initF(size)

    print(f"{initF.__name__}, size={size}, steps={steps}, fName={fName}")
    
    for ss in range(steps):

        for i in range(gridSize):
            for j in range(gridSize):
                rewardGrid[i][j] = computeReward(i, j)

        for i in range(gridSize):
            for j in range(gridSize):
                workGrid[i][j] = actionGrid[i][j]
                bestReward = rewardGrid[i][j]
                neighbors = getNeighbors(i, j, gridSize)
                for (ii, jj) in neighbors:
                    if (rewardGrid[ii][jj] > bestReward):
                        bestReward = rewardGrid[ii][jj]
                        workGrid[i][j] = actionGrid[ii][jj]

        for i in range(gridSize):
            for j in range(gridSize):
                actionGrid[i][j] = workGrid[i][j]

        count1, count2 = 0, 0
        for i in range(gridSize):
            for j in range(gridSize):
                if (actionGrid[i][j] == cooperate):
                    count1 = count1 + 1
                else:
                    count2 = count2 + 1

        print(f"step {ss}: {count1} cooperates, {count2} defects")

        
    with open(fName, "w") as f:
        for i in range(gridSize):
            f.write(f"{i}: {actionGrid[i]}\n")
                                                            
# Run

#runSimulation(initF = initializeActionGrid0, size=gridSize, steps=steps, fName = f'output_grid0_{gridSize}_{steps}_seq.txt')

if __name__ == '__main__':
    #runSimulation(initF = initializeActionGrid1, size=gridSize, steps=steps, fName = f'output_grid1_{gridSize}_{steps}_seq.txt')
    run_sim_sharedMP(initF = initializeActionGrid1, size=gridSize, steps=steps, fName = f'output_grid1_{gridSize}_{steps}_MP.txt')

    #runSimulation(initF = initializeActionGrid2, size=gridSize, steps=steps, fName = f'output_grid2_{gridSize}_{steps}_seq.txt')

    #runSimulation(initF = initializeActionGrid3, size=gridSize, steps=steps, fName = f'output_grid3_{gridSize}_{steps}_seq.txt')

    #runSimulation(initF = initializeActionGrid4, size=gridSize, steps=steps, fName = f'output_grid4_{gridSize}_{steps}_seq.txt')


