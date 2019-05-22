import re
import struct
import time
import serial
import glob
import datetime
servoX = 0
servoY = 1
servoZ1 = 2
servoZ2 = 3
xPos = 16175
yPos = 16175
z1Pos = 16175
z2Pos = 16175
baudRate = 115200
port = "COM5"
ser = serial.Serial()
class HerkulexError(Exception):
    """ Class to handle sservo errors
    """
    def __init__(self,  message):
        super(HerkulexError, self).__init__(message)
        self.message = message


def open_port():
    ser.baudrate = baudRate
    ser.port = port
    ser.timeout = 1
    ser.open()


def send_cmd(cmd, data, servoID):
    packetsize = 7 + len(data)
    checksum1 = packetsize ^ servoID ^ cmd
    for byte in data:
        checksum1 = checksum1 ^ byte
    checksum1 = checksum1&0xFE
    checksum2 = (~checksum1)&0xFE
    packet = [0xFF, 0xFF, packetsize, servoID, cmd, checksum1, checksum2]
    for byte in data:
        packet.append(byte)
    #print(packet)
    ser.write(serial.to_bytes(packet))


def read_position(servoID):
    send_cmd(0x04, [0x3A, 0x02], servoID)
    try:
        rxdata = ser.read(13)
        if(rxdata == b''):
            return None
        position = (256*rxdata[10]) + rxdata[9]
        #print(rxdata[9])
        #print(rxdata[10])
        print("Servo " + str(servoID) + " currently at " + str(position)+"\n")
        return (position)
    except HerkulexError:
        raise HerkulexError("could not communicate with motors")


def torque_on(servoID):
    send_cmd(0x03, [0x34, 0x01, 0x60], servoID)
    #file.write("Servo " + str(servoID) + " Torque On\n")

def torque_off(servoID):
    send_cmd(0x03, [0x34, 0x01, 0x40], servoID)
    #file.write("Servo " + str(servoID) + " Torque Off\n")

def move_to_angle(angle,servoID):  # recommended range is within 0 - 300 deg
    #position = int((angle*35.9971202) + 9903)
    position = int(angle*35.9971202)
    pos_LSB = position & 0xFF
    pos_MSB = (position & 0xFF00) >> 8
    led = 8 # green*4 + blue*8 + red*16
    playtime = 0x3C # execution time
    send_cmd(0x05, [pos_LSB, pos_MSB, led, servoID, playtime], servoID)


def move_to_pos(position, servoID):  # recommended range is within 0 - 300 deg
    pos_LSB = position & 0xFF
    pos_MSB = (position & 0xFF00) >> 8
    led = 8 # green*4 + blue*8 + red*16
    playtime = 0x3C # execution time
    print("Servo " + str(servoID) + " moving to " + str(position)+"\n")
    send_cmd(0x05, [pos_LSB, pos_MSB, led, servoID, playtime], servoID)
    currentPos = read_position(servoID)
    if(currentPos != None):
        time.sleep(0.7)
        while(currentPos != read_position(servoID)):
            currentPos = read_position(servoID)
            time.sleep(0.01)
        logPosition()
    else:
        print("Servo " + str(servoID) + " position not found\n")


def set_speed(speed, servoID):
    goalSpeedSign = 0
    if speed>0:
        goalSpeedSign = speed
    elif speed<0:
        goalSpeedSign = -speed
        goalSpeedSign |= 0x4000
    speed_LSB = goalSpeedSign & 0xFF
    speed_MSB = (goalSpeedSign & 0xFF00) >> 8
    led = 4 # green*4 + blue*8 + red*16
    playtime = 0x3C # execution time
    send_cmd(0x05, [speed_LSB, speed_MSB, led, servoID, playtime], servoID)


def reboot():
    send_cmd(0x09, [], servoX)
    send_cmd(0x09, [], servoY)
    send_cmd(0x09, [], servoZ1)
    send_cmd(0x09, [], servoZ2)
    time.sleep(3)
    torque_on(servoX)
    torque_on(servoY)
    torque_on(servoZ1)
    torque_on(servoZ2)

def close():
    torque_off(servoX)
    torque_off(servoY)
    torque_off(servoZ1)
    torque_off(servoZ2)
    ser.close()


def init():
    path = "C:/Users/gator/herkulexpython-master/herkulexpython-master/Logs/*.txt"
    files = glob.glob(path)
    for name in files:
        if(re.findall(r'[\d.]+', name)[0].replace(".","") == "0"):
            file = open(name, "r")
            positions = file.readlines()
            if(len(positions) == 2):
                xPos = int(positions[0])
                yPos = int(positions[1])
        elif(re.findall(r'[\d.]+', name)[0].replace(".","") == "1"):
            file = open(name, "r")
            positions = file.readlines()
            if(len(positions) == 2):
                xPos = int(positions[0])
                yPos = int(positions[1])
    open_port()
    torque_on(servoX)
    torque_on(servoY)
    torque_on(servoZ1)
    torque_on(servoZ2)
    rebootneeded = False
    if(xPos-read_position(servoX)<0):
        if(xPos-read_position(servoX)<-12000):
            move_to_pos(25000,servoX)
            rebootneeded = True
    elif(xPos-read_position(servoX)>0):
        if(xPos-read_position(servoX)>12000):
            move_to_pos(8000,servoX)
            rebootneeded = True
    if (yPos - read_position(servoY) < 0):
        if (yPos - read_position(servoY) < -12000):
            move_to_pos(25000, servoY)
            rebootneeded = True
    elif (yPos - read_position(servoY) > 0):
        if (yPos - read_position(servoY) > 12000):
            move_to_pos(8000, servoY)
            rebootneeded = True
    if(rebootneeded == True):
        reboot()
def logPosition():
    file = open("Logs/0.txt", "w")
    if(read_position(servoX) != None):
        file.write(str(read_position(servoX))+"\n")
    if(read_position(servoY) != None):
        file.write(str(read_position(servoY))+"\n")
    file.close()
    file = open("Logs/1.txt", "w")
    if (read_position(servoX) != None):
        file.write(str(read_position(servoX)) + "\n")
    if (read_position(servoY) != None):
        file.write(str(read_position(servoY)) + "\n")
    file.close()


def goTo(x, y):
    if(x<0):
        x = 0
    elif(x>32350):
        x = 32350
    if (y < 0):
        x = 0
    elif (y > 32350):
        x = 32350
    x = x + 100  #16175
    y = y + 100  #16175
    move_to_pos(x , servoX)
    move_to_pos(y, servoY)

init()
#for x in range(3):
#    goTo(16175, 16175)
#    goTo(0, 0)
goTo(200,200)
move_to_pos(22000,servoZ1)
move_to_pos(12000,servoZ1)
#for x in range(1):
    #goTo(25000, 25000)
    #reboot()
    #read_position(servoX)
    #goTo(8000, 8000)
    #reboot()
    #read_position(servoX)
    #goTo(16175, 16175)
close()
