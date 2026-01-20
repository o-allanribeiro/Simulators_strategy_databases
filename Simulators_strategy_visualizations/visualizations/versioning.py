import streamlit as st
from graphviz import Digraph

# A simplified representation of an LSM-Tree
class LSMTree:
    def __init__(self, memtable_threshold=4):
        self.memtable = {}
        self.sstables = []
        self.memtable_threshold = memtable_threshold

    def write(self, key, value):
        self.memtable[key] = value
        if len(self.memtable) >= self.memtable_threshold:
            self.flush()
            return f"Memtable threshold reached. Flushed to SSTable {len(self.sstables)}."
        return f"Wrote '{key}:{value}' to Memtable."

    def flush(self):
        if not self.memtable:
            return
        # SSTables are sorted by key
        sorted_memtable = sorted(self.memtable.items())
        self.sstables.insert(0, sorted_memtable) # Newest first
        self.memtable = {}

    def read(self, key):
        # Check memtable first (most recent data)
        if key in self.memtable:
            return self.memtable[key], "Memtable"
        
        # Check SSTables from newest to oldest
        for i, sstable in enumerate(self.sstables):
            for k, v in sstable:
                if k == key:
                    return v, f"SSTable {i+1}"
        
        return None, "Not Found"

    def compact(self):
        if not self.sstables:
            return "No SSTables to compact."
        
        self.flush() # Ensure memtable is empty first
        
        all_data = {}
        # Iterate from oldest to newest to ensure we keep the latest version
        for sstable in reversed(self.sstables):
            for key, value in sstable:
                all_data[key] = value
        
        self.sstables = [sorted(all_data.items())] if all_data else []
        return "Compaction complete. All SSTables merged into one."


def generate_lsm_tree_visualization(lsm_tree: LSMTree):
    """Generates a graphviz visualization of the LSM-Tree state."""
    
    dot = Digraph('LSMTree', comment='Log-Structured Merge-Tree')
    dot.attr(rankdir='TB', splines='ortho')

    # Client
    dot.node('client', 'Client Application', shape='box', style='rounded')

    # Memtable
    with dot.subgraph(name='cluster_memtable') as c:
        c.attr(label='Memtable (In-Memory, Sorted)', style='filled', color='lightyellow')
        memtable_content = "\n".join([f"{k}: {v}" for k, v in sorted(lsm_tree.memtable.items())])
        if not memtable_content:
            memtable_content = "(empty)"
        c.node('memtable', memtable_content, shape='record')

    dot.edge('client', 'memtable', 'Writes')

    # SSTables
    with dot.subgraph(name='cluster_sstables') as c:
        c.attr(label='SSTables (On-Disk, Immutable)', style='filled', color='lightblue')
        if not lsm_tree.sstables:
            c.node('sstables_empty', '(No SSTables on disk)', shape='plaintext')
        else:
            for i, sstable in enumerate(lsm_tree.sstables):
                sstable_content = "|".join([f"<{k}>{k}: {v}" for k,v in sstable])
                c.node(f'sstable_{i}', sstable_content, shape='record')

    if len(lsm_tree.sstables) > 1:
        for i in range(len(lsm_tree.sstables) - 1):
            dot.edge(f'sstable_{i}', f'sstable_{i+1}', style='invis')

    dot.edge('memtable', 'sstable_0' if lsm_tree.sstables else 'sstables_empty', 'Flush', style='dashed', constraint='false')
    
    return dot