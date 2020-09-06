#!/usr/bin/env python
# coding: utf-8

# Invoke SDE Process
import subprocess
import time
import os
import signal
import datetime
fileName = 'logOpcode_' + datetime.datetime.now().strftime("%m-%d-%Y-%H-%M") + '.txt'
appName = 'notepad.exe'
startPssCmd = '(Start-Process '+appName+' -passthru).ID'
cmdRes = subprocess.Popen(["powershell",startPssCmd], stdout=subprocess.PIPE)
pssPid = str(cmdRes.communicate()[0]).replace('\\r\\n\'','').replace('b\'','')
iPid = int(pssPid)
sdePssCmd = "C:\\Users\\balajima\\Desktop\\intelSDE\\sde-external-8.50.0-2020-03-26-win\\sde -attach-pid "+ pssPid +" -mix -omix "+ fileName
os.system(sdePssCmd)


os.kill(iPid, signal.SIGTERM)

# create opcode list from trace log
opcodeList=[]
for line in reversed(list(open(fileName))):
    if(not('#' in line) and not('*' in line)):
        opcodeList.append(str(line.split(' ')[0]))             
    if("opcode" in line):
        break
print(opcodeList)


# DONT USE - TRIAL WORK
opcodeDictionaryFile = 'opcodeDictionary1.txt'
for opcodeStr in opcodeList:
    with open(opcodeDictionaryFile, "r+") as fileHandle:
        if opcodeStr in fileHandle.read():
            continue
        else:
            fileHandle.write(opcodeStr+'\n')
    fileHandle.close()


# Create unique Dictionary of opcodes
opcodeDictionaryFile = 'opcodeDictionary.txt'
with open(opcodeDictionaryFile, "r+") as fileHandle:
    dictionaryList = fileHandle.read()
    for opcodeStr in opcodeList:
        if opcodeStr in dictionaryList:
            continue
        else:
            fileHandle.write(opcodeStr+'\n')
fileHandle.close()
