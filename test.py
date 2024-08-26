import os
import datetime
import time

import asyncio
from typing import List

import can
from can.notifier import MessageRecipient

os.system('sudo ip link set can0 type can bitrate 100000')
os.system('sudo ip link set can1 type can bitrate 100000')
os.system('sudo ifconfig can0 up')
os.system('sudo ifconfig can1 up')

# Can Flag byte
flagByteDict = { 
    "status": 0x01, 
    "alarmThreshold": 0x02, 
    "rwSetting": 0x04,
    "RTC": 0x08, 
    "history":0x10
}

# Slave IDs
slaveIDs = {
    0x01, 0x02,0x03
}

canMsgData = []
receivedMsgData = []
alarmThresholdCurrent = 2234
rAlarmThresholdCurrent = 1234

rwDict = {    
    "P":10,
    "I":10,
    "D":10,
    "T":10,
    "Calibration":20,
    "RW":False
}

historyDict = {
    "maxCurrent":1234,
    "minCurrent":1056,
    "average":1642
}

def createMessage( msgType ):
    canMsgData.clear()
    canMsgData[0] = msgType
    if msgType == flagByteDict["status"]:
        print("status")
    elif msgType == flagByteDict["alarmThreshold"]:
        print("alarmThreshold")
        canMsgData[1] = (alarmThresholdCurrent / 100)
        canMsgData[2] = (alarmThresholdCurrent % 100)
    elif msgType == flagByteDict["rwSetting"]:
        print("rwSetting")
        canMsgData[1] = rwDict["P"]
        canMsgData[2] = rwDict["I"]
        canMsgData[3] = rwDict["D"]
        canMsgData[4] = rwDict["T"]
        canMsgData[5] = rwDict["Calibration"]
        canMsgData[6] = rwDict["RW"]
    elif msgType == flagByteDict["RTC"]:
        print("RTC")
        currentTime = datetime.datetime.now()
        canMsgData[1] = currentTime.hour
        canMsgData[2] = currentTime.minute
        canMsgData[3] = currentTime.second
        canMsgData[4] = currentTime.date
        canMsgData[5] = currentTime.month
        canMsgData[6] = currentTime.year

    elif msgType == flagByteDict["history"]:
        print("History")
        canMsgData[1] = historyDict["maxCurrent"] / 100
        canMsgData[2] = historyDict["maxCurrent"] % 100
        canMsgData[3] = historyDict["minCurrent"] / 100
        canMsgData[4] = historyDict["minCurrent"] % 100
        canMsgData[5] = historyDict["average"] / 100
        canMsgData[6] = historyDict["average"] % 100


def analyzeMessage(receivedID, receivedMsg):
    print("analyzeMessage")
    if receivedMsg[0] == flagByteDict["status"]:
        print("status")
    elif receivedMsg[0] == flagByteDict["alarmThreshold"]:
        print("alarmThreshold")
    elif receivedMsg[0] == flagByteDict["rwSetting"]:
        print("rwSetting")
    elif receivedMsg[0] == flagByteDict["RTC"]:
        print("RTC")
    elif receivedMsg[0] == flagByteDict["history"]:
        print("history")
                                                                                                                     
                                                                              
def main() -> None:                                                                                                                                                                                                                                                                                                       
    # Initializing CAN module
    can0 = can.interface.Bus(channel='can0', interface='socketcan')  # using socketcan
    #can1 = can.interface.Bus(channel='can1', interface='socketcan')  # using socketcan

    try:

        # Transmiting can0
        # can0.send(msg)
        # print("Sent:", msg)
        # Receiving can0 info
        previous_timestamp = 0
        current_timestamp = 0
        difference_timestamp = 0
        
        while True:
            bStatus = False
            bAlarmThreshold = False
            bRWSetting = False
            bRTC = False
            bHistory = False
            current_timestamp = datetime.datetime.now()
            if previous_timestamp!= 0:
                difference_timestamp = current_timestamp - previous_timestamp
            previous_timestamp = current_timestamp
            if difference_timestamp >= 30:
                bRTC = True
            for id in slaveIDs:
                createMessage(flagByteDict["status"])
                msg = can.Message(arbitration_id=id, data=canMsgData, is_extended_id=False)
                can0.send(msg)
                print("Sent: ", msg)
                if bAlarmThreshold == True:
                    createMessage(flagByteDict['alarmThreshold'])
                    alarmMsg = can.Message(arbitration_id=id, data=canMsgData, is_extended_id=False)
                    can0.send(alarmMsg)
                if bRWSetting == True:
                    createMessage(flagByteDict['rwSetting'])
                    rwMsg = can.Message(arbitration_id=id, data=canMsgData, is_extended_id=False)
                    can0.send(rwMsg)
                if bRTC == True:
                    createMessage(flagByteDict['RTC'])
                    rtcMsg = can.Message(arbitration_id=id, data=canMsgData, is_extended_id=False)
                    can0.send(rtcMsg)
                if bHistory == True:
                    createMessage(flagByteDict['history'])
                    historyMsg = can.Message(arbitration_id=id, data=canMsgData, is_extended_id=False)
                    can0.send(historyMsg)
            #Receive part

            reader = can.AsyncBufferedReader()
            logger = can.Logger("logfile.asc")

            listeners :List[MessageRecipient] = [
                analyzeMessage(), # Callback function
                reader, # AsyncBufferReader() Listner
                logger, # Regular Listner object
            ]
            #Create Notifier with an explicit loop to use for scheduling of callbacks
            loop = asyncio.get_running_loop()
            notifier = can.Notifier(can0, listeners,loop=loop)
            await reader.get_message()

    finally:
        # Closing CAN module
        can0.shutdown()
        #can1.shutdown()

        # Closing CAN communication
        os.system('sudo ifconfig can0 down')
        os.system('sudo ifconfig can1 down')

if __name__ == "__main__":
    main()
