import pigpio
import time
steps_per_rotation = 3200 #this is the steps per rotation
#speedtable = [20000, 10000, 5000, 4000, 2500, 2000, 1250, 1000, 800, 625, 500, 400, 250, 200, 100, 50]
speedtable = [10000, 5000, 2500, 2000, 1250, 1000, 625, 500, 400, 313, 250, 400, 250, 200, 125, 100, 50, 25]
def find_closest(lst, x):
    """
    Finds the value in lst that is closest to x.

    :param lst: List of numbers.
    :param x: Target number.
    :return: Value from lst closest to x.
    """
    return min(lst, key=lambda number: abs(number - x))

class Stepper:
    def __init__(self, enable, step, direction, stop):
        #Define pins
        self.ENABLE = enable
        self.STEP = step
        self.DIRECTION = direction
        self.STOP = stop
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



    def initialize(self):
        print("initializing")
        if(self.pi.read(self.STOP) == 1):
            print("in loop")
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


    def generate_ramp(self, ramp):
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
    def move(self,loc):
        if(self.position == -1):
            print("You must initialize the position of the stepper first")
        if (self.pi.wave_tx_busy()):
            #print("Wave is busy. Wait before sending another input.")
            return
        else:
            if(loc > 7 or loc < 0):
                print("location out of bounds")
                return
            x = loc - self.position
            self.position = loc
            #print(self.position)
            #print(x)
            if(x == 0):
                return
            if(x > 0):
                self.pi.write(self.DIRECTION,1)
            else:
                self.pi.write(self.DIRECTION,0)

            #freqlist = []
            start_freq = 100   # Starting frequency for the ramp
            max_freq = 2500    # Maximum frequency
            steps_per_inch = steps_per_rotation//2.78333
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
            print(ramp)
            # Call generate_ramp function with the ramp profile
            #self.enable_motor()
            self.generate_ramp(ramp)
            #self.disable_motor()


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

    def is_busy(self):
        return self.pi.wave_tx_busy()





# Example usage
# pi = pigpio.pi()
# stepper = Stepper(enable_pin, step_pin, direction_pin, pi)
# stepper.enable_motor()
# stepper.set_direction(0)  # Set direction
# stepper.move(1)  # Move 1 inch
# stepper.disable_motor()


