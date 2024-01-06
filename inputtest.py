import pigpio

# Start the pigpio daemon before running this script
# Use command: sudo pigpiod

# GPIO pin number to read
gpio_pin = 21

# Create an instance of the pigpio interface
pi = pigpio.pi()

# Read the state of the GPIO pin
pi.set_mode(gpio_pin, pigpio.INPUT)
#pi.set_pull_up_down(gpio_pin, pigpio.PUD_DOWN)

while(1):
    state = pi.read(gpio_pin)
    print(f"State of GPIO {gpio_pin}: {state}")

# Clean up
pi.stop()
