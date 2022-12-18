import pyaudio
import wave
import os
import time

form_1 = pyaudio.paInt16 # 16-bit resolution
chans = 1 # 1 channel
samp_rate = 44100 # 44.1kHz sampling rate
chunk = 4096 #4096 # 2^12 samples for buffer
record_secs = 2 # seconds to record
dev_index = 1 # device index found by p.get_device_info_by_index(ii)


def captureAudio(iterative_data):
	start_time = time.time()

	audio = pyaudio.PyAudio() # create pyaudio instantiation

	filepath = '/home/pi/Desktop/%s/' % iterative_data[0] 

	if not os.path.exists(filepath):
		os.makedirs(filepath)
	wav_output_filename = '/home/pi/Desktop/%s/%s_%s_%s_%s_%s.wav' % (iterative_data[0],iterative_data[0],iterative_data[1],iterative_data[2],iterative_data[3],iterative_data[4]) # name of .wav file
	# create pyaudio stream
	stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                    input_device_index = dev_index,input = True, \
                    frames_per_buffer=chunk)
	frames = []

	# loop through stream and append audio chunks to frame array
	for ii in range(0,int((samp_rate/chunk)*record_secs)):
		data = stream.read(chunk)
		frames.append(data)

	# stop the stream, close it, and terminate the pyaudio instantiation
	stream.stop_stream()
	stream.close()
	audio.terminate()

	# save the audio frames as .wav file
	wavefile = wave.open(wav_output_filename,'wb')
	wavefile.setnchannels(chans)
	wavefile.setsampwidth(audio.get_sample_size(form_1))
	wavefile.setframerate(samp_rate)
	wavefile.writeframes(b''.join(frames))
	wavefile.close()
	print(time.time() - start_time)