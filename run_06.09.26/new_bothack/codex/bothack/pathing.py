"""Low-level search algorithms from pathing.clj, GPL-2.0, 2026-09-06.

Move costs and action-producing game navigation still require the full game
model. The original A* integer truncation and unreachable-target rule are kept.
"""
import heapq
from itertools import count
from .position import DIAGONAL, distance, neighbors
from . import tile as t


def base_cost(level, direction, tile, opts):
    cost = 1
    if opts.get("prefer-items") and not tile.get("new-items"): cost += 0.5
    if opts.get("prefer-items") and opts.get("pick") and t.boulder(tile) and tile.get("new-items"): cost -= 5
    if t.trap(tile): cost += 15
    if {"castle", "medusa"}.intersection(level.get("tags", ())):
        from .position import Position
        positions = (Position(tile["x"], tile["y"]), *neighbors(Position(tile["x"], tile["y"])))
        if any(level["tiles"][p.y - 1][p.x].get("feature") == "pool" for p in positions): cost += 5
    if direction in DIAGONAL: cost += 0.1
    if tile.get("feature") is None and not tile.get("seen"): cost += 3
    if tile.get("feature") not in {"stairs-up", "stairs-down"}: cost += 0.1
    if not t.engravable(tile): cost += 0.5
    if tile.get("feature") == "cloud": cost += 10
    if tile.get("blocked") is not None: cost += 10 * tile["blocked"]
    if tile.get("dug") in (None, False) and tile.get("walked") is None: cost += 0.2
    if tile.get("walked") is None and tile.get("feature") == "floor": cost += 0.5
    return cost


def _search(start, goal, move, target=None, max_steps=None):
    serial = count()
    queue, opened, closed = [], {}, {}

    def add(node, priority, dist, prev):
        entry = (priority, next(serial), dist, prev)
        if node not in opened or priority <= opened[node][0]:
            opened[node] = entry
            heapq.heappush(queue, (priority, entry[1], node))

    add(start, 0, 0, None)
    while queue:
        priority, sequence, node = heapq.heappop(queue)
        if node not in opened or opened[node][1] != sequence:
            continue
        _, _, dist, previous = opened.pop(node)
        path = closed.get(previous, ()) + (node,)
        delta = distance(node, target) if target is not None else 0
        if goal(node):
            return path[1:]
        if target is not None and delta == 1 and not any(move(p, target) is not None for p in neighbors(target)):
            return path[1:] + (target,)
        if max_steps is not None and max_steps < delta + len(path):
            return None
        closed[node] = path
        for neighbor in neighbors(node):
            if neighbor in closed:
                continue
            edge = move(node, neighbor)
            if edge is not None and edge[1] is not None:
                cost, action = edge
                new_dist = int(dist + cost) if target is not None else dist + cost
                add(neighbor, new_dist + (distance(neighbor, target) if target is not None else 0), new_dist, node)
    return None


def astar(start, target, move, max_steps=None):
    return _search(start, lambda p: p == target, move, target, max_steps)


def dijkstra(start, goal, move, max_steps=None):
    return _search(start, goal, move, max_steps=max_steps)
