import os
import numpy as np
import pandas as pd


def writeheader(model_number, test_id, label):
    filepath = f'/home/pi/Desktop/{model_number}_{test_id}/'
    csvfilepath = f'/home/pi/Desktop/{model_number}_{test_id}/{model_number}_Summary.csv'

    if not os.path.exists(filepath):
        os.makedirs(filepath)

    with open(csvfilepath, "w+", encoding='UTF-8') as file:
        if os.stat(csvfilepath).st_size == 0:
            file.write(str(label)[1:-1]+'\n')
    file.close()


def writedata(model_number, test_id, data):
    csvfilepath = f'/home/pi/Desktop/{model_number}_{test_id}/{model_number}_Summary.csv'
    with open(csvfilepath, "a", encoding='UTF-8') as file:
        file.write(str(data)[1:-1]+'\n')
    file.close()


def writeoscilloscopedata(output_data, index_data, oscilloscope_data):

    Model_Number = output_data[index_data.index('model_number')]
    Test_ID = output_data[index_data.index('test_id')]
    Test_Number = output_data[index_data.index('test_counter')]
    Voltage = output_data[index_data.index('voltage_setting')]
    Microstep = output_data[index_data.index('microstep')]
    Current = output_data[index_data.index('tmc_current')]
    Speed = output_data[index_data.index('speed')]

    filepath = f'/home/pi/Desktop/{Model_Number}_{Test_ID}/Oscilloscope_Data/'

    if not os.path.exists(filepath):
        os.makedirs(filepath)

    csvfilepath = f'/home/pi/Desktop/{Model_Number}_{Test_ID}/Oscilloscope_Data/{Model_Number}_{Test_ID}_{Test_Number}_{Voltage}V_{Microstep}ms_{Current}A_{Speed}mms.csv'
    oscilloscope_data_transposed = np.transpose(oscilloscope_data)

    DF = pd.DataFrame(oscilloscope_data_transposed, columns=['Time (ms)', 'Voltage (V)', 'Current (A)', 'Power (W)'])
    DF.round({'Time (ms)':8, 'Voltage (V)':4, 'Current (A)':4, 'Power (W)':4})
    DF.to_csv(csvfilepath)

