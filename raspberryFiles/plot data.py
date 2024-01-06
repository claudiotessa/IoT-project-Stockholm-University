import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import MiniBatchKMeans
import time
import joblib
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
import json
from mlxtend.plotting import plot_decision_regions

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

nl1= 0
nl2= 0
for i in kmeans: 
    if i==1: nl1+=1
    if i==0: nl2+=1

print(nl1)
print(nl2)
print(time.asctime())

sc= StandardScaler()
sc.fit(df)
df_transformed= sc.transform(df)

model= SVC(class_weight={0:1, 1:nl2/nl1}, kernel="linear", verbose=1, gamma=10, C=0.1)
joblib.dump(model, 'poly2.pkl')

model.fit(df_transformed, kmeans)

u=model.predict(df_transformed)
joblib.dump(u, 'predictionsrbf.pkl')

print(time.asctime())
with open('output.txt', 'w') as filehandle:
    json.dump(u.tolist(), filehandle)
tp=0
tn=0
fp=0
fn=0

for i in range(len(u)):
    if u[i] == kmeans[i] and u[i]==1:
        tp+=1
    if u[i] == kmeans[i] and u[i]==0:
        tn+=1
    if u[i] != kmeans[i] and u[i]==1:
        fp+=1
    if u[i] != kmeans[i] and u[i]==0:
        fn+=1

print(len(u))
print(len(kmeans))
# summarize performance
print('recall: %.3f' % (tp/(tp+fn)))
print('recall negatives: %.3f' % (tn/(tn+fp)))
print('precision: %.3f' % (tp/(tp+fp)))
print('precision negatives: %.3f' % (tn/(tn+fn)))

df= df.assign(classes=kmeans)

on= df_transformed[df["classes"]==1]
#print(on)
x=df['date']
y=df['wattage']

coeff=np.polyfit(on[:,0], on[:,1], 8)

regression= np.poly1d(coeff) 

print(model.coef_)
print(coeff)

plot_decision_regions(df_transformed, u, clf=model, legend=2)

polyline = np.linspace(0, 10, 100) 
#plt.scatter(on[:,0], on[:,1]) 
plt.plot(polyline, regression(polyline)) 
plt.show()