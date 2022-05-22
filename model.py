import numpy as np
import pandas as pd



# 3 Different Models
# 1) No Battery
# 2) Battery
# 3) Battery With arbitrage

cluster_battery_types = {
    0: 'Lithium Ion',
    1: 'Open Lead Acid',
    2: 'Flow',
    3: 'Open Lead Acid',
    4: 'Lithium Ion',
    5: 'Nickel Cobalt'
}
# Per Kwh
battery_type_costs = {
    'Lithium Ion':      200,
    'Open Lead Acid':   120,
    'Nickel Cobalt':    325,
    'Flow':             400,
    'None':             0
}

class UTC:
    def __init__(self, _year, _month, _day, _hour, _minute):
        self.year = _year
        self.month = _month
        self.day = _day
        self.hour = _hour
        self.minute = _minute
    def create_utc_string(self):
        return f"{self.year}-{'{:02}'.format(self.month)}-{'{:02}'.format(self.day)} {'{:02}'.format(self.hour)}:{'{:02}'.format(self.minute)}"

states_cost = {
    'off_peak': 
        {
        'NT':   12.73,
        'NSW':  13.72, 
        'VIC':  14.14,
        'QLD':  13.38,
        'SA':   15.98,
        'WA':   13.44,
        'TAS':  11.45,
        'ACT': 13.72
        },
    'shoulder':
        {
        'NT':   20.21,
        'NSW':  21.78, 
        'VIC':  22.46,
        'QLD':  21.24,
        'SA':   25.37,
        'WA':   21.33,
        'TAS':  18.18,
        'ACT':  21.50,
        }, 
    'adj_peak':
        {
        'NT':   30.53,
        'NSW':  32.90, 
        'VIC':  33.92,
        'QLD':  32.08,
        'SA':   38.32,
        'WA':   32.22,
        'TAS':  27.46,
        'ACT':  30.00
        }
    }
def utc_cost(utc_timestamp, state):
    # IN c/Kwh
    # return cost of electricity for a given time
    
    timestamp = UTC(0,0,0, int(utc_timestamp[11:13]), int(utc_timestamp[14:16]))
    hour_min_sum = timestamp.hour + timestamp.minute/60

    if hour_min_sum >= 0 and hour_min_sum <= 7 or hour_min_sum >= 22:
        # 10pm - 7am
        return states_cost['off_peak'][state]
    elif hour_min_sum >= 7 and hour_min_sum <= 15:
        # 7am - 3pm
        return states_cost['shoulder'][state]
    elif hour_min_sum >= 15 and hour_min_sum <= 20:
        # 3pm - 8pm
        return states_cost['adj_peak'][state]
    elif hour_min_sum >= 20 and hour_min_sum <= 22:
        # 8pm - 10pm
        return states_cost['shoulder'][state]
    else:
        print('Error: Exiting Program')
        exit()

def utc_fit(state):
    # will return feed in tarif for given time.
    states_cost = {
    'NT':   25.95,
    'NSW':  11.00, 
    'VIC':  12.00,
    'QLD':  9.37,
    'SA':   12.75,
    'WA':   7.1,
    'TAS':  9.35,
    'ACT':  12
    }
    return states_cost[state]

def utc_arbitrage_buy(utc_timestamp):
    timestamp = UTC(0,0,0, int(utc_timestamp[11:13]), int(utc_timestamp[14:16]))
    hour_min_sum = timestamp.hour + timestamp.minute/60
    if hour_min_sum >= 0 and hour_min_sum <= 7 or hour_min_sum >= 22:
        # 10pm - 7am
        return 1
    else:
        return 0

def utc_arbitrage_sell(utc_timestamp):
    timestamp = UTC(0,0,0, int(utc_timestamp[11:13]), int(utc_timestamp[14:16]))
    hour_min_sum = timestamp.hour + timestamp.minute/60
    if hour_min_sum >= 20 and hour_min_sum <= 22:
        return 1
    else:
        return 0


def model_battery():
    site_df = pd.read_csv("C:/Users/Rohan/Desktop/ENG2112/TESTING/training_sites_clustered.csv")
    battery_sizes = [1, 0] 
    # consider depth of discharge?
    battery_sites_size = pd.DataFrame(np.zeros((site_df.shape[0], len(battery_sizes))))
    # Organise by cluster...
    for index, row in site_df.iterrows():
        current_site_id = row["site_id"]
        site_filename = "C:/Users/Rohan/Desktop/ENG2112/TESTING/{current_site}.csv".format(current_site = current_site_id)
        data = pd.read_csv(site_filename)
        for battery_size in battery_sizes:
            battery = 0     # Battery initally starts at zero capacity
            cost_sum = 0    # Reset cost sum after every battery size
            for index2, row2 in data.iterrows():
                # Battery will always attempt to recharge power
                power_sum = ((row2[1] - row2[2])/1000)*(5/60)  # Load - PV IN KWh
                if power_sum < 0:
                    # CHARGE BATTERY
                    battery += abs(power_sum)
                    if battery > battery_size:
                        # Feed back difference into grid. (Feed in tarrifs not dependant on time)
                        cost_sum -= abs(utc_fit(row[2])*(battery - battery_size))
                        battery = battery_size # Set battery to maximum size
                else:
                    # DISCHARGE BATTERY
                    if  battery > power_sum:
                        # Battery will discharge by power_sum amount
                        battery -= power_sum
                    else:
                        # Battery had small or zero amount left (but less than power_sum)
                        # and power must be bought off the grid
                        cost_sum += abs(utc_cost(row2[0], row[2])*(power_sum - battery))
                        battery = 0
            cost_sum -=  utc_fit('VIC')*(battery)
            battery_sites_size.loc[index, battery_sizes.index(battery_size)] = cost_sum
        print(battery_sites_size)
    battery_sites_size.to_csv('battery_testdata.csv', index=False)
    # Positive cost sum = bad
    # Negative cost sum = good
    return

def model_battery_arb():
    battery_charge_rate = 0.07 # Charge battery at 840 W/h
    battery_discharge_rate = 0.07
    site_df = pd.read_csv("C:/Users/Rohan/Desktop/ENG2112/TESTING/training_sites_clustered.csv")
    battery_sizes = [0,3,5,7,10] 
    # consider depth of discharge?
    battery_sites_size = pd.DataFrame(np.zeros((site_df.shape[0], len(battery_sizes))))
    battery_sites_size.columns = battery_sizes
    # Organise by cluster...
    for index, row in site_df.iterrows():
        current_site_id = row["site_id"]
        site_filename = "C:/Users/Rohan/Desktop/ENG2112/TESTING/{current_site}.csv".format(current_site = current_site_id)
        data = pd.read_csv(site_filename)
        for battery_size in battery_sizes:
            battery = 0     # Battery initally starts at zero capacity
            cost_sum = 0    # Reset cost sum after every battery size
            for index2, row2 in data.iterrows():
                utc_timestamp = row2[0]
                site_state = row[2]
                # Battery will always attempt to recharge power
                power_sum = ((row2[1] - row2[2])/1000)*(5/60)  # Load - PV IN KWh
                if power_sum < 0:
                    # CHARGE BATTERY
                    battery += abs(power_sum)
                    if battery > battery_size:
                        # Feed back difference into grid. (Feed in tarrifs not dependant on time)
                        cost_sum -= abs(utc_fit(site_state)*(battery - battery_size))
                        battery = battery_size # Set battery to maximum size
                else:
                    # DISCHARGE BATTERY
                    if  battery > power_sum:
                        # Battery will discharge by power_sum amount
                        battery -= power_sum
                    else:
                        # Battery had small or zero amount left (but less than power_sum)
                        # and power must be bought off the grid
                        cost_sum += abs(utc_cost(utc_timestamp, site_state)*(power_sum - battery))
                        battery = 0
                if utc_arbitrage_buy(utc_timestamp ) == 1:
                    # Buy off the grid
                    if battery + battery_charge_rate < battery_size:
                        battery +=  battery_charge_rate
                        cost_sum += abs(utc_cost(utc_timestamp, site_state)*battery_charge_rate)
                elif utc_arbitrage_sell(utc_timestamp) == 1:
                    # Sell to grid
                    if battery - battery_discharge_rate > 0:
                        battery -= battery_discharge_rate
                        cost_sum -= abs(utc_fit(site_state)*battery_discharge_rate)
            battery_sites_size.loc[index, battery_size] = cost_sum
        print(current_site_id)
    battery_sites_size.to_csv('battery_testdata.csv', index=False)
    # Positive cost sum = bad
    # Negative cost sum = good
    return


def best_battery_size():
    # Determine best battery size for each cluster
    site_df = pd.read_csv("C:/Users/Rohan/Desktop/ENG2112/TESTING/training_sites_clustered.csv")
    battery_sites_size = pd.read_csv("battery_testdata.csv")
    # Cluster amount
    clusters = [0,1,2,3,4,5]
    cluster_av = np.zeros((len(clusters), int(battery_sites_size.columns.shape[0])))
    for index, row in battery_sites_size.iterrows():
        battery_min = int(row.idxmin())
        # cluster as rows, battery size as columns
        cluster_av[int(site_df.loc[index, 'cluster']), np.where(battery_sites_size.columns.to_numpy(dtype = int) == battery_min)[0].item()] += 1
    battery_cluster_size = pd.DataFrame(cluster_av)
    battery_cluster_size.columns = battery_sites_size.columns
    battery_cluster_size.to_csv('battery_cluster_vs_size.csv')
    return

def model_battery_arb_test():
    battery_charge_rate = 0.07 # Charge battery at 840 W/h
    battery_discharge_rate = 0.07
    site_df = pd.read_csv("C:/Users/Rohan/Desktop/ENG2112/TESTING/test_sites_clustered.csv")
    # consider depth of discharge?
    battery_size = 3
    battery_sites_size = pd.DataFrame(np.zeros((site_df.shape[0], 1)))
    # Organise by cluster...
    for index, row in site_df.iterrows():
        current_site_id = row["site_id"]
        site_filename = "C:/Users/Rohan/Desktop/ENG2112/TESTING/{current_site}.csv".format(current_site = current_site_id)
        data = pd.read_csv(site_filename)

        battery_array = np.zeros((data.shape[0],1))
        battery_array_count = 0

        battery = 0     # Battery initally starts at zero capacity
        cost_sum = 0    # Reset cost sum after every battery size
        for index2, row2 in data.iterrows():
            utc_timestamp = row2[0]
            site_state = row[2]
            # Battery will always attempt to recharge power
            power_sum = ((row2[1] - row2[2])/1000)*(5/60)  # Load - PV IN KWh
            if power_sum < 0:
                # CHARGE BATTERY
                battery += abs(power_sum)
                if battery > battery_size:
                    # Feed back difference into grid. (Feed in tarrifs not dependant on time)
                    cost_sum -= abs(utc_fit(site_state)*(battery - battery_size))
                    battery = battery_size # Set battery to maximum size
            else:
                # DISCHARGE BATTERY
                if  battery > power_sum:
                    # Battery will discharge by power_sum amount
                    battery -= power_sum
                else:
                    # Battery had small or zero amount left (but less than power_sum)
                    # and power must be bought off the grid
                    cost_sum += abs(utc_cost(utc_timestamp, site_state)*(power_sum - battery))
                    battery = 0
            if utc_arbitrage_buy(utc_timestamp ) == 1:
                # Buy off the grid
                if battery + battery_charge_rate < battery_size:
                    battery +=  battery_charge_rate
                    cost_sum += abs(utc_cost(utc_timestamp, site_state)*battery_charge_rate)
            elif utc_arbitrage_sell(utc_timestamp) == 1:
                # Sell to grid
                if battery - battery_discharge_rate > 0:
                    battery -= battery_discharge_rate
                    cost_sum -= abs(utc_fit(site_state)*battery_discharge_rate)
            # add cost sum to array
            battery_array[battery_array_count] = battery
            battery_array_count += 1
        battery_sites_size.loc[index, 1] = cost_sum
        data['battery'] = battery_array
        data.to_csv("{current_site}.csv".format(current_site = current_site_id), index = False)   
        print(current_site_id)
    battery_sites_size.to_csv('battery_testdata.csv', index=False)
    # Positive cost sum = bad
    # Negative cost sum = good
    return
model_battery_arb_test()