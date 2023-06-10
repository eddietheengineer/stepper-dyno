import os
import numpy as np
import pandas as pd
from dataclasses import fields


def writeheader(model_number, test_id, header):
    filepath = f'/home/pi/Desktop/{model_number}_{test_id}/'
    filename = f'{model_number}_{test_id}_Summary.csv'

    if not os.path.exists(filepath):
        os.makedirs(filepath)

    with open(f'{filepath}{filename}', "w+", encoding='UTF-8') as file:
        if os.stat(f'{filepath}{filename}').st_size == 0:
            file.write(str(header)[1:-1]+'\n')
    file.close()


def writedata(model_number, test_id, data):
    filepath = f'/home/pi/Desktop/{model_number}_{test_id}/'
    filename = f'{model_number}_{test_id}_Summary.csv'
    with open(f'{filepath}{filename}', "a", encoding='UTF-8') as file:
        file.write(str(data)[1:-1]+'\n')
    file.close()


def writeoscilloscopedata(testiddata, raw):

    Model_Number = testiddata.stepper_model
    Test_ID = testiddata.test_id
    Test_Number = testiddata.test_counter
    Voltage = testiddata.test_voltage
    Microstep = testiddata.test_microstep
    Current = testiddata.test_current
    Speed = testiddata.test_speed

    filepath = f'/home/pi/Desktop/RawDataArchive/{Model_Number}_{Test_ID}/Oscilloscope_Data/'

    if not os.path.exists(filepath):
        os.makedirs(filepath)

    filename = f'{Model_Number}_{Test_ID}_{Test_Number}_{Voltage}V_{Microstep}ms_{Current}A_{Speed}mms'

    header = tuple(field.name for field in fields(raw))
    array = np.transpose(np.stack((raw.time_array, raw.voltin_array, raw.ampin_array,
                         raw.powerin_array, raw.voltout_array, raw.ampout_array, raw.powerout_array, raw.encoder_array, raw.encoder_ref_array), axis=0))

    DF = pd.DataFrame(data=array, columns=header)
    DF.to_parquet(f'/{filepath}{filename}.parquet')