import os
# import imageio.v2 as imageio
import imageio
from natsort import natsorted

def generategif(ID):
    png_dir = f'/home/pi/Desktop/LDO_42STH48-2504AC_{ID}/Oscilloscope_Plots_Out/'
    images = []
    list_png = natsorted(os.listdir(png_dir))
    # print(list_png)
    for file_name in list_png:
        if file_name.endswith('.png'):
            file_path = os.path.join(png_dir, file_name)
            images.append(imageio.imread(file_path))

    # Make it pause at the end so that the viewers can ponder
    # for _ in range(10):
    #    images.append(imageio.imread(file_path))

    imageio.mimsave(
        f'/home/pi/Desktop/LDO_42STH48-2504AC_{ID}/LDO_42STH48-2504AC_{ID}.gif', images, duration=200, loop=3)

#generategif('5.27d')