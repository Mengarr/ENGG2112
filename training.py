import site
from matplotlib import pyplot as plt
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np
import csv

class UTC:
    def __init__(self, _year, _month, _day, _hour, _minute):
        self.year = _year
        self.month = _month
        self.day = _day
        self.hour = _hour
        self.minute = _minute
    def create_utc_string(self):
        return f"{self.year}-{'{:02}'.format(self.month)}-{'{:02}'.format(self.day)} {'{:02}'.format(self.hour)}:{'{:02}'.format(self.minute)}"


def test():
    # Produce filenames to open
    filenames = []
    for i in range(1,10):
        filenames.append("C:/Users/Rohan/Desktop/ENG2112/Data_Modification/to_share_2019-0{i}.csv".format(i = i))
    for i in range(10,13):
        filenames.append("C:/Users/Rohan/Desktop/ENG2112/Data_Modification/to_share_2019-{i}.csv".format(i = i))
    
    for i in range(len(filenames)): 
        data1 = pd.read_csv(filenames[i])
        print('Data', i, 'Loaded')
        csvs_created = []
        current_site = data1['site_id'][0]
        aux_array = []
        aux_df = pd.DataFrame()
        #aux_df.to_csv(site_filename, index=False)
        for index, row in data1.iterrows():
            if current_site != row[1]:
                # Write CSV FILE
                site_filename = "{current_site}.csv".format(current_site = current_site)      
                # Check if csv allready exists
                if current_site in csvs_created or i >= 1:
                    aux_df.to_csv(site_filename, mode='a', header=False, index=False)
                else:
                    aux_df.columns = ["time", "load", "pv"]
                    csvs_created.append(current_site)   # Add site to allready created csv's list
                    aux_df.to_csv(site_filename, index=False)      
                # Reset auxiliary dataframe
                aux_df = pd.DataFrame() 
                # Update site 
                current_site = row[1]
            if index % 2 == 0:
                # Power load data
                aux_array.append(row[3])
            else:
                aux_array.insert(0, row[0][:16])
                aux_array.append(row[3])
                aux_df = pd.concat([aux_df, pd.DataFrame([aux_array])], axis = 0)
                aux_array = []
        # Update last site that didnt compare to next bcus there was no nxt site in file...
        site_filename = "{current_site}.csv".format(current_site = current_site)
        # Write CSV FILE
        aux_df.to_csv(site_filename, mode='a', header=False, index=False)
    return

def modify_timezones():
    """
    Modifys timezones of all site ids in directory
    ONLY RUN ONCE!
    """
    utc_modifications = {'Australia/Darwin': '+09:30','Australia/Sydney':'+10:00', 'Australia/Melbourne':'+10:00','Australia/Brisbane':'+10:00','Australia/Adelaide':'+09:30','Australia/Perth':'+08:00','Australia/Hobart':'+10:00'}
    site_details = pd.read_csv("C:/Users/Rohan/Desktop/ENG2112/site_details_USYD_202010.csv")
    for index, row in site_details.iterrows():
        current_site_id = row[0]   # Site-ID
        site_filename = "{current_site}.csv".format(current_site = current_site_id)
        data = pd.read_csv(site_filename)
        utc_modification = utc_modifications[row[1]]  # row[1] = timezone_id
        for index2, row2 in data.iterrows():
            # Modify utc_times, row2[0] = utc_timestamp
            data.iat[index2, 0] = add_time(row2[0], utc_modification)
        # Write file back again
        data.to_csv(site_filename, index=False) 
        print(current_site_id)     
    return

def add_time(utc_timestamp, utc_modification):
    """
    Basic function to add a time to a utc_timestamp
    Under assumptions that utc_modification is just hour and minutes
    Only consideres non leap years
    """
    timestamp = UTC(int(utc_timestamp[0:4]), int(utc_timestamp[5:7]),  int(utc_timestamp[8:10]), int(utc_timestamp[11:13]), int(utc_timestamp[14:16]))
    modify = UTC(0, 0, 0, int(utc_modification[1:3]), int(int(utc_modification[4:6]))) 
    months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]   # Amount of days in each month (non leap year)
    month_carry = 0
    day_carry = 0
    hour_carry = 0
    if(timestamp.minute + modify.minute >= 60):   # minutes go up to 59
        hour_carry = 1
        timestamp.minute = abs(60 - timestamp.minute - modify.minute)
    else:
        timestamp.minute += modify.minute
    if(timestamp.hour + modify.hour + hour_carry >= 24):
        day_carry = 1
        timestamp.hour = abs(24 - timestamp.hour - modify.hour - hour_carry)
    else:
        timestamp.hour = timestamp.hour + modify.hour + hour_carry
    # Use timestamp month to determine if the day should be in a new month
    if(timestamp.day + day_carry > months[timestamp.month-1]):
        month_carry = 1
        timestamp.day = 1  # Can only be 1 carry in this example
    else:
        timestamp.day += day_carry
    if(timestamp.month + month_carry > 12):
        timestamp.month = 1
        timestamp.year += 1  # ADD one to the year
    else: 
        timestamp.month += month_carry

    return timestamp.create_utc_string() 

def create_means():
    # Creates a csv file with:
    # site_id | cluster
    site_means = pd.DataFrame()
    column_names = []
    site_df = pd.read_csv("C:/Users/Rohan/Desktop/ENG2112/site_details_USYD_202010.csv")
    for index, row in site_df.iterrows():
         if (index + 1) % 5 != 0:
            current_site_id = row["site_id"]
            column_names.append(current_site_id)
            # Create filename for site
            site_filename = "{current_site}.csv".format(current_site = current_site_id)
            data = pd.read_csv(site_filename)
            mean_df = pd.DataFrame(np.zeros(288))
            aux_df = pd.DataFrame()
            count1 = 0
            count2 = 0
            # Go through data file for individual site
            for index2, row2, in data.iterrows():
                if row2['time'][11:] == '00:00':
                    count1 += 1
                if count1 == 1:
                    aux_df = pd.concat([aux_df, pd.DataFrame([row2['load']])])
                elif count1 ==  2:
                    aux_df = aux_df.reset_index(drop=True)
                    if aux_df.size == 288:
                        mean_df = mean_df.add(aux_df)
                        count2 += 1
                    aux_df = pd.DataFrame()
                    count1 = 1
                    aux_df = pd.concat([aux_df, pd.DataFrame([row2['load']])])
            site_means = pd.concat([site_means, mean_df/count2], axis = 1)
            print(current_site_id)
    site_means.columns = column_names
    site_means.to_csv('24hr_load_means.csv', index=False)
    return

def normalise_means():
    means = pd.read_csv('24hr_load_means.csv')
    column_num = means.shape[1]
    for i in range(column_num):
        means.iloc[:,i] = means.iloc[:,i]/np.sum(means.iloc[:,i].to_numpy())
    means.to_csv('24hr_load_means_normalised.csv',  index=False)
    return 

def elbow_plot(means):
    #https://www.codecademy.com/learn/machine-learning/modules/dspath-clustering/cheatsheet
    X = means.to_numpy()
    distorsions = []
    k_range = range(2, 20)
    for k in k_range:
        kmeans = KMeans(n_clusters=k)
        kmeans.fit(X)
        distorsions.append(kmeans.inertia_)
    fig = plt.figure(figsize=(15, 5))
    plt.plot(k_range, distorsions)
    plt.title('Optimal Number of Clusters')
    plt.ylabel('Distorsion Score')
    plt.xlabel('Number of Clusters (k)')
    plt.grid(True)
    plt.show()
    return 
    
def create_clusters():
    means = pd.read_csv('24hr_load_means.csv')
    #elbow_plot(means)
    normalised_means = pd.read_csv('24hr_load_means_normalised.csv')
    OPTIMUM_K = 6
    kmeans = KMeans(n_clusters=OPTIMUM_K, random_state=0, n_init=100, max_iter=300).fit(normalised_means.T.to_numpy())
    site_df = pd.read_csv("C:/Users/Rohan/Desktop/ENG2112/site_details_USYD_202010.csv")
    cluster_array = kmeans.labels_
    test_array = pd.DataFrame(np.zeros((means.shape[1], 5)))
    test_array.columns = ['site_id','timezone_id','state','postcode', 'cluster']
    count = 0
    for index, row in site_df.iterrows():
        if (index + 1) % 5 != 0:
            test_array.loc[count, :] = pd.concat([row, pd.DataFrame([cluster_array[count]])]).to_numpy(dtype=str).flatten()
            count += 1
    test_array.to_csv('test_sites_clustered.csv', index=False)
    """
    columns = range(0,OPTIMUM_K)
    for i in columns:
        print(means[i])

    
    time_array = np.linspace(0,24,288)
    for i in columns:
        if i != 3:
            fig, axs = plt.subplots(2, 3)
            axs[0,0].plot(time_array, means[i].iloc[:, 0].to_numpy())
            axs[0,1].plot(time_array, means[i].iloc[:, 1].to_numpy())
            axs[1,0].plot(time_array, means[i].iloc[:, 2].to_numpy())
            axs[1,1].plot(time_array, means[i].iloc[:, 3].to_numpy())
            axs[1,2].plot(time_array, means[i].iloc[:, 4].to_numpy())
            axs[0,2].plot(time_array, means[i].iloc[:, 5].to_numpy())

            for ax in axs.flat:
                ax.set(xlabel='Time (hr)', ylabel='Load Energy (W)')

            # Hide x labels and tick labels for top plots and y ticks for right plots.
            for ax in axs.flat:
                ax.label_outer()
            fig.suptitle(f"Cluster {i}")
            plt.show()
    
    plt.plot(time_array, means[3].to_numpy())
    plt.xlabel('Time (hr)')
    plt.ylabel('Load Energy (W)')
    plt.title('Cluster 3')
    plt.show()
    # Use pd.drop() to drop the site id coulumn
    # Convert to numpy array
    # Feed into sk_learn model
    # Add cluster number into site_details_v2
    """
    return

create_clusters()


