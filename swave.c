#define GPIO 18

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <pigpio.h>

/*
gcc -o swave swave.c -lpigpio -lrt -lpthread
sudo ./swave
*/

/* generates a simple stepper ramp. */
int ramp(
   unsigned start_delay,
   unsigned final_delay,
   unsigned step,
   unsigned count)
{
   int i, j, p, npulses, np, wid=-1;
   rawWaveInfo_t waveInfo;
   rawCbs_t *cbp1, *cbp2;
   gpioPulse_t *pulses;

   npulses = (((start_delay-final_delay) / step) + 1 ) * count * 2;
   npulses += 10;

   pulses = (gpioPulse_t*) malloc(npulses*sizeof(gpioPulse_t));

   if (pulses)
   {
      p = 0;

      for (i=start_delay; i>=final_delay; i-=step)
      {
         for (j=0; j<count; j++)
         {
            pulses[p].gpioOn = (1<<GPIO);
            pulses[p].gpioOff = 0;
            pulses[p].usDelay = i;
            p++;

            pulses[p].gpioOn = 0;
            pulses[p].gpioOff = (1<<GPIO);
            pulses[p].usDelay = i;
            p++;
         }
      }

       /* dummy last pulse, will never be executed */

      pulses[p].gpioOn = (1<<GPIO);
      pulses[p].gpioOff = 0;
      pulses[p].usDelay = i;
      p++;

      np = gpioWaveAddGeneric(p, pulses);

      wid = gpioWaveCreate();

      if (wid >= 0)
      {
         waveInfo = rawWaveInfo(wid);
         /*
         -7 gpio off         next-> -6
         -6 delay final step next-> -5
         -5 gpio on          next-> -4
         -4 delay final step next-> -3
         -3 gpio off         next-> -2
         -2 delay final step next-> -1
         -1 dummy gpio on    next->  0
          0 dummy delay      next-> first CB
         */
         /* patch -2 to point back to -5 */
         cbp1 = rawWaveCBAdr(waveInfo.topCB-2);
         cbp2 = rawWaveCBAdr(waveInfo.topCB-6);
         cbp1->next = cbp2->next;
      }
      free(pulses);
   }
   return wid;
}

#define START_DELAY 5000
#define FINAL_DELAY 100
#define STEP_DELAY  100
#define STEP_COUNT 5

int main(int argc, char *argv[])
{
   int arg, pos = 0, np, wid, steps;

   if (gpioInitialise() < 0) return 1;

   printf("start piscope\n");

   getchar();

   gpioSetMode(GPIO, PI_OUTPUT);

   wid = ramp(START_DELAY, FINAL_DELAY, STEP_DELAY, STEP_COUNT);

   if (wid >= 0)
   {
      gpioWaveTxSend(wid, PI_WAVE_MODE_ONE_SHOT);

      time_sleep(1.0);
   }

   printf("stop piscope\n");

   getchar();

   gpioTerminate();

}