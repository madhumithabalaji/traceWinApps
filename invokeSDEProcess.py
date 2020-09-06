#!/usr/bin/env python
# coding: utf-8

import subprocess
import time
import os
import signal
import datetime

appList = {
    1:{'name': 'notepad.exe', 'repeat':'1', 'sleeptime':'30'}, 
    2:{'name': 'cmd.exe', 'repeat':'2', 'sleeptime':'30'}

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
            time.sleep(10)
            #send filename to 
            opcodeList = opcodesGeneration(fileName)
            print(opcodeList)
            writeOpcodeDictionary(opcodeList)
        else:
            break
        i +=1
    
#start an SDE process to trace apps
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
                fileHandle.write(opcodeStr+'\n')
                print('wrote ',opcodeStr)
    fileHandle.close()
    return 1
