#!/usr/local/bin/python3

csvFilePath = 'example.csv'

SPI_BIT_CS = 0
SPI_BIT_CLK = 1
SPI_BIT_DATA_3 = 2
SPI_BIT_DATA_2 = 3
SPI_BIT_DATA_1 = 4
SPI_BIT_DATA_0 = 5

class CsvSignalChange:
    def __init__(self, csvLine, previousCsvSignalChange):
        csvLineSplit = csvLine.split(',')
        self._time = csvLineSplit[0]
        self._signals = list(map(lambda x: int(x), csvLineSplit[1:]))
        self._previousCsvSignalChange = previousCsvSignalChange

    def getTime(self):
        return self._time
    def getSignal(self, bitNumber):
        return self._signals[bitNumber]

    def getSignalChange(self):
        if self._previousCsvSignalChange:
            return list(map(int.__sub__, self._signals, self._previousCsvSignalChange._signals))
        else:
            return self._signals

    def isFallingEdge(self, bit):
        return self.getSignalChange()[bit] == -1
    def isRaisingEdge(self, bit):
        return self.getSignalChange()[bit] == 1

class SpiPacket:
    startTime = None
    endTime = None
    digits = []

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
        SpiPacket.showSpiPacket()
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
    def addDigit(bit0, bit1, bit2, bit3):
        digit = [bit0, bit1, bit2, bit3]
        SpiPacket.digits.append(digit)
        
    @staticmethod
    def showSpiPacket():
        print("packet start:%s--end:%s :: opcode=%02x" % (SpiPacket.startTime, SpiPacket.endTime, SpiPacket.getOpcode()))

csvFile = open(csvFilePath)
csvLines = csvFile.readlines()
csvSignalChange = None

for csvLine in csvLines:
    csvSignalChange = CsvSignalChange(csvLine, csvSignalChange)
    
    if not SpiPacket.isStarted():
        if csvSignalChange.isFallingEdge(SPI_BIT_CS):
            SpiPacket.start(csvSignalChange.getTime())
    else:
        if csvSignalChange.isRaisingEdge(SPI_BIT_CS):
            SpiPacket.end(csvSignalChange.getTime())
        elif csvSignalChange.isRaisingEdge(SPI_BIT_CLK):
            SpiPacket.addDigit(csvSignalChange.getSignal(SPI_BIT_DATA_0),
                               csvSignalChange.getSignal(SPI_BIT_DATA_1),
                               csvSignalChange.getSignal(SPI_BIT_DATA_2),
                               csvSignalChange.getSignal(SPI_BIT_DATA_3))

