
import serial
import time
currentAngle = 0
servoID = 219
baudRate = 115200
port ="COM5"
ser = serial.Serial("COM5", baudRate, timeout=0.1)


def send_cmd(cmd, data):
    packetsize = 7 + len(data)
    checksum1 = packetsize ^ servoID ^ cmd
    for byte in data:
        checksum1 = checksum1 ^ byte
    checksum1 = checksum1&0xFE
    checksum2 = (~checksum1)&0xFE
    packet = [0xFF, 0xFF, packetsize, servoID, cmd, checksum1, checksum2]
    for byte in data:
        packet.append(byte)
    print(packet)
    ser.write(serial.to_bytes(packet))


def read_data(size=10):
    rxdata = ser.read(size)
    return [ord(b) for b in rxdata]


def torque_on():
    send_cmd(0x03, [0x34, 0x01, 0x60])


def torque_off():
    send_cmd(0x03, [0x34, 0x01, 0x40])


def move_to_angle(angle):  # recommended range is within 0 - 300 deg
    currentAngle = angle
    position = int((angle*35.9971202) + 9903)
    led = 8  # green*4 + blue*8 + red*16
    playtime = 0x5C  # execution time
    if currentAngle != 0:
        pos_LSB = 0 & 0xFF
        pos_MSB = (0 & 0xFF00) >> 8
        send_cmd(0x05, [pos_LSB, pos_MSB, led, servoID, playtime])
        currentAngle = 0
    else:
        pos_LSB = position & 0xFF
        pos_MSB = (position & 0xFF00) >> 8
        send_cmd(0x05, [pos_LSB, pos_MSB, led, servoID, playtime])

    send_cmd(0x05, [pos_LSB, pos_MSB, led, servoID, playtime])


def set_speed(speed):
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
    send_cmd(0x05, [speed_LSB, speed_MSB, led, servoID, playtime])

def reboot():
    send_cmd(0x09,[])


def close():
    ser.close()


torque_on()
move_to_angle(0)
time.sleep(1)
move_to_angle(360)
time.sleep(1)
move_to_angle(-265)
time.sleep(1)
torque_off()
reboot()
close()
