import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import MiniBatchKMeans
import numpy as np

df = pd.DataFrame()
df= pd.read_csv("12-2023detections1.csv")
print(df.columns)

print("normalizing")
first_of_month=df.iloc[0]['date']
df['date'] = df['date']-(86400000*((df['date']-first_of_month)//86400000))-first_of_month
print(first_of_month)
print(df.iloc[0]['date'])
print(df.iloc[-1]['date'])

df = df.drop('id', axis=1)
to_fit=df.drop('date', axis=1)
kmeans = MiniBatchKMeans(n_clusters=2, n_init='auto', verbose=1).fit_predict(to_fit)

df= df.assign(classes=kmeans)

on= df[df["classes"]==1].to_numpy()
#print(on)
x=df['date']
y=df['wattage']
 
perc=int(len(on)*0.1)
sorted_time= on[on[:,0].argsort()]
first= sorted_time[:perc,0]
last= sorted_time[1-perc:,0]
start=np.mean(first)-10*1000*60
end=np.mean(last)+10*1000*60
print(sorted_time)
print(start)
print(end)
plt.scatter(sorted_time[:perc,0], sorted_time[:perc,1], c="b") 
plt.scatter(sorted_time[1-perc:,0], sorted_time[1-perc:,1], c="r")
plt.show()