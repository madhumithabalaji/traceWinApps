dictFile       = 'opcodeDictionary.txt'                                  #Dictionary with unique opcodes
csvFile        = 'opcodeFrequency.csv'                                   #count of opcodes for each app instance in csv
logfile        = 'logCSVGen.txt'                                         #Framework log info
logsPath       = '/data2/balajima/windows_malware/SDElogs/log_*'

import subprocess
import time
import os
import signal
import datetime
import glob
import csv
import pandas as pdHandle
import logging

global dictFile, csvFile, logfile, logsPath

# Entry point
logging.basicConfig(filename=logfile, level=logging.INFO)
for fileName in glob.glob(logsPath):
    opcodeList = opcodesGeneration(fileName)
    if len(opcodeList) > 0:
        try:
            dictRes = writeOpcodeDictionary(opcodeList, dictFile)
            logging.info('New Dictionary Entries for %s' if dictRes else 'No new Dictionary Entries for %s',fileName)
        except IOError:
            logging.warning('Check if file exists and try again!', dictFile)
            break
    else:
        logging.warning('Incomplete SDE log: No opcodes generated for %s', fileName)
        break
fillColRes = fillColNames(dictFile, csvFile)
logging.info('Fill CSV Column Names sucess' if fillColRes else 'Fill CSV Column Names Fail')
recordOpcodeOccurence(csvFile)

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
    
def recordOpcodeOccurence(csvFile):
    # for all files starting with log_ read the files reverse, have opcode list,
    # open csv, add row with pid as col 1, append values under proper col, fill others with 0
    try:
        csvReadHandle = pdHandle.read_csv(csvFile)
        #replace all empty cells with 0
        csvReadHandle.fillna(0,inplace=True)
        for fileName in glob.glob(logsPath):
            #construct a dataframe with filename as row
            opcodeList = [0] * len(csvReadHandle.columns)
            opcodeList[0] = fileName.split('logs/')[1]
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
    
# Create opcode list from trace log files
def opcodesGeneration(fileName):
    opcodeList=[]
    for line in reversed(list(open(fileName))):
        if(not('#' in line) and not('*' in line)):
            opcodeList.append(str(line.split(' ')[0]))             
        if("opcode" in line):
            break
    return opcodeList
