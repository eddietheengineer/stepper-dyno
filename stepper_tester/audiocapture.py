import sounddevice as sd
import os
from scipy.io.wavfile import write

samplingfrequency = 48000

def recordAudio(testpoint, duration):
    complete = 0
    Model_Number = testpoint.stepper_model
    Test_ID = testpoint.test_id
    Test_Number = testpoint.test_counter
    Voltage = testpoint.test_voltage
    Microstep = testpoint.test_microstep
    Current = testpoint.test_current
    Speed = testpoint.test_speed

    filepath = f'/home/pi/Desktop/RawDataArchive/{Model_Number}_{Test_ID}/Audio_Recording/'

    if not os.path.exists(filepath):
        os.makedirs(filepath)
    
    myrecording = sd.rec(int(duration * samplingfrequency), samplerate=samplingfrequency, channels=2)
    sd.wait()

    filename = f'{Model_Number}_{Test_ID}_{Test_Number}_{Voltage}_{Microstep}_{Current}_{Speed}.wav'

    write(f'{filepath}{filename}', samplingfrequency, myrecording)
    complete = 1
    return complete