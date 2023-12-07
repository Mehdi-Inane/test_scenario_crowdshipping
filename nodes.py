import uuid
from config import HYPER_PARAMS
from utils import *
from crowdshipper import Crowdshipper
import numpy as np
from order import *
from truck import *
#Node class of the network
class Node:
    def __init__(self,type,zone,graph):
        self.type = type
        self.id = uuid.uuid1()
        self.zone = zone
        self.G = graph
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self,node):
        if self and node:
            return self.id == node.id
        else:
            return False

class Depot(Node):
    def __init__(self,type,zone,graph,order_limit = 6):
        super(Depot,self).__init__(type,zone,graph)
        self.trucks = []
        self.orders = []
        self.order_limit = order_limit
    
    def add_order(self,order):
        self.orders.append(order)
    
    def add_orders_from(self,orders):
        self.orders += orders
    
    
    def get_available_trucks(self):
        available_trucks = []
        for truck in self.trucks:
            if truck.current_node == self:
                available_trucks.append(truck)
        return available_trucks

    def add_trucks(self,trucks):
        self.trucks += trucks

    def deploy_trucks(self,truck_list,orders,policy = None):
        if policy:
            pass #Amir VRP
        deployed_trucks = []
        for truck in truck_list:
            added_orders = []
            for order in orders:
                if not truck.is_at_max():
                    truck.add_order(order)
                    added_orders.append(order)
                else:
                    break
            for order in added_orders:
                orders.remove(order)
            if len(added_orders):
                deployed_trucks.append(truck)
            if len(orders) == 0:
                break
        for truck in deployed_trucks:
            truck.set_route()
        


    def step(self):
        trucks = self.get_available_trucks()
        if len(self.orders) >= self.order_limit and len(trucks): # If trucks are available and we need to deploy them
            self.deploy_trucks(trucks,self.orders)






#Node that represents a Microhub. This node also has all of the information related to the zone 
#For instance, a list of customers, microhub crowdshippers and zone crowdshippers
class Microhub(Node):
    def __init__(self,type,zone,graph,resource_crowdshippers,free_crowdshippers,links = HYPER_PARAMS['links_per_zone'],customers = HYPER_PARAMS['customers_per_zone']):
        super(Microhub,self).__init__(type,zone,graph)
        #Create customers in the zone, customers argument is the nb of customers within the zone
        #self.customer_nodes = [Customer('Customer',self.zone,self.G) for _ in range(customers)]
        self.customer_nodes = []
        #creating links in the network to create different routes
        self.links = [Node('links',self.zone,self.G) for _ in range(links)]
        self.G.add_nodes_from(self.links)
        #Creating a random subgraph representing the zone by randomly adding edges until the subgraph is connected
        self.connect_zone()
        #Orders in the microhub
        self.orders = []
        #Orders in the microhub that need to be transferred
        self.truck_orders = []
        #Orders in the microhub that need to be delivered
        self.crowdshipper_orders = []
        #If the truck is currently going to the microhub
        self.truck_on_the_way = False
        #Number of crowdshippers not working FOR the microhub 
        self.free_crowdshippers = free_crowdshippers
        #number of crowdshippers that are only resources of the microhub
        self.resource_crowdshippers = resource_crowdshippers
        self.put_crowdshippers()
    

    

    
    def generate_customers_orders(self,customer_nb):
        new_customers = [Customer('Customer',self.zone,self.G) for _ in range(customer_nb)]
        self.customer_nodes += new_customers
        nb_immutable_nodes = len(self.links) + 1
        node_choices = self.links + [self]
        for customer in new_customers:
            connected_nodes = set()
            nb_edges = random.randint(1,3) #Random number of edges to add
            self.G.add_node(customer)
            for i in range(nb_edges):
                picked_node = random.choice(node_choices)
                while picked_node in connected_nodes:
                    picked_node = random.choice(node_choices)
            
                self.G.add_edge(customer,picked_node)
            #origin = get_random_origin(self.G)
            origin = get_depot(self.G)
            order = Order(origin=origin,destination=customer,zone=self.zone)
            self.add_order(order)
            customer.add_order(order)


    
    
    def put_crowdshippers(self):
        self.crowdshippers_free = [Crowdshipper(random_origin_destination(self.G,self.zone),self.zone,'free') for _ in range(self.free_crowdshippers)]
        self.crowdshipper_resources = [Crowdshipper(random_origin_destination(self.G,self.zone),self.zone,'resource') for _ in range(self.resource_crowdshippers)]





    def connect_zone(self):
        nodes = [self] + self.links + self.customer_nodes
        subgraph = self.G.subgraph(nodes)
        while not networkx.is_connected(subgraph):
            subgraph = self.G.subgraph(nodes)
            node1 = random.choice(list(subgraph.nodes()))
            node2 = random.choice(list(subgraph.nodes()))
            while (node1 == node2) or (subgraph.has_edge(node1,node2)):
                node1 = random.choice(list(nodes))
                node2 = random.choice(list(nodes))
            # Avoid self-loops and duplicate edges
            self.G.add_edge(node1, node2)


    def add_order(self, order):
            self.orders.append(order)
            #If the order is to be delivered within the zone, assign it to crowdshipper orders
            if order.within_zone(self.zone):
                self.crowdshipper_orders.append(order)
            
            #assign it to truck orders if it needs to be transferred to another zone
            else:
                self.truck_orders.append(order)

    def remove_order(self, order):
        self.orders.remove(order)
        if order in self.truck_orders:
            self.truck_orders.remove(order)
        else:
            self.crowdshipper_orders.remove(order)


    def deploy_crowdshippers(self):
        for order in self.crowdshipper_orders:
            if not order.assigned:
                order_pos = order.arrival_node
                #We will pick the crowdshipper with the nearest destination to the delivery
                min_distance = np.inf
                temp = None
                for crowdshipper in self.crowdshippers_free:
                    if crowdshipper.current_order is None:
                        distance = shortest_distance(self.G,crowdshipper.arrival_node,order.arrival_node)
                        if distance < min_distance:
                            min_distance = distance
                            temp = crowdshipper
                # With probability 0.5 we deliver
                p = random.random()
                if p < 0.5:
                    order.assigned = True
                    order.shipper = temp  
                    temp.current_order = order
                    temp.add_stop(order.arrival_node)
                    temp.add_stop(self)
        #Deliver the remaining orders with 0.7 probability (resource crowdshippers)
        for order in self.crowdshipper_orders:
            if not order.assigned:
                p = random.random()
                if p > 0.3:
                    for crowdshipper in self.crowdshipper_resources:
                        if crowdshipper.current_order is None:
                            order.assigned = True
                            order.shipper = crowdshipper
                            crowdshipper.current_order = order  
                            crowdshipper.add_stop(self) #In order to come back to microhub
                            crowdshipper.add_stop(order.arrival_node)  
                            break        
    
    
    def get_transfer_capacity(self):
        return len(self.truck_orders)



    def get_customers(self):
        return self.customer_nodes


    def get_all_unattributed_orders(self):
        ret_list = []
        for elem in self.customer_nodes:
            ret_list += elem.orders
        return self.orders + ret_list
    
    def all_order_summary(self):
        print('In zone ' + str(self.zone))
        orders = self.get_all_unattributed_orders()
        for order in orders:
            print(order.describe())
    

    def get_all_undelivered_orders(self): #returns all orders that are not delivered or are still in the microhub
        ret_list = []
        ret_list += self.orders
        for customer in self.customer_nodes:
            ret_list += customer.orders
        return ret_list

    def get_delivered_orders(self):#returns a list of delivered order IDs
        ret_lis = []
        for order in self.orders:
            if order.delivered():
                ret_lis.append(order)
        return ret_lis


    def concat_order_info(self):
        all_orders = self.get_all_undelivered_orders()
        dico = {}
        dico['id'] = []
        dico['Zone'] = []
        dico['weight'] = []
        dico['origin'] = []
        dico['destination'] = []
        dico['current_pos'] = []
        dico['arrival_time'] = []
        dico['assigned'] = []
        dico['picked_up'] = []
        dico['delivered'] = []
        dico['delivery mode'] = []
        for order in all_orders:
            order_desc = order.info()
            for key in dico.keys():
                dico[key].append(order_desc[key])
            
        return dico



#########   Define customer class #######

class Customer(Node):
    def __init__(self,type,zone,graph):
        super(Customer,self).__init__(type,zone,graph)
        self.orders = []
    

    def add_order(self,order): ##Orders the customer currently has : for expenditures
        self.orders.append(order)