import os
import numpy as np
from time import sleep

def load():#devName,address):
    #Open csv file
    # filename  =  devName.split(' ')[2]+'.csv'
    filename = 'test.csv'
    try:
        data = np.genfromtxt(filename, dtype=float, skip_header=1)
        #find last window and flush the rest of the data
        lastid = data[-1][2]
        data = data[np.where(data[:, 2] == lastid)]
        return data, lastid
    except Exception as e:
        print(e)

def interpolation(data,WID):
    i=0
    while i<len(data)-2:
        delta_t = data[i+1][0]-data[i][0]
        if (delta_t > 1.5):
            n_dati = int(np.floor(delta_t))+1
            intpolTime = np.linspace(data[i][0], data[i+1][0], n_dati)
            intpolBPM = np.linspace(data[i][1], data[i+1][1], n_dati)
            intpolID = np.array([WID for x in range(n_dati)])
            ins = np.stack((intpolTime, intpolBPM, intpolID), axis=1)
            for k in range(1,len(ins)-1):
                data = np.insert(data, [i+k], ins[k], axis=0)
        i+=(1+len(ins))
    return data

def findwindow (data, start=0, sizewindow = 300):
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

def parse_write(data,startwindow,filePointer):
    # Cerca finestre
        RR = getRR(data)
        while True:
            endwindow = findwindow(data,startwindow)# finestra da 5 min data
            if endwindow:
                m,sd,pnn100 = statistic(RR,startwindow,endwindow)
                output  =  str(RR[startwindow][0]) + '\t' + str(RR[endwindow][0]) +'\t' + str(m) +'\t' + str(sd) +'\t' + str(pnn100) + '\n'
                filePointer.write(output)
                startwindow = findwindow(data,startwindow,20)
                if not startwindow:
                    return endwindow+1 #Ritorna l'indice della finestra da analizzare
            else:
                return startwindow


def therad_analysis():#devName,address):
    #Open csv file
    # filename  =  devName.split(' ')[2]+'.csv'
    sleep(300) #Wait at least 5 min for a 
    failures=0
    # data, lastid = load()
    if(os.path.isfile('./'+filename)):
        filePointer  =  open(filename, 'a')
    else:
        filePointer  =  open(filename, 'w')
        filePointer.write('TIME_START\tTIME_END\tMEAN\tSDNN\tpNN100\n')
    
    startwindow=0

    while(failures<3):
        data, lastid = load()
        if findwindow(data):
            data=interpolation(data,lastid)
            startwindow=parse_write(data,startwindow,filePointer)
        else:
            #Idle per 20 s , fail counter + 1 e cicla
            sleep(20)
            failures+=1
    else:
        filePointer.close()


def batch_analysis():#devName,address):
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

    # Controllo se la finestra di lettura ha durata abbastanza lunga da avere significanza
    if findwindow(data,0):
        #Apro il file

        # filename  =  devName.split(' ')[2]+'Analysis.csv'
        filename = 'test_out.csv'

        if(os.path.isfile('./'+filename)):
            filePointer  =  open(filename, 'a')
        else:
            filePointer  =  open(filename, 'w')
            filePointer.write('TIME_START\tTIME_END\tMEAN\tSDNN\tpNN100\n')

        # Cerca finestre
        RR = getRR(data)
        startwindow = 0
        while True:
            endwindow = findwindow(data,startwindow)# finestra da 5 min data
            if endwindow:
                m,sd,pnn100 = statistic(RR,startwindow,endwindow)
                output  =  str(RR[startwindow][0]) + '\t' + str(RR[endwindow][0]) +'\t' + str(m) +'\t' + str(sd) +'\t' + str(pnn100) + '\n'
                filePointer.write(output)
                startwindow = findwindow(data,startwindow,20)
                if not startwindow:
                    break
            else:
                break
        else:
            filePointer.close()
