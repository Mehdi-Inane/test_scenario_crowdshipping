from network import City
city = City(size = 3,num_zones = 3)
city.display()
city.reset()
city.display()
steps = 6
for i in range(30):
    city.steps()
print(city.truck_load_microhubs(f'info_step6.csv',0,3))