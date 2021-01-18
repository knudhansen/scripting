#!/usr/bin/python3

import argparse
import sys

parser = argparse.ArgumentParser(prog='PROG')
parser.add_argument('-i', '--input', required=True, help='input file')
args = parser.parse_args()

inputFilePath = args.input
inputFile = open(inputFilePath)
inputLines = inputFile.readlines()

lastWriteTime = [0,0,0,0]
writeCount = [0,0,0,0]

minInterwriteTimeFirstWrite = 1
maxInterwriteTimeFirstWrite = 0
minInterwriteTimeFollowingWrite = 1
maxInterwriteTimeFollowingWrite = 0

for inputLine in inputLines:
    inputLineSplit = inputLine.split()
    time = float(inputLineSplit[1])
    operation = inputLineSplit[5]
    data = inputLineSplit[14]
    module = -1
    newMinFirstWrite = '-'
    newMaxFirstWrite = '-'
    newMinFollowingWrite = '-'
    newMaxFollowingWrite = '-'
    if (operation == 'WRITE'):
        module = int(data[0], 16) / 2
        timeSinceLast = 0
        if (lastWriteTime[module] != 0):
            timeSinceLast = time - lastWriteTime[module]
        if (writeCount[module] == 1):
            if (timeSinceLast < minInterwriteTimeFirstWrite):
                minInterwriteTimeFirstWrite = timeSinceLast
                newMinFirstWrite = 'N'
            if (timeSinceLast > maxInterwriteTimeFirstWrite):
                maxInterwriteTimeFirstWrite = timeSinceLast
                newMaxFirstWrite = 'N'
        elif (writeCount[module] > 1):
            if (timeSinceLast < minInterwriteTimeFollowingWrite):
                minInterwriteTimeFollowingWrite = timeSinceLast
                newMinFollowingWrite = 'N'
            if (timeSinceLast > maxInterwriteTimeFollowingWrite):
                maxInterwriteTimeFollowingWrite = timeSinceLast
                newMaxFollowingWrite = 'N'
#        print("%-15s %-10s %d %4d %f %s %f %s %f %s %f %s %f" % (time, operation, module, writeCount[module], timeSinceLast, newMinFirstWrite, minInterwriteTimeFirstWrite, newMaxFirstWrite, maxInterwriteTimeFirstWrite, newMinFollowingWrite, minInterwriteTimeFollowingWrite, newMaxFollowingWrite, maxInterwriteTimeFollowingWrite))
        print("%-15s %-10s %d %4d %f  ||  %s %f %s %f" % (time, operation, module, writeCount[module], timeSinceLast, newMinFirstWrite, minInterwriteTimeFirstWrite, newMinFollowingWrite, minInterwriteTimeFollowingWrite))
        lastWriteTime[module] = time
        writeCount[module] = writeCount[module] + 1
    elif (operation == 'OPEN_W'):
        module = int(data[0], 16) / 4
        lastWriteTime[module] = 0
        writeCount[module] = 0
        print("%-15s %-10s %d" % (time, operation, module))

print "\n\n"

print "Minimum time after first write after OPEN_W: %f" % (minInterwriteTimeFirstWrite)
print "Miminum time after following write : %f" % (minInterwriteTimeFollowingWrite)
