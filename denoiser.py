import sounddevice as sd
import numpy as np
import noisereduce as nr
import queue

import argparse

MONO_AUDIO = 1
OPTIMAL_BLOCK_SIZE = 1024

DEFAULT_INPUT_DEVICE = sd.default.device[0]
DEFAULT_OUTPUT_DEVICE = sd.default.device[1]

# Create a queue for storing processed audio data
audio_queue = queue.Queue()

input_device_id = -1


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
                                    prop_decrease=.7,
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


def initialize_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list-devices", help="show a list of available devices", action="store_true")
    parser.add_argument("-li", "--list-inputs", help="show a list of available input devices", action="store_true")
    parser.add_argument("-lo", "--list-outputs", help="show a list of available output devices", action="store_true")

    parser.add_argument(
        '-i', '--input-device', type=int, help='input device (numeric ID)')
    parser.add_argument(
        '-o', '--output-device', type=int, help='output device (numeric ID)')
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

    if not (args.input_device and args.output_device):
        print("Input and output devices must be specified")
        return
    global input_device_id
    input_device_id = args.input_device

    continuous_stream(args.input_device, args.output_device)


if __name__ == "__main__":
    main()
