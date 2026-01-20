import streamlit as st
import hashlib

def generate_consistent_hash_ring(nodes, data_key):
    """
    Generates a graphviz visualization of a consistent hash ring.

    Args:
        nodes (list): A list of node names.
        data_key (str): The key of the data to be placed on the ring.

    Returns:
        str: A graphviz string representing the consistent hash ring.
    """
    if not nodes:
        return ""

    # Use a larger hash space for better distribution visualization
    hash_space = 2**16 
    
    node_hashes = {}
    for node in nodes:
        # Use a simple hash for demonstration
        node_hash = int(hashlib.md5(node.encode()).hexdigest(), 16) % hash_space
        node_hashes[node_hash] = node

    # Hash the data key
    data_hash = int(hashlib.md5(data_key.encode()).hexdigest(), 16) % hash_space

    # Find the node responsible for the data
    sorted_node_hashes = sorted(node_hashes.keys())
    responsible_node_hash = -1
    for node_hash in sorted_node_hashes:
        if data_hash <= node_hash:
            responsible_node_hash = node_hash
            break
    
    # If the data_hash is greater than all node_hashes, it belongs to the first node (wraps around)
    if responsible_node_hash == -1:
        responsible_node_hash = sorted_node_hashes[0]
        
    responsible_node = node_hashes[responsible_node_hash]

    # --- Create Graphviz Diagram ---
    dot_string = "digraph ConsistentHashRing {\n"
    dot_string += "    rankdir=LR;\n"
    dot_string += "    node [shape=circle];\n"
    dot_string += '    layout=circo;\n'
    dot_string += '    overlap=false;\n'
    dot_string += '    splines=true;\n'


    # Add nodes to the ring
    for h, node in node_hashes.items():
        label = f"{node}\n(h={h})"
        if node == responsible_node:
            dot_string += f'    "{label}" [style=filled, fillcolor=lightblue];\n'
        else:
            dot_string += f'    "{label}";\n'

    # Add data key to the ring
    data_label = f"Data Key: '{data_key}'\n(h={data_hash})"
    dot_string += f'    "{data_label}" [shape=diamond, style=filled, fillcolor=lightgreen];\n'

    # Draw arrows to show ownership
    dot_string += f'    "{data_label}" -> "{responsible_node}\n(h={responsible_node_hash})" [label=" Belongs to"];\n'
    
    dot_string += "}"
    
    return dot_string