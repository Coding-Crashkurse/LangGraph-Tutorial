from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import socketio
from langchain_core.messages import HumanMessage
from langgraph.graph import END, MessageGraph
import time
from collections import defaultdict

# Create FastAPI app and SocketIO server
app = FastAPI()
sio = socketio.AsyncServer(async_mode="asgi")
socket_app = socketio.ASGIApp(sio, app)


# Function to calculate node coordinates dynamically
def calculate_node_coordinates(graph_state):
    levels = defaultdict(list)
    coordinates = {}

    # Determine the level of each node
    def assign_levels(node, level):
        if node in coordinates:
            return  # Already processed
        levels[level].append(node)
        coordinates[node] = None  # Placeholder
        for edge in graph_state["edges"]:
            if edge[0] == node:
                assign_levels(edge[1], level + 1)

    # Start by assigning levels, beginning with the entry point
    assign_levels("__start__", 0)

    # Now calculate coordinates
    level_spacing = 100
    node_spacing = 200
    for level, nodes in levels.items():
        y = level * level_spacing + 50  # Vertical position
        total_width = (len(nodes) - 1) * node_spacing
        for i, node in enumerate(nodes):
            x = (250 - total_width / 2) + i * node_spacing  # Center horizontally
            coordinates[node] = {"x": x, "y": y}

    return coordinates


# Define the graph
def add_one(input: list[HumanMessage]):
    input[0].content = input[0].content + "a"
    time.sleep(1)
    print(input)
    return input


graph = MessageGraph()

graph.add_node("branch_a", add_one)
graph.add_edge("branch_a", "branch_b")
graph.add_edge("branch_a", "branch_c")

graph.add_node("branch_b", add_one)
graph.add_node("branch_c", add_one)

graph.add_edge("branch_b", "final_node")
graph.add_edge("branch_c", "final_node")

graph.add_node("final_node", add_one)
graph.add_edge("final_node", END)

graph.set_entry_point("branch_a")
runnable = graph.compile()

# Global variable to keep track of graph state
graph_state = {
    "nodes": ["__start__", "branch_a", "branch_b", "branch_c", "final_node"],
    "edges": [
        ("__start__", "branch_a"),
        ("branch_a", "branch_b"),
        ("branch_a", "branch_c"),
        ("branch_b", "final_node"),
        ("branch_c", "final_node"),
    ],
    "current_node": None,
    "output": [],
}

# Calculate and store node coordinates
graph_state["node_coordinates"] = calculate_node_coordinates(graph_state)


@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit(
        "update", graph_state, to=sid
    )  # Send initial graph state on connection


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")


async def update_graph_state(node_name, output, sid):
    graph_state["current_node"] = node_name
    graph_state["output"].append(f"{node_name}: {output[0].content}")
    print(f"Updating graph state to node: {node_name}")  # Debug log
    await sio.emit("update", graph_state, to=sid)


@sio.event
async def run_graph_event(sid):
    print(f"Graph run triggered by {sid}")
    messages = [HumanMessage(content="a")]

    for node in ["__start__", "branch_a", "branch_b", "branch_c", "final_node"]:
        output = runnable.invoke(messages)
        await update_graph_state(node, output, sid)
        await sio.sleep(1)  # Simulate asynchronous processing

    await sio.emit("acknowledge", {"status": "completed"}, to=sid)


# Serve the React frontend
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
