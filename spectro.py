import numpy as np
import librosa
import matplotlib.pyplot as plt
import os

def save_power_spectrum_as_jpg(audio):
    """
    Generate and save the mean power spectrum of an audio file as a JPG.

    Args:
    - file_path (str): Path to the input WAV file.

    Returns:
    - str: Path to the saved JPG file.
    """
    # Define a chunk size (in samples), e.g., 10 seconds of audio
    chunk_duration = 10  # seconds
    chunk_size = 12500 * chunk_duration  # Assuming 22.05 kHz sample rate

    # Initialize arrays for mean power
    mean_power_over_time = []

    # Use librosa.stream to process in chunks (stream-based processing)
    stream = librosa.stream(audio, block_length=chunk_duration, frame_length=2048, hop_length=512)

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
    output_path = os.path.splitext(audio)[0] + "_power_spectrum.jpg"
    plt.savefig(output_path)
    plt.close()

    return output_path

file_path = 'library/20241225_181630_sound.wav'
output_file = save_power_spectrum_as_jpg(file_path)
print(f"Power spectrum saved as: {output_file}")
