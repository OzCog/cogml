
#include "sense/audio/AudioCap.hpp"

AudioCap::AudioCap(string dev)
{  
	this->device = dev;
	this->sample_rate = 16000;
	this->pcm_format = SND_PCM_FORMAT_S16_LE;
	frms = 16;
	
	setup();
}


void AudioCap::shutdown()
{
	is_running = false;
	usleep(10000);
	run->join();
	snd_pcm_drain(d_handle);
	snd_pcm_close(d_handle);
	free(buffer);
	printf("CLOSED AUDIO CAPTURE DOWN!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
}

void AudioCap::setup()
{
	 is_running = false;
	 //open device
	 ret = snd_pcm_open(&d_handle, device.c_str(), SND_PCM_STREAM_CAPTURE, 0);
	 if(ret < 0) {
	   fprintf(stderr, "ERROR: Unable to open PCM Device for Recording: %s\n",
		                snd_strerror(ret));
		exit(1);
	}

	snd_pcm_hw_params_alloca(&hw_params);
	snd_pcm_hw_params_any(d_handle, hw_params); // set default hardware params
	snd_pcm_hw_params_set_format(d_handle, hw_params, pcm_format); // set format
	snd_pcm_hw_params_set_channels(d_handle, hw_params, 1); // set channel
	snd_pcm_hw_params_set_rate_near(d_handle, hw_params, &sample_rate, &dir); //set sample rate
	snd_pcm_hw_params_set_period_size_near(d_handle, hw_params, &frms, &dir); //set period size

	ret = snd_pcm_hw_params(d_handle, hw_params);
	if(ret < 0) {
       fprintf(stderr, "Unable to set HW Params: %s\n", snd_strerror(ret));
		 exit(1);
	}

	size = frms * 2; // 2 bytes per sample
	buffer = malloc(size);
}

void AudioCap::set_callback(void(*f) (void* buf, uint32_t samples))
{
	this->cb_func = f;
}


void AudioCap::start()
{
	is_running = true;
	snd_pcm_prepare(d_handle);
	run = new thread(AudioCap::run_capture, this);
}


void AudioCap::pause()
{
	is_running = false;
	snd_pcm_drop(d_handle);
}


void AudioCap::run_capture(AudioCap *ac)
{
	int r;
	while(ac->is_running) {
		r = snd_pcm_readi(ac->d_handle, ac->buffer, ac->frms);
		if(r == -EPIPE) {
			fprintf(stderr, "Warning: Overrun!\n");
			snd_pcm_prepare(ac->d_handle);
		}
		else if(r < 0) {
			fprintf(stderr, "Error: Problem Reading: %s\n", snd_strerror(r));
		}
		else if(r != (int)ac->frms) {
			fprintf(stderr, "Warning: Short Read %d frames\n", r);
		}

		//call callback
		ac->cb_func(ac->buffer, r);
	}
}
