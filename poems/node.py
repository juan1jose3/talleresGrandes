from flask import Flask, jsonify, request
import requests
import os
import time

class Node:
    def __init__(self, node_id, phrase_number, phrase_content, neighbors, port):
        self.node_id = node_id
        self.phrase_number = int(phrase_number)
        self.phrase_content = phrase_content
        self.neighbors = set(neighbors) if neighbors else set()
        self.port = port
        
    def get_phrase(self):
        return {
            "node_id": self.node_id,
            "phrase_number": self.phrase_number,
            "content": self.phrase_content
        }
    
    def get_complete_text(self, visited_nodes=None):
        if visited_nodes is None:
            visited_nodes = set()
        
        collected_phrases = {}
        visited_nodes.add(self.node_id)
        
        collected_phrases[self.phrase_number] = {
            "content": self.phrase_content,
            "node_id": self.node_id
        }
        
        for neighbor in self.neighbors:
            neighbor_id = neighbor.split(':')[0]
            
            if neighbor_id not in visited_nodes:
                try:
                    response = requests.get(
                        f"http://{neighbor}/internal/collect",
                        params={"visited": ",".join(visited_nodes)},
                        timeout=3
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for key, value in data["phrases"].items():
                            collected_phrases[int(key)] = value
                        visited_nodes.update(data["visited"])
                        
                except Exception as e:
                    print(f"Error connecting to {neighbor}: {e}")
                    continue
        
        return {
            "phrases": collected_phrases,
            "visited": list(visited_nodes)
        }
    
    def discover_neighbors(self):
        discovered = []
        for i in range(1, 10):
            service_name = f"node{i}"
            if service_name != self.node_id:
                try:
                    response = requests.get(
                        f"http://{service_name}:5000/health",
                        timeout=2
                    )
                    if response.status_code == 200:
                        neighbor_address = f"{service_name}:5000"
                        if neighbor_address not in self.neighbors:
                            self.neighbors.add(neighbor_address)
                            discovered.append(neighbor_address)
                except:
                    continue
        return discovered
    
    def add_neighbor(self, neighbor_address):
        self.neighbors.add(neighbor_address)
        return True
    
    def remove_neighbor(self, neighbor_address):
        if neighbor_address in self.neighbors:
            self.neighbors.remove(neighbor_address)
            return True
        return False
    
    def update_phrase(self, new_content=None, new_number=None):
        if new_content is not None:
            self.phrase_content = new_content
        if new_number is not None:
            self.phrase_number = int(new_number)
        return True


app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False
app.json.ensure_ascii = False


node_id = os.getenv("NODE_ID", "node1")
phrase_number = int(os.getenv("PHRASE_NUMBER", "1"))
phrase_content = os.getenv("PHRASE_CONTENT", "Default phrase")
neighbors_str = os.getenv("NEIGHBORS", "")
port = int(os.getenv("PORT", "5000"))

neighbors = [n.strip() for n in neighbors_str.split(",") if n.strip()]
node = Node(node_id, phrase_number, phrase_content, neighbors, port)


@app.route("/phrase", methods=["GET"])
def get_phrase():
    return jsonify(node.get_phrase()), 200


@app.route("/complete", methods=["GET"])
def get_complete_text():
    result = node.get_complete_text()
    
    sorted_phrases = sorted(result["phrases"].items())
    
    complete_text = "\n".join([
        f"Frase {num}: {data['content']}"
        for num, data in sorted_phrases
    ])
    
    response = jsonify({
        "complete_text": complete_text,
        "phrases": result["phrases"],
        "nodes_visited": len(result["visited"]),
        "visited_nodes": result["visited"]
    })
    
    # IMPORTANTE: Desactivar escape de caracteres Unicode
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    app.config['JSON_AS_ASCII'] = False
    
    return response, 200

@app.route("/internal/collect", methods=["GET"])
def collect_phrases():
    visited_str = request.args.get("visited", "")
    visited_nodes = set(visited_str.split(",")) if visited_str else set()
    
    result = node.get_complete_text(visited_nodes)
    return jsonify(result), 200


@app.route("/neighbors", methods=["GET"])
def get_neighbors():
    return jsonify({
        "node_id": node.node_id,
        "neighbors": list(node.neighbors)
    }), 200


@app.route("/neighbors", methods=["POST"])
def add_neighbor():
    data = request.get_json()
    neighbor_address = data.get("address")
    
    if not neighbor_address:
        return jsonify({"error": "Address is required"}), 400
    
    node.add_neighbor(neighbor_address)
    return jsonify({
        "message": f"Neighbor {neighbor_address} added",
        "neighbors": list(node.neighbors)
    }), 200


@app.route("/neighbors", methods=["DELETE"])
def remove_neighbor():
    data = request.get_json()
    neighbor_address = data.get("address")
    
    if not neighbor_address:
        return jsonify({"error": "Address is required"}), 400
    
    success = node.remove_neighbor(neighbor_address)
    
    if success:
        return jsonify({
            "message": f"Neighbor {neighbor_address} removed",
            "neighbors": list(node.neighbors)
        }), 200
    else:
        return jsonify({"error": "Neighbor not found"}), 404


@app.route("/neighbors/discover", methods=["POST"])
def discover_neighbors():
    discovered = node.discover_neighbors()
    return jsonify({
        "message": f"Discovered {len(discovered)} new neighbors",
        "discovered": discovered,
        "all_neighbors": list(node.neighbors)
    }), 200


@app.route("/phrase", methods=["PUT"])
def update_phrase():
    data = request.get_json()
    new_content = data.get("content")
    new_number = data.get("number")
    
    if new_content is None and new_number is None:
        return jsonify({
            "error": "Must provide 'content' or 'number'"
        }), 400
    
    node.update_phrase(new_content, new_number)
    
    return jsonify({
        "message": "Phrase updated successfully",
        "phrase": node.get_phrase()
    }), 200


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "node_id": node.node_id,
        "phrase_number": node.phrase_number,
        "neighbors_count": len(node.neighbors)
    }), 200


@app.route("/status", methods=["GET"])
def get_status():
    return jsonify({
        "node_id": node.node_id,
        "phrase_number": node.phrase_number,
        "phrase_content": node.phrase_content,
        "neighbors": list(node.neighbors),
        "port": node.port
    }), 200


if __name__ == "__main__":
    time.sleep(3)
    print(f"Starting {node.node_id} on port {port}...")
    node.discover_neighbors()
    print(f"Neighbors: {node.neighbors}")
    app.run(host="0.0.0.0", port=port, debug=False)
