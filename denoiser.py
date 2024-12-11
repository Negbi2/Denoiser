import argparse
import queue

import noisereduce as nr
import numpy as np

import sounddevice as sd
import soundfile as sf

import threading

MONO_AUDIO = 1
OPTIMAL_BLOCK_SIZE = 1024

DEFAULT_INPUT_DEVICE = sd.default.device[0]
DEFAULT_OUTPUT_DEVICE = sd.default.device[1]

# Create a queue for storing processed audio data
audio_queue = queue.Queue()

input_device_id = -1

# save current frame for file processing
current_frame = 0

# how aggressive to be when noice reducing
prop_decrease = .7

def list_devices():
    default_input_device = DEFAULT_INPUT_DEVICE
    default_output_device = DEFAULT_OUTPUT_DEVICE

    for key, device in enumerate(sd.query_devices()):
        if key == default_input_device:
            print(
                f"> {key}: {device['name']} ({device['max_input_channels']} in, {device['max_output_channels']} out) rate:{sd.query_devices(key)['default_samplerate']}")
        elif key == default_output_device:
            print(
                f"< {key}: {device['name']} ({device['max_input_channels']} in, {device['max_output_channels']} out) rate:{sd.query_devices(key)['default_samplerate']}")
        else:
            print(
                f"  {key}: {device['name']} ({device['max_input_channels']} in, {device['max_output_channels']} out) rate:{sd.query_devices(key)['default_samplerate']}")


def list_inputs():
    default_input_device = DEFAULT_INPUT_DEVICE

    for key, device in enumerate(sd.query_devices()):
        if device['max_input_channels'] > 0:
            if key == default_input_device:
                print(
                    f"> {key}: {device['name']} ({device['max_input_channels']} in, {device['max_output_channels']} out) rate:{sd.query_devices(key)['default_samplerate']}")
            else:
                print(
                    f"  {key}: {device['name']} ({device['max_input_channels']} in, {device['max_output_channels']} out) rate:{sd.query_devices(key)['default_samplerate']}")


def list_outputs():
    default_output_device = DEFAULT_OUTPUT_DEVICE

    for key, device in enumerate(sd.query_devices()):
        if device['max_output_channels'] > 0:
            if key == default_output_device:
                print(
                    f"< {key}: {device['name']} ({device['max_input_channels']} in, {device['max_output_channels']} out) rate:{sd.query_devices(key)['default_samplerate']}")
            else:
                print(
                    f"  {key}: {device['name']} ({device['max_input_channels']} in, {device['max_output_channels']} out) rate:{sd.query_devices(key)['default_samplerate']}")


def input_callback(indata, frames, time, status):
    if status:
        print(status)

    global input_device_id
    # Perform noise reduction on the resampled input
    reduced_noise = nr.reduce_noise(y=indata[:, 0], sr=sd.query_devices(input_device_id)['default_samplerate'],
                                    prop_decrease=prop_decrease,
                                    time_mask_smooth_ms=20,
                                    freq_mask_smooth_hz=300,
                                    stationary=True)  # Assume stationary noise (e.g., hum or consistent noise)
    audio_queue.put_nowait(reduced_noise)  # Non-blocking put into the queue


def output_callback(outdata, frames, time, status):
    if status:
        print(status)

    # Try to get the processed audio from the queue
    try:
        output_audio = audio_queue.get_nowait()  # Non-blocking get from the queue
        # Ensure the length of the audio matches the required frames
        if len(output_audio) < frames:
            outdata[:len(output_audio), 0] = output_audio
        else:
            outdata[:, 0] = output_audio[:frames]
    except queue.Empty:
        outdata[:, 0] = 0  # If no audio is available, fill with silence


def denoise_file(filename, output_device_id):
    event = threading.Event()

    try:
        data, fs = sf.read(filename, always_2d=True, dtype=np.float32)

        # Perform noise reduction on the file data
        denoised_data = nr.reduce_noise(y=data[:, 0], sr=fs, prop_decrease=prop_decrease,
                                        time_mask_smooth_ms=20, freq_mask_smooth_hz=300, stationary=True)

        def file_callback(outdata, frames, time, status):
            global current_frame
            if status:
                print(status)

            # Get the chunk size for the current playback
            chunksize = min(len(denoised_data) - current_frame, frames)

            # Reshape the denoised data to match output format
            chunk = denoised_data[current_frame:current_frame + chunksize]
            outdata[:chunksize, 0] = chunk[:chunksize]  # Ensure data fits the outdata array

            # If the chunk is smaller than the requested frame, fill the rest with silence
            if chunksize < frames:
                outdata[chunksize:, :] = 0
                raise sd.CallbackStop()  # End the playback if all data has been processed

            # Update the current frame position
            current_frame += chunksize

        # Open the OutputStream with the denoised data
        with sd.OutputStream(samplerate=fs, device=output_device_id, channels=MONO_AUDIO,
                             callback=file_callback, dtype=np.float32, finished_callback=event.set):
            event.wait()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(e)


def continuous_stream(intput_device_id, output_device_id):
    try:
        # rates in Hz
        output_rate = sd.query_devices(intput_device_id)['default_samplerate']
        input_rate = sd.query_devices(output_device_id)['default_samplerate']

        # capture audio
        with sd.InputStream(samplerate=input_rate,
                            device=intput_device_id,
                            channels=MONO_AUDIO,
                            dtype=np.float32,
                            callback=input_callback,
                            blocksize=OPTIMAL_BLOCK_SIZE):

            # playback audio
            with sd.OutputStream(samplerate=output_rate,
                                 device=output_device_id,
                                 channels=MONO_AUDIO,
                                 dtype=np.float32,
                                 callback=output_callback,
                                 blocksize=OPTIMAL_BLOCK_SIZE):
                print('#' * 80)
                print('Press Return to quit')
                print('#' * 80)
                input()
                print("Program stopped by user")
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    except Exception as ex:
        print("invalid input or output device")
        print(ex)


def initialize_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list-devices", help="show a list of available devices", action="store_true")
    parser.add_argument("-li", "--list-inputs", help="show a list of available input devices", action="store_true")
    parser.add_argument("-lo", "--list-outputs", help="show a list of available output devices", action="store_true")

    parser.add_argument("-a", "--aggressive", help="make the noise canceling more aggressive (may result in artifacts)", action="store_true")

    parser.add_argument(
        '-i', '--input-device', type=int, help='input device (numeric ID)')
    parser.add_argument(
        '-o', '--output-device', type=int, help='output device (numeric ID)')

    parser.add_argument(
        '-f', '--filename', metavar='FILENAME', help='Process file')
    return parser.parse_args()


def main():
    args = initialize_arguments()

    if args.list_devices:
        list_devices()
        return
    if args.list_inputs:
        list_inputs()
        return
    if args.list_outputs:
        list_outputs()
        return

    if args.aggressive:
        global prop_decrease
        prop_decrease = 1

    if args.filename:
        if args.output_device is None:
            print("must specify output device")
            return

        denoise_file(args.filename, args.output_device)
        return

    if args.input_device is None or args.output_device is None:
        print("Input and output devices must be specified")
        return
    global input_device_id
    input_device_id = args.input_device

    continuous_stream(args.input_device, args.output_device)


if __name__ == "__main__":
    main()
