import os
import datetime
import asyncio
from typing import List

import can
from can.notifier import MessageRecipient

os.system('sudo ip link set can0 type can bitrate 100000')
os.system('sudo ifconfig can0 up')


def print_message(msg: can.Message) -> None:
    """Regular callback function. Can also be a coroutine."""
    print(msg)


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
    #canMsgData[0] = msgType
    canMsgData.append(msgType)
    if msgType == flagByteDict["status"]:
        print("status")
    
    elif msgType == flagByteDict["alarmThreshold"]:
        print("alarmThreshold")
        canMsgData.append(alarmThresholdCurrent / 100)
        canMsgData.append(alarmThresholdCurrent % 100)
    elif msgType == flagByteDict["rwSetting"]:
        print("rwSetting")
        canMsgData.append(rwDict["P"])
        canMsgData.append(rwDict["I"])
        canMsgData.append(rwDict["D"])
        canMsgData.append(rwDict["T"])
        canMsgData.append(rwDict["Calibration"])
        canMsgData.append(rwDict["RW"])
    elif msgType == flagByteDict["RTC"]:
        print("RTC")
        currentTime = datetime.datetime.now()
        canMsgData.append(currentTime.hour)
        canMsgData.append(currentTime.minute)
        canMsgData.append(currentTime.second)
        canMsgData.append(currentTime.date)
        canMsgData.append(currentTime.month)
        canMsgData.append(currentTime.year)
    elif msgType == flagByteDict["history"]:
        print("History")
        canMsgData.append(historyDict["maxCurrent"] / 100)
        canMsgData.append(historyDict["maxCurrent"] % 100)
        canMsgData.append(historyDict["minCurrent"] / 100)
        canMsgData.append(historyDict["minCurrent"] % 100)
        canMsgData.append(historyDict["average"] / 100)
        canMsgData.append(historyDict["average"] % 100)
       
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
        
async def main() -> None:
    """The main function that runs in the loop."""
    with can.Bus(
        interface="socketcan", channel="can0", receive_own_messages=True
    ) as bus:
        reader = can.AsyncBufferedReader()
        logger = can.Logger("logfile.asc")
        listeners: List[MessageRecipient] = [
            print_message, # Callback function
            reader, #AsyncBufferReader() listener
            logger, #Regular Listener object
         ]

        # Create Notifier with an explicit loop to use for scheduling of callbacks
        loop = asyncio.get_running_loop()
        notifier = can.Notifier(bus, listeners, loop=loop)
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
            if previous_timestamp != 0:
                difference_timestamp = current_timestamp - previous_timestamp
            previous_timestamp = current_timestamp
            if difference_timestamp >= 30:
                bRTC = True
            """for id in slaveIDs:
                createMessage(flagByteDict["status"])
                msg = can.Message(arbitration_id=id, data=canMsgData,is_extended_id=False)
                bus.send(msg)
                """
            # Start sending first message
            createMessage(flagByteDict["status"])
            msg = can.Message(arbitration_id=1, data=canMsgData, is_extended_id=False)
            bus.send(msg)
            #bus.send(can.Message(arbitration_id=0, data=[1,2,3], is_extended_id=False))

            print("Bouncing 10 messages...")
            for _ in range(10):
                # Wait for next message from AsyncBufferedReader
                msg = await reader.get_message()
                # Delay response
                await asyncio.sleep(0.5)
                msg.arbitration_id += 1
                bus.send(msg)

            # Wait for last message to arrive
            await reader.get_message()
            print("Done!")

        # Clean-up
        notifier.stop()


if __name__ == "__main__":
    asyncio.run(main())