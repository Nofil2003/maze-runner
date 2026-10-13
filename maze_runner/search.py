"""
search.py
---------
THE MAZE RUNNER — Mini Project 1: Classical Search

This is where you implement the search algorithms (Questions 1–7).

Every algorithm receives a SearchProblem (see problems.py) and must return a
LIST OF ACTIONS that leads from the start state to a goal state, e.g.
['South', 'South', 'East']. Return [] if the start state is already a goal.

Conventions the grader relies on (please read — they matter!):

  * Use the fringe containers from util.py (Stack, Queue, PriorityQueue).
  * Calling problem.getSuccessors(state) counts as EXPANDING that state.
    Call it exactly once per expanded state, and never for a state you only
    generated.
  * Goal test when a state is POPPED from the fringe (just before you would
    expand it), not when it is pushed. (For BFS the grader also accepts
    the "early" goal test done when a state is generated.)
  * Push successors in the order getSuccessors returns them.
  * Q1, Q2, Q5, Q6, Q7 are GRAPH searches: keep a set of already-expanded
    states and never expand the same state twice.
"""

import util
from util import Stack, Queue, PriorityQueue, CUTOFF
from heuristics import nullHeuristic


# ----------------------------------------------------------------------
# Q0 (worked example, not graded): always go right
# ----------------------------------------------------------------------
def alwaysRightSearch(problem):
    """
    Not a real search: the runner keeps stepping right ('East') until he
    reaches the goal. If a wall blocks the way east, he is stuck and gives up
    (returns None). It shows you how to use the problem's methods. Try it:
        python runner.py -l maze_tiny -a right     (escapes)
        python runner.py -l maze_small -a right       (walks into a wall)
    """
    state = problem.getStartState()
    actions = []
    while not problem.isGoalState(state):
        successors = problem.getSuccessors(state)  # list of (next, action, cost)
        east = [s for s in successors if s[1] == "East"]
        if not east:
            return None  # a wall straight ahead: the doors close with him inside
        nextState, action, stepCost = east[0]
        actions.append(action)
        state = nextState
    return actions


# ----------------------------------------------------------------------
# The shared graph-search loop (used by Q1, Q2, Q5, Q6 and Q7)
# ----------------------------------------------------------------------
def graphSearch(problem, fringe, priorityFunction=None):
    """
    One graph-search loop, many fringes.

    DFS, BFS, UCS, greedy and A* differ only in the order they take states out
    of the fringe, so all of them run through here. 'fringe' is a Stack, a
    Queue or a PriorityQueue from util. For a PriorityQueue,
    'priorityFunction' is called as priorityFunction(state, costSoFar) and
    returns the priority to push with; the plain containers ignore it.

    A fringe entry is (state, actionsSoFar, costSoFar), so a goal popped off
    the fringe hands back its own path. Returns the list of actions, [] if the
    start state is already a goal, or None if no goal is reachable.
    """

    def push(entry):
        if priorityFunction is None:
            fringe.push(entry)
        else:
            state, _, costSoFar = entry
            fringe.push(entry, priorityFunction(state, costSoFar))

    push((problem.getStartState(), [], 0))
    expanded = set()

    while not fringe.isEmpty():
        state, actions, costSoFar = fringe.pop()

        # Goal test when the state is POPPED, not when it was generated.
        if problem.isGoalState(state):
            return actions

        # The same state can sit in the fringe more than once; expand it once.
        if state in expanded:
            continue
        expanded.add(state)

        # getSuccessors is what counts as an expansion: exactly one call here.
        for nextState, action, stepCost in problem.getSuccessors(state):
            if nextState not in expanded:
                push((nextState, actions + [action], costSoFar + stepCost))

    return None


# ----------------------------------------------------------------------
# Q1: Depth-First Search
# ----------------------------------------------------------------------
def depthFirstSearch(problem):
    """
    Search the deepest nodes in the search tree first (graph search).

    To get started, try printing:
        print("Start:", problem.getStartState())
        print("Is the start a goal?", problem.isGoalState(problem.getStartState()))
        print("Start's successors:", problem.getSuccessors(problem.getStartState()))

    Hint: a fringe entry can hold more than a state. Storing
    (state, actionsSoFar) is an easy way to remember how you got there.
    """
    # A LIFO fringe makes the shared loop take the most recently generated
    # state first, which is depth-first order.
    return graphSearch(problem, Stack())


# ----------------------------------------------------------------------
# Q2: Breadth-First Search
# ----------------------------------------------------------------------
def breadthFirstSearch(problem):
    """Search the shallowest nodes in the search tree first (graph search)."""
    # A FIFO fringe makes the shared loop take the oldest generated state
    # first, so states come out in order of increasing depth.
    return graphSearch(problem, Queue())


# ----------------------------------------------------------------------
# Q3: Depth-Limited Search
# ----------------------------------------------------------------------
def depthLimitedSearch(problem, limit):
    """
    Depth-first search that never goes deeper than 'limit' actions.

    Return value:
      * a list of at most 'limit' actions that reaches a goal, or
      * CUTOFF (from util) if no goal was found but the search was stopped
        by the depth limit somewhere, so a deeper solution may exist, or
      * None if no goal was found and the limit was never reached, which
        proves there is no solution at all.

    The start state is at depth 0. A state at depth == limit may be goal
    tested but must not be expanded.

    Do NOT use a global explored set here (think about why that can make the
    search miss a solution that fits within the limit). Instead, avoid cycles
    by not revisiting a state that is already on the current path.
    """
    start = problem.getStartState()

    def recursiveDLS(state, actions, path, depth):
        # Check goal first
        if problem.isGoalState(state):
            return actions

        # Goal was not found and we cannot go deeper
        if depth == limit:
            return CUTOFF

        cutoff_occurred = False

        # Expand current state
        successors = problem.getSuccessors(state)

        for nextState, action, stepCost in successors:
            # Avoid cycles on the CURRENT path only
            if nextState in path:
                continue

            result = recursiveDLS(
                nextState, actions + [action], path | {nextState}, depth + 1
            )

            # Goal found
            if result is not None and result is not CUTOFF:
                return result

            # At least one branch hit the depth limit
            if result is CUTOFF:
                cutoff_occurred = True

        if cutoff_occurred:
            return CUTOFF

        return None

    return recursiveDLS(start, [], {start}, 0)


# ----------------------------------------------------------------------
# Q4: Iterative Deepening Search
# ----------------------------------------------------------------------
def iterativeDeepeningSearch(problem, maxDepth=10000):
    """
    Run depthLimitedSearch with limit = 0, 1, 2, ... until it finds a
    solution. Return that solution, or None if the problem has no solution
    (or none within maxDepth).
    """
    for depth in range(maxDepth + 1):
        result = depthLimitedSearch(problem, depth)

        # A solution was found
        if result is not CUTOFF and result is not None:
            return result

        # No solution exists
        if result is None:
            return None

    return None


# ----------------------------------------------------------------------
# Q5: Uniform-Cost Search
# ----------------------------------------------------------------------
def uniformCostSearch(problem):
    """Search the node of least total path cost g(n) first (graph search)."""
    # Priority is g(n): the cost of the path that reached this state.
    return graphSearch(problem, PriorityQueue(), lambda state, costSoFar: costSoFar)


# ----------------------------------------------------------------------
# Q6: Greedy Best-First Search
# ----------------------------------------------------------------------
def greedyBestFirstSearch(problem, heuristic=nullHeuristic):
    """
    Search the node that SEEMS closest to the goal first, i.e. the one with
    the lowest heuristic(state, problem) value (graph search).
    """
    # Priority is h(n) alone: the cost already paid is ignored.
    return graphSearch(
        problem, PriorityQueue(), lambda state, costSoFar: heuristic(state, problem)
    )


# ----------------------------------------------------------------------
# Q7: A* Search
# ----------------------------------------------------------------------
def aStarSearch(problem, heuristic=nullHeuristic):
    """
    Search the node with the lowest f(n) = g(n) + heuristic(n) first
    (graph search).
    """
    # Priority is f(n) = g(n) + h(n).
    return graphSearch(
        problem,
        PriorityQueue(),
        lambda state, costSoFar: costSoFar + heuristic(state, problem),
    )


# Abbreviations
always_right = alwaysRightSearch
dfs = depthFirstSearch
bfs = breadthFirstSearch
dls = depthLimitedSearch
ids = iterativeDeepeningSearch
ucs = uniformCostSearch
gbfs = greedyBestFirstSearch
astar = aStarSearch
