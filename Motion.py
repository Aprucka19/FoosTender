import pigpio



def generate_ramp(STEP, pi, ramp):
    """Generate ramp wave forms.
    ramp:  List of [Frequency, Steps]
    """
    pi.wave_clear()     # clear existing waves
    length = len(ramp)  # number of ramp levels
    wid = [-1] * length

    # Generate a wave per ramp level
    for i in range(length):
        frequency = ramp[i][0]
        micros = int(500000 / frequency)
        wf = []
        wf.append(pigpio.pulse(1 << STEP, 0, micros))  # pulse on
        wf.append(pigpio.pulse(0, 1 << STEP, micros))  # pulse off
        pi.wave_add_generic(wf)
        wid[i] = pi.wave_create()

    # Generate a chain of waves
    chain = []
    for i in range(length):
        steps = ramp[i][1]
        x = steps & 255
        y = steps >> 8
        chain += [255, 0, wid[i], 255, 1, x, y]

    pi.wave_chain(chain)  # Transmit chain.

def move(STEP,pi,x):
    start_freq = 1000   # Starting frequency for the ramp
    max_freq = 8000    # Maximum frequency
    steps_per_inch = 400
    total_steps = int(x * steps_per_inch)  # Total steps to move

    # Assuming linear ramp-up and ramp-down
    #ramp_up_steps = max(total_steps // 6, 400)  # One-third for ramping up
    ramp_up_steps = min(800,total_steps//2)
    ramp_down_steps = ramp_up_steps    # Same for ramping down
    constant_steps = total_steps - ramp_up_steps - ramp_down_steps  # Remainder for constant speed

    # Create ramp profile


    # Ramp up frequency
    freq_increase_steps = ramp_up_steps // ((max_freq - start_freq) // 1000)
    ramp = []
    freq = start_freq
    while freq < max_freq:
        
        ramp.append([freq, freq_increase_steps])
        freq += 1000  # Increase frequency in steps

    # Constant speed
    if constant_steps > 0:
        ramp.append([max_freq, constant_steps])

    # Ramp down frequency
    freq_decrease_steps = ramp_down_steps // ((max_freq - start_freq) // 1000)
    while freq > start_freq:
        freq -= 1000  # Decrease frequency in steps
        ramp.append([freq, freq_decrease_steps])
    #ramp.append([0,0])
    print(ramp)
    # Call generate_ramp function with the ramp profile
    generate_ramp(STEP, pi,ramp)
