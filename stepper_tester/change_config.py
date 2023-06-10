
def updateMS(microstep):  # looping through the file
    line_idx = identifyLine('microsteps')
    with open("/home/pi/printer_data/config/printer.cfg", "r", encoding='UTF-8') as file:

        replaced_content = ""
        i = 0

        for line in file:
            line = line.strip()
        # replacing the text if the line number is reached
            if (i == line_idx):
                new_line = f'microsteps:{microstep}'
            else:
                new_line = line

            # concatenate the new string and add an end-line break
            replaced_content = replaced_content + new_line + "\n"

            # Increase loop counter
            i = i + 1

    # Open file in write mode
    with open("/home/pi/printer_data/config/printer.cfg", "w", encoding='UTF-8') as write_file:

        # overwriting the old file contents with the new/replaced content
        write_file.write(replaced_content)

    print(f'      Microsteps: {microstep}')

def update(microstep):  # looping through the file
    line_idx = identifyLine('microsteps')
    with open("/home/pi/printer_data/config/printer.cfg", "r", encoding='UTF-8') as file:

        replaced_content = ""
        i = 0

        for line in file:
            line = line.strip()
        # replacing the text if the line number is reached
            if (i == line_idx):
                new_line = f'microsteps:{microstep}'
            else:
                new_line = line

            # concatenate the new string and add an end-line break
            replaced_content = replaced_content + new_line + "\n"

            # Increase loop counter
            i = i + 1

    # Open file in write mode
    with open("/home/pi/printer_data/config/printer.cfg", "w", encoding='UTF-8') as write_file:

        # overwriting the old file contents with the new/replaced content
        write_file.write(replaced_content)

    print(f'      Microsteps: {microstep}')

def identifyLine(identifier):
    with open("/home/pi/printer_data/config/printer.cfg", "r", encoding='UTF-8') as file:
        lines = file.readlines()
        line_number = 0
        for row in lines:
            word = identifier
            if row.find(word) != -1:
                line_number = lines.index(row)
                break
        return line_number
