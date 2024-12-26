import subprocess
import time
from datetime import datetime, timedelta
import threading
import librosa
import numpy as np
import soundfile as sf
import os
from pydub import AudioSegment
import signal
import matplotlib.pyplot as plt

# Ensure 'library' folder exists
LIBRARY_FOLDER = "library"
os.makedirs(LIBRARY_FOLDER, exist_ok=True)


def record(duration):
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename = f"{LIBRARY_FOLDER}/{timestamp}_sound.wav"

    # Remove existing file if exists
    if os.path.exists(filename):
        os.remove(filename)
        print(f"Removed existing file: {filename}")

    # Start recording using rtl_fm
    command = f"rtl_fm -f 145575000 -s 12500 -g 35 -p 1 -M fm | sox -t raw -r 12500 -e signed -b 16 -c 1 - -t wav -r 12500 -e signed -b 16 -c 1 {filename}"

    print(f"Recording started: {filename}")
    process = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)

    try:
        # Record for the specified duration
        time.sleep(duration)
    finally:
        # Stop recording and terminate process
        print("Stopping the recording process...")
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
            print("Recording process terminated successfully.")
        except Exception as e:
            print(f"Error while terminating process: {e}")
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            print("Recording process forcefully killed.")

        # Ensure device is ready for reuse
        subprocess.run("killall rtl_fm", shell=True, stderr=subprocess.DEVNULL)
        print(f"Recording stopped: {filename}")

    return filename


def record_until_next_interval():
    now = datetime.now()

    # Calculate time until the next 6-hour interval (00, 06, 12, 18)
    next_run = now.replace(minute=0, second=0, microsecond=0)
    while next_run.hour % 6 != 0:
        next_run += timedelta(hours=1)

    # Ensure next_run is in the future
    if next_run <= now:
        next_run += timedelta(hours=6)  # Move to the next interval

    duration_until_next = (next_run - now).total_seconds()

    print(f"Recording until next interval at {next_run.strftime('%Y-%m-%d %H:%M:%S')}...")
    recorded_file = record(duration=duration_until_next)

    # Process audio after initial recording
    process_audio(recorded_file)
    print(f"Initial recording and processing complete. Switching to 6-hour schedule.")



def remove_high_power_segments_chunked(input_audio, output_audio, threshold=13, buffer_length=73, chunk_duration=8000):
    sr = 12500  # Sample rate
    chunk_size = sr * chunk_duration  # Chunk size in samples
    filtered_chunks = []
    print("Processing audio in chunks...")

    # Stream audio in chunks using librosa
    stream = librosa.stream(input_audio, block_length=1, frame_length=chunk_size, hop_length=chunk_size)

    for chunk_index, y_chunk in enumerate(stream):
        print(f"Processing chunk {chunk_index + 1}")
        D = librosa.stft(y_chunk, n_fft=2048, hop_length=512)
        power_spectrogram = np.abs(D) ** 2
        mean_power = np.mean(power_spectrogram, axis=0)

        # Identify high-power segments
        mask = mean_power >= threshold

        # Expand buffer
        expanded_indices = set()
        for idx in np.nonzero(mask)[0]:
            for i in range(max(0, idx - buffer_length), min(len(mean_power), idx + buffer_length + 1)):
                expanded_indices.add(i)

        hop_length = 512
        chunk_filtered_data = []
        for idx in sorted(expanded_indices):
            start_idx = idx * hop_length
            end_idx = min((idx + 1) * hop_length, len(y_chunk))
            chunk_filtered_data.append(y_chunk[start_idx:end_idx])

        if chunk_filtered_data:
            filtered_chunks.append(np.concatenate(chunk_filtered_data))

    filtered_data = np.concatenate(filtered_chunks) if filtered_chunks else np.array([])

    # Save to wav
    sf.write(output_audio, filtered_data, sr)
    print(f"Filtered audio saved as: {output_audio}")

    # Convert to mp3
    mp3_output = output_audio.replace('.wav', '.mp3')
    sound = AudioSegment.from_wav(output_audio)
    sound.export(mp3_output, format="mp3")
    print(f"MP3 saved as: {mp3_output}")

    # Generate spectrogram
    generate_spectrogram(input_audio)


def generate_spectrogram(audio_file):
    

    # Define a chunk size (in samples), e.g., 10 seconds of audio
    chunk_duration = 10  # seconds
    chunk_size = 12500 * chunk_duration  # Assuming 22.05 kHz sample rate

    # Initialize arrays for mean power
    mean_power_over_time = []

    # Use librosa.stream to process in chunks (stream-based processing)
    stream = librosa.stream(audio_file, block_length=chunk_duration, frame_length=2048, hop_length=512)

    for y in stream:
        # Compute STFT on the chunk
        D = librosa.stft(y, n_fft=2048, hop_length=512)
        power_spectrogram = np.abs(D)**2

        # Calculate mean power across frequency bins for this chunk
        mean_power = np.mean(power_spectrogram, axis=0)
        mean_power_over_time.extend(mean_power)

    # Generate the plot
    plt.figure(figsize=(10, 6))
    plt.plot(mean_power_over_time)
    plt.xlabel('Time Frame')
    plt.ylabel('Mean Power')
    plt.title('Mean Power Spectrum (Streamed Processing)')

    # Save the plot as a JPG file in the same directory as the input file
    output_path = os.path.splitext(audio_file)[0] + "_power_spectrum.jpg"
    plt.savefig(output_path)
    plt.close()



def process_audio(file):
    output_audio = file.replace('_sound.wav', '_filtered.wav')
    remove_high_power_segments_chunked(file, output_audio)


def schedule_every_6h():
    now = datetime.now()
    next_run = now.replace(minute=0, second=0, microsecond=0)
    while next_run.hour % 6 != 0:
        next_run += timedelta(hours=1)

    print(f"First 6-hour job scheduled at {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

    while True:
        now = datetime.now()
        if now >= next_run:
            job()
            next_run += timedelta(hours=6)
            print(f"Next job scheduled at {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(1)


def job():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Job started at {now}")
    recorded_file = record(duration=21558)
    threading.Thread(target=process_audio, args=(recorded_file,)).start()


if __name__ == "__main__":
    record_until_next_interval()
    schedule_every_6h()
