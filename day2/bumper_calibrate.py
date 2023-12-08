# This example makes the 3pi+ 2040 drive forward until it hits a wall, detect
# the collision with its bumpers, then reverse, turn, and keep driving.

from pololu_3pi_2040_robot import robot
from pololu_3pi_2040_robot.extras import editions
import time

motors = robot.Motors()
bump_sensors = robot.BumpSensors()
buzzer = robot.Buzzer()
display = robot.Display()
yellow_led = robot.YellowLED()

max_speed = 1125
turn_time = 150

display.fill(0)
display.show()

bump_sensors.calibrate()

time.sleep_ms(1000)

def int_percent(value, percent):
    return value * percent // 100

while True:
    motors.set_speeds(int_percent(max_speed, 120), max_speed)
    bump_sensors.read()

    if bump_sensors.left_is_pressed():
        yellow_led.on()
        motors.set_speeds(0, 0)
        buzzer.play("a32")
        display.fill(0)
        display.text("Left", 0, 0)
        display.show()

        motors.set_speeds(max_speed, -max_speed)
        time.sleep_ms(turn_time)

        motors.set_speeds(0, 0)
        buzzer.play("b32")
        yellow_led.off()

        display.fill(0)
        display.show()

    if bump_sensors.right_is_pressed():
        yellow_led.on()
        motors.set_speeds(0, 0)
        buzzer.play("e32")
        display.fill(0)
        display.text("Right", 88, 0)
        display.show()

        motors.set_speeds(-max_speed, max_speed)
        time.sleep_ms(turn_time)

        motors.set_speeds(0, 0)
        buzzer.play("f32")
        yellow_led.off()

        display.fill(0)
        display.show()
