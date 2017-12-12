import numpy as np
import csv

def findwindow (data,start,sizewindow=300):
    index=np.where(data[:,0]>data[start][0]+sizewindow)[0][0]
    return index

def getRR(data):
    RR=[]
    for i in range(len(data)):
        RR.append([data[i][0],1/data[i][1]])
    RR=np.array(RR)
    return RR

def pNN100(RR):
    #calcolo differenze successive
    SSD=[]
    for i in range(len(RR)-1):
        SSD.append(RR[i+1]-RR[i])
    SSD=np.array(SSD)
    SSD=np.abs(SSD)
    return (np.count_nonzero(np.where(SSD>0.1)))/len(SSD)

def statistic(data,startwindow,endwindow):
    m=np.mean(data,axis=0)[1]
    sd=np.std(data,axis=0)[1]
    pnn100=pNN100(data[:,1])
    return m,sd,pnn100



def ba_analysis(devName,address):
    #Open csv file
    filename = devName.split(' ')[2]+'.csv'
    try:
        with open(filename, newline='\n') as csvfile:
            data=csv.reader(csvfile, delimiter='\t',quotechar='|')
            data=np.array(list(data))
        pass
   except Exception as e:
        print (e)
        break
    #Find last window and flush the rest

    lastid=data[-1][2]
    data=data[np.where(data[:,2]==lastid)]
    
   #interpolazione se necesssaria
    for i in range(len(data)):
        delta_t=data[i+1][0]-data[i][0]
        if (delta_t>1.5):
            n_dati=int(delta_t)-1
            intpolTime=np.linspace(data[i][0],data[i+1][0],n_dati)
            intpolBPM=np.linspace(data[i][1],data[i+1][1],n_dati)
            intpolID=[lastid for x in range(n_dati-1)]
            ins=np.array([intpolTime,intpolBPM,intpolID])
            ins=np.array(ins)
            for k in range(len(ins)):
                data=np.insert(data,[i+k],ins[k])
            
    # Cerca finestre

    filename = devName.split(' ')[2]+'Analysis.csv'
    if(os.path.isfile('./'+filename)):
            filePointer = open(filename, 'a')
        else:
            filePointer = open(filename, 'w')
            filePointer.write('TIME_START\tTIME_END\tMEAN\tSDNN\tpNN100\n')

    startwindow=0
    RR=getRR(data)
    while True:
        endwindow=findwindow(data,startwindow)# finestra da 5 min
        if endwindow is None:
            break
        m,sd,pnn100=statistic(RR,startwindow,endwindow-1)
        output = str(RR[startwindow][0]) + '\t' + str(RR[endwindow-1][0]) +'\t' + str(m) +'\t' + str(sd) +'\t' + str(pnn100) + '\n'
        filePointer.write(output) 
        startwindow=findwindow(data,startwindow,20)
        if startwindow is None or startwindow==0:
            break
    else:
        filePointer.close()