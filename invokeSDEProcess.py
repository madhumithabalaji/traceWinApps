#!/usr/bin/env python
# coding: utf-8

import subprocess
import time
import os
import signal
import datetime
def invokeSDEProcess(appInstance, fileName):
    print('start ', appInstance['name'], i)
    print(fileName)
    startPssCmd = '(Start-Process '+appInstance['name']+' -passthru).ID'
    cmdRes = subprocess.Popen(["powershell",startPssCmd], stdout=subprocess.PIPE)
    pssPid = str(cmdRes.communicate()[0]).replace('\\r\\n\'','').replace('b\'','')
    iPid = int(pssPid)
    sdePssCmd = "C:\\Users\\balajima\\Desktop\\intelSDE\\sde-external-8.50.0-2020-03-26-win\\sde -attach-pid "+ pssPid +" -mix -omix "+ fileName
    sdeCmdRes = subprocess.Popen(sdePssCmd, stdout=subprocess.PIPE)
    print(iPid, ' pss starts to sleep at ', datetime.datetime.now().strftime("%H-%M"))
    time.sleep(int(appInstance['sleeptime']))
    print(iPid, ' pss ctrl return')
    # if pss exists return pid else 0
    return iPid;

# create opcode list from trace log files
def opcodesGeneration(fileName):
    opcodeList=[]
    for line in reversed(list(open(fileName))):
        if(not('#' in line) and not('*' in line)):
            opcodeList.append(str(line.split(' ')[0]))             
        if("opcode" in line):
            break
    return opcodeList

# Create unique Dictionary of opcodes
def writeOpcodeDictionary(opcodeList):
    opcodeDictionaryFile = 'opcodeDictionary.txt'
    with open(opcodeDictionaryFile, "r+") as fileHandle:
        dictionaryList = fileHandle.read()
        for opcodeStr in opcodeList:
            if opcodeStr in dictionaryList:
                continue
            else:
                fileHandle.write(opcodeStr+',')
                print('wrote ',opcodeStr)
    fileHandle.close()
    return opcodeDictionaryFile

#Fillup the col names in CSV file
def fillColNames(dictFile, csvFile):
    import pandas as pdHandle
    fileLines =pdHandle.read_csv(opcodeDictFile, sep=',')
    fileLines.rename(columns={'Unnamed: 0':'Pss ID'}, inplace = True) #col 1 placeholder
    fileLines.drop(fileLines.columns[len(fileLines.columns)-1], axis=1, inplace=True) #cleanup
    print(fileLines)
    fileLines.to_csv(csvFile,index=False)
    return 1;

#Read log files for opcode occurence
import glob
import csv
import pandas as pdHandle
def recordOpcodeOccurence(csvFile, pid):
    # for all files starting with logOpcode_ read the files reverse, have opcode list,
    # open csv, add row with pid as col 1, append values under proper col, fill others with 0
    csvReadHandle = pdHandle.read_csv(csvFile)
    for fileName in glob.glob('logOpcode_*'):
        #construct a dataframe with pid as row
        opcodeList = [0] * len(csvReadHandle.columns)
        opcodeList[0] = fileName
        for line in reversed(list(open(fileName))):
            if(not('#' in line) and not('*' in line)):
                #print(str(line.split(' ')[0])) 
                for col in csvReadHandle.columns:
                    #for the same row, look for col name matching to line[0] and write line[1]
                    if(str(line.split(' ')[0]) == col):
                        opcodeList[int(csvReadHandle.columns.get_loc(str(line.split(' ')[0])))] = str(line.split(' ',1)[1]).replace(' ','').replace('\n','')
            if("opcode" in line):
                break 
        print(opcodeList)
        #push to csv
        with open(csvFile, "a") as fp:
            wr = csv.writer(fp,dialect='excel')
            wr.writerow(opcodeList)
    return 1;
recordOpcodeOccurence('opcodeFrequency.csv', 1)


appList = {
    1:{'name': 'notepad.exe', 'repeat':'1', 'sleeptime':'30'},
    2:{'name': 'cmd.exe', 'repeat':'1', 'sleeptime':'30'}
}
for app, appInfo in appList.items():
    i = 0
    while i < int(appInfo['repeat']):
        fileName = 'logOpcode_' + datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S") + '.txt'
        resCode = invokeSDEProcess(appInfo, fileName)
        if(resCode != 0):
            #rescode = pssid and kill the process
            print('Pss kill at ', datetime.datetime.now().strftime("%H-%M"))
            killCmd =  "get-process -Id "+str(resCode)+ "| % { $_.CloseMainWindow() }"
            #killCmdRes = subprocess.Popen("taskkil /F /PID "+resCode, stdout=subprocess.PIPE)
            killCmdRes = subprocess.Popen(["powershell",killCmd], stdout=subprocess.PIPE)
            time.sleep(30)
            opcodeList = opcodesGeneration(fileName)
            print(opcodeList)
            dictFile = writeOpcodeDictionary(opcodeList)
        else:
            #Handle errors TODO
            break
        i +=1
    fillColNames(dictFile, 'opcodeFrequency.csv')
