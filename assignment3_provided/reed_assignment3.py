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

#---------------------------------------------------------------------
# Above is the original functions and below is the start of my mp code
#---------------------------------------------------------------------

from multiprocessing import Process, Queue, cpu_count

def split_rows(nrows, nprocs):
    size = (nrows + nprocs - 1) // nprocs
    bounds = []
    for i in range(nprocs):
        start = i * size
        end = min(nrows, start + size)
        
        if start < end:
            bounds.append((start, end))
    
    return bounds

def rewards_worker(start, end, actionGrid, size, outQ):
    chunk = []
    for i in range(start, end):
        row = []
        for j in range(size):
            total = 0
            a = actionGrid[i][j]
            for (ni, nj) in getNeighbors(i, j, size):
                total += payoffMatrix[a][actionGrid[ni][nj]]
            row.append(total) # add one row at a time
        chunk.append((i, row)) # at one chunk at a time
    outQ.put(chunk)

def update_worker(start, end, actionGrid, rewardGrid, size, outQ):
    chunk = []
    for i in range(start, end):
        row = []
        for j in range(size):
            best_reward = rewardGrid[i][j]
            best_action = actionGrid[i][j]
            for (ni, nj) in getNeighbors(i, j, size):
                r = rewardGrid[ni][nj]
                if r > best_reward:
                    best_reward = r
                    best_action = actionGrid[ni][nj]
            row.append(best_action)
        chunk.append((i, row))
    outQ.put(chunk)

def count_worker(start, end, actionGrid, outQ):
    c = d = 0
    for i in range(start, end):
        for a in actionGrid[i]:
            if a == cooperate:
                c += 1
            else:
                d += 1
    outQ.put((c, d))

def rewards_row(i, size, A):
    row = []
    for j in range(size):
        a = A[i][j]
        total = 0
        for (ni, nj) in getNeighbors(i, j, size):
            total += payoffMatrix[a][A[ni][nj]]
        row.append(total)
    return (i, row)

def update_row(i, size, A, R):
    row = []
    for j in range(size):
        best_reward = R[i][j]
        best_action = A[i][j]
        for (ni,nj) in getNeighbors(i, j, size):
            r = R[ni][nj]
            if r > best_reward:
                best_reward = r
                best_action = A[ni][nj]
        row.append(best_action)
    return (i, row)


#---------------------------------------------------------------
#  MP Simulation
#---------------------------------------------------------------
from multiprocessing import Pool
def runSimulation_pool(initF = initializeActionGrid3, size=8, steps=10, fName = 'mp_out.txt'):
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

    nprocs = min(cpu_count(), gridSize)

    with Pool(processes=nprocs) as pool:
        # Parallel Portion
        for ss in range(steps):

            A = [row[:] for row in actionGrid]
            # rewards 
            rewards = pool.starmap(rewards_row, [(i, gridSize, A) for i in range(gridSize)])
            for (i, row) in rewards:
                rewardGrid[i] = row
            
            R = [row[:] for row in rewardGrid]
            # updates
            updates = pool.starmap(update_row, [(i, gridSize, A, R) for i in range(gridSize)])
            for (i, row) in updates:
                workGrid[i] = row

            # swap 
            for i in range(size):
                actionGrid[i] = workGrid[i][:]

            # count
            count1 = sum(a == cooperate for row in actionGrid for a in row)
            count2 = size*size - count1
            print(f"step {ss}: {count1} cooperates, {count2} defects")

    with open(fName, "w") as f:
        for i in range(gridSize):
            f.write(f"{i}: {actionGrid[i]}\n")

