import sounddevice as sd
import os
from scipy.io.wavfile import write

samplingfrequency = 48000

def recordAudio(alldata, duration):
    Model_Number = alldata.id.stepper_model
    Test_ID = alldata.id.test_id
    Test_Number = alldata.id.test_counter
    Voltage = alldata.id.test_voltage
    Microstep = alldata.id.test_microstep
    Current = alldata.id.test_current
    Speed = alldata.id.test_speed

    filepath = f'/home/pi/Desktop/{Model_Number}_{Test_ID}/Audio_Recording/'

    if not os.path.exists(filepath):
        os.makedirs(filepath)
    
    myrecording = sd.rec(int(duration * samplingfrequency), samplerate=samplingfrequency, channels=2)
    sd.wait()

    filename = f'{Model_Number}_{Test_ID}_{Test_Number}_{Voltage}_{Microstep}_{Current}_{Speed}.wav'

    write(filename, samplingfrequency, myrecording)