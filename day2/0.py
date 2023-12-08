from pololu_3pi_2040_robot import robot
import time
from machine import I2C, Pin
from vl6180x import Sensor

welcome_line1 = "Baby"
welcome_line2 = "Shark"
name_line1 = "Wall"
name_line2 = "Follower"

welcome = ">g32>>c32"
go = "L16 cdegreg4"

tof_left = None
tof_right = None
tof_front = None

display_interval_ms = 100

motors = robot.Motors()
line_sensors = robot.LineSensors()
button_a = robot.ButtonA()

max_speed = 2000
calibration_speed = 1000
calibration_count = 100

display = robot.Display()
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
line = []

path = " " * 100
path_length = 0
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

def turn_in_place():
    motors.set_speeds(80, -80)
    time.sleep_ms(100)
    pass

def turn_around():
    motors.set_speeds(80, -80)
    time.sleep_ms(200)
    pass

def turn(dir):
    if dir == 'L':
        motors.set_speeds(-80, 80)
        time.sleep_ms(200)
    elif dir == 'R':
        motors.set_speeds(80, -80)
        time.sleep_ms(200)
    elif dir == 'B':
        motors.set_speeds(80, -80)
        time.sleep_ms(400)
    elif dir == 'S':
        pass

def display_path():
    global path, path_length
    path[path_length] = 0

    print(path)

    if path_length > 8:
        lcd_goto_xy(0, 1)
        print(path + 8)
    pass

def select_turn(found_left, found_straight, found_right):
    if found_left:
        return 'L'
    elif found_straight:
        return 'S'
    elif found_right:
        return 'R'
    else:
        return 'B'

def simplify_path():
    global path, path_length
    if path_length < 3 or path[path_length-2] != 'B':
        return

    total_angle = 0
    for i in range(1, 4):
        if path[path_length-i] == 'R':
            total_angle += 90
        elif path[path_length-i] == 'L':
            total_angle += 270
        elif path[path_length-i] == 'B':
            total_angle += 180

    total_angle = total_angle % 360

    if total_angle == 0:
        path[path_length - 3] = 'S'
    elif total_angle == 90:
        path[path_length - 3] = 'R'
    elif total_angle == 180:
        path[path_length - 3] = 'B'
    elif total_angle == 270:
        path[path_length - 3] = 'L'

    path_length -= 2
    pass

def follow_segment():
    last_proximity = 0
    base_speed = 50
    set_point = 300
    integral = 0
    global t1, t2, line, max_speed, run_motors, tof_left, tof_right, tof_front

    while True:
        line = line_sensors.read_calibrated()[:]
        line_sensors.start_read()
        t1 = t2
        t2 = time.ticks_us()

        if line[0] > 600 and line[1] > 600 and line[2] > 600 and line[3] > 600 and line[4] > 600 :
            motors.off()
            return
        front = tof_front.range()
        right = tof_right.range()
        left = tof_left.range()
        left_proximity = 0
        proportional = left_proximity - set_point
        derivative = left_proximity - last_proximity
        integral += derivative
        pd = proportional/6 + integral/200 + derivative*2/5
        left_set = base_speed + pd
        right_set = base_speed - pd
        last_proximity = left_proximity
        if left_set < (base_speed - 100):
            motors.set_speeds(base_speed + 10, base_speed - 10)
            time.sleep_ms(80)
        motors.set_speeds(left_set, right_set)
        if front == 0 and right == 0 and left == 0:
            turn_around()
            return
        elif front == 0:
            turn_in_place()
            continue

def maze_solve():
    global tof_left, tof_right, tof_front, path, path_length
    while True:
        follow_segment()

        found_left = False
        found_straight = False
        found_right = False
        front = tof_front.range()
        right = tof_right.range()
        left = tof_left.range()

        if front < 30 and right < 30 and left < 30:
            turn_around()
            break

        dir = select_turn(found_left, found_straight, found_right)

        turn(dir)

        path.append(dir)

        simplify_path()

        display_path()

    while True:
        motors.set_speeds(0, 0)
        play(">>a32")

        while not button_b.check():
            if get_ms() % 2000 < 1000:
                clear()
                print("Solved!")
                lcd_goto_xy(0, 1)
                print("Press B")
            else:
                display_path()
            time.sleep_ms(30)

        while button_b.check():
            pass
        time.sleep_ms(1000)

        for i in range(path_length):
            follow_segment()
            turn(path[i])

        follow_segment()

initialize()
maze_solve()

