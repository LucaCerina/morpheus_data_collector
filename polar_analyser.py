import os
import csv
import numpy as np

def findwindow (data, start, sizewindow = 300):
    index = np.argwhere(data[:, 0]>data[start][0]+sizewindow)
    if index.any():
        return index[0,0]

def getRR(data):
    RR = []
    for i in range(len(data)):
        RR.append([data[i][0], 1/data[i][1]])
    RR = np.array(RR)
    print(RR)
    return RR

def pNN100(RR):
    #calcolo differenze successive
    SSD = []
    for i in range(len(RR)-1):
        SSD.append(RR[i+1]-RR[i])
    SSD = np.array(SSD)
    SSD = np.abs(SSD)
    return (np.count_nonzero(np.where(SSD > 0.1)))/len(SSD)

def statistic(data, startwindow, endwindow):
    m = np.mean(data[startwindow:endwindow], axis = 0)[1]
    sd = np.std(data[startwindow:endwindow], axis = 0)[1]
    pnn100 = pNN100(data[startwindow:endwindow][1])
    return m, sd, pnn100



def ba_analysis():#devName,address):
    #Open csv file
    # filename  =  devName.split(' ')[2]+'.csv'
    filename = 'test.csv'
    try:
        data = np.genfromtxt(filename, dtype=float, skip_header=1)
        # with open(filename, newline = '\n') as csvfile:
        #     csvfile.readline() #skip the headers
        #     data = csv.reader(csvfile, delimiter = '\t', quotechar = '|', quoting=csv.QUOTE_NONNUMERIC)
        #     data = list(data)
        #     data = np.array(data)
    except Exception as e:
        print(e)

    #find last window and flush the rest of the data
    lastid = data[-1][2]
    data = data[np.where(data[:, 2] == lastid)]

    #interpolazione se necesssaria
    i=0
    while i<len(data)-2:
        delta_t = data[i+1][0]-data[i][0]
        if (delta_t > 1.5):
            n_dati = int(np.floor(delta_t))+1
            intpolTime = np.linspace(data[i][0], data[i+1][0], n_dati)
            intpolBPM = np.linspace(data[i][1], data[i+1][1], n_dati)
            intpolID = np.array([lastid for x in range(n_dati)])
            ins = np.stack((intpolTime, intpolBPM, intpolID), axis=1)
            for k in range(1,len(ins)-1):
                data = np.insert(data, [i+k], ins[k], axis=0)
        i+=(1+len(ins))


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
        if endwindow:
            m,sd,pnn100 = statistic(RR,startwindow,endwindow)
            output  =  str(RR[startwindow][0]) + '\t' + str(RR[endwindow][0]) +'\t' + str(m) +'\t' + str(sd) +'\t' + str(pnn100) + '\n'
            filePointer.write(output)
            startwindow = findwindow(data,startwindow,20)
            if not startwindow:
                break
            startwindow=startwindow
        else:
            break
    else:
        filePointer.close()
