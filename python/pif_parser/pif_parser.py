#!/usr/bin/python

import fileinput


class Pif2hwPacket:
    def __init__(self):
        self._access = None
        self._elements = None

    def createFromBytes(self, bytes):
        index = 0
        self._elements = []
        while index < len(bytes):
            pif2hwheader = Pif2hwHeader()
            pif2hwheader.createFromBytes(bytes[index:])
            self._elements.append(pif2hwheader)
            index = index + pif2hwheader.getByteSize()
            if pif2hwheader.getMessageType() == "fw write":
                pif2hwpayload = Pif2hwPayload()
                pif2hwpayload.createFromBytes(bytes[index:], pif2hwheader.getPayloadLength())
                self._elements.append(pif2hwpayload)
                index = index + pif2hwpayload.getByteSize()
            elif pif2hwheader.getMessageType() == 'fw read':
                pass
            else:
                print pif2hwheader.getMessageType()
                raise "unknown message type %s" % pif2hwheader.getMessageType()

            if not pif2hwheader.getConcatenated():
                break

    def getByteSize(self):
        byteSize = 0
        for element in self._elements:
            byteSize = byteSize + element.getByteSize()
        return byteSize
    
    def getElements(self):
        if self._elements == None:
            raise "trying to get elements in hw packet before packet was created."
        return self._elements

    def setHeader(self, pif2hwHeader):
        self._header = pif2hwHeader

    def setPayload(self, pif2hwPayload):
        self._payload = pif2hwPayload

    def display(self):
        for element in self._elements:
            element.display()

class Pif2hwResult:
    def __init__(self):
        self._byte_size = None
        self._result = None

    def createFromBytes(self, bytes, byteSize):
        self._byte_size = byteSize + 3   # 3: CRC + dummy byte
        self._result = bytes[0:byteSize]

    def display(self):
        print "Pif2hwResult"

class Pif2hwHeader:
    def __init__(self):
        self._concatenated = None
        self._message_type = None
        self._transfer_mode = None
        self._reserved = None
        self._payload_length = None
        self._byte_size = 6

    def createFromBytes(self, bytes):
        self._concatenated = ((int(bytes[0],16) >> 7) == 1)
        self._payload_length = ((int(bytes[2],16) & 0x0f) << 8) + int(bytes[3],16)
        msgtypeInt = int(bytes[1],16) >> 3
        if msgtypeInt == 0x00:
            self._message_type = "identification request"
        elif msgtypeInt == 0x01:
            self._message_type = "control command"
        elif msgtypeInt == 0x02:
            self._message_type = "status request"
        elif msgtypeInt == 0x04:
            self._message_type = "hw read"
        elif msgtypeInt == 0x05:
            self._message_type = "hw write"
        elif msgtypeInt == 0x06:
            self._message_type = "fw read"
        elif msgtypeInt == 0x07:
            self._message_type = "fw write"
        else:
            raise "illegal message type"

    def getByteSize(self):
        if self._byte_size == None:
            raise "trying to get size of hw header before it has been created"
        return self._byte_size

    def getMessageType(self):
        if self._message_type == None:
            raise "trying to get message type before header was created."
        return self._message_type

    def getConcatenated(self):
        if self._concatenated == None:
            raise "trying to get message type before header was created."
        return self._concatenated

    def getPayloadLength(self):
        return self._payload_length

    def display(self):
        print "pif2hw header: concatenated=%s, transfer_mode=NOT_IMPLEMENTED message_type=%s, payload_length=%d" % (self._concatenated, self._message_type, self._payload_length)


class Pif2hwPayload:
    def __init__(self):
        self._payload = None
        self._byte_size = None

    def createFromBytes(self, bytes, byteSize):
        self._payload = bytes[0:byteSize]
        print byteSize
        print len(self._payload)
        self._byte_size = byteSize + 3   # 3: CRC + dummy byte

    def getByteSize(self):
        if self._byte_size == None:
            raise "trying to get size of hw payload before it has been created"
        return self._byte_size

    def getBytes(self):
        if self._payload == None:
            raise "trying to get hw payload bytes before it has been created"
        return self._payload

    def display(self):
        print "pif2hw payload: %s" % self._payload


class Pif2fwPacket:
    def __init__(self):
        self._elements = None

    def createFromBytes(self, bytes):
        index = 0
        self._elements = []
        while (index != len(bytes)):
            pif2fwheader = Pif2fwHeader()
            pif2fwheader.createFromBytes(bytes[index:])
            self._elements.append(pif2fwheader)
            index = index + pif2fwheader.getByteSize()
            if pif2fwheader.getSequenceType() == 'post':
                pif2fwpayload = Pif2fwPayload()
                pif2fwpayload.createFromBytes(bytes[index:], pif2fwheader.getSequenceLength())
                self._elements.append(pif2fwpayload)
                index = index + pif2fwpayload.getByteSize()
            if index > len(bytes):
                raise "index error while creating pif2fw packet."

    def createFromHwPayload(self, hwpayload):
        self.createFromBytes(hwpayload.getBytes())

    def getElements(self):
        if self._elements == None:
            raise "trying to get elements of a pif2fw packet before it was created."
        return self._elements

    def display(self):
        if self._elements == None:
            raise "trying to display a pif2fw packet before it was created."
        print "Pif2fwPacket:"
        for element in self._elements:
            element.display()
        

class Pif2fwHeader:
    def __init__(self):
        self._sequence_type = None
        self._sequence_id = None
        self._sequence_length = None
        self._byte_size = 3

    def createFromBytes(self, bytes):
        byte0 = int(bytes[0],16)
        if byte0 & 0xe0 == 0x80:
            self._sequence_type = 'post'
        elif byte0 & 0xe0 == 0x40:
            self._sequence_type = 'get'
        elif byte0 & 0xe0 == 0x20:
            self._sequence_type = 'coq'
        else:
            raise "illegal sequence type in fw header"

        self._sequence_id = byte0 & 0x0f

        self._sequence_length = (int(bytes[1],16) << 8) + int(bytes[2],16)

    def getByteSize(self):
        return self._byte_size

    def getSequenceType(self):
        if self._sequence_type == None:
            raise "trying to get fwheader sequence type before the header was parsed"
        return self._sequence_type
    
    def getSequenceId(self):
        if self._sequence_id == None:
            raise "trying to get fwheader sequence id before the header was parsed"
        return self._sequence_id

    def getSequenceLength(self):
        if self._sequence_length == None:
            raise "trying to get fwheader sequence length before the header was parsed"
        return self._sequence_length

    def display(self):
        print "pif2fw header: sequence_type=%s, sequence_id=%d, sequence_length=%d" % (self._sequence_type, self._sequence_id, self._sequence_length)


class Pif2fwPayload:
    def __init__(self):
        self._opcode = None
        self._operations = None
        self._byte_size = None
        
    def createFromBytes(self, bytes, byteSize):
        self._byte_size = byteSize
        self._operations = []
        self._opcode = int(bytes[0], 16)
        index = 1
        while index < byteSize:
            if self._opcode == 0x17:
                operation = readFromNvramAndCheckCrcOperation()
                operation.createFromBytes(bytes[index:])
                self._operations.append(operation)
                index = index + operation.getByteSize()
            else:
                print self._opcode
                raise "there were no operations defined for opcode %d" % self._opcode

    def createFromHwPayload(self, hwpayload):
        createFromBytes(self, hwpayload.getBytes(), hwpayload.getByteSize())

    def getByteSize(self):
        if self._byte_size == None:
            raise "trying to get fwpayload byte size before payload was parsed"
        return self._byte_size

    def getOperations(self):
        if self._operations == None:
            raise "trying to get operations from fw payload before the payload was created"
        return self._operations

    def display(self):
        for operation in self._operations:
            operation.display()


class Operation:
    def __init__(self, opcode):
        self._opcode = opcode
        self._byte_size = None

    def getByteSize(self):
        if self._byte_size == None:
            raise "trying to get operation byte size before operation was parsed"
        return self._byte_size


class readFromNvramAndCheckCrcOperation (Operation):
    def __init__(self):
        Operation.__init__(self, 0x17)
        self._file_index = None
        self._offset = None
        self._length = None
        self._byte_size = 6

    def createFromBytes(self, bytes):
        self._file_index = (int(bytes[0],16) << 8) + int(bytes[1],16)
        self._offset = (int(bytes[2],16) << 8) + int(bytes[3],16)
        self._length = (int(bytes[4],16) << 8) + int(bytes[5],16)

    def getResultSize(self):
        return self._length

    def display(self):
        print "readFromNvramAndCheckCrcOperation: file_number=%d, offset=%d, length=%d" % (self._file_index, self._offset, self._length)
    


bytes = []
for line in fileinput.input():
    line = line.split("#")[0]
    bytes.extend(line.split())

index = 0
hwpackets = []

while (index != len(bytes)):
    hwpacket = Pif2hwPacket()
    hwpacket.createFromBytes(bytes[index:])
    index = index + hwpacket.getByteSize()
    hwpackets.append(hwpacket)
    if index > len(bytes):
        raise "index error"
  
fwpackets = []
 
for hwpacket in hwpackets:
    print "## HWPACKET ##"
    pif2hwheader = None
    for element in hwpacket.getElements():
        if isinstance(element, Pif2hwHeader):
            pif2hwheader = element
        if isinstance(element, Pif2hwPayload):
            if pif2hwheader.getMessageType() == "fw write":
                pif2fwpacket = Pif2fwPacket()
                pif2fwpacket.createFromHwPayload(element)
                pif2fwpacket.display()
                fwpackets.append(pif2fwpacket)

sequence = []
for i in range(0,16):
    sequence.append(None)

def printSequences():
    for i in range(0,16):
        resultSize = 0
        if sequence[i] == None:
            print "sequence[%d] -- UNUSED" % (i)
        else:
            for operation in sequence[i]:
                resultSize = resultSize + operation.getResultSize()
            print "sequence[%d] -- result size = %d" % (i, resultSize)
    
def processFwPacket(fwpacket):
    sequenceId = None
    packetResultSize = 0
    for element in fwpacket.getElements():
        if isinstance(element, Pif2fwHeader):
            sequenceResultSize = 0
            if element.getSequenceType() == 'post':
                sequenceId = element.getSequenceId()
                sequenceResultSize = 1
            elif element.getSequenceType() == 'get':
                for operation in sequence[element.getSequenceId()]:
                    sequenceResultSize = sequenceResultSize + operation.getResultSize()
            packetResultSize = packetResultSize + sequenceResultSize
        elif isinstance(element, Pif2fwPayload):
            sequence[sequenceId] = element.getOperations()
            sequenceId = None
        else:
            raise "illegal element in Pif2fwPacket"

def getCyclicMemoryUsage():
    cyclicMemoryUsage = 0
    for i in range(0,16):
        if sequence[i] == None:
            continue
        for operation in sequence[i]:
            cyclicMemoryUsage = cyclicMemoryUsage + operation.getByteSize() + operation.getResultSize()
    return cyclicMemoryUsage
    

for fwpacket in fwpackets:
    processFwPacket(fwpacket)
    print getCyclicMemoryUsage()

