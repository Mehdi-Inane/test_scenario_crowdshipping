import uuid,networkx
from utils import *

class Truck:
    def __init__(self, node_position,capacity):
        self.id = uuid.uuid1()
        self.current_node = node_position
        self.orders = []
        self.capacity = capacity
        self.stops = []
        self.destination = None
        self.load = 0
        self.en_route = False
        
    def load_orders(self, node):
        self.orders = node.truck_orders[:]
        for order in self.orders:
            node.remove_order(order)
            self.load += order.weight

    def add_orders_from(self,orders):
        self.orders += orders
        for order in orders:
            self.load += order.weight
    def add_order(self,order):
        self.orders.append(order)
        self.load += order.weight

    def arrival_time(self,node):
        if self.traverses_link(node):
            ##Compute otherwise
            return self.stops.index(node)
        return None

    def unload_orders(self, microhub):
        for order in self.orders:
            if order.zone == microhub.zone:
                microhub.add_order(order)
                self.load -= order.weight
                self.orders.remove(order)
    
    def is_transferring(self):
        return (len(self.orders) > 0)
    
    def is_going_to_microhub(self):
        return (len(self.orders) == 0 and self.destination is not None)

    def traverses_link(self,link):
        return (link in self.stops)

    def get_load(self):
        return self.load

    def is_at_max(self):
        return self.load >= self.capacity

    def is_waiting(self):
        return self.destination is None

    def move_to(self,node):
        self.current_node = node
        if self.is_at_destination():
            self.stops.pop(0)
        
    def set_destination(self, node):
        self.destination = node
        
    def is_at_destination(self):
        return self.destination is None or (self.current_node) == self.destination
        
    def update_position(self):
        next_stop = self.get_next_destination()
        if next_stop is not None and not self.is_at_destination():
            path = networkx.shortest_path(self.current_node.G,self.current_node,next_stop)
            self.move_to(path[0])
          

    def set_route(self):
        nodes_to_visit = set()
        for order in self.orders:
            nodes_to_visit.add(get_microhub(order.arrival_node.G,order.arrival_node.zone))
        origin_node = self.current_node
        final_path = []
        for node in nodes_to_visit: #Setting the itinerary of the truck
            shortest_path = custom_shortest_path(self.current_node.G,origin_node,node)
            origin_node = node
            final_path += shortest_path
        shortest_path = custom_shortest_path(self.current_node.G,origin_node,get_depot(self.current_node.G)) #Return to depot
        final_path += shortest_path
        self.stops = list(final_path)


    def get_next_stop(self):
        return self.stops[0]
    
    def drop_orders_microhub(self,node):
        if node.type != 'Microhub':
            return
        orders_zone = []
        for order in self.orders:
            if order.zone == node.zone:
                orders_zone.append(order)
        for order in orders_zone:
            self.orders.remove(order)
            self.load -= order.weight
            node.add_order(order)
    
    def step(self):
        if len(self.stops) == 0:
            return
        next_stop = self.stops.pop(0)
        self.current_node = next_stop
        for order in self.orders:
            order.update_position(next_stop)
        self.drop_orders_microhub(next_stop)
        return
