import os
# import imageio.v2 as imageio
import imageio
from natsort import natsorted

png_dir = '/home/pi/Desktop/LDO_42STH48-2504AC_4.22.23/Oscilloscope_Plots/'
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
    '/home/pi/Desktop/LDO_42STH48-2504AC_4.22.23/LDO_42STH48-2504AC_5fps.gif', images, fps=5)
