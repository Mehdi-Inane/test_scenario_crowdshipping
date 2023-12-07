import networkx
import random



def get_depot(graph):
    nodes = graph.nodes()
    for node in nodes:
        if node.type == 'Depot':
            return node


def get_microhub(graph,zone):
    nodes = graph.nodes()
    for node in nodes:
        if node.type == 'Microhub' and node.zone == zone:
            return node

def shortest_distance(G,node_1,node_2):
    new_graph = G.copy()
    removable_nodes = []
    for node in G.nodes():
        if node.type == 'Customer':
            if not (node == node_1 or node == node_2):
                removable_nodes.append(node)
    new_graph.remove_nodes_from(removable_nodes)
    return networkx.shortest_path_length(new_graph,node_1,node_2)


def custom_shortest_path(G,node_1,node_2):
    new_graph = G.copy()
    removable_nodes = []
    for node in G.nodes():
        if node.type == 'Customer':
            if not (node == node_1 or node == node_2):
                removable_nodes.append(node)
    new_graph.remove_nodes_from(removable_nodes)
    return networkx.shortest_path(new_graph,node_1,node_2)


def random_origin_destination(graph,zone):
    nodes = graph.nodes()
    zone_nodes = []
    for node in nodes:
        if node.zone == zone:
            zone_nodes.append(node)
    return random.sample(zone_nodes, 2)

def is_connected_subgraph(graph, nodes):
    return networkx.is_connected(graph.subgraph(nodes))

def check_all_nodes_in_zone(zone,node_list):
    target = len(node_list) * zone
    value = 0
    for node in node_list:
        value += node.zone
    return value == target


def connect_subgraph(G,subset_of_nodes):
    while (not is_connected_subgraph(G, subset_of_nodes)) or (len(list(networkx.isolates(G.subgraph(subset_of_nodes)))) != 0):
        # Randomly choose two nodes from the subset
        node1 = random.choice(subset_of_nodes)
        node2 = random.choice(subset_of_nodes)
        # Avoid self-loops and duplicate edges
        if node1 != node2 and not G.has_edge(node1, node2):
            G.add_edge(node1, node2)


def get_random_origin(graph):
    nodes = graph.nodes()
    choice_nodes = []
    for node in nodes:
        if node.type == 'Microhub' or node.type == 'Depot':
            choice_nodes.append(node)
    return random.choice(choice_nodes)