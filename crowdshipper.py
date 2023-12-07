from config import HYPER_PARAMS
import networkx
from utils import *


#class for crowdshippers, representing one of the RL agents
class Crowdshipper:
    def __init__(self,origin_destination,zone,type,max_d = HYPER_PARAMS['max_distance_crowdshipper'],capacity = HYPER_PARAMS['crowdshipper_capcity']):
        self.current_node = origin_destination[0] #Destination
        self.arrival_node = origin_destination[1] #Arrival
        self.zone = zone #operating zone
        self.type = type #resource crowdshipper (works completely for the microhub) or free crowdshippers
        self.capacity = capacity
        self.current_order = None #Order to be delivered
        self.has_order = False #If the crowdshipper picked the order
        self.max_threshold = max_d #threshold for accepting a delivery
        self.stops = [self.arrival_node] #Stops along the way, sequence of nodes
    

    def add_stop(self,node):
        self.stops.insert(0,node) #prepend a stop
    def get_next_destination(self):
        if len(self.stops) > 0:
            return self.stops[0]
        return None

    def is_at_destination(self):
        dest = self.get_next_destination()
        if dest is not None:
            return (self.current_node == dest)
        return False
    
    def move_to(self,node):
        self.current_node = node
        if self.is_at_destination():
            self.stops.pop(0)


    def arrival_time(self,stop):
        if self.traverses_link(stop):
            ##Custom compute
            return self.stops.index(stop) #We suppose that arrival time = number of steps left to reach the stop
        return None


    def traverses_link(self,link):
        return (link in self.stops)
    
    def update_position(self):
        next_stop = self.get_next_destination()
        if next_stop is not None and not self.is_at_destination():
            path = custom_shortest_path(self.current_node.G,self.current_node,next_stop)
            self.move_to(path[0])
            if self.current_order is not None and self.has_order:
                self.current_order.update_position(path[0])

    
    def get_position(self):
        return self.current_node
    

    def pickup_order(self,microhub):
        microhub.orders.remove(self.current_order)
        microhub.crowdshipper_orders.remove(self.current_order)
        self.has_order = True

    
    def drop_order(self):
        self.current_order = None

    def time_to_next_stop(self,next_stop): #time to reach next top in steps
        path = shortest_distance(self.current_node.G,self.current_node,next_stop)
        return path
