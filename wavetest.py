import time

import pigpio

START_DELAY=5000
FINAL_DELAY=100
STEP=100

GPIO=18

pi = pigpio.pi()

pi.set_mode(GPIO, pigpio.OUTPUT)

pi.wave_clear()

# short waveform to repeat final speed

wf=[]

wf.append(pigpio.pulse(1<<GPIO, 0,       FINAL_DELAY))
wf.append(pigpio.pulse(0,       1<<GPIO, FINAL_DELAY))

pi.wave_add_generic(wf)

wid0 = pi.wave_create()

# build initial ramp

wf=[]

for delay in range(START_DELAY, FINAL_DELAY, -STEP):
   wf.append(pigpio.pulse(1<<GPIO, 0,       delay))
   wf.append(pigpio.pulse(0,       1<<GPIO, delay))

pi.wave_add_generic(wf)

# add lots of pulses at final rate to give timing lee-way

wf=[]

# add after existing pulses

offset = pi.wave_get_micros()

print("ramp is {} micros".format(offset))

wf.append(pigpio.pulse(0, 0, offset))

for i in range(2000):
   wf.append(pigpio.pulse(1<<GPIO, 0,       FINAL_DELAY))
   wf.append(pigpio.pulse(0,       1<<GPIO, FINAL_DELAY))

pi.wave_add_generic(wf)

wid1 = pi.wave_create()

# send ramp, stop when final rate reached

pi.wave_send_once(wid1)

time.sleep(float(offset)/1000000.0) # make sure it's a float

pi.wave_send_repeat(wid0)

time.sleep(1)

pi.wave_tx_stop()

pi.stop()