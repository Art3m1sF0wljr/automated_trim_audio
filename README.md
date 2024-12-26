app.py
records audio from sdr and saves into library/ directory
at the 00-06-12-18 h mark interrupts the recording and starts another one
with the previous recording it does the trimming (in a new thread)
the trimming is done by cutting the parts of the wav that have modulus of the signal less than a threshold
the trimming takes some buffer signals before and after the part with the threshold, to avoid cutting in the middle of the word
the trimmed wav is saved as mp3
in the same thread, after the conversion to mp3, from the original recording a spectrogram image is generated, with the same proceeding as the trimming
the original wav is big generally, so it gets processed in smaller chunks i.e. there isnt a discrete fourier transform on the whole wav, 
just on few seconds to minutes of the wav at the time, adjustable

execute.sh 
it contains the virtual enviroment activation and the libraries to be imported

spectro.py
generates only the spectrogram of the input file, is alr implemented in app.py
