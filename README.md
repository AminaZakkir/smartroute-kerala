# SmartRoute Kerala

A multi-purpose intelligent route planning and emergency management system.
BCA Semester 3 - Data Structures and Algorithms vacation mini project.

**Live demo:** https://smartroutekerala.pythonanywhere.com

## Five modes in one application

| Mode | Purpose | Main DSA |
|---|---|---|
| Normal Navigation | Shortest, fastest, fewest-stops and alternative routes | Dijkstra, BFS, DFS, sorting |
| Flood Evacuation | Safest route to a relief camp with free space | Graph, hash map, heap, Dijkstra |
| EV Route Planner | Routes with battery range and charging stops | Dijkstra over (city, battery) states |
| Ambulance Routing | Nearest hospital that has free beds | Dijkstra, hash map |
| Campus Navigator | Walking routes between campus locations | Graph, Dijkstra |

## Data structures and algorithms

- Graph (adjacency list) for roads and cities
- Hash map (dictionary) for flood levels, camps, hospitals
- Priority queue (min-heap) for Dijkstra and emergency requests
- Queue for BFS, stack and recursion for DFS
- Sorting to rank alternative routes

## Files

- `smartroute_kerala.py` - all algorithms and sample data (also runs as a terminal menu)
- `app.py` - Flask web server that exposes the algorithms as an API and logs usage
- `static/index.html` - the web page with the map, route comparison and learning icons

## Run it on your computer

```
pip install flask
python app.py
```

Then open http://localhost:5000

To use the usage statistics page, set your own password with the `ADMIN_KEY`
environment variable, then open `/stats?key=YOUR_KEY`.

## Limitations

All distances, travel times, flood levels, hospital beds and camp capacities are
approximate sample data. This is a working prototype, not a live navigation or
emergency dispatch service.

## Future scope

Google Maps integration, real-time traffic, live flood and rainfall data, AI travel-time
prediction, real hospital bed availability, EV charging station data, GPS location.
