#!/usr/bin/env python
# coding: utf-8

SDEpath        = 'C:\\Users\\balajima\\Downloads\\sde-external-8.50.0-2020-03-26-win\\sde' #path where SDE command is found
startupSleep   = 5                                                      #time given in secs for process to show up on UI
logCreateSleep = 20                                                      #time given in secs for SDE to generate trace logs
samplingSleep  = 5                                                       #sampling time
interSamplSleep= 10
repeatInstance = 2                                                       #number of times each app will be started
appList        = {                                                       #list of apps to be sampled
                    #1:{'name': 'choice.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\'},
                    #2:{'name': 'Utilman.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\'},
                    #3:{'name': 'DevicePairingWizard.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\'},
                    #4:{'name': 'cmd.exe', 'path':''},
                    #5:{'name': 'notepad.exe', 'path':''},
                    #6:{'name': 'fontview.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\'},
                    #7:{'name': 'ftp.exe', 'path':'C:\\Users\\balajima\\Downloads\\trainingData\\'},
                }           
dictFile       = 'opcodeDictionary.txt'                                  #Dictionary with unique opcodes
csvFile        = 'opcodeFrequency.csv'                                   #count of opcodes for each app instance in csv
logfile        = 'logTraceWinApps.txt'                                   #Framework log info
mouseClickrFile= 'AutoClicker.exe'                                       #Random mouse clicker path
remoteServPath = ' xxxx@111.111.111.111:/data2/balajima/windows_malware/SDElogs'

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

global SDEpath, appList, logCreateSleep, startupSleep, samplingSleep, interSamplSleep, repeatInstance, dictFile, csvFile, logfile, mouseClickrFile, remoteServPath

# Entry point; Run only once
if __name__ == '__main__':
    main()
fillColRes = fillColNames(dictFile, csvFile)
logging.info('Fill CSV Column Names sucess' if fillColRes else 'Fill CSV Column Names Fail')
csvWriteRes = recordOpcodeOccurence(csvFile)
logging.info('CSV write sucess' if csvWriteRes else 'CSV Write Fail')
logging.info('------Ended the framework on %s------', datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S"))

 #Main method with all function calls to create unique dictionary of opcodes
def main():
    logging.basicConfig(filename=logfile, level=logging.INFO)
    logging.info('------Started the framework on %s------', datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S"))
    from os import path
    intrSampleSlp = 0
    for appIndex, appInfo in appList.items():
        i = 1
        while i <= repeatInstance:
            fileName = 'log_' +appInfo['name'].replace('.exe','')+'_'+ datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S") + '.txt'
            toggleMouseClicker(1)
            resCode = invokeSDEProcess(intrSampleSlp, appInfo, fileName)
            if(resCode != 0):
                logging.info('%s pss kill at %s', resCode, datetime.datetime.now().strftime("%H:%M:%S"))
                toggleMouseClicker(0)
                killCmd =  "get-process -Id "+str(resCode)+ "| % { $_.CloseMainWindow() }"
                killCmdRes = subprocess.Popen(["powershell",killCmd], stdout=subprocess.PIPE)
                logging.info('Program sleeps to complete sampling')
                time.sleep(logCreateSleep)
                #if pss still exists kill command with Pid
                if psutil.pid_exists(resCode):
                    os.kill(resCode, signal.SIGTERM)
                logging.info('SCP log file Transfer: %s',transferLogFile(fileName))
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
                logging.warning('No log created for %s', fileName)
                break
            intrSampleSlp += interSamplSleep
            i +=1
 
# SCP log files to remote server after operations
def transferLogFile(fileName):
    moveCmd =  "pscp -P 22 -pw \"ilovevick\" "+ fileName + remoteServPath
    #print(moveCmd)
    return True if (os.system(moveCmd) == 0) else False     
       
# Create opcode list from trace log files
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

# Fillup the col names in CSV file
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

# Read log files for opcode occurence
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
  
# Start/stop mouseclicker exe file for random clicks
def toggleMouseClicker(toggleNum):
    if (toggleNum == 1):
        os.startfile(mouseClickrFile)
        if (mouseClickrFile in (p.name() for p in psutil.process_iter())):
            logging.info('Started Mouse Clicker app')
        else:
            logging.warning('Error starting Mouse Clicker app') 
    else:
        for proc in psutil.process_iter():
            if(proc.name()==mouseClickrFile):
                proc.kill()
                logging.info('Stopped Mouse Clicker app')
    return True
  
# Bring pss to foreground
def bringPssForeground(pid):
    pssFrontCmd = '(New-Object -ComObject WScript.Shell).AppActivate((Get-Process -Id '+pid+').MainWindowTitle)'
    subprocess.Popen(["powershell",pssFrontCmd], stdout=subprocess.PIPE)
    return True

# Start Process, SDE attach-pid and sleep for a while
def invokeSDEProcess(intrSampleSlp, appInstance, fileName):
    iPid = 0
    logging.info('Start pss %s', appInstance['name'])
    logging.info('Trace log file created for %s: %s', appInstance['name'], fileName)
    startPssCmd = '(Start-Process -WindowStyle maximized \"'+appInstance['path'] + appInstance['name']+'\" -passthru).ID'
    cmdRes = subprocess.Popen(["powershell",startPssCmd], stdout=subprocess.PIPE)
    pssPid = str(cmdRes.communicate()[0]).replace('\\r\\n\'','').replace('b\'','')
    iPid = int(pssPid)
    logging.info('%s pss starts to sleep at %s for GUI Start up', iPid, datetime.datetime.now().strftime("%H:%M:%S"))
    time.sleep(startupSleep)
    bringPssForeground(pssPid)
    #print(intrSampleSlp)
    time.sleep(intrSampleSlp) #increment in mutiples of n from the start time
    sdePssCmd = SDEpath + " -attach-pid "+ pssPid +" -mix -omix "+ fileName
    sdeCmdRes = subprocess.Popen(sdePssCmd, stdout=subprocess.PIPE)
    keyboard = Controller()
    keyboard.press(Key.ctrl)
    keyboard.press('m')
    keyboard.release('m')
    keyboard.release(Key.ctrl)
    logging.info('%s pss goes to sleep for sampling %s',iPid, datetime.datetime.now().strftime("%H:%M:%S"))
    time.sleep(samplingSleep)
    logging.info('%s pss ctrl returned after sampling sleep %s',iPid, datetime.datetime.now().strftime("%H:%M:%S"))
    return iPid
  
