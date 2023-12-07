
HYPER_PARAMS = {
    'crowdshipper_capcity' : 5, #capacity of crowdshippers
    'resource_crowdshippers' : 10, #number of resource crowdshippers in a microhub
    'free_crowdshippers' : 10, #number of free crowdshippers in the zone
    'customers_per_zone' : 3, #nb of customers per zone
    'links_per_zone': 3, #Nodes in a zone different from microhubs and customers --> to improve routing
    'max_distance_crowdshipper': 200, 
    'truck_capacity':10, #capacity of trucks
    'num_trucks' : 10, #number of trucks in the network
    'max_orders_before_transfer':20, #max number of orders in microhub inventory before calling the truck transer
    'order_weight':1, #weight of orders, can be variable 
    'max_init_orders': 5, #Generate n in [0,max_init_orders] orders in the initial random order generation of the network
}
