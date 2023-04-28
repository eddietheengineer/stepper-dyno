import os


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
