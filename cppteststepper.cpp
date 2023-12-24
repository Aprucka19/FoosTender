#include <iostream>
#include <pigpio.h>

#define DIR 13
#define STEP 18
#define ENA 26

int main() {
    if (gpioInitialise() < 0) {
        std::cerr << "pigpio initialisation failed\n";
        return 1;
    }

    gpioSetMode(DIR, PI_OUTPUT);
    gpioSetMode(STEP, PI_OUTPUT);
    gpioSetMode(ENA, PI_OUTPUT);

    int freq = 500;
    gpioHardwarePWM(STEP, freq, 500000); // 50% duty cycle

    gpioWrite(DIR, 0);
    gpioWrite(ENA, 0);

    char command;
    int newFreq;
    while (true) {
        std::cout << "Enter 'u' to update frequency, or 'q' to quit: ";
        std::cin >> command;

        if (command == 'u') {
            std::cout << "Enter the new frequency: ";
            std::cin >> newFreq;
            freq = newFreq;

            gpioHardwarePWM(STEP, freq, 500000);
            std::cout << "Frequency set to: " << freq << std::endl;
        } else if (command == 'q') {
            break;
        } else {
            std::cout << "Invalid command." << std::endl;
        }
    }

    gpioHardwarePWM(STEP, 0, 500000);
    gpioWrite(DIR, 0);
    gpioWrite(ENA, 1);

    gpioTerminate();
    return 0;
}
