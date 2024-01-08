import pigpio
import time
import queue
import threading
import math
#Constants:
steps_per_rotation = 3200 #this is the steps per rotation
start_freq = 1000
max_freq = 20000
steps_per_inch = steps_per_rotation//2.78333
steps_per_wave = 200
ramp_steps = 200
speedtable = [20000, 10000, 5000, 4000, 2500, 2000, 1250, 1000, 800, 625, 500, 400, 250, 200, 100, 50]
#speedtable = [10000, 5000, 2500, 2000, 1250, 1000, 625, 500, 400, 313, 250, 400, 250, 200, 125, 100, 50, 25]
def find_closest(lst, x):
    """
    Finds the value in lst that is closest to x.

    :param lst: List of numbers.
    :param x: Target number.
    :return: Value from lst closest to x.
    """
    return min(lst, key=lambda number: abs(number - x))

class Stepper:
    def __init__(self, enable, step, direction, stop, verbose=False,timing = False):
        #Define pins
        self.verbose = verbose
        self.ENABLE = enable
        self.STEP = step
        self.DIRECTION = direction
        self.STOP = stop
        

        #timing
        self.timing = timing
        self.timer = 0
        self.count = 0


        #Initialize pigpio
        self.pi = pigpio.pi()

        #Initialize switch
        self.pi.set_mode(self.STOP, pigpio.INPUT)
        #self.pi.set_pull_up_down(self.STOP, pigpio.PUD_DOWN)
        #Cant move till initialized
        self.position = -1

        #Initialize outputs
        self.pi.set_mode(self.DIRECTION, pigpio.OUTPUT)
        self.pi.set_mode(self.STEP, pigpio.OUTPUT)
        self.pi.set_mode(self.ENABLE, pigpio.OUTPUT)

        #Step OFF standard
        self.pi.set_PWM_dutycycle(self.STEP, 0)  # 50% duty cycle
        self.disable_motor()


        #Movement state stores the direction and final frequency of the last sent wave
        self.currdirec = 0
        self.lastfreq = 0

        # Initialize a lock for thread-safe operations
        self.queue_lock = threading.Lock()

        # Initialize queue for ramp profiles
        self.ramp_queue = queue.Queue()
        
        # Start the generate_ramp thread
        self.ramp_thread = threading.Thread(target=self.generate_ramp, daemon=True)
        self.ramp_thread.start()



    def initialize(self):
        if (self.verbose):
            print("initializing")
        if(self.pi.read(self.STOP) == 1):
            if (self.verbose):print("in loop")
            self.set_direction(0)  # Set direction to 1
            self.pi.set_PWM_frequency(self.STEP, steps_per_rotation)  # Set PWM frequency
            self.pi.set_PWM_dutycycle(self.STEP, 128)  # Set duty cycle

            self.enable_motor()  # Enable the stepper motor

            # Move until STOP pin goes high
            state = self.pi.read(self.STOP)
            ctr = 0
            while ctr < 5:
                state = self.pi.read(self.STOP)
                #print(state)
                if state == 0:
                    ctr += 1
                else:
                    ctr = 0
                pass  # Continue moving
            self.pi.set_PWM_dutycycle(self.STEP, 0)  # Set duty cycle

            # Once STOP pin is high
            #self.pi.set_PWM_dutycycle(self.STEP, 0)  # Set duty cycle to 0
        self.enable_motor()
        self.position = 0


    def generate_ramp(self):
        while True:
            if not self.ramp_queue.empty() and not self.pi.wave_tx_busy():
                with self.queue_lock:
                    if(self.timing):
                        start = time.time()
                        self.count += 1
                    move = self.ramp_queue.get()
                    ramp = move[0]
                    loc = move[1]
                    self.pi.write(self.DIRECTION, move[2])
                    self.currdirec = move[2]
                    self.lastfreq = ramp[-1][0]
                    if (self.verbose):print("Ramp generating")
                    if (self.verbose):print(move)
                    if (self.verbose):print(f"start position: {self.position}, destination {loc}")
                    self.position = loc
                    """Generate ramp wave forms."""
                    self.pi.wave_clear()  # clear existing waves
                    length = len(ramp)  # number of ramp levels
                    wid = [-1] * length

                    # Generate a wave per ramp level
                    for i in range(length):
                        frequency = ramp[i][0]
                        micros = int(500000 / frequency)
                        wf = []
                        wf.append(pigpio.pulse(1 << self.STEP, 0, micros))  # pulse on
                        wf.append(pigpio.pulse(0, 1 << self.STEP, micros))  # pulse off
                        self.pi.wave_add_generic(wf)
                        wid[i] = self.pi.wave_create()

                    # Generate a chain of waves
                    chain = []
                    for i in range(length):
                        steps = ramp[i][1]
                        x = steps & 255
                        y = steps >> 8
                        chain += [255, 0, wid[i], 255, 1, x, y]

                    self.pi.wave_chain(chain)  # Transmit chain.
                    self.ramp_queue.task_done()
                    if(self.timing):
                        self.timer += time.time()-start


    def calculate_ramp(self, loc):
        x = loc - self.position
        if (self.verbose):print(f"Position: {self.position}")
        if (self.verbose):print(f"Location requested: {loc}")
        #print(self.position)
        #print(x)
        if(x == 0):
            return
        if(x > 0):
            direc = 1
            #self.pi.write(self.DIRECTION,1)
        else:
            direc = 0
            #self.pi.write(self.DIRECTION,0)

        total_steps = int(abs(x) * steps_per_inch)  # Total steps to move
        #print(f"total steps: {total_steps}")

        # Assuming linear ramp-up and ramp-down
        #ramp_up_steps = max(total_steps // 6, 400)  # One-third for ramping up
        ramp_up_steps = min(steps_per_rotation // 8,total_steps//2)
        ramp_down_steps = ramp_up_steps    # Same for ramping down
        constant_steps = total_steps - ramp_up_steps - ramp_down_steps  # Remainder for constant speed

        # Create ramp profile


        # Ramp up frequency
        freq_increase_steps = ramp_up_steps // 5
        ramp = []
        freq = start_freq
        ctr = 0
        while ctr < 5:
            
            ramp.append([find_closest(speedtable, freq), freq_increase_steps])
            freq += ((max_freq-start_freq)//5)  # Increase frequency in steps
            ctr += 1

        # Constant speed
        if constant_steps > 0:
            ramp.append([max_freq, constant_steps])

        # Ramp down frequency
        freq_decrease_steps = ramp_down_steps // 5
        ctr = 0
        while ctr < 5:
            freq -= ((max_freq-start_freq)//5)  # Decrease frequency in steps
            ramp.append([find_closest(speedtable, freq), freq_decrease_steps])
            ctr += 1
        #ramp.append([0,0])
        move = (ramp,loc,direc)
        #print(move)
        self.ramp_queue.put(move)
        # Call generate_ramp function with the ramp profile
        #self.enable_motor()
    
    def calculate_ramp2(self, loc):
        x = loc - self.position
        loc = self.position
        if (self.verbose):print(f"Position: {self.position}")
        if (self.verbose):print(f"Location requested: {loc}")
        if(x == 0):
            return
        if(x > 0):
            direc = 1
        else:
            direc = 0
        total_steps = int(abs(x) * steps_per_inch)  # Total steps to move
        decel_flag = 0 #Decel flag set to 1 if we were moving in the wrong direction and need to turn around
        ##CONSTANTS
        accel_ramp = [[1000, 20], [2500, 30], [5000, 50], [10000, 90], [20000, 10]]
        decel_ramp = [[20000, 10], [10000, 90], [5000, 50], [2500, 30], [1000, 20]]
        accel_dist = 200/steps_per_inch



        #Moving the other direction
        if (self.lastfreq > 1000 and self.currdirec != direc):
            ### TODO: If needed, break the ramp into multiple waves
            #ramp_amount = (maxfreq - self.lastfreq)/maxfreq

            #How many waves are needed to decelerate
            #wavecount = (ramp_amount * ramp_steps)/steps_per_wave
            if(self.currdirec):
                loc = accel_dist + loc
            else:
                loc = loc - accel_dist
            move = (decel_ramp, loc, self.currdirec)
            self.ramp_queue.put(move)
            total_steps = total_steps + 200
            decel_flag = 1
        
        #Accelerating from stop
        if (self.lastfreq <= 1000 or decel_flag == 1):
            if(direc):
                loc = accel_dist + loc
            else:
                loc = loc - accel_dist
            move = (accel_ramp, loc, direc)
            self.ramp_queue.put(move)
            total_steps = total_steps - 200

        full_speed_steps = total_steps - 200
        motionwaves = math.ceil((full_speed_steps)/200)

        for i in range(motionwaves):
            steps = min(full_speed_steps, 200)
            distance = steps / steps_per_inch
            if(direc):
                loc = distance + loc
            else:
                loc = loc - distance
            move = ([[20000, steps]], loc, direc)
            self.ramp_queue.put(move)
            full_speed_steps = full_speed_steps - steps
        
        if(direc):
            loc = accel_dist + loc
        else:
            loc = loc - accel_dist
        move = (decel_ramp, loc, direc)
        self.ramp_queue.put(move)






    def move(self, loc):
        # Acquire the lock before modifying the queue
        if(self.position == -1):
            print("You must initialize the position of the stepper first")
        else:
            with self.queue_lock:
                # Clear the queue
                while not self.ramp_queue.empty():
                    try:
                        self.ramp_queue.get_nowait()
                        self.ramp_queue.task_done()
                    except queue.Empty:
                        break
                if(self.position == -1):
                    print("You must initialize the position of the stepper first")
                else:
                    if(loc > 7 or loc < 0):
                        print("location out of bounds")
                        return
                    if(abs(self.position - loc) < .35):
                        return
                    # Add the new ramp profile to the queue
                    self.calculate_ramp2(loc)
                


    def run_wave(self):
        """
        Generates a wave at 8000 Hz on a given GPIO pin and sends it once.

        :param pi: Instance of pigpio.pi()
        :param gpio_pin: GPIO pin number to output the waveform
        """
        frequency = 4000  # 8000 Hz
        cycle_time = int(1e6 / frequency)  # Total time for one cycle in microseconds
        on_time = cycle_time // 2  # 50% duty cycle
        off_time = cycle_time - on_time

        # Create a waveform
        waveform = []
        for _ in range(1000):  # Create 1000 cycles
            waveform.append(pigpio.pulse(1 << self.STEP, 0, on_time))
            waveform.append(pigpio.pulse(0, 1 << self.STEP, off_time))

        # Add and send the waveform
        self.pi.wave_add_generic(waveform)
        wave_id = self.pi.wave_create()
        self.pi.wave_send_once(wave_id)

        # Wait for the wave to be sent
        while self.pi.wave_tx_busy():
            time.sleep(0.001)

        # Delete the waveform
        self.pi.wave_delete(wave_id)

    
    def enable_motor(self):
        self.pi.write(self.ENABLE, 0)

    def disable_motor(self):
        self.pi.write(self.ENABLE, 1)

    def set_direction(self, direction):
        # Assuming 0 for one direction and 1 for the opposite
        self.pi.write(self.DIRECTION, direction)
    def change_direction(self):
        direc = self.pi.read(self.DIRECTION)
        self.pi.write(self.DIRECTION, abs(direc - 1))
    
    def cleanup(self):
        self.pi.set_PWM_dutycycle(self.STEP, 0)
        self.pi.write(self.DIRECTION, 0)
        self.pi.write(self.ENABLE, 1)
        self.pi.stop()
        if(self.timing):
            print(f"Generate ramp time value: {self.timer}")
            print(f"Generate ramp average fps: {self.count/self.timer}")

    def is_busy(self):
        return self.pi.wave_tx_busy()





# Example usage
# pi = pigpio.pi()
# stepper = Stepper(enable_pin, step_pin, direction_pin, pi)
# stepper.enable_motor()
# stepper.set_direction(0)  # Set direction
# stepper.move(1)  # Move 1 inch
# stepper.disable_motor()


