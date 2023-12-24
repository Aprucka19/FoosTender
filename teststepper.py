from time import sleep
import pigpio

DIR = 13
STEP = 19
ENA = 26

pi = pigpio.pi()

pi.set_mode(DIR, pigpio.OUTPUT)
pi.set_mode(STEP, pigpio.OUTPUT)
pi.set_mode(ENA, pigpio.OUTPUT)

freq = 500
pi.hardware_PWM(STEP, freq, 500000)  # 50% duty cycle

pi.write(DIR, 0)
pi.write(ENA, 0)

try:
    while True:
        command = input("Enter 'u' to increase, 'd' to decrease frequency, or 'q' to quit: ").strip().lower()
        if command == 'u':
            freq *= 1.1
            pi.hardware_PWM(STEP, int(freq), 500000)
            print("Frequency increased to: ", freq)
        elif command == 'd':
            freq *= 0.9
            pi.hardware_PWM(STEP, int(freq), 500000)
            print("Frequency decreased to: ", freq)
        elif command == 'q':
            break
        else:
            print("Invalid command.")



except KeyboardInterrupt:
    print("\nCtrl-C pressed. Stopping PIGPIO and exiting...")
finally:
    pi.hardware_PWM(STEP, 0, 500000)
    pi.write(DIR, 0)
    pi.write(ENA, 1)
    pi.stop()
