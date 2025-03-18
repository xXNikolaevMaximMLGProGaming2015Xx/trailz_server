from math import *

radius = 6378160

def sqr(num):
    return num*num

def process_trail_validation(trail_json,rerun_json):
    go_off_count = 0
    max_delta = float(trail_json["MinDistance"])
    trail_data = trail_json["GPSData"]
    rerun_data = rerun_json["GPSData"]
    trail_cord_list = [cord[1] for _,cord in sorted(zip(list(trail_data.keys()),list(trail_data.items())))]
    rerun_cord_list = [cord[1] for _,cord in sorted(zip(list(rerun_data.keys()),list(rerun_data.items())))]
    current = 0
    max_go_offs = int(trail_json["distance"] * 3)
    
    
    min_start_distance = -1
    min_fin_distance = -1
    for point in rerun_cord_list:
        
        strat_distance = check_points_distance(*degree_to_meter(trail_cord_list[0]["lat"],trail_cord_list[0]["lon"],point["lat"],point["lon"]))
        fin_distance = check_points_distance(*degree_to_meter(trail_cord_list[-1]["lat"],trail_cord_list[-1]["lon"],point["lat"],point["lon"]))        
        if strat_distance < min_start_distance or min_start_distance == -1:
            min_start_distance = strat_distance
            strat_point = point
        if fin_distance < min_fin_distance or min_fin_distance == -1:
            min_fin_distance = min_fin_distance
            fin_point = point
        

    for point in rerun_cord_list[rerun_cord_list.index(strat_point): rerun_cord_list.index(fin_point)]:
        if check_distance(*degree_to_meter(trail_cord_list[current]["lat"],trail_cord_list[current]["lon"],trail_cord_list[current + 1]["lat"],trail_cord_list[current + 1]["lon"],point["lat"],point["lon"])) <= max_delta + point["accuracy"] + ((trail_cord_list[current]["accuracy"] + trail_cord_list[current + 1]["accuracy"])/2):
            if current < len(trail_cord_list) - 2:
                current += 1
            if check_distance(*degree_to_meter(trail_cord_list[current]["lat"],trail_cord_list[current]["lon"],trail_cord_list[current + 1]["lat"],trail_cord_list[current + 1]["lon"],point["lat"],point["lon"])) <= max_delta + point["accuracy"] + ((trail_cord_list[current]["accuracy"] + trail_cord_list[current + 1]["accuracy"])/2):
                pass
            else:
                if current < len(trail_cord_list) - 2:
                    current -= 1
                go_off_count += 1
                
    run_time = int(list(rerun_data.keys())[list(rerun_data.values()).index(fin_point)]) - int(list(rerun_data.keys())[list(rerun_data.values()).index(strat_point)])
    if max_go_offs >= go_off_count:
        return True, run_time
    else:
        return False, run_time
        
        
def degree_to_meter(*args):
    global radius
    return [2*pi*radius*(arg/360) for arg in args]
    
  
def check_points_distance(x1,x2,y1,y2):
    return sqrt(sqr(x1-x2)+sqr(y1-y2))

def check_distance(x1,y1,x2,y2,x3,y3):
    x4 = y3 + x3*sin(atan(((y2-y1)/(x2-x1))))
    y4 = ((y2-y1)/(x2-x1))*(x4 - x1) + y1
    if (sqrt(sqr(x4-x1) + sqr(y4-y1)) + sqrt(sqr(x4-x2) + sqr(y4-y2))) <= sqrt(sqr(x2-x1)+ sqr(y2-y1)):
        return sqrt(sqr(x4-x3) + sqr(y4-y3))
    else:
        return min(sqrt(sqr(x3-x1)+ sqr(y3-y1)),sqrt(sqr(x3-x2)+ sqr(y3-y2)))
    
    


