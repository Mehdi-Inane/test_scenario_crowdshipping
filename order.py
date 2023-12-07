import uuid,networkx
from config import HYPER_PARAMS
class Order:
    def __init__(self, origin,destination,zone,weight=HYPER_PARAMS['order_weight']):
        self.id = uuid.uuid1()
        self.origin = origin #expenditure node
        self.position = origin #current position
        self.arrival_node = destination #arrival node
        self.zone = zone #current zone
        self.assigned = False
        self.weight = weight
        self.shipper = None #truck or crowdshipper supposed to deliver it
        if self.origin.type == 'Depot':
            self.origin.add_order(self)
    
    def get_id(self):
        return self.id

    def get_origin(self):
        return self.origin

    def update_position(self,new_pos):
        self.position = new_pos

    def drop(self,network):
        self.shipper = None
        self.assigned = False
        if self.position.type == 'Microhub' and self.zone != self.position.zone:
            self.arrival_node = network.get_microhub(self.zone)
            self.arrival_node.add_order(self)
            return
            



    def get_delivery_mode(self):
        if self.position.zone == self.arrival_node.zone:
            return 'Crowdshipper'
        else:
            return 'Truck'
    def delivered(self):
        if self.position == self.arrival_node and self.zone == self.arrival_node.zone:
            return True
        return False
    
    def __eq__(self,order_1):
        return self.id == order_1.id
    
    def __hash__(self):
        return hash(self.id)
    
    def within_zone(self,zone):
        if self.zone == zone:
            return True
        return False
    
    def describe(self):
        st = 'Order id: ' + str(self.id) + ' Origin: ' + self.origin.type + ' ' + str(self.origin.zone) + ' Destination: ' + self.arrival_node.type + ' ' + str(self.zone)
        return st
    
    def arrival_time(self):
        if not self.assigned or not self.shipper:
            return None
        else:
            return self.shipper.time_to_next_stop(self.position) + len(networkx.shortest_path(self.position.G,self.position,self.arrival_node)) #Time for the crowdshipper to reach the order location + deivery time
        
    def info(self):
        dico = {}
        dico['id'] = self.id
        dico['Zone'] = self.position.zone
        dico['weight'] = self.weight
        dico['origin'] = self.origin.type + ' ' +  str(self.origin.zone) if self.origin.type == 'Microhub' else self.origin.type + ' id: ' + str(self.origin.id) + 'zone : ' + str(self.origin.zone)
        dico['destination'] = self.arrival_node.type + ' ' +  str(self.arrival_node.zone) if self.arrival_node.type == 'Microhub' else self.arrival_node.type + ' id: ' + str(self.arrival_node.id) + 'zone : ' + str(self.arrival_node.zone)
        dico['current_pos'] = self.position.type + ' ' +  str(self.position.zone) if self.position.type == 'Microhub' else self.position.type + ' id: ' + str(self.position.id) + 'zone : ' + str(self.position.zone)
        dico['arrival_time'] = self.arrival_time()
        dico['assigned'] = self.assigned
        dico['picked_up'] = (self.shipper is not None)
        dico['delivered'] = self.delivered()
        dico['delivery mode'] = self.get_delivery_mode()
        return dico
    