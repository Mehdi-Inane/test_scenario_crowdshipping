import random
import uuid
import math



def cartesian_distance(x_1,y_1,x_2,y_2):
    return math.sqrt((x_1 - x_2)**2 + (y_1 - y_2)**2)


def generate_origin_destination(x_1,y_1,x_2,y_2):
    origin = (random.randint(x_1,x_2),random.randint(y_1,y_2))
    destination = (random.randint(x_1,x_2),random.randint(y_1,y_2))
    return [origin,destination]



class Zone:
    def __init__(self,nb,x_min,x_max,y_min,y_max,crowdshippers_free = 30,crowdshippers_resources = 20):
        self.nb = nb
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.microhub = Microhub(self,resource_crowdshippers=crowdshippers_resources,free_crowdshippers=crowdshippers_free)
    
    def get_coordinates(self):
        return (self.x_min,self.y_min,self.x_max,self.y_max)

    def get_nb(self):
        return self.nb

class Microhub:
    def __init__(self, zone,resource_crowdshippers,free_crowdshippers):
        self.zone_nb = zone.get_nb
        self.zone_coord = zone.get_coordinates()
        coord = zone.get_coordinates()
        self.x = (coord[0] + coord[2]) / 2
        self.y = (coord[1] + coord[3]) / 2
        self.orders = []
        self.truck_orders = []
        self.crowdshipper_orders = []
        self.crowdshippers_free = [Crowdshipper(self.zone_nb, generate_origin_destination(*coord),200,'free') for _ in range(free_crowdshippers)]
        self.crowdshipper_resources = [Crowdshipper(self.zone_nb, [(self.x,self.y),(self.x,self.y)],200,'resource') for _ in range(resource_crowdshippers)]
        self.truck_on_the_way = False
    
    def get_coordinates(self):
        return (self.x,self.y)
    
            
    def add_order(self, order):
        self.orders.append(order)
        if order.within_zone(self.zone_coord):
            self.crowdshipper_orders.append(order)
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
                order_pos = (order.x,order.y)
                #We will pick the crowdshipper with the nearest destination to the delivery
                min_distance = 100000
                temp = None
                for crowdshipper in self.crowdshippers_free:
                    if crowdshipper.current_order is None:
                        distance = cartesian_distance(order_pos[0],order_pos[1],crowdshipper.x,crowdshipper.y)
                        if distance < min_distance:
                            min_distance = distance
                            temp = crowdshipper
                # With probability 0.5 we deliver
                p = random.random()
                if p < 0.5:
                    order.assigned = True
                    temp.current_order = order
                    temp.add_stop(order.x,order.y)
                    temp.add_stop(self.x,self.y)
        

        #Deliver the remaining orders with 0.3 probability
        for order in self.crowdshipper_resources:
            if not order.assigned:
                p = random.random()
                if p > 0.3:
                    for crowdshipper in self.crowdshipper_resources:
                        if crowdshipper.current_order is None:
                            order.assigned = True
                            crowdshipper.current_order = order  
                            crowdshipper.add_stop(order.x,order.y)  
                            break        


    def get_transfer_capacity(self):
        return len(self.truck_orders)
    
        
class Order:
    def __init__(self, x, y): #x,y are delivery coordinates
        self.id = uuid.uuid1()
        self.x = x
        self.y = y
        self.assigned = False
    
    def get_id(self):
        return self.id

    def get_coordinates(self):
        return (self.x,self.y)


    def __eq__(self,order_1):
        return self.id == order_1.id
    
    def within_zone(self,zone_coord):
        if ((self.x >= zone_coord[0]) and (self.x >= zone_coord[2]) and (self.y >= zone_coord[1]) and (self.y >= zone_coord[3])):
            return True
        
class Truck:
    def __init__(self, x, y):
        self.id = uuid.uuid1()
        self.x = x
        self.y = y
        self.orders = []
        self.destination = None
        
    def load_orders(self, microhub):
        self.orders = microhub.truck_orders[:]
        for order in self.orders:
            microhub.remove_order(order)


    def unload_orders(self, microhub):
        for order in self.orders:
            microhub.add_order(order)
        self.orders = []
    
    def is_transferring(self):
        return (len(self.orders) > 0)
    
    def is_going_to_microhub(self):
        return (len(self.orders) == 0 and self.destination is not None)


    def is_waiting(self):
        return self.destination is None

    def move_to(self, x, y):
        self.x = x
        self.y = y
        self.destination = None
        
    def set_destination(self, x, y):
        self.destination = (x, y)
        
    def is_at_destination(self):
        return self.destination is None or (self.x, self.y) == self.destination
        
    def update_position(self):
        if self.destination and not self.is_at_destination():
            dest_x, dest_y = self.destination
            tmp_x = dest_x - self.x
            tmp_y = dest_y - self.y
            if tmp_x < 1 or tmp_y < 1:
                if tmp_x < 1:
                    self.x += tmp_x
                if tmp_y < 1:
                    self.y += tmp_y
                return
            if dest_x > self.x:
                self.x += 1
            if dest_x < self.x:
                self.x -= 1
            if dest_y > self.y:
                self.y += 1
            if dest_y < self.y:
                self.y -= 1



    def plan_route(self):
        ### Here we solve with VRP optimization
        pass
        
class Crowdshipper:
    def __init__(self, zone, origin_dest_matrix,max_d,type):
        self.zone = zone
        self.type = type
        self.origin_dest_matrix = origin_dest_matrix
        self.current_order = None
        self.max_threshold = max_d
        self.x,self.y = self.origin_dest_matrix[0][0],self.origin_dest_matrix[0][1]
        self.stops = [origin_dest_matrix[1]]
    
    def add_stop(self,x,y):
        self.stops.insert(0,(x,y))

    def get_next_destination(self):
        if len(self.stops) > 0:
            return self.stops[0]
        return None
    
    def is_at_destination(self):
        dest = self.get_next_destination()
        if dest is not None:
            return (self.x == dest[0]) and (self.y == dest[1])
        return False
    
    def update_position(self):
        if self.get_next_destination() is not None and not self.is_at_destination():
            dest_x, dest_y = self.get_next_destination()
            tmp_x = dest_x - self.x
            tmp_y = dest_y - self.y
            if tmp_x < 1 or tmp_y < 1:
                if tmp_x < 1:
                    self.x += tmp_x
                if tmp_y < 1:
                    self.y += tmp_y
                return
            if dest_x > self.x:
                self.x += 1
            if dest_x < self.x:
                self.x -= 1
            if dest_y > self.y:
                self.y += 1
            if dest_y < self.y:
                self.y -= 1
    
    def get_coordinates(self):
        return self.x,self.y
    
    def pickup_order(self,microhub):
        microhub.orders.remove(self.current_order)
        microhub.crowdshipper_orders.remove(self.current_order)
        self.stops.pop[0]
    
    def drop_order(self):
        self.current_order = None
        self.stops.pop[0]

class City:
    def __init__(self, size, num_zones,max_orders_before_transfer = 20):
        self.num_zones = num_zones
        self.size = size
        self.zones = []
        step_size = math.sqrt(self.size / self.num_zones)
        self.max_orders_transfer = max_orders_before_transfer
        #Cutting the region into a grid
        for zone in range(self.num_zones):
            x_min = zone*step_size
            x_max = (zone+1)*step_size
            for j in range(self.num_zones):
                y_min = j*step_size
                y_max = (j+1)*step_size
                self.zones.append(Zone(zone,x_min,x_max,y_min,y_max))
        self.microhubs = []
        #Adding the microhubs in the center of each zone
        self.microhubs = [zone.microhub for zone in self.zones]
        #Trucks initially start in the microhub area
        self.trucks = [Truck(microhub.x, microhub.y) for microhub in self.microhubs]        
    def get_truck(self,t_id):
        for truck in self.trucks:
            if truck.id == t_id:
                return truck
        return None
    

    def get_microhub(self,t_id):
        for microhub in self.microhubs:
            if microhub.id == t_id:
                return microhub
        return None
    
    def get_zone(self,nb):
        for zone in self.zones:
            if zone.nb == nb:
                return zone
        return None

    def generate_origin_dest_matrix(self):
        matrix = [[random.choice(range(math.sqrt(self.num_zones))) for _ in range(self.size)] for _ in range(math.sqrt(self.size))]
        return matrix
        
    def generate_orders(self):
        for microhub in self.microhubs:
            nb_orders = random.randint(0,10)
            for order in range(nb_orders):
                prob = random.random()
                if prob < 0.4:
                    x = random.randint(0, math.sqrt(self.size))	
                    y = random.randint(0, math.sqrt(self.size))	
                    microhub.add_order(Order(x, y))
    
    def get_nearest_free_truck(self,microhub):
        truck_distances = {truck.id : 0 for truck in self.trucks if truck.destination is None }
        for truck in self.trucks:
            truck_distances[truck.id] = cartesian_distance(microhub.x,microhub.y,truck.x,truck.y)
        return min(truck_distances, key=truck_distances.get)
    
    
    
    def truck_controller(self):
        #Controlling the free trucks : checking if any truck is free to make a transfer
        microhubs_to_free = []
        for microhub in self.microhubs:
            if (microhub.get_transfer_capacity() > self.max_orders_transfer) and not microhub.truck_on_the_way:
                microhubs_to_free.append(microhub)
        for microhub in microhubs_to_free:
            truck_id = self.get_nearest_free_truck(microhub)
            truck = self.get_truck(truck_id)
            if truck:
                truck.set_destination(microhub.x,microhub.y)
        for truck in self.trucks:
            if not truck.is_waiting():
                truck.update_position()
                if truck.is_at_destination:
                    (x,y) = (truck.x,truck.y)
                    for microhub in self.microhubs:
                        if microhub.get_coordinates() == (x,y):
                            if truck.is_transferring:
                                truck.unload_orders(microhub)
                                break
                            else:
                                truck.load_orders(microhub)
                                microhub.truck_on_the_way = False
            

                    truck.destination = None
    
    
    def crowdshipper_controller(self):
        for microhub in self.microhubs:
            m_x,m_y = microhub.get_coordinates()
            #Distributing orders to crowdshippers
            microhub.deploy_crowdshippers()
            #Updating positions of the crowdshippers
            for crowdshipper in microhub.crowdshippers_free:
                crowdshipper.update_position()
                if crowdshipper.is_at_destination():
                    c_x,c_y = crowdshipper.get_coordinates()
                    #If the crowshipper is at the microhub --> Pick up order
                    if (c_x == m_x) and (c_y == m_y):
                        crowdshipper.pickup_order(microhub)
                    else:
                        if crowdshipper.current_order is not None:
                            crowdshipper.drop_order
                        else:
                            microhub.crowdshippers_free.remove(crowdshipper)



    

            
    def simulate(self, num_steps):
        for step in range(num_steps):
            print(f"Step {step + 1}")
            self.generate_orders()
            self.truck_controller()
            ##Control crowdshippers
            self.crowdshipper_controller()
            for truck in self.trucks:
                print(f"Truck at ({truck.x}, {truck.y}) has {len(truck.orders)} orders")

    def show(self):
        for zone in self.zones:
            print("Zone coordinates :",zone.get_coordinates())
            print("Corresponding microhub coordinates: ",zone.microhub.get_coordinates())
                



city = City(size=9, num_zones=9)
city.simulate(num_steps=10)
