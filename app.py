"""SmartRoute Kerala - web server.
Run:  python app.py   then open http://localhost:5000
The route logic lives in smartroute_kerala.py; this file only exposes it to the web page."""
import heapq
import html
import io
import os
import sqlite3
from collections import Counter
from contextlib import redirect_stdout
from flask import Flask, jsonify, request, send_from_directory
import smartroute_kerala as sk

app = Flask(__name__, static_folder="static")
INF = float("inf")
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usage.db")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "change-me")   # change this before hosting


def db_run(sql, args=(), fetch=False):
    """Tiny helper: open the usage database, run one command, close it."""
    con = sqlite3.connect(DB)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS usage(t TEXT, mode TEXT, a TEXT, b TEXT, rng INTEGER, ok INTEGER)")
        rows = con.execute(sql, args).fetchall() if fetch else con.execute(sql, args).rowcount
        con.commit()
        return rows
    finally:
        con.close()


def log_use(mode, a, b, rng, ok):
    try:
        db_run("INSERT INTO usage VALUES(datetime('now'),?,?,?,?,?)", (mode, a, b, rng, int(ok)))
    except Exception:
        pass                                       # logging must never break the website

KM, MIN = sk.KM, sk.MIN


def stats(g, path):
    km = mins = 0
    for u, v in zip(path, path[1:]):
        e = next(x for x in g[u] if x[0] == v)
        km += e[1]
        mins += e[2]
    return km, mins


def route(g, label, path, color, algos, why, dash=False, note="", minutes=None, charges=()):
    km, mins = stats(g, path)
    return {"label": label, "path": path, "color": color, "algos": algos, "why": why,
            "k": km, "m": mins if minutes is None else minutes,
            "dash": dash, "note": note, "charges": list(charges)}


def navigate(g, a, b, campus=False):
    if a == b:
        return {"R": [], "err": "Choose two different places."}
    dist, par = sk.dijkstra(g, a, KM)
    if dist[b] == INF:
        return {"R": [], "err": f"{b} is not connected to {a} by road in this data. "
                                "Depth-first search finds such disconnected regions."}
    R = [route(g, "Shortest distance", sk.build_path(par, b), 0, ["dijkstra"],
               "Dijkstra minimised total distance, so no other route is shorter.")]
    if not campus:
        d2, p2 = sk.dijkstra(g, a, MIN)
        R.append(route(g, "Fastest time", sk.build_path(p2, b), 1, ["dijkstra"],
                       "Dijkstra again, but each road is weighted by minutes instead of km. "
                       "A longer road can win if it is quicker."))
    R.append(route(g, "Fewest stops", sk.bfs_fewest_stops(g, a, b), 2, ["bfs"],
                   "BFS counts roads, not distance. It guarantees the smallest number of roads."))
    seen = [r["path"] for r in R]
    for _, _, p in sk.all_routes(g, a, b, limit=60):
        if p not in seen:
            R.append(route(g, "Alternative route", p, 3, ["dfs"],
                           "DFS with backtracking found every simple route. Sorting by distance "
                           "ranked this as the next best choice.", dash=True))
            break
    return {"R": R}


def flood(a):
    bl = {c for c, lv in sk.FLOOD_LEVEL.items() if lv >= sk.FLOOD_BLOCK_LEVEL and c != a}
    dist, par = sk.dijkstra(sk.GRAPH, a, KM, bl)
    best = None
    for camp, (cap, occ) in sk.RELIEF_CAMPS.items():
        if cap - occ > 0 and dist[camp] < INF and (best is None or dist[camp] < dist[best]):
            best = camp
    heap = []
    for i, (urg, text) in enumerate([(3, "Elderly patients stranded, Alappuzha"),
                                     (1, "Food supply, Kozhikode camp"),
                                     (2, "Family on rooftop, Kottayam"),
                                     (1, "Drinking water, Thrissur camp"),
                                     (3, "Medical emergency, Pathanamthitta")]):
        heapq.heappush(heap, (-urg, i, text))
    queue = [[-u, t] for u, _, t in (heapq.heappop(heap) for _ in range(len(heap)))]
    if best is None:
        return {"R": [], "err": "No reachable relief camp has space. Contact the district control room.",
                "bl": sorted(bl), "queue": queue}
    cap, occ = sk.RELIEF_CAMPS[best]
    R = [route(sk.GRAPH, "Safe route to " + best, sk.build_path(par, best), 0,
               ["block", "dijkstra", "hash"],
               f"Flooded places (level 3) were blocked, then Dijkstra found the closest camp. "
               f"The hash map showed {best} still has {cap - occ} free places.",
               note="avoids " + (", ".join(sorted(bl)) or "nothing"))]
    d2, p2 = sk.dijkstra(sk.GRAPH, a, KM)
    direct = sk.build_path(p2, best)
    if any(c in bl for c in direct):
        R.append(route(sk.GRAPH, "Direct route (flooded)", direct, 1, ["dijkstra"],
                       "Shortest road ignoring floods. It passes through a flooded place, "
                       "so it is shown only to compare.", dash=True, note="unsafe"))
    return {"R": R, "bl": sorted(bl), "queue": queue}


