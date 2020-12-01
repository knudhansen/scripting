#!/usr/bin/python3

import argparse
import sys

parser = argparse.ArgumentParser(prog='PROG')
parser.add_argument('-i', '--input', required=True, help='input file')
args = parser.parse_args()

csvFilePath = args.input

SPI_BIT_CS = 3
SPI_BIT_CLK = 2
SPI_BIT_DATA_3 = 5
SPI_BIT_DATA_2 = 4
SPI_BIT_DATA_1 = 1
SPI_BIT_DATA_0 = 0
RESET_BIT = 6

###################### helper classes ######################

class CsvSignalChange:
    def __init__(self, csvLine, previousCsvSignalChange):
        csvLineSplit = csvLine.split(',')
        self._time = csvLineSplit[0]
        self._signals = list(map(lambda x: int(x), csvLineSplit[1:]))
        if previousCsvSignalChange:
            self._previousCsvSignalChangeSignals = previousCsvSignalChange._signals
        else:
            self._previousCsvSignalChangeSignals = None

    def getTime(self):
        return self._time
    def getSignal(self, bitNumber):
        return self._signals[bitNumber]

    def getSignalChange(self):
        if self._previousCsvSignalChangeSignals:
            return list(map(int.__sub__, self._signals, self._previousCsvSignalChangeSignals))
        else:
            return self._signals

    def isFallingEdge(self, bit):
        return self.getSignalChange()[bit] == -1
    def isRisingEdge(self, bit):
        return self.getSignalChange()[bit] == 1

class SpiOpcodeDescription:
    def __init__(self, opcode, name, serialBytes=0, inputBytes=0, ignoredBytes=0):
        self._opcode = opcode
        self._name = name
        self._serialBytes = serialBytes
        self._inputBytes = inputBytes
        self._ignoredBytes = ignoredBytes
    def getOpcode(self):
        return self._opcode
    def getName(self):
        return self._name
    def getSerialBytes(self):
        return self._serialBytes
    def getInputBytes(self):
        return self._inputBytes
    def getIgnoredBytes(self):
        return self._ignoredBytes

class SpiPacket:
    startTime = None
    endTime = None
    digits = []

    spiOpcodeDescriptions = [
        SpiOpcodeDescription(0x0B, "READ"      , 3, 3, 4),
        SpiOpcodeDescription(0x1B, "READ_B"    , 3, 3, 4),
        SpiOpcodeDescription(0x12, "OPEN_W"    , 0, 1, 0),
        SpiOpcodeDescription(0x22, "WRITE"     , 3, 19, 0),
        SpiOpcodeDescription(0x32, "OPEN_WV"   , 0, 1, 0),
        SpiOpcodeDescription(0x42, "WRITE_V"   , 3, 19, 0),
        SpiOpcodeDescription(0x02, "CLOSE_W"   , 0, 1, 0),
        SpiOpcodeDescription(0x17, "OPEN_V"    , 0, 1, 0),
        SpiOpcodeDescription(0x27, "VERIFY"    , 3, 19, 0),
        SpiOpcodeDescription(0x07, "CLOSE_V"   , 0, 1, 0),
        SpiOpcodeDescription(0x40, "ERASE"     , 3, 4, 0),
        SpiOpcodeDescription(0x41, "ECHECK"    , 3, 4, 0),
        SpiOpcodeDescription(0xB9, "SLEEP"     , 0, 1, 0),
        SpiOpcodeDescription(0xAB, "WAKE_UP"   , 0, 1, 0),
        SpiOpcodeDescription(0x05, "STATUS"    , 0, 1, 1),
        SpiOpcodeDescription(0x15, "CL_STATUS" , 0, 1, 0),
        SpiOpcodeDescription(0x06, "UNLOCK"    , 0, 1, 0),
        SpiOpcodeDescription(0x16, "UNLOCK_S0" , 0, 1, 0),
        SpiOpcodeDescription(0x04, "LOCK"      , 0, 1, 0),
        SpiOpcodeDescription(0x0E, "IFSTATUS"  , 0, 0, 0),
        SpiOpcodeDescription(0x1E, "SDQ"       , 0, 1, 0),
        SpiOpcodeDescription(0x2E, "CLK_DIV"   , 0, 1, 0),
        SpiOpcodeDescription(0xE1, "POWER_UP"  , 0, 0, 0),
        SpiOpcodeDescription(0xE7, "POWER_DOWN", 0, 1, 0),
    ]

    @staticmethod
    def reset():
        SpiPacket.startTime = None
        SpiPacket.endTime = None
        SpiPacket.digits=[]
    @staticmethod
    def start(time):
        SpiPacket.startTime = time
    @staticmethod
    def end(time):
        SpiPacket.endTime = time
        SpiPacket.show()
        SpiPacket.reset()

    @staticmethod
    def isStarted():
        return SpiPacket.startTime != None
    @staticmethod
    def getOpcode():
        opcodeDigits = SpiPacket.digits[0:8]
        opcode = 0
        for opcodeDigit in opcodeDigits:
            opcode = (opcode << 1) + opcodeDigit[0]
        return opcode
    @staticmethod
    def getOpcodeDescription():
        for spiOpcodeDescription in SpiPacket.spiOpcodeDescriptions:
            if (SpiPacket.getOpcode() == spiOpcodeDescription.getOpcode()):
                return spiOpcodeDescription
        return SpiOpcodeDescription(SpiPacket.getOpcode(), 'unknown')

    @staticmethod
    def addDigit(bit0, bit1, bit2, bit3):
        digit = [bit0, bit1, bit2, bit3]
        SpiPacket.digits.append(digit)

    @staticmethod
    def getBytes():
        bytes = []
        byte = 0
        bitsInByte = 0
        nonOpcodeDigits = SpiPacket.digits[8:]
        for digitIndex in range(len(nonOpcodeDigits)):
            if digitIndex < (SpiPacket.getOpcodeDescription().getSerialBytes() * 8):
                bitsInDigit = 1
            else:
                bitsInDigit = 4
            for bit in range(bitsInDigit):
                byte = (byte << 1) | (nonOpcodeDigits[digitIndex][bitsInDigit - 1 - bit])
                bitsInByte = bitsInByte + 1
            if bitsInByte == 8:
                bytes.append(byte)
                byte = 0
                bitsInByte = 0
        return bytes

    @staticmethod
    def show():
        opcodeDescription = SpiPacket.getOpcodeDescription()
        bytes = SpiPacket.getBytes()
        spiPacketString = "packet %s -- %s :: %10s %02x -- %d digits -- %d bytes -- " % (SpiPacket.startTime, SpiPacket.endTime, opcodeDescription.getName(), SpiPacket.getOpcode(), len(SpiPacket.digits), len(bytes))
        bytesToIgnore = 0
        for byteIndex in range(len(bytes)):
            if byteIndex == opcodeDescription.getInputBytes():
                spiPacketString += ' '
                bytesToIgnore = opcodeDescription.getIgnoredBytes()
            if bytesToIgnore > 0:
                bytesToIgnore -= 1
            else:
                spiPacketString += "%02x" % bytes[byteIndex]
        print(spiPacketString)





###################### main code ######################

sys.stderr.write("parsing file %s\n" % csvFilePath)
csvFile = open(csvFilePath)
csvLines = csvFile.readlines()[1:] ## getting rid of header line
csvSignalChange = None

lastTime = "0.0"
fullTime = None

sys.stderr.write("time: %s" % lastTime)

try:
    for csvLine in csvLines:
        csvSignalChange = CsvSignalChange(csvLine, csvSignalChange)
        fullTime = csvSignalChange.getTime()
        time = fullTime.split('.')[0] + '.' + fullTime.split('.')[1][0]
        if time != lastTime:
            sys.stderr.write("\rtime: %10s" % time)
            lastTime = time

        if not SpiPacket.isStarted():
            if csvSignalChange.isFallingEdge(SPI_BIT_CS):
                SpiPacket.start(csvSignalChange.getTime())
        else:
            if csvSignalChange.isRisingEdge(SPI_BIT_CS):
                SpiPacket.end(csvSignalChange.getTime())
            elif csvSignalChange.isRisingEdge(SPI_BIT_CLK):
                SpiPacket.addDigit(csvSignalChange.getSignal(SPI_BIT_DATA_0),
                                   csvSignalChange.getSignal(SPI_BIT_DATA_1),
                                   csvSignalChange.getSignal(SPI_BIT_DATA_2),
                                   csvSignalChange.getSignal(SPI_BIT_DATA_3))
        if csvSignalChange.isRisingEdge(RESET_BIT):
            print("RESET at %s" % csvSignalChange.getTime())
except MemoryError:
    sys.stderr.write("\nMemoryError at %s\n" % fullTime)
sys.stderr.write("\n")
