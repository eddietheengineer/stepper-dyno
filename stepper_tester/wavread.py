import os
#import imageio.v2 as imageio
import imageio
from natsort import natsorted, ns
import audio_fft

png_dir = '/home/pi/Desktop/17HM19-2004S1_16ms/'
images = []
list_png = natsorted(os.listdir(png_dir))
#print(list_png)
for file_name in list_png:
    if file_name.endswith('.wav'):
        file_path = os.path.join(png_dir, file_name)
        audio_fft.processfile(png_dir, file_name)