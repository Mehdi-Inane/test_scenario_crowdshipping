import networkx
import uuid
import random
import matplotlib.pyplot as plt
from config import HYPER_PARAMS
from utils import *
from nodes import Node,Microhub,Depot
from truck import Truck
from order import Order
import pandas as pd
import json

class City:
    def __init__(self, size, num_zones,max_orders_before_transfer = HYPER_PARAMS['max_orders_before_transfer'],num_trucks = HYPER_PARAMS['num_trucks'],truck_capacity = HYPER_PARAMS['truck_capacity'],resouce_crowdshippers = HYPER_PARAMS['resource_crowdshippers'],free_crowdshippers = HYPER_PARAMS['free_crowdshippers'],seed = True):
        if seed: #to have reproducible scenarios
            self.seed()
        self.num_zones = num_zones #number of zones
        self.network = networkx.Graph() #network
        self.size = size#area
        self.max_orders_transfer = max_orders_before_transfer
        #Cutting the region into a grid
        #Adding the microhubs in the center of each zone
        self.H = [Microhub('Microhub',i,self.network,resouce_crowdshippers,free_crowdshippers) for i in range(num_zones)]
        self.depot = Depot('Depot',num_zones + 1,self.network)
        self.F = [Truck(self.depot,truck_capacity) for _ in range(num_trucks)]     #Trucks starting in the depot area  
        self.depot.add_trucks(self.F)
        self.H0 = self.H + [self.depot]
        self.add_nodes(self.H)
        self.add_nodes([self.depot])
        self.connect_city() #connecting the components of the graph by adding random edges until connection (zones)
        self.step = None
        self.depot_microhub_distances()

    def reset(self):
        self.step = 0
        for microhub in self.H:
            num_customers = random.randint(1,5) #Generate between 1 and 5 customers
            microhub.generate_customers_orders(num_customers)
        """for i in range(self.num_zones):
            self.generate_init_orders(i)"""
    
    def seed(self,seed = 42):
        random.seed(seed)


    def display(self): #showing the network
        zones = list(range(self.num_zones + 2))
        type_colors = {node_type: plt.cm.tab20(node_type) for node_type in zones}
        pos = networkx.kamada_kawai_layout(self.network)
        node_types = [node.zone for node in self.network.nodes]
        node_colors = [type_colors[node_type] for node_type in node_types]
        node_labels = {node: self.reduce_type(node.type) for node in self.network.nodes}
        networkx.draw_networkx(self.network,pos, with_labels=True, labels = node_labels, node_color=node_colors)
        plt.show()


    def reduce_type(self,label):
        if label == 'Microhub':
            return 'M'
        if label == 'Depot':
            return 'D'
        if label =='Customer':
            return 'C'
        if label == 'links':
            return 'l'
        
    def add_nodes(self,nodes):
        self.network.add_nodes_from(nodes)
    
    def add_egdes(self,edges): #edges are a tuple
        return self.network.add_edges_from(edges)




    def current_order_info(self):
        for i in range(self.num_zones):
            microhub = self.get_microhub(i)
            microhub.all_order_summary()
    



    def connect_city(self):
        while not networkx.is_connected(self.network):
            node1 = random.choice(list(self.network.nodes()))
            node2 = random.choice(list(self.network.nodes()))
            while (node1 == node2) or (node1.zone == node2.zone) or (self.network.has_edge(node1,node2)):
                node1 = random.choice(list(self.network.nodes()))
                node2 = random.choice(list(self.network.nodes()))
            # Avoid self-loops and duplicate edges
            self.network.add_edge(node1, node2)


    def generate_init_orders(self,zone,num_orders = None):
        if num_orders is None:
            #### Within zone orders
            micro_to_customer_orders = random.randint(1,HYPER_PARAMS['max_init_orders'])
            customer_to_micro_orders = random.randint(1,HYPER_PARAMS['max_init_orders'])
            trans_zone_orders = random.randint(1,HYPER_PARAMS['max_init_orders'])
        else:
            micro_to_customer_orders = num_orders['micro_to_customer_orders']
            customer_to_micro_orders = num_orders['customer_to_micro_orders']
            trans_zone_orders = num_orders['trans_zone_orders']
        ##Generate the orders
        microhub = self.get_microhub(zone)
        m_to_c = [Order(microhub,random.choice(microhub.get_customers()),zone) for _ in range(micro_to_customer_orders)] #Orders in microhub to a customer within a zone
        for orders in m_to_c:
            microhub.add_order(orders)
        c_to_m = [Order(random.choice(microhub.get_customers()),microhub,zone) for _ in range(customer_to_micro_orders)] #Order from a customer to a microhub in the same zone
        for orders in c_to_m:
            customer = orders.origin
            customer.add_order(orders)
        t_to_m = []
        for i in range(trans_zone_orders):
            random_zone = random.randint(0,self.num_zones - 1)
            if random.random() < 0.5: #Customer in the zone to another zone
                customer = random.choice(microhub.get_customers()) #Origin customer
                arrival_hub = self.get_microhub(random_zone)
                arrival_customer = random.choice(arrival_hub.get_customers())
                order = Order(customer,arrival_customer,random_zone)
                customer.add_order(order)
            else:
                arrival_hub = self.get_microhub(random_zone)
                arrival_customer = random.choice(arrival_hub.get_customers())
                order = Order(microhub,arrival_customer,random_zone)
                microhub.add_order(order)
                

    def crowdshipper_controller(self):
        microhubs = [self.get_microhub(zone) for zone in range(self.num_zones)] #getting the microhubs of the full network
        for microhub in microhubs:
            #Distributing orders to crowdshippers
            microhub.deploy_crowdshippers()
            #Updating positions of the crowdshippers
            for crowdshipper in microhub.crowdshippers_free:
                crowdshipper.update_position()
                if crowdshipper.is_at_destination():
                    node = crowdshipper.get_position()
                    #If the crowshipper is at the microhub --> Pick up order
                    if node == microhub and (not crowdshipper.has_order):
                            crowdshipper.pickup_order(microhub)
                    #"""elif node == microhub and crowdshipper.current_order is not None: #If the crowdshipper delivers from customer to microhub
                    #    crowdshipper.drop_order()"""
                    else:
                        if crowdshipper.current_order is not None:
                            crowdshipper.current_order.drop(self)
                            crowdshipper.drop_order()
                            self.display()
                            
    
    
    
    
    def get_microhub(self,zone):
        for node in self.H0:
            if node.zone == zone:
                return node
            


    def steps(self):
        self.depot.step()
        for truck in self.F:
            truck.step()
        
        self.crowdshipper_controller()
        self.step += 1
        self.info()
        self.update_network()
        self.summary_load(self.get_microhub(2),self.get_microhub(1))

    def info(self):
        microhubs = [self.get_microhub(zone) for zone in range(self.num_zones)]
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
        for microhub in microhubs:
            order_desc = microhub.concat_order_info()
            for key in dico.keys():
                dico[key] += (order_desc[key])
        new_df = pd.DataFrame.from_dict(dico)
        new_df.to_csv('info_step'+ str(self.step)+'.csv')
        return dico
    


    def truck_load_microhubs(self,info_file_name,origin_zone,dest_zone):
        df = pd.read_csv(info_file_name)
        df['origin zone'] = df['origin'].apply(lambda x: x[-1])
        df['position zone'] = df['current_pos'].apply(lambda x: x[-1])
        df['destination zone'] = df['destination'].apply(lambda x: x[-1])
        sub_df = df[(df['delivery mode'] == 'Truck') & (df['picked_up'] == False) & (df['origin zone'] ==origin_zone) & (df['destination zone'] == dest_zone)]
        return len(sub_df)
    

    def remove_node(self,node):
        self.network.remove_node(node)



    def update_network(self):#removes customers that received their order
        microhubs = [self.get_microhub(zone) for zone in range(self.num_zones)]
        for microhub in microhubs:
            orders = microhub.get_delivered_orders()
            for order in orders:#Remove the order and the customer from the simulation
                microhub.remove_order(order)
                if order.origin.type == 'Customer':
                    self.remove_node(order.origin)
                    order.origin = None
                if order.arrival_node.type =='Customer':
                    self.remove_node(order.arrival_node)
                    order.arrival_node = None



    def depot_microhub_distances(self):
        dico = {}
        for microhub in self.H:
            dico[f'Microhub {microhub.zone}'] = shortest_distance(self.network,microhub,self.depot)
        file_path = 'micro_to_depot_distances.json'
        with open(file_path, 'w') as file:
            json.dump(dico, file)

    
    def load_from_to(self,origin,destination):
        load = []
        #Microhubs
        for microhub in self.H:
            for order in microhub.orders:
                if order.origin.zone == origin.zone and (order.arrival_node.zone == destination.zone or order.position.zone == destination.zone):
                    load.append(order)
            #Crowdshippers
            for crowdshipper in microhub.crowdshippers_free:
                if crowdshipper.current_order:
                    if crowdshipper.current_order.origin.zone == origin.zone and (crowdshipper.current_order.arrival_node.zone == destination.zone or crowdshipper.current_order.position.zone == destination.zone):
                        load.append(order)
            for crowdshipper in microhub.crowdshipper_resources:
                if crowdshipper.current_order:
                    if crowdshipper.current_order.origin.zone == origin.zone and (crowdshipper.current_order.arrival_node.zone == destination.zone or crowdshipper.current_order.position.zone == destination.zone):
                        load.append(order)
        #trucks
        for truck in self.F:
            for order in truck.orders:
                if order.origin.zone == origin.zone and (order.arrival_node.zone == destination.zone or order.position.zone == destination.zone):
                    load.append(order)
        return load,len(load)
    

    def summary_load(self,origin,destination):
        dico_list = []
        load,load_length = self.load_from_to(origin,destination)
        for order in load:
            dico = {'ID':order.id,'Weight':order.weight}
            dico_list.append(dico)
        df = pd.DataFrame.from_records(dico_list)
        df.to_csv(f'order_load_{origin.zone}_{destination.zone}')
            



    def manage_trucks(self):
        depot = self.depot


