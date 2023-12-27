from time import sleep
import pigpio
from Motion import move
from Stepper import Stepper
DIR = 13
STEP = 19
ENA = 26


step = Stepper(ENA, STEP, DIR)

try:
    while True:
        # Prompt user for input
        user_input = input("Enter distance to move (in inches) or type 'exit' to quit: ")

        # Check if user wants to exit
        if user_input.lower() == 'exit':
            break

        # Convert input to a number and call move_to
        try:
            distance = float(user_input)
            step.move(distance)
        except ValueError:
            print("Invalid input. Please enter a valid number.")
           



except KeyboardInterrupt:
    print("\nCtrl-C pressed.")
finally:
    print("Stopping PIGPIO and exiting...")
    step.cleanup()



