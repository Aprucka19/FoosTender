import pigpio

class Stepper:
    def __init__(self, enable, step, direction):
        self.position = -1
        self.ENABLE = enable
        self.STEP = step
        self.DIRECTION = direction
        self.pi = pigpio.pi()

        self.pi.set_mode(self.DIRECTION, pigpio.OUTPUT)
        self.pi.set_mode(self.STEP, pigpio.OUTPUT)
        self.pi.set_mode(self.ENABLE, pigpio.OUTPUT)
        self.pi.set_PWM_dutycycle(self.STEP, 0)  # 50% duty cycle

        self.pi.write(self.DIRECTION, 0)
        self.pi.write(self.ENABLE, 0)

    # def initialize(self):
    #     self.set_direction(0)  # Set direction to 0
    #     self.pi.set_PWM_frequency(self.step, 100)  # Set PWM frequency
    #     self.pi.set_PWM_dutycycle(self.step, 128)  # Set duty cycle

    #     self.enable_motor()  # Enable the stepper motor

    #     # Move until STOP pin goes high
    #     while self.pi.read(self.stop) == 0:
    #         pass  # Continue moving

    #     # Once STOP pin is high
    #     self.pi.set_PWM_dutycycle(self.step, 0)  # Set duty cycle to 0
    #     self.disable_motor()
    #     self.position = 0


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
        start_freq = 1000   # Starting frequency for the ramp
        max_freq = 20000    # Maximum frequency
        steps_per_inch = 228
        total_steps = int(abs(x) * steps_per_inch)  # Total steps to move

        # Assuming linear ramp-up and ramp-down
        #ramp_up_steps = max(total_steps // 6, 400)  # One-third for ramping up
        ramp_up_steps = min(400,total_steps//2)
        ramp_down_steps = ramp_up_steps    # Same for ramping down
        constant_steps = total_steps - ramp_up_steps - ramp_down_steps  # Remainder for constant speed

        # Create ramp profile


        # Ramp up frequency
        freq_increase_steps = ramp_up_steps // ((max_freq - start_freq) // (max_freq//6))
        ramp = []
        freq = start_freq
        while freq < max_freq:
            
            ramp.append([freq, freq_increase_steps])
            freq += (max_freq//6)  # Increase frequency in steps

        # Constant speed
        if constant_steps > 0:
            ramp.append([max_freq, constant_steps])

        # Ramp down frequency
        freq_decrease_steps = ramp_down_steps // ((max_freq - start_freq) // (max_freq//6))
        while freq > start_freq:
            freq -= (max_freq//6)  # Decrease frequency in steps
            ramp.append([freq, freq_decrease_steps])
        #ramp.append([0,0])
        print(ramp)
        # Call generate_ramp function with the ramp profile
        self.generate_ramp(ramp)


    def enable_motor(self):
        self.pi.write(self.ENABLE, 0)

    def disable_motor(self):
        self.pi.write(self.ENABLE, 1)

    def set_direction(self, direction):
        # Assuming 0 for one direction and 1 for the opposite
        self.pi.write(self.DIRECTION, direction)
    def cleanup(self):
        self.pi.set_PWM_dutycycle(self.STEP, 0)
        self.pi.write(self.DIRECTION, 0)
        self.pi.write(self.ENABLE, 1)
        self.pi.stop()

# Example usage
# pi = pigpio.pi()
# stepper = Stepper(enable_pin, step_pin, direction_pin, pi)
# stepper.enable_motor()
# stepper.set_direction(0)  # Set direction
# stepper.move(1)  # Move 1 inch
# stepper.disable_motor()