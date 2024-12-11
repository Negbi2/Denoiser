# Real Time Denoiser


A simple python program that cleans up microphone audio in real time

## Help

```
usage: denoiser.py [-h] [-l] [-li] [-lo] [-a] [-i INPUT_DEVICE] [-o OUTPUT_DEVICE] [-f FILENAME]

options:
  -h, --help            show this help message and exit
  -l, --list-devices    show a list of available devices
  -li, --list-inputs    show a list of available input devices
  -lo, --list-outputs   show a list of available output devices
  -a, --aggressive      make the noise canceling more aggressive (may result in artifacts)
  -i INPUT_DEVICE, --input-device INPUT_DEVICE
                        input device (numeric ID) not needed when processing a file
  -o OUTPUT_DEVICE, --output-device OUTPUT_DEVICE
                        output device (numeric ID)
  -f FILENAME, --filename FILENAME
                        Process file
```


<br>

## Installation

* clone the repository (or just download the denoiser.py file)
* install this project's dependencies

```
pip install sounddevice soundfile numpy noisereduce
```

* run the program with the wanted arguments

#### Run it live on microphone audio
```
python denoiser.py -i INPUT_DEVICE -o OUTPUT_DEVICE
```

#### Run it on an audio file
```
python denoiser.py -o OUTPUT_DEVICE -f AUDIO_FILE -a
```

if done correctly it should just work :)
