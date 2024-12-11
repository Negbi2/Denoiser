# Real Time Denoiser

___

A simple python program that cleans up microphone audio in real time

___
## Help

```
usage: denoiser.py [-h] [-l] [-li] [-lo] [-i INPUT_DEVICE] [-o OUTPUT_DEVICE]

options:
  -h, --help            show this help message and exit
  -l, --list-devices    show a list of available devices
  -li, --list-inputs    show a list of available input devices
  -lo, --list-outputs   show a list of available output devices
  -i INPUT_DEVICE, --input-device INPUT_DEVICE
                        input device (numeric ID)
  -o OUTPUT_DEVICE, --output-device OUTPUT_DEVICE
                        output device (numeric ID)
```

___

<br>

## Installation
___

* clone the repository (or just download the denoiser.py file)
* install this project's dependencies

```
pip install sounddevice numpy noisereduce
```

* run the program with the wanted arguments

```
python denoiser.py -i INPUT_DEVICE -o OUTPUT_DEVICE
```

if done correctly it should just work
