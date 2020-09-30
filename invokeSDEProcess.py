#!/usr/bin/env python
# coding: utf-8

import subprocess
import time
import os
import signal
import datetime
import subprocess
import time
import os
import signal
import datetime
def invokeSDEProcess(appInstance, fileName):
    iPid = 0
    print('start pss ', appInstance['name'])
    print('trace pss file @', fileName)
    startPssCmd = '(Start-Process \"'+appInstance['path'] + appInstance['name']+'\" -passthru).ID'
    cmdRes = subprocess.Popen(["powershell",startPssCmd], stdout=subprocess.PIPE)
    pssPid = str(cmdRes.communicate()[0]).replace('\\r\\n\'','').replace('b\'','')
    iPid = int(pssPid)
    sdePssCmd = "C:\\intelSDE\\sde-external-8.50.0-2020-03-26-win\\sde -attach-pid "+ pssPid +" -mix -omix "+ fileName
    sdeCmdRes = subprocess.Popen(sdePssCmd, stdout=subprocess.PIPE)
    print(iPid, ' pss starts to sleep at ', datetime.datetime.now().strftime("%H-%M"))
    time.sleep(int(appInstance['sample-sleeptime']))
    print(iPid, ' pss ctrl return')
    return iPid

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
def writeOpcodeDictionary(opcodeList, opcodeDictionaryFile):
    dictRes = False
    with open(opcodeDictionaryFile, "r+") as fileHandle:
        dictionaryList = fileHandle.read()
        for opcodeStr in opcodeList:
            if opcodeStr in dictionaryList:
                continue
            else:
                fileHandle.write(opcodeStr+',')
                dictRes = True
    fileHandle.close()
    return dictRes

def fillColNames(opcodeDictFile, csvFile):
    fillCollRes = False
    import pandas as pdHandle
    try:
        fileLines =pdHandle.read_csv(opcodeDictFile, sep=',')
        fileLines.rename(columns={'Unnamed: 0':'File Name'}, inplace = True) #col 1 placeholder
        fileLines.drop(fileLines.columns[len(fileLines.columns)-1], axis=1, inplace=True) #cleanup
        #print(fileLines)
        fileLines.to_csv(csvFile,index=False)
        fillCollRes = True
    except IOError:
                print('Error writing: Please try again', csvFile)
                return False
    return True

#Read log files for opcode occurence
import glob
import csv
import pandas as pdHandle
def recordOpcodeOccurence(csvFile):
    # for all files starting with log_ read the files reverse, have opcode list,
    # open csv, add row with pid as col 1, append values under proper col, fill others with 0
    try:
        csvReadHandle = pdHandle.read_csv(csvFile)
        #replace all empty cells with 0
        csvReadHandle.fillna(0,inplace=True)
        for fileName in glob.glob('log_*'):
            #construct a dataframe with filename as row
            opcodeList = [0] * len(csvReadHandle.columns)
            opcodeList[0] = fileName
            for line in reversed(list(open(fileName,'r'))):
                if(not('#' in line) and not('*' in line)):
                    for col in csvReadHandle.columns:
                        #for the same row, look for col name matching to line[0] and write line[1]
                        if(str(line.split(' ')[0]) == col):
                            opcodeList[int(csvReadHandle.columns.get_loc(str(line.split(' ')[0])))] = str(line.split(' ',1)[1]).replace(' ','').replace('\n','')
                if('opcode' in line):
                    break 
            #print(opcodeList)
            #push to csv
            with open(csvFile, 'a', newline='') as fileHandle:
                writeRow = csv.writer(fileHandle,dialect='excel')
                writeRow.writerow(opcodeList)
                fileHandle.close()
        return True
    except IOError:
        print('Error: Close the Excel file and try again!')
    return False


appList = {
    #1:{'name': 'choice.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\','repeat':'10', 'sample-sleeptime':'20', 'log-sleeptime':'30'},
    #2:{'name': 'Utilman.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\','repeat':'10', 'sample-sleeptime':'50', 'log-sleeptime':'45'},
    #3:{'name': 'DevicePairingWizard.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\','repeat':'10', 'sample-sleeptime':'50', 'log-sleeptime':'45'},
    #4:{'name': 'cmd.exe', 'path':'', 'repeat':'1', 'sample-sleeptime':'30', 'log-sleeptime':'30'},
    #5:{'name': 'notepad.exe', 'path':'', 'repeat':'1', 'sample-sleeptime':'15', 'log-sleeptime':'30'},
    #6:{'name': 'fontview.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\','repeat':'10', 'sample-sleeptime':'20', 'log-sleeptime':'30'},
    #7:{'name': 'ftp.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\','repeat':'10', 'sample-sleeptime':'20', 'log-sleeptime':'30'},
}
dictFile = 'opcodeDictionary.txt'
csvFile = 'opcodeFrequency.csv'
from os import path
for app, appInfo in appList.items():
    i = 1
    while i <= int(appInfo['repeat']):
        fileName = 'log_' +appInfo['name'].replace('.exe','')+'_'+ datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S") + '.txt'
        resCode = invokeSDEProcess(appInfo, fileName)
        if(resCode != 0) and (path.exists(fileName)):
            #rescode = pssid and kill the process
            print(resCode, 'pss kill at ', datetime.datetime.now().strftime("%H-%M"))
            killCmd =  "get-process -Id "+str(resCode)+ "| % { $_.CloseMainWindow() }"
            #killCmdRes = subprocess.Popen("taskkil /F /PID "+resCode, stdout=subprocess.PIPE)
            killCmdRes = subprocess.Popen(["powershell",killCmd], stdout=subprocess.PIPE)
            #if pss still exists kill command with Pid
            print('Pss sleep to complete sampling')
            time.sleep(int(appInfo['log-sleeptime']))
            opcodeList = opcodesGeneration(fileName)
            if len(opcodeList) > 0:
                try:
                    dictRes = writeOpcodeDictionary(opcodeList, dictFile)
                    print('New Dictionary Entries' if dictRes else 'No new Dictionary Entries')
                except IOError:
                    print('Error: Check if file exists and try again!', dictFile)
                    break
            else:
                print('Incomplete SDE log: No opcodes generated for', fileName)
                os.rename(fileName,fileName.replace('log','logcrash'))
                print('Find missing log info from files logcrash*_')
                break
        else:
            print('Error: No Trace info for', fileName)

            break
        i +=1
  
dictFile = 'opcodeDictionary.txt'
csvFile = 'opcodeFrequency.csv'
fillColRes = fillColNames(dictFile, csvFile)
print('Fill CSV Column Names sucess' if fillColRes else 'Fill CSV Column Names Fail')
# Run only once after generating all log files to record Opcode counts for each
csvWriteRes = recordOpcodeOccurence(csvFile)
print('CSV write sucess' if csvWriteRes else 'CSV Write Fail')
