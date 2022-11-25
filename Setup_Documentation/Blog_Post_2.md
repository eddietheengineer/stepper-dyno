Hello everyone! 

It's time for another update. The last few weeks I've put a ton of time into this, and most of it's due to me gradually learning python which has been slow but rewarding.

I finally 3d printed the structural parts for the dyno! You can see the BLDC motor on the left, which for now isn't really doing much, but in the future will be a programmable load for the stepper motor. I'm still not sure how that will work--the Texas Instruments programs are pretty much Windows/x86 only, and I'll need to interface with the control board via the Raspberry Pi/USB. That's a problem for future me :) 

![img](https://cdn.discordapp.com/attachments/662800325195071491/1041405314458714122/IMG_6895.jpg)

In the center, the stepper motor is mounted on a freely rotating pivot. An extrusion extends from the center of the stepper axis to the right, which applies a force on the 1kg load cell at a specific distance from the stepper axis. Here we can measure the torque of the stepper motor. This part is working fairly well--the last two columns here show the torque output from the stepper motor (force * moment arm). The last column, Motor_Power, is the mechanical power in watts that the stepper motor is actually outputting (Torque * Speed). The numbers in this calculation below for power weren't quite correct, but at least it's partially working!

![img](https://cdn.discordapp.com/attachments/662800325195071491/1043708464016400444/Screen_Shot_2022-11-19_at_9.04.26_PM.png)

You can also see here where the torque dropped to 0 at 800mm/s! This, combined with future encoder feedback, will allow us to detect when the motor stalls, which will allow us to skip test points that the motor can't hit. One more note--right now the Torque output is only due to the phases of the BLDC motor being tied together--so the BLDC motor isn't actively trying to hold a specified torque during each test. That will have to come at a later date!

I did run into some issues with the Bitscope USB oscilloscope interfering with my Riden power supply, so with $$$ and a lot of PyVisa assistance from Thebrakshow, I have a new Siglent SDS1104X-E oscilloscope integrated into the stepper tester. Instead of 12000 samples per plot, we can capture over 500,000! Part of the fun has been adjusting the scope configuration per test point in order to maximize the resolution. 

I started out with the voltage and current on channels 1 and 2, but will be changing them to channels 1 and 3 since the SDS1104X-E can maintain full sample rate on two channels as long as they are split between 1/2 and 3/4! The plot below is still with 1/2 the resolution at higher speed points. 

![721ypi](/Users/joshualongenecker/Github/jdlongenecker/documentation/vibration_data/data/images/721ypi.gif)

The other component of this that is important is timing! Since we are looking at potentially hundreds of thousands of test points, the time for each point is critical. I spent some time working on threading the data capture portion of each sequence, since capturing data sequentially takes a long time! Here's an example of 5 test points without threading:

![img](https://cdn.discordapp.com/attachments/662800325195071491/1045379089558671451/Screen_Shot_2022-11-24_at_11.42.38_AM.png)

And here's the same test points, with threading:

![img](https://cdn.discordapp.com/attachments/662800325195071491/1045386828481568808/Screen_Shot_2022-11-24_at_12.13.55_PM.png)

Since these tests, the cycle time has increased since I'm capturing more data with the oscilloscope (10k to ~100k-1M samples), but this is a huge improvement nonetheless. 

What's next? 

Once I have the oscilloscope sampling updated, next step will be to add the encoder feedback! This will be the most reliable way to determine when the motor has stalled. Then, I want to work some more on data processing. With even the current setup, so much data is being generated that having graphs auto generated per data point (oscilloscope plots) as well as summaries per motor (current/power vs. speed and voltage) will be critical to save time. At that point, I'll likely try and do some bigger test sweeps and present the data I have! 

The final big piece is still the BLDC torque conttrol--that will be another big effort :) but that's for another day.