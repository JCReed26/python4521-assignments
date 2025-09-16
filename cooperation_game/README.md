# Assignment 1

Consider a simple game that works as follows: the game involves two players who can choose to either cooperate or defect. If both players cooperate, each receives a reward of 3 coins. If one player cooperates and the other one defects, the defector receives 5 coins, and the cooperator receives 0 coins. If both defect, then each receives 1 coin.

creating: simulate game between 2 strategies. for each strat the program will simulate for a specified number of rounds against each of the other strategies and calculate the total rewards

### Strategies to implement:

each strat is to be implemented as a separate function named strategy_strategyName.

1. [0] alwaysCooperate - player always chooses to cooperate
2. [1] alwaysDefect - player always chooses to defect
3. [2] probeAndLock - player defects first 20 rounds then cooperates second 20 rounds. After those 40 rounds choose whichever yielded a higher reward for the rest of the game.
4. [3] continuousProbe - players defects in 1st and cooperates in 2nd. After player calculates average reward obtained when choosing defect or cooperate, player chooses higher
5. [4] defectUntilCooperate - always defect until other player cooperates after always cooperate
6. opponentCooperatePercentage - players decides based on % of times opponent has chosen to cooperate so far. if rate exceeds threshold, players chooses cooperate otherwise defect 
    a. [5] opponentCooperate10Percentage (10%)
    b. [6] opponentCooperate50Percentage (50%)
    c. [7] opponentCooperate90Percentage (90%)
7. [8] random50 - player randomly chooses with 50/50 probability

8. [9] JamesCReed - my own strategy ideally most effective against previous 9 strats 

### CMD-Line Arguments

num_of_iterations = 2000 (num of rounds between two strategies)
num_of_strategies = 8