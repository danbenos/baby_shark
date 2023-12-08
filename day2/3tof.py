from pololu_3pi_2040_robot import robot
import time
from machine import I2C, Pin
from vl6180x import Sensor
from pcf8574 import PCF8574
display = robot.Display()


i2c = I2C(id=0, scl=Pin(5), sda=Pin(4), freq=100_000)

pcf = PCF8574(i2c, 0x20)

pcf.port = 0x00
pcf.pin(0, 1)
pcf.pin(1, 0)
pcf.pin(2, 0)


display.fill(0)
display.text("PCF init", 0, 0)
display.show()
time.sleep_ms(1000)

tof1 = Sensor(i2c,0x29)
tof1.address(0x2A)

display.fill(0)
display.text("TOF1 init", 0, 0)
display.show()
time.sleep_ms(1000)


pcf.pin(1, 1)
time.sleep_ms(100)

tof2 = Sensor(i2c,0x29)
tof2.address(0x2B)

display.fill(0)
display.text("TOF2 init", 0, 0)
display.show()
time.sleep_ms(1000)

pcf.pin(2, 1)
time.sleep_ms(100)

tof3 = Sensor(i2c,0x29)
tof3.address(0x2C)
time.sleep_ms(100)
display.fill(0)
display.text("TOF3 init", 0, 0)
display.show()
time.sleep_ms(1000)

while True:
  distance1 = tof1.range()
  distance2 = tof2.range()
  distance3 = tof3.range()
  display.fill(0)
  display.text("Range : " + str(distance1), 0, 10)
  display.text("Range : " + str(distance2), 0, 20) 
  display.text("Range : " + str(distance3), 0, 40)
  display.show()
