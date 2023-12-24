from time import sleep
from rpi_hardware_pwm import HardwarePWM

# Define constants
DIR = 19
STEP = 13  # Assuming this is the PWM pin
ENA = 26

# Initialize the PWM on channel 0 (GPIO 18 by default)
pwm = HardwarePWM(pwm_channel=0, hz=500)

# Other GPIO setup code remains the same
# ...

# Start the PWM with a full duty cycle
pwm.start(50)

try:
    while True:
        command = input("Enter 'u' to increase, 'd' to decrease frequency, or 'q' to quit: ").strip().lower()
        if command == 'u':
            pwm.change_frequency(pwm.get_frequency() * 1.1)
            print("Frequency increased to: ", pwm.get_frequency())
        elif command == 'd':
            pwm.change_frequency(pwm.get_frequency() * 0.9)
            print("Frequency decreased to: ", pwm.get_frequency())
        elif command == 'q':
            break
        else:
            print("Invalid command.")

except KeyboardInterrupt:
    print("\nCtrl-C pressed. Stopping PWM and exiting...")
finally:
    pwm.stop()
    # Additional cleanup code for other GPIOs if needed
    # ...
