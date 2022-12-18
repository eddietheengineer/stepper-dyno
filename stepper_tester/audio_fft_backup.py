import pyaudio
import matplotlib.pyplot as plt
import numpy as np
import time

# form_1 = pyaudio.paInt16 # 16-bit resolution
# chans = 1 # 1 channel
# samp_rate = 44100 # 44.1kHz sampling rate
# chunk = 8192 # 2^12 samples for buffer
# dev_index = 1 # device index found by p.get_device_info_by_index(ii)
# 
# audio = pyaudio.PyAudio() # create pyaudio instantiation
# 
# # create pyaudio stream
# stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
#                     input_device_index = dev_index,input = True, \
#                     frames_per_buffer=chunk)
# 
# # record data chunk 
# stream.start_stream()
# data = np.fromstring(stream.read(chunk),dtype=np.int16)
# stream.stop_stream()

#newtry
form_1 = pyaudio.paInt16 # 16-bit resolution
chans = 1 # 1 channel
samp_rate = 44100 # 44.1kHz sampling rate
chunk = 4096 #4096 # 2^12 samples for buffer
record_secs = 2 # seconds to record
dev_index = 1 # device index found by p.get_device_info_by_index(ii)


audio = pyaudio.PyAudio() # create pyaudio instantiation

#filepath = '/home/pi/Desktop/Test/' % iterative_data[0] 

#if not os.path.exists(filepath):
#	os.makedirs(filepath)
#wav_output_filename = '/home/pi/Desktop/Test.wav' % (iterative_data[0],iterative_data[0],iterative_data[1],iterative_data[2],iterative_data[3],iterative_data[4]) # name of .wav file
# create pyaudio stream
stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
				input_device_index = dev_index,input = True, \
				frames_per_buffer=chunk)
frames = []

# loop through stream and append audio chunks to frame array
for ii in range(0,int((samp_rate/chunk)*record_secs)):
	data = np.fromstring(stream.read(chunk),dtype=np.int16)
	frames.append(data)

# stop the stream, close it, and terminate the pyaudio instantiation
stream.stop_stream()
stream.close()
audio.terminate()

# mic sensitivity correction and bit conversion
mic_sens_dBV = -47.0 # mic sensitivity in dBV + any gain
mic_sens_corr = np.power(10.0,mic_sens_dBV/20.0) # calculate mic sensitivity conversion factor

# (USB=5V, so 15 bits are used (the 16th for negatives)) and the manufacturer microphone sensitivity corrections
data = ((data/np.power(2.0,15))*5.25)*(mic_sens_corr) 

# compute FFT parameters
f_vec = samp_rate*np.arange(chunk/2)/chunk # frequency vector based on window size and sample rate
mic_low_freq = 20 # low frequency response of the mic (mine in this case is 100 Hz)
low_freq_loc = np.argmin(np.abs(f_vec-mic_low_freq))
fft_data = (np.abs(np.fft.fft(data))[0:int(np.floor(chunk/2))])/chunk
fft_data[1:] = 2*fft_data[1:]

max_loc = np.argmax(fft_data[low_freq_loc:])+low_freq_loc

rms_audio = np.sqrt(np.mean(data**2))
db = 20 * np.log10(rms_audio * 20000000)

# A-weighting function and application
f_vec = f_vec[1:]
fft_data = fft_data[1:]
R_a = ((12194.0**2)*np.power(f_vec,4))/(((np.power(f_vec,2)+20.6**2)*np.sqrt((np.power(f_vec,2)+107.7**2)*(np.power(f_vec,2)+737.9**2))*(np.power(f_vec,2)+12194.0**2)))
a_weight_data_f = (20*np.log10(R_a)+2.0)+(20*np.log10(fft_data/0.00002))
a_weight_sum = np.sum(np.power(10,a_weight_data_f/20)*0.00002)
dBa = 20*np.log10(a_weight_sum/0.00002)
print('dB = %0.2f, dBA = %0.2f' % (db, dBa))

# plot
plt.style.use('ggplot')
plt.rcParams['font.size']=18
fig = plt.figure(figsize=(13,8))
ax = fig.add_subplot(111)
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

ax1.plot(f_vec,fft_data)
ax2.plot(f_vec,a_weight_data_f, 'blue')
#ax1.set_ylim([0,2*np.max(fft_data)])
ax1.set_xlim([100,22050])
ax1.set_ylim([0,0.00008])
ax2.set_ylim([-100,10])

plt.xlabel('Frequency [Hz]')
plt.ylabel('Amplitude [Pa]')
ax1.set_xscale('log')
plt.grid(True)

# max frequency resolution 
#plt.annotate(r'$\Delta f_{max}$: %2.1f Hz' % (samp_rate/(2*chunk)),xy=(0.7,0.92),\
#             xycoords='figure fraction')
plt.title('dB = %0.2f, dBa = %0.2f' % (db, dBa))

# annotate peak frequency
annot = ax.annotate('Freq: %2.1f'%(f_vec[max_loc]),xy=(f_vec[max_loc],fft_data[max_loc]),\
                    xycoords='data',xytext=(0,30),textcoords='offset points',\
                    arrowprops=dict(arrowstyle="->"),ha='center',va='bottom')
    
plt.savefig('fft_1kHz_signal.png',dpi=300,facecolor='#FCFCFC')
#plt.show()