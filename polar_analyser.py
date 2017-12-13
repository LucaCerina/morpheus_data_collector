import numpy as np
import csv
import os

def findwindow (data,start,sizewindow = 300):
    print(data[start].shape)
    print (start)
    index = np.argwhere(data[:,0]>data[start][0]+sizewindow)
    # print(index)
    if index.any():
        print('ok')
        return index[0]
    else:
        print('no')
    # if index[0]==[]:
    #     return index [0]
    # else:
    #     print (index[0][0])
    #     return index[0][0] 
        
    

def getRR(data):
    RR = []
    for i in range(len(data)):
        RR.append([data[i][0],1/data[i][1]])
    RR = np.array(RR)
    return RR

def pNN100(RR):
    #calcolo differenze successive
    SSD = []
    for i in range(len(RR)-1):
        SSD.append(RR[i+1]-RR[i])
    SSD = np.array(SSD)
    SSD = np.abs(SSD)
    return (np.count_nonzero(np.where(SSD>0.1)))/len(SSD)

def statistic(data,startwindow,endwindow):
    m = np.mean(data,axis = 0)[1]
    sd = np.std(data,axis = 0)[1]
    pnn100 = pNN100(data[:,1])
    return m,sd,pnn100

def testfunction():#devName,address):
    #Open csv file
    # filename  =  devName.split(' ')[2]+'.csv'
    filename = 'test.csv'
    try:
        with open(filename, newline = '\n') as csvfile:
            csvfile.readline() #skip the headers
            data = csv.reader(csvfile, delimiter = '\t',quotechar = '|',quoting=csv.QUOTE_NONNUMERIC)
            data = list(data)
            data = np.array(data)
        pass
    except Exception as e:
        print (e)
    #find last window and flush the rest of the data
    lastid = data[-1][2]
    data = data[np.where(data[:,2] == lastid)]

    #interpolazione se necesssaria
    for i in range(len(data)-1):
        delta_t = data[i+1][0]-data[i][0]
        if (delta_t>1.5):
            n_dati = int(np.floor(delta_t))+1
            intpolTime = np.linspace(data[i][0],data[i+1][0],n_dati)
            intpolBPM = np.linspace(data[i][1],data[i+1][1],n_dati)
            intpolID = np.array([lastid for x in range(n_dati)])
            ins=np.stack((intpolTime,intpolBPM,intpolID), axis=1)
            # ins = np.array([intpolTime,intpolBPM,intpolID])
            # ins = np.transpose(ins)
            print (ins)
            for k in range(1,len(ins)-1):
                data = np.insert(data,[i+k],ins[k],axis=0)
    # Cerca finestre
    with open('data_out.csv','w') as out:
        for i in data:
            for k in i:
                out.write(str(k)+'\t')
            out.write('\n')


    # filename  =  devName.split(' ')[2]+'Analysis.csv'
    filename = 'test_out.csv'
    if(os.path.isfile('./'+filename)):
        filePointer  =  open(filename, 'a')
    else:
        filePointer  =  open(filename, 'w')
        filePointer.write('TIME_START\tTIME_END\tMEAN\tSDNN\tpNN100\n')

    startwindow = 0
    RR = getRR(data)
    while True:
        endwindow = findwindow(data,startwindow)# finestra da 5 min
        if endwindow:
            m,sd,pnn100 = statistic(RR,startwindow,endwindow-1)
            output  =  str(RR[startwindow][0]) + '\t' + str(RR[endwindow-1][0]) +'\t' + str(m) +'\t' + str(sd) +'\t' + str(pnn100) + '\n'
            filePointer.write(output) 
            startwindow = findwindow(data,startwindow,20)
            if not startwindow:
                break
        else:
            break
    else:
        filePointer.close()

def ba_analysis():#devName,address):
    #Open csv file
    # filename  =  devName.split(' ')[2]+'.csv'
    filename = 'test.csv'
    try:
        with open(filename, newline = '\n') as csvfile:
            csvfile.readline() #skip the headers
            data = csv.reader(csvfile, delimiter = '\t',quotechar = '|',quoting=csv.QUOTE_NONNUMERIC)
            data = list(data)
            data = np.array(data)
        pass
    except Exception as e:
        print (e)
    #find last window and flush the rest of the data
    lastid = data[-1][2]
    data = data[np.where(data[:,2] == lastid)]

    #interpolazione se necesssaria
    for i in range(len(data)-1):
        delta_t = data[i+1][0]-data[i][0]
        if (delta_t>1.5):
            n_dati = int(delta_t)+1
            intpolTime = np.linspace(data[i][0],data[i+1][0],n_dati)
            intpolBPM = np.linspace(data[i][1],data[i+1][1],n_dati)
            intpolID = [lastid for x in range(n_dati)]
            ins = np.array([intpolTime,intpolBPM,intpolID])
            ins = np.array(ins)
            ins = np.transpose(ins)
            for k in range(1,len(ins)-1):
                data = np.insert(data,[i+k],ins[k],axis=0)
            
    # Cerca finestre

    # filename  =  devName.split(' ')[2]+'Analysis.csv'
    filename = 'test_out.csv'
    if(os.path.isfile('./'+filename)):
        filePointer  =  open(filename, 'a')
    else:
        filePointer  =  open(filename, 'w')
        filePointer.write('TIME_START\tTIME_END\tMEAN\tSDNN\tpNN100\n')

    startwindow = 0
    RR = getRR(data)
    while True:
        endwindow = findwindow(data,startwindow)# finestra da 5 min
        if endwindow is None:
            break
        m,sd,pnn100 = statistic(RR,startwindow,endwindow-1)
        output  =  str(RR[startwindow][0]) + '\t' + str(RR[endwindow-1][0]) +'\t' + str(m) +'\t' + str(sd) +'\t' + str(pnn100) + '\n'
        filePointer.write(output) 
        startwindow = findwindow(data,startwindow,20)
        if startwindow is None or startwindow == 0:
            break
    else:
        filePointer.close()