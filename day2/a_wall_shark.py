# PID line follower demo.
#
# Place the robot on the line and press A to calibrate, then press A
# again to start it following the line.  You can also press A later
# to stop the motors.
#
# This demo shows how to use the _thread library to run a fast main
# loop on one core of the RP2040.  The other core is free to run
# slower functions like updating the display without impacting the
# speed of the main loop.

from pololu_3pi_2040_robot import robot
from pololu_3pi_2040_robot.extras import editions
import time
from machine import I2C, Pin
from vl6180x import Sensor
import _thread

display = robot.Display()
motors = robot.Motors()
line_sensors = robot.LineSensors()

# Note: It's not safe to use Button B in a
# multi-core program.
button_a = robot.ButtonA()

tof_left = None
tof_right = None
tof_front = None

max_speed = 2000
calibration_speed = 1000
calibration_count = 100
#motors.flip_left(True)
#motors.flip_right(True)

display.fill(0)
display.text("Line Follower", 0, 0)
display.text("Place on line", 0, 20)
display.text("and press A to", 0, 30)
display.text("calibrate.", 0, 40)
display.show()

while not button_a.check():
    pass

display.fill(0)
display.show()
time.sleep_ms(500)

motors.set_speeds(calibration_speed, -calibration_speed)
for i in range(calibration_count/4):
    line_sensors.calibrate()

motors.off()
time.sleep_ms(200)

motors.set_speeds(-calibration_speed, calibration_speed)
for i in range(calibration_count/2):
    line_sensors.calibrate()

motors.off()
time.sleep_ms(200)

motors.set_speeds(calibration_speed, -calibration_speed)
for i in range(calibration_count/4):
    line_sensors.calibrate()

motors.off()

t1 = 0
t2 = time.ticks_us()
p = 0
line = []
starting = False
run_motors = False
last_update_ms = 0

def int_percent(value, percent):
    return value * percent // 100


def initialize():
    global tof_left, tof_right, tof_front

    i2c = I2C(id=0, scl=Pin(5), sda=Pin(4), freq=400_000)
    time.sleep_ms(1000)

    pinL = Pin(16, Pin.OUT)
    pinF = Pin(17, Pin.OUT)
    pinR = Pin(18, Pin.OUT)

    # Set I2C addresses of the sensors
    pinL.value(1)
    time.sleep_ms(100)
    pinF.value(0)
    time.sleep_ms(100)
    pinR.value(0)
    time.sleep_ms(100)
    tof_left = Sensor(i2c)
    time.sleep_ms(100)
    tof_left.address(100)
    time.sleep_ms(10)

    pinF.value(1)
    time.sleep_ms(100)
    tof_front = Sensor(i2c)
    time.sleep_ms(100)
    tof_front.address(10)
    time.sleep_ms(10)

    pinR.value(1)
    time.sleep_ms(100)
    tof_right = Sensor(i2c)
    time.sleep_ms(100)
    tof_right.address(9)
    time.sleep_ms(10)

    display.fill(0)
    display.text("Initialized", 0, 0)
    display.show()
    time.sleep_ms(1000)

    display.fill(0)
    display.text("    Go!", 0, 0)
    display.show()

def update_display():
    display.fill(0)
    display.text("Line Follower", 0, 0)
    if starting:
        display.text("Press A to stop", 0, 10)
    else:
        display.text("Press A to start", 0, 10)
    
    ms = (t2 - t1)/1000
    display.text(f"Main loop: {ms:.1f}ms", 0, 20)
    display.text('p = '+str(p), 0, 30)

    # 64-40 = 24
    scale = 24/1000

    print(line)
    display.fill_rect(36, 64-int(line[0]*scale), 8, int(line[0]*scale), 1)
    display.fill_rect(48, 64-int(line[1]*scale), 8, int(line[1]*scale), 1)
    display.fill_rect(60, 64-int(line[2]*scale), 8, int(line[2]*scale), 1)
    display.fill_rect(72, 64-int(line[3]*scale), 8, int(line[3]*scale), 1)
    display.fill_rect(84, 64-int(line[4]*scale), 8, int(line[4]*scale), 1)

    display.show()

def follow_line():
    last_p = 0
    global p, ir, t1, t2, line, max_speed, run_motors, starting
    while True:
        # save a COPY of the line sensor data in a global variable
        # to allow the other thread to read it safely.
        line = line_sensors.read_calibrated()[:]
        line_sensors.start_read()
        t1 = t2
        t2 = time.ticks_us()

        # postive p means robot is to left of line
        if line[0] > 600 and line[1] > 600 and line[2] > 600 and line[3] > 600 and line[4] > 600 :
            if run_motors:
                motors.off()
                starting = False
                run_motors = False

        front = tof_front.range()
        right = tof_right.range()
        left = tof_left.range()

        l = (right - left) * 4
        
        # if line[1] < 400 and line[2] < 400 and line[3] < 400:
        #     if p < 0:
        #         l = 0
        #     else:
        #         l = 4000
        # else:
        #     # estimate line position
        #     l = (1000*line[1] + 2000*line[2] + 3000*line[3] + 4000*line[4]) // \
        #         sum(line)

        p = l
        d = p - last_p
        last_p = p
        pid = p*90 + d*2000

        min_speed = 0
        left = int_percent(max(min_speed, min(max_speed, max_speed + pid)), 50)
        right = int_percent(max(min_speed, min(max_speed, max_speed - pid)), 50)


        if run_motors:
            motors.set_speeds(left, right)
        else:
            motors.off()

initialize()

# Sleep immediately after starting a thread to work around this bug:
# https://github.com/micropython/micropython/issues/10621
_thread.start_new_thread(follow_line, ())
time.sleep_ms(1)

while True:
    t = time.ticks_ms()

    if time.ticks_diff(t, last_update_ms) > 100:
        last_update_ms = t
        update_display()

    if button_a.check():
        if not starting:
            starting = True
            start_ms = t
        else:
            starting = False
            run_motors = False

    if starting and time.ticks_diff(t, start_ms) > 1000:
        run_motors = True
