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
import _thread

display = robot.Display()
motors = robot.Motors()
line_sensors = robot.LineSensors()

# Note: It's not safe to use Button B in a
# multi-core program.
button_a = robot.ButtonA()


max_speed = 6000
final_max_speed = 2000
initial_max_speed = 6000
counter = 1600

calibration_speed = 1000
calibration_count = 100

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

def update_display():
    display.fill(0)
    display.text(f"Max speed {max_speed}", 0, 0)
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
    global p, ir, t1, t2, line, max_speed, final_max_speed, run_motors, counter, initial_max_speed
    while True:
        # save a COPY of the line sensor data in a global variable
        # to allow the other thread to read it safely.
        line = line_sensors.read_calibrated()[:]
        line_sensors.start_read()
        t1 = t2
        t2 = time.ticks_us()

        # postive p means robot is to left of line
        if line[0] > 600 and line[1] > 600 and line[2] > 600 and line[3] > 600 and line[4] > 600 :
            motors.off()
            return
        
        if line[1] < 400 and line[2] < 400 and line[3] < 400:
            if p < 0:
                l = 0
            else:
                l = 4000
        else:
            # estimate line position
            l = (1000*line[1] + 2000*line[2] + 3000*line[3] + 4000*line[4]) // \
                sum(line)

        p = l - 2000
        d = p - last_p
        last_p = p
        pid = p*90 + d*2000

        min_speed = 0
        left = max(min_speed, min(max_speed, max_speed + pid))
        right = max(min_speed, min(max_speed, max_speed - pid))


        if run_motors:
            motors.set_speeds(left, right)
            if counter > 0:
                counter -= 1
                if 400 <= counter <= 1000 or counter <= 0:
                    max_speed = final_max_speed
                else:
                    max_speed = initial_max_speed
        else:
            motors.off()


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
