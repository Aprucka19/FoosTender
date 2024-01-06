from time import sleep
import pigpio
from Stepper import Stepper
DIR = 13
STEP = 18
ENA = 26
STOP = 21


step = Stepper(ENA, STEP, DIR, STOP)
step.initialize()
try:
    while True:
        # Prompt user for input
        user_input = input("Enter distance to move (in inches) or type 'q' to quit: ")

        # Check if user wants to exit
        if user_input.lower() == 'q':
            break
        if user_input.lower() == 'w':
            step.run_wave()
        if user_input.lower() == 'r':
            step.change_direction()

        # Convert input to a number and call move_to
        try:
            distance = float(user_input)
            step.move(distance)
        except ValueError:
            print("Invalid input. Please enter a valid number.")
           



except KeyboardInterrupt:
    print("\nCtrl-C pressed.")
    step.cleanup()
finally:
    print("Stopping PIGPIO and exiting...")
    step.cleanup()



