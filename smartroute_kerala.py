"""
SmartRoute Kerala
A Multi-Purpose Intelligent Route Planning and Emergency Management System
BCA Sem 3 - DSA Vacation Mini Project

NOTE: All distances, travel times, flood levels, bed counts and camp
capacities are APPROXIMATE SAMPLE DATA for demonstration only.

Data structures : Graph (adjacency list), Hash Map (dict), Priority Queue (heap),
                  Queue (deque), Stack, List sorting
Algorithms      : Dijkstra, BFS, DFS, modified Dijkstra (EV state graph)
"""

import heapq
from collections import deque

# ----------------------------------------------------------------------
# 1. GRAPH: cities and roads  (adjacency list)  city -> [(neighbour, km, minutes)]
# ----------------------------------------------------------------------
ROADS = [
    ("Thiruvananthapuram", "Kollam", 70, 110),
    ("Thiruvananthapuram", "Pathanamthitta", 100, 160),
    ("Kollam", "Pathanamthitta", 70, 110),
    ("Kollam", "Alappuzha", 85, 130),
    ("Kollam", "Kottayam", 75, 120),
    ("Pathanamthitta", "Kottayam", 55, 90),
    ("Alappuzha", "Kottayam", 45, 70),
    ("Alappuzha", "Kochi", 55, 80),
    ("Kottayam", "Kochi", 60, 95),
    ("Kottayam", "Idukki", 65, 120),
    ("Kochi", "Idukki", 130, 220),
    ("Kochi", "Thrissur", 80, 120),
    ("Thrissur", "Palakkad", 80, 115),
    ("Thrissur", "Kozhikode", 115, 170),
    ("Palakkad", "Kozhikode", 120, 175),
    ("Kozhikode", "Kannur", 90, 130),
    ("Kannur", "Kasaragod", 90, 125),
]
# "Wayanad" is deliberately left isolated to demonstrate DFS component detection
CITIES = ["Thiruvananthapuram", "Kollam", "Pathanamthitta", "Alappuzha", "Kottayam",
          "Idukki", "Kochi", "Thrissur", "Palakkad", "Kozhikode", "Kannur",
          "Kasaragod", "Wayanad"]


def build_graph(roads):
    g = {c: [] for c in CITIES}
    for a, b, km, mins in roads:           # roads are two-way
        g[a].append((b, km, mins))
        g[b].append((a, km, mins))
    return g


GRAPH = build_graph(ROADS)
KM, MIN = 1, 2   # index of the weight inside each edge tuple


# ----------------------------------------------------------------------
# 2. CORE ALGORITHMS
# ----------------------------------------------------------------------
def dijkstra(graph, src, weight=KM, blocked=frozenset()):
    """Min-cost paths from src using a min-heap (priority queue).
    Returns (dist, parent). Cities in `blocked` are never entered."""
    dist = {c: float("inf") for c in graph}
    parent = {c: None for c in graph}
    dist[src] = 0
    heap = [(0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for edge in graph[u]:
            v, w = edge[0], edge[weight]
            if v in blocked:
                continue
            if d + w < dist[v]:
                dist[v] = d + w
                parent[v] = u
                heapq.heappush(heap, (dist[v], v))
    return dist, parent


def build_path(parent, dst):
    path = []
    while dst is not None:
        path.append(dst)
        dst = parent[dst]
    return path[::-1]


def shortest_path(graph, src, dst, weight=KM, blocked=frozenset()):
    dist, parent = dijkstra(graph, src, weight, blocked)
    if dist[dst] == float("inf"):
        return None, None
    return dist[dst], build_path(parent, dst)


def bfs_fewest_stops(graph, src, dst):
    """BFS with a Queue: path with the fewest intermediate cities."""
    queue = deque([src])
    parent = {src: None}
    while queue:
        u = queue.popleft()
        if u == dst:
            return build_path(parent, dst)
        for v, *_ in graph[u]:
            if v not in parent:
                parent[v] = u
                queue.append(v)
    return None


def dfs_components(graph):
    """Iterative DFS with a Stack: finds disconnected regions."""
    seen, components = set(), []
    for start in graph:
        if start in seen:
            continue
        comp, stack = [], [start]
        seen.add(start)
        while stack:
            u = stack.pop()
            comp.append(u)
            for v, *_ in graph[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        components.append(comp)
    return components


def all_routes(graph, src, dst, limit=8, blocked=frozenset()):
    """DFS/recursion (backtracking) to collect simple routes; caller sorts them."""
    routes = []

    def dfs(u, visited, km, mins):
        if len(routes) >= 200:
            return
        if u == dst:
            routes.append((km, mins, list(visited)))
            return
        for v, k, m in graph[u]:
            if v not in visited and v not in blocked:
                visited.append(v)
                dfs(v, visited, km + k, mins + m)
                visited.pop()

    dfs(src, [src], 0, 0)
    routes.sort(key=lambda r: (r[0], r[1]))      # SORTING: shortest first
    return routes[:limit]


def fmt_path(path):
    return " -> ".join(path)


def fmt_time(mins):
    return f"{mins // 60}h {mins % 60:02d}m"


# ----------------------------------------------------------------------
# 3. MODE 1 - NORMAL NAVIGATION
# ----------------------------------------------------------------------
def normal_navigation(src, dst):
    print(f"\n=== Normal Navigation: {src} to {dst} ===")
    km, p = shortest_path(GRAPH, src, dst, KM)
    if not p:
        print("No road connection exists between these places.")
        return
    print(f"Shortest distance : {km} km   {fmt_path(p)}")
    mins, p = shortest_path(GRAPH, src, dst, MIN)
    print(f"Fastest time      : {fmt_time(mins)}   {fmt_path(p)}")
    p = bfs_fewest_stops(GRAPH, src, dst)
    print(f"Fewest stops      : {len(p) - 2} stop(s)   {fmt_path(p)}")
    print("Alternative routes (sorted by distance):")
    for i, (k, m, path) in enumerate(all_routes(GRAPH, src, dst, 4), 1):
        print(f"  {i}. {k} km, {fmt_time(m)} : {fmt_path(path)}")


# ----------------------------------------------------------------------
# 4. MODE 2 - FLOOD EVACUATION
# ----------------------------------------------------------------------
FLOOD_LEVEL = {            # Hash map: 0 = safe ... 3 = severe (sample values)
    "Alappuzha": 3, "Kottayam": 2, "Kochi": 1, "Thrissur": 0, "Idukki": 2,
    "Kollam": 0, "Pathanamthitta": 3, "Palakkad": 0, "Kozhikode": 0,
}
RELIEF_CAMPS = {           # Hash map: city -> [capacity, current occupancy]
    "Kollam": [500, 120], "Kochi": [800, 790], "Thrissur": [600, 200],
    "Palakkad": [400, 50], "Kozhikode": [700, 300],
}
FLOOD_BLOCK_LEVEL = 3


def flood_evacuation(src):
    print(f"\n=== Flood Evacuation from {src} ===")
    blocked = {c for c, lv in FLOOD_LEVEL.items() if lv >= FLOOD_BLOCK_LEVEL and c != src}
    print("Flooded (blocked) areas:", ", ".join(sorted(blocked)) or "none")
    dist, parent = dijkstra(GRAPH, src, KM, blocked)
    options = []
    for camp, (cap, occ) in RELIEF_CAMPS.items():
        free = cap - occ
        if camp == src or (dist[camp] < float("inf") and free > 0):
            options.append((dist[camp], camp, free))
    if not options:
        print("No reachable relief camp with space. Contact district control room.")
        return
    options.sort()
    d, camp, free = options[0]
    print(f"Nearest SAFE camp : {camp} ({d} km, {free} places free)")
    print("Safe route        :", fmt_path(build_path(parent, camp)))
    others = [o for o in options[1:3]]
    if others:
        print("Other options     :", "; ".join(f"{c} ({k} km)" for k, c, _ in others))


def emergency_requests():
    """Priority queue: most urgent request is served first."""
    print("\n=== Emergency Request Priority Queue ===")
    requests = [(3, "Elderly patients stranded - Alappuzha"),
                (1, "Food supply request - Kozhikode camp"),
                (2, "Family on rooftop - Kottayam"),
                (1, "Drinking water - Thrissur camp"),
                (3, "Medical emergency - Pathanamthitta")]
    heap = []
    for order, (urgency, text) in enumerate(requests):
        heapq.heappush(heap, (-urgency, order, text))   # max-heap via negative key
    rank = 1
    while heap:
        neg, _, text = heapq.heappop(heap)
        print(f"  {rank}. [urgency {-neg}] {text}")
        rank += 1


# ----------------------------------------------------------------------
# 5. MODE 3 - EV ROUTE PLANNER
# ----------------------------------------------------------------------
CHARGERS = {"Kollam", "Alappuzha", "Kottayam", "Kochi", "Thrissur", "Palakkad", "Kozhikode", "Kannur"}
CHARGE_MINUTES = 40


def ev_route(src, dst, range_km):
    """Dijkstra over states (city, battery_left). Minimises total time.
    Charging at a station refills the battery fully and costs CHARGE_MINUTES."""
    print(f"\n=== EV Route Planner: {src} to {dst} (full range {range_km} km) ===")
    start = (src, range_km)
    best = {start: 0}
    parent = {start: None}
    heap = [(0, src, range_km)]
    goal = None
    while heap:
        t, u, bat = heapq.heappop(heap)
        if best.get((u, bat), float("inf")) < t:
            continue
        if u == dst:
            goal = (u, bat)
            break
        moves = [(v, km, mins, bat - km) for v, km, mins in GRAPH[u] if km <= bat]
        if u in CHARGERS and bat < range_km:
            moves.append((u, 0, CHARGE_MINUTES, range_km))   # charge in place
        for v, km, mins, nb in moves:
            nt = t + mins
            if nt < best.get((v, nb), float("inf")):
                best[(v, nb)] = nt
                parent[(v, nb)] = (u, bat)
                heapq.heappush(heap, (nt, v, nb))
    if not goal:
        print("Destination not reachable with this battery range.")
        return None
    states = []
    s = goal
    while s:
        states.append(s)
        s = parent[s]
    states.reverse()
    path = [states[0][0]] + [b[0] for a, b in zip(states, states[1:]) if a[0] != b[0]]
    charges = [a[0] for a, b in zip(states, states[1:]) if a[0] == b[0]]
    print("Route:", fmt_path(path))
    print(f"Charging stops : {', '.join(charges) if charges else 'none needed'}")
    print(f"Total time     : {fmt_time(best[goal])} (including {len(charges) * CHARGE_MINUTES} min charging)")
    print(f"Battery left   : {goal[1]} km")
    return {"path": path, "charges": charges, "min": best[goal], "left": goal[1]}


# ----------------------------------------------------------------------
# 6. MODE 4 - AMBULANCE ROUTING
# ----------------------------------------------------------------------
HOSPITALS = {                     # Hash map: city -> {name, beds}
    "Thiruvananthapuram": {"name": "Medical College Hospital", "beds": 0},
    "Kollam": {"name": "District Hospital Kollam", "beds": 5},
    "Alappuzha": {"name": "General Hospital Alappuzha", "beds": 2},
    "Kottayam": {"name": "Kottayam Medical College", "beds": 0},
    "Kochi": {"name": "Ernakulam General Hospital", "beds": 8},
    "Thrissur": {"name": "Thrissur Medical College", "beds": 4},
    "Kozhikode": {"name": "Kozhikode Medical College", "beds": 6},
    "Kannur": {"name": "Kannur District Hospital", "beds": 1},
}


def ambulance_route(src):
    print(f"\n=== Ambulance Routing from {src} ===")
    dist, parent = dijkstra(GRAPH, src, MIN)     # time matters most
    candidates = sorted((dist[c], c) for c in HOSPITALS if dist[c] < float("inf"))
    for t, city in candidates:
        h = HOSPITALS[city]
        if h["beds"] > 0:
            print(f"Go to : {h['name']}, {city} ({h['beds']} beds free)")
            print(f"ETA   : {fmt_time(t)}")
            print(f"Route : {fmt_path(build_path(parent, city))}")
            return
        print(f"Skipping {h['name']} ({city}) - no beds available")
    print("No reachable hospital with free beds.")


# ----------------------------------------------------------------------
# 7. MODE 5 - CAMPUS NAVIGATOR
#    DEMO DATA - replace with your college's real buildings and distances (metres)
# ----------------------------------------------------------------------
CAMPUS_EDGES = [
    ("Main Gate", "Admin Block", 120), ("Main Gate", "Parking", 80),
    ("Admin Block", "Library", 90), ("Admin Block", "Class Block A", 150),
    ("Library", "Class Block A", 70), ("Library", "Computer Lab", 110),
    ("Class Block A", "Computer Lab", 60), ("Class Block A", "Canteen", 130),
    ("Computer Lab", "Canteen", 90), ("Parking", "Canteen", 200),
]
CAMPUS = {}
for a, b, m in CAMPUS_EDGES:
    CAMPUS.setdefault(a, []).append((b, m, m))
    CAMPUS.setdefault(b, []).append((a, m, m))


def campus_navigator(src, dst):
    print(f"\n=== Campus Navigator: {src} to {dst} ===")
    d, p = shortest_path(CAMPUS, src, dst, KM)
    if not p:
        print("Location not found / not connected.")
        return
    print(f"Walking distance: {d} m (about {round(d / 80)} min)")
    print("Route:", fmt_path(p))


# ----------------------------------------------------------------------
# 8. MENU
# ----------------------------------------------------------------------
def pick(options, prompt):
    for i, o in enumerate(options, 1):
        print(f"  {i}. {o}")
    while True:
        s = input(prompt).strip()
        if s.isdigit() and 1 <= int(s) <= len(options):
            return options[int(s) - 1]
        print("Invalid choice, try again.")


def main():
    while True:
        print("\n" + "=" * 52)
        print(" SmartRoute Kerala - Intelligent Route Planner")
        print("=" * 52)
        print(" 1. Normal Navigation\n 2. Flood Evacuation\n 3. EV Route Planner")
        print(" 4. Ambulance Routing\n 5. Campus Navigator")
        print(" 6. Road network check (DFS)\n 0. Exit")
        ch = input("Choose mode: ").strip()
        if ch == "0":
            print("Thank you for using SmartRoute Kerala.")
            break
        elif ch == "1":
            print("Select start:"); s = pick(CITIES, "Start no: ")
            print("Select destination:"); d = pick(CITIES, "Destination no: ")
            normal_navigation(s, d)
        elif ch == "2":
            print("Select your location:"); s = pick(CITIES, "Location no: ")
            flood_evacuation(s); emergency_requests()
        elif ch == "3":
            print("Select start:"); s = pick(CITIES, "Start no: ")
            print("Select destination:"); d = pick(CITIES, "Destination no: ")
            r = int(input("Battery range in km (e.g. 150): "))
            ev_route(s, d, r)
        elif ch == "4":
            print("Select accident location:"); s = pick(CITIES, "Location no: ")
            ambulance_route(s)
        elif ch == "5":
            places = list(CAMPUS)
            print("Select start:"); s = pick(places, "Start no: ")
            print("Select destination:"); d = pick(places, "Destination no: ")
            campus_navigator(s, d)
        elif ch == "6":
            print("\nConnected regions found by DFS:")
            for i, comp in enumerate(dfs_components(GRAPH), 1):
                print(f"  Region {i}: {len(comp)} place(s) - {', '.join(comp)}")
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