def ev(a, b, rng):
    if a == b:
        return {"R": [], "err": "Choose two different places."}
    with redirect_stdout(io.StringIO()):          # ev_route also prints; hide that here
        res = sk.ev_route(a, b, rng)
    if not res:
        return {"R": [], "err": f"Not reachable with a {rng} km range. Try a larger range."}
    n = len(res["charges"])
    R = [route(sk.GRAPH, "EV plan", res["path"], 0, ["ev", "heap"],
               f"Dijkstra searched (city, battery) states. It added {n} charging stop(s) "
               "only where the battery would not reach the next city.",
               note=("charge at " + ", ".join(res["charges"])) if n else "no charging needed",
               minutes=res["min"], charges=res["charges"])]
    d2, p2 = sk.dijkstra(sk.GRAPH, a, MIN)
    plain = sk.build_path(p2, b)
    if plain != res["path"]:
        R.append(route(sk.GRAPH, "Plain fastest (ignores battery)", plain, 1, ["dijkstra"],
                       f"Fastest by time, but it does not check the battery, so with a {rng} km "
                       "range it may fail midway.", dash=True, note="no charging plan"))
    return {"R": R}


def ambulance(a):
    dist, par = sk.dijkstra(sk.GRAPH, a, MIN)
    order = sorted((c for c in sk.HOSPITALS if dist[c] < INF), key=lambda c: dist[c])
    if not order:
        return {"R": [], "err": "No hospital is reachable from here."}
    best = next((c for c in order if sk.HOSPITALS[c]["beds"] > 0), None)
    if best is None:
        return {"R": [], "err": "No reachable hospital has free beds."}
    R = []
    if order[0] != best:
        h = sk.HOSPITALS[order[0]]
        R.append(route(sk.GRAPH, f"Nearest: {h['name']} (full)", sk.build_path(par, order[0]), 1,
                       ["dijkstra", "hash"], "Closest by time, but the hash map shows 0 beds, "
                       "so the ambulance skips it.", dash=True, note="0 beds, skipped"))
    h = sk.HOSPITALS[best]
    R.append(route(sk.GRAPH, h["name"], sk.build_path(par, best), 0, ["dijkstra", "hash"],
                   "Dijkstra ranked hospitals by travel time. The hash map filtered out the ones "
                   "with no free beds.", note=f"{h['beds']} beds free"))
    return {"R": R}


@app.route("/api/meta")
def meta():
    return jsonify({"roads": [list(r) for r in sk.ROADS],
                    "campus": [list(e) for e in sk.CAMPUS_EDGES],
                    "flood": sk.FLOOD_LEVEL, "camps": sk.RELIEF_CAMPS,
                    "hospitals": {c: [h["name"], h["beds"]] for c, h in sk.HOSPITALS.items()},
                    "chargers": sorted(sk.CHARGERS)})


@app.route("/api/routes")
def routes():
    mode, a, b = request.args.get("mode"), request.args.get("a"), request.args.get("b", "")
    rng = int(request.args.get("range", 150))
    graph = sk.CAMPUS if mode == "campus" else sk.GRAPH
    if a not in graph or (mode in ("nav", "ev", "campus") and b not in graph):
        return jsonify({"R": [], "err": "Unknown place."})
    if mode in ("nav", "campus"):
        out = navigate(graph, a, b, campus=(mode == "campus"))
    elif mode == "flood":
        out = flood(a)
    elif mode == "ev":
        out = ev(a, b, rng)
    elif mode == "amb":
        out = ambulance(a)
    else:
        return jsonify({"R": [], "err": "Unknown mode."})
    log_use(mode, a, b if mode in ("nav", "ev", "campus") else "", rng if mode == "ev" else 0, not out.get("err"))
    return jsonify(out)


def table(title, counter, n=5):
    rows = "".join(f"<tr><td>{html.escape(str(k))}</td><td>{v}</td>"
                   f"<td><div style='background:#0f766e;height:10px;width:{v * 100 // max(counter.values())}%'></div></td></tr>"
                   for k, v in counter.most_common(n))
    return f"<h2>{title}</h2><table>{rows or '<tr><td>No data yet</td></tr>'}</table>"


@app.route("/stats")
def stats_page():
    if request.args.get("key") != ADMIN_KEY:
        return "Not allowed. Add ?key=YOUR_KEY to the address.", 403
    rows = db_run("SELECT t,mode,a,b,rng,ok FROM usage ORDER BY t DESC", fetch=True)
    modes, starts, dests, pairs, days = Counter(), Counter(), Counter(), Counter(), Counter()
    for t, mode, a, b, rng, ok in rows:               # Counter = hash map of counts
        modes[mode] += 1
        starts[a] += 1
        if b:
            dests[b] += 1
            pairs[a + " -> " + b] += 1
        days[t[:10]] += 1
    failed = sum(1 for r in rows if not r[5])
    recent = "".join(f"<tr><td>{r[0]}</td><td>{html.escape(r[1])}</td><td>{html.escape(r[2])}</td>"
                     f"<td>{html.escape(r[3])}</td><td>{'ok' if r[5] else 'no route'}</td></tr>" for r in rows[:10])
    page = ("<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>SmartRoute usage</title><style>body{font:15px system-ui;max-width:760px;margin:20px auto;padding:0 14px}"
            "table{width:100%;border-collapse:collapse}td{padding:6px;border-bottom:1px solid #ccc}h2{margin-top:26px}</style></head><body>"
            f"<h1>SmartRoute Kerala - usage</h1><p><b>{len(rows)}</b> searches in total, <b>{failed}</b> with no route found.</p>"
            + table("Most used mode", modes) + table("Most searched start places", starts)
            + table("Most searched destinations", dests) + table("Most searched routes", pairs)
            + table("Searches per day", days, 7)
            + f"<h2>Last 10 searches</h2><table>{recent or '<tr><td>No data yet</td></tr>'}</table></body></html>")
    return page


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    import threading
    import webbrowser
    threading.Timer(1.0, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run()