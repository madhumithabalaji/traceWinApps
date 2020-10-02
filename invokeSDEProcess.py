#!/usr/bin/env python
# coding: utf-8

#CHANGE APPINFO
SDEpath        = 'C:\\intelSDE\\sde-external-8.50.0-2020-03-26-win\\sde' #path where SDE command is found
startupSleep   = 10                                                      #time given in secs for process to show up on UI
samplingSleep  = 30                                                      #time given in secs for SDE to generate trace logs
repeatInstance = 1                                                       #number of times each app will be started
appList        = {                                                       #list of apps to be sampled
                    #1:{'name': 'choice.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\'},
                    #2:{'name': 'Utilman.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\'},
                    #3:{'name': 'DevicePairingWizard.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\'},
                    #4:{'name': 'cmd.exe', 'path':''},
                    5:{'name': 'notepad.exe', 'path':''},
                    #6:{'name': 'fontview.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\'},
                    #7:{'name': 'ftp.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\'},
                }           
dictFile       = 'opcodeDictionary.txt'                                  #Dictionary with unique opcodes
csvFile        = 'opcodeFrequency.csv'                                   #count of opcodes for each app instance in csv
logfile        = 'logTraceWinApps.txt'                                   #Framework log info
mouseClickrFile= 'C:\\Users\\14632\\Downloads\\RandomMouseClicker.exe'   #Random mouse clicker path

import subprocess
import time
import os
import signal
import datetime
import glob
import csv
import pandas as pdHandle
import logging
import psutil    
from pynput.keyboard import Key, Controller

global SDEpath, appList, startupSleep, samplingSleep, repeatInstance, dictFile, csvFile, logfile


# Start Process, SDE attach-pid and sleep for a while
def invokeSDEProcess(appInstance, fileName):
    iPid = 0
    logging.info('Start pss %s', appInstance['name'])
    logging.info('Trace log file created for %s: %s', appInstance['name'], fileName)
    startPssCmd = '(Start-Process -WindowStyle normal \"'+appInstance['path'] + appInstance['name']+'\" -passthru).ID'
    cmdRes = subprocess.Popen(["powershell",startPssCmd], stdout=subprocess.PIPE)
    pssPid = str(cmdRes.communicate()[0]).replace('\\r\\n\'','').replace('b\'','')
    iPid = int(pssPid)
    sdePssCmd = SDEPath + " -attach-pid "+ pssPid +" -mix -omix "+ fileName
    sdeCmdRes = subprocess.Popen(sdePssCmd, stdout=subprocess.PIPE)
    logging.info('%s pss starts to sleep at %s', iPid, datetime.datetime.now().strftime("%H-%M"))
    mouseClikrStatus = toggleMouseClicker()
    logging.info('Started Mouse Clicker' if mouseClikrStatus else 'Not started Mouse Clicker')
    time.sleep(startupSleep)
    logging.info('%s pss ctrl return',iPid)
    return iPid
  
#start/stop mouseclicker exe file for random clicks
def toggleMouseClicker():
    status = False
    os.startfile(mouseClickrFile)
    if ("RandomMouseClicker.exe" in (p.name() for p in psutil.process_iter())):
        keyboard = Controller()
        keyboard.press(Key.ctrl)
        keyboard.press('m')
        keyboard.release('m')
        keyboard.release(Key.ctrl)
        status = True
    return status

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

#Fillup the col names in CSV file
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
                logging.warning('Error writing to %s:! Please try again', csvFile)
                return False
    return True

#Read log files for opcode occurence
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
        logging.warning('Error: Close the Excel file and try again!')
    return False

def main():
    logging.basicConfig(filename=logfile, level=logging.INFO)
    logging.info('------Started the framework on %s------', datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S"))
    from os import path
    for app, appInfo in appList.items():
        i = 1
        while i <= repeatInstance:
            fileName = 'log_' +appInfo['name'].replace('.exe','')+'_'+ datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S") + '.txt'
            resCode = invokeSDEProcess(appInfo, fileName)
            if(resCode != 0) and (path.exists(fileName)):
                logging.info('%s pss kill at %s', resCode, datetime.datetime.now().strftime("%H-%M"))
                killCmd =  "get-process -Id "+str(resCode)+ "| % { $_.CloseMainWindow() }"
                killCmdRes = subprocess.Popen(["powershell",killCmd], stdout=subprocess.PIPE)
                mouseClikrStatus = toggleMouseClicker()
                logging.info('Stopping Mouse Clicker' if mouseClikrStatus else 'Not stopped Mouse Clicker')
                logging.info('Program sleeps to complete sampling')
                time.sleep(samplingSleep)
                #if pss still exists kill command with Pid
                if psutil.pid_exists(resCode):
                    os.kill(resCode, 0)
                opcodeList = opcodesGeneration(fileName)
                if len(opcodeList) > 0:
                    try:
                        dictRes = writeOpcodeDictionary(opcodeList, dictFile)
                        logging.info('New Dictionary Entries' if dictRes else 'No new Dictionary Entries')
                    except IOError:
                        logging.warning('Check if file exists and try again!', dictFile)
                        break
                else:
                    logging.warning('Incomplete SDE log: No opcodes generated for %s', fileName)
                    os.rename(fileName,fileName.replace('log','logcrash'))
                    logging.warning('Find missing log info from files logcrash*_')
                    break
            else:
                logging.warning('No Trace info for %s', fileName)
                break
            i +=1
            
#Entry point; Run only once
if __name__ == '__main__':
    main()
fillColRes = fillColNames(dictFile, csvFile)
logging.info('Fill CSV Column Names sucess' if fillColRes else 'Fill CSV Column Names Fail')
csvWriteRes = recordOpcodeOccurence(csvFile)
logging.info('CSV write sucess' if csvWriteRes else 'CSV Write Fail')
logging.info('------Ended the framework on %s------', datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S"))