def runSimulation_mp(initF = initializeActionGrid3, size=8, steps=10, fName = 'mp_out.txt'):
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
    
    # Parallel Portion
    for ss in range(steps):
        # get processor count 
        nprocs = cpu_count()

        # rewards
        bounds = split_rows(gridSize, nprocs)
        rq = Queue()
        rq_procs = [] 
        # create reward processes
        for (s,e) in bounds:
            p = Process(target=rewards_worker, args=(s, e, actionGrid, gridSize, rq))
            p.start()
            rq_procs.append(p)

        # Drain before join to avoid deadlocks
        seen = [False] * gridSize # track written rows for consistency
        for _ in bounds:
            chunk = rq.get()
            for (i, row) in chunk:
                if not (0 <= i < gridSize):
                    raise ValueError(f"Bad row index {i}")
                if seen[i]:
                    raise ValueError(f"Duplicate row {i} in rewards")
                rewardGrid[i] = row
                seen[i] = True
        if not all(seen):
            missing = [i for i, v in enumerate(seen) if not v]
            raise RuntimeError(f"Missing reward rows: {missing}")

        for p in rq_procs:
            p.join()

        rq.close()
        rq.join_thread()

        # -------------------------------------------

        # update 
        uq = Queue()
        uq_procs = [] 
        # create update processes
        for (s,e) in bounds:
            p = Process(target=update_worker, args=(s, e, actionGrid, rewardGrid, gridSize, uq))
            p.start()
            uq_procs.append(p)
        
        seen = [False] * gridSize
        for _ in bounds:
            chunk = uq.get()
            for (i, row) in chunk:
                if not (0 <= i < gridSize):
                    raise ValueError(f"Bad row index {i}")
                if seen[i]:
                    raise ValueError(f"Duplicate row {i} in update")
                workGrid[i] = row
                seen[i] = True
        if not all(seen):
            missing = [i for i, v in enumerate(seen) if not v]
            raise RuntimeError(f"Missing work rows: {missing}")
        
        for p in uq_procs:
            p.join()

        uq.close()
        uq.join_thread()

        for i in range(gridSize):
            for j in range(gridSize):
                actionGrid[i][j] = workGrid[i][j]

        # -------------------------------------------------

        # count 
        cq = Queue()
        cq_procs = []
        # create count process
        for (s,e) in bounds:
            p = Process(target=count_worker, args=(s, e, actionGrid, cq))
            p.start()
            cq_procs.append(p)

        count1 = count2 = 0
        for _ in bounds:
            c, d = cq.get()
            count1 += c
            count2 += d

        for p in cq_procs:
            p.join()

        cq.close()
        cq.join_thread()

        print(f"step {ss}: {count1} cooperates, {count2} defects")

    with open(fName, "w") as f:
        for i in range(gridSize):
            f.write(f"{i}: {actionGrid[i]}\n")

# --------------------------------------------------------------
# Old Simulation Below MP Above
# Run Simulation Sequential Implementation
#  
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

# sequential simulations
#if __name__ == '__main__':
#    runSimulation(initF = initializeActionGrid1, size=gridSize, steps=steps, fName = f'output_grid1_{gridSize}_{steps}_seq.txt')
#    runSimulation(initF = initializeActionGrid2, size=gridSize, steps=steps, fName = f'output_grid2_{gridSize}_{steps}_seq.txt')
#    runSimulation(initF = initializeActionGrid3, size=gridSize, steps=steps, fName = f'output_grid3_{gridSize}_{steps}_seq.txt')
#    runSimulation(initF = initializeActionGrid4, size=gridSize, steps=steps, fName = f'output_grid4_{gridSize}_{steps}_seq.txt')

# multiprocess simulations
#if __name__ == '__main__':
#    runSimulation_mp(initF = initializeActionGrid1, size=gridSize, steps=steps, fName = f'output_grid1_{gridSize}_{steps}_seq.txt')
#    runSimulation_mp(initF = initializeActionGrid2, size=gridSize, steps=steps, fName = f'output_grid2_{gridSize}_{steps}_seq.txt')
#    runSimulation_mp(initF = initializeActionGrid3, size=gridSize, steps=steps, fName = f'output_grid3_{gridSize}_{steps}_seq.txt')
#    runSimulation_mp(initF = initializeActionGrid4, size=gridSize, steps=steps, fName = f'output_grid4_{gridSize}_{steps}_seq.txt')

# Pool multiprocess
if __name__ == '__main__':
    runSimulation_pool(initF = initializeActionGrid1, size=gridSize, steps=steps, fName = f'output_grid1_{gridSize}_{steps}_pool.txt')
    runSimulation_pool(initF = initializeActionGrid2, size=gridSize, steps=steps, fName = f'output_grid2_{gridSize}_{steps}_pool.txt')
    runSimulation_pool(initF = initializeActionGrid3, size=gridSize, steps=steps, fName = f'output_grid3_{gridSize}_{steps}_pool.txt')
    runSimulation_pool(initF = initializeActionGrid4, size=gridSize, steps=steps, fName = f'output_grid4_{gridSize}_{steps}_pool.txt')