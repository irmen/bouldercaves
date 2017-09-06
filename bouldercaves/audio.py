"""
Various audio output options. Here the specific audio library code is located.
Supported audio output libraries:
- pyaudio
- sounddevice (both thread+blocking stream, and nonblocking callback stream variants)
- winsound

Written by Irmen de Jong (irmen@razorvine.net) - License: MIT open-source.
"""

import threading
import queue
import os
import time
import wave
import pkgutil
import io
import subprocess
import tempfile
import audioop
import math


__all__ = ["PyAudio", "Sounddevice", "SounddeviceThread", "Winsound", "best_api", "Output"]


# stubs for optional audio library modules:
sounddevice = None
pyaudio = None
winsound = None

norm_samplerate = 44100
norm_samplewidth = 2
norm_channels = 2
norm_chunksize = norm_samplerate * norm_samplewidth * norm_channels // 50


def best_api(dummy_enabled=False):
    try:
        return Sounddevice()
    except ImportError:
        try:
            return SounddeviceThread()
        except ImportError:
            try:
                return PyAudio()
            except ImportError:
                try:
                    return Winsound()
                except ImportError:
                    if dummy_enabled:
                        return DummyAudio()
                    raise Exception("no suitable audio output api available") from None


class Sample:
    """A sample of raw PCM audio data. Uncompresses .ogg to PCM if needed."""
    def __init__(self, name, filename=None, data=None):
        self.duration = 0
        self.name = name
        self.filename = filename
        if filename:
            inputfile = open(filename, "rb")
        else:
            inputfile = io.BytesIO(data)
        try:
            with self.convertformat(inputfile) as inputfile:
                with wave.open(inputfile, "r") as wavesample:
                    assert wavesample.getframerate() == norm_samplerate
                    assert wavesample.getsampwidth() == norm_samplewidth
                    numchannels = wavesample.getnchannels()
                    assert numchannels in (1, 2)
                    self.sampledata = wavesample.readframes(wavesample.getnframes())
                    self.duration = wavesample.getnframes() / norm_samplerate
            if numchannels == 1 and norm_channels == 2:
                # on the fly conversion to stereo if it is a mono sample
                self.sampledata = audioop.tostereo(self.sampledata, norm_samplewidth, 1, 1)
        except FileNotFoundError as x:
            print(x)
            raise SystemExit("'oggdec' (vorbis-tools) must be installed on your system to hear sounds in this game. "
                             "Or you can start it with the --nosound option.")

    def convertformat(self, stream):
        conversion_required = True
        try:
            # maybe the existing data is already a WAV in the correct format
            with wave.open(stream, "r") as wavesample:
                if wavesample.getframerate() == norm_samplerate and wavesample.getnchannels() in (1, 2) \
                        and wavesample.getsampwidth() == norm_samplewidth:
                    conversion_required = False
        except (wave.Error, IOError):
            conversion_required = True
        finally:
            stream.seek(0, 0)
        if not conversion_required:
            return stream
        # use oggdec to convert the audio file on the fly to a WAV
        if os.name == "nt":
            oggdecexe = Winsound.ensure_oggdegexe()
            uncompress_command = [oggdecexe, "--quiet", "--output", "-", "-"]
        else:
            uncompress_command = ["oggdec", "--quiet", "--output", "-", "-"]
        with tempfile.NamedTemporaryFile() as tmpfile:
            tmpfile.write(stream.read())
            tmpfile.seek(0, 0)
            converter = subprocess.Popen(uncompress_command, stdin=tmpfile, stdout=subprocess.PIPE)
            return io.BytesIO(converter.stdout.read())


class DummySample(Sample):
    def __init__(self, name, filename=None, duration=0):
        self.name = name
        self.filename = filename
        self.duration = duration
        self.sampledata = b""



class SampleMixer:
    """
    Real-time audio sample mixer. Simply adds a number of samples, clipping if values become too large.
    Produces (via a generator method) chunks of audio stream data to be fed to the sound output stream.
    """
    def __init__(self, chunksize):
        self.active_samples = []
        self.chunksize = chunksize
        self.mixed_chunks = self.chunks()

    def add_sample(self, sounddata, repeat=False):
        self.active_samples.append(self._chunked(memoryview(sounddata), chunksize=self.chunksize, repeat=repeat))

    @staticmethod
    def _chunked(data, chunksize=norm_chunksize, repeat=False, stopcondition=lambda: False):
        if repeat:
            # continuously repeated
            data = bytes(data)
            if len(data) < chunksize:
                data = data * math.ceil(chunksize / len(data))
            length = len(data)
            data += data[:chunksize]
            data = memoryview(data)
            i = 0
            while not stopcondition():
                yield data[i: i + chunksize]
                i = (i + chunksize) % length
        else:
            # one-shot
            i = 0
            while i < len(data) and not stopcondition():
                yield data[i: i + chunksize]
                i += chunksize

    def chunks(self):
        silence = b"\0" * self.chunksize
        while True:
            chunks_to_mix = []
            for s in list(self.active_samples):
                try:
                    chunk = next(s)
                    if len(chunk) < self.chunksize:
                        chunk = chunk.tobytes() + silence[:self.chunksize-len(chunk)]
                    chunks_to_mix.append(chunk)
                except StopIteration:
                    self.active_samples.remove(s)
            assert all(len(c) == self.chunksize for c in chunks_to_mix)
            if chunks_to_mix:
                mixed = chunks_to_mix[0]
                for to_mix in chunks_to_mix[1:]:
                    mixed = audioop.add(mixed, to_mix, norm_channels)
                yield mixed
            else:
                yield silence


class AudioApi:
    """Base class for the various audio APIs."""
    def __init__(self):
        self.samplerate = norm_samplerate
        self.samplewidth = norm_samplewidth
        self.nchannels = norm_channels
        self.samp_queue = queue.Queue(maxsize=100)

    def __str__(self):
        api_ver = self.query_api_version()
        if api_ver and api_ver != "unknown":
            return self.__class__.__name__ + ", " + self.query_api_version()
        else:
            return self.__class__.__name__

    def play(self, sample, repeat=False):
        if sample:
            self.samp_queue.put({"sample": sample, "repeat": repeat})
        else:
            self.samp_queue.put(None)

    def close(self):
        self.samp_queue.put(None)

    def query_api_version(self):
        return "unknown"


class PyAudio(AudioApi):
    """Api to the somewhat older pyaudio library (that uses portaudio)"""
    def __init__(self):
        super().__init__()
        global pyaudio
        import pyaudio

        def audio_thread():
            audio = pyaudio.PyAudio()
            mixer = SampleMixer(chunksize=norm_chunksize)
            try:
                audio_format = audio.get_format_from_width(self.samplewidth) if self.samplewidth != 4 else pyaudio.paInt32
                stream = audio.open(format=audio_format, channels=self.nchannels, rate=self.samplerate, output=True)
                try:
                    while True:
                        try:
                            job = self.samp_queue.get_nowait()
                            if job is None:
                                break
                        except queue.Empty:
                            pass
                        else:
                            mixer.add_sample(job["sample"].sampledata, job["repeat"])
                        data = next(mixer.mixed_chunks)
                        if isinstance(data, memoryview):
                            data = data.tobytes()   # PyAudio stream can't deal with memoryview
                        stream.write(data)
                finally:
                    stream.close()
            finally:
                audio.terminate()

        outputter = threading.Thread(target=audio_thread, name="audio-pyaudio", daemon=True)
        outputter.start()

    def query_api_version(self):
        return pyaudio.get_portaudio_version_text()


class SounddeviceThread(AudioApi):
    """Api to the more featureful sounddevice library (that uses portaudio) -
    using blocking streams with an audio output thread"""
    def __init__(self):
        super().__init__()
        global sounddevice
        import sounddevice
        if self.samplewidth == 1:
            dtype = "int8"
        elif self.samplewidth == 2:
            dtype = "int16"
        elif self.samplewidth == 3:
            dtype = "int24"
        elif self.samplewidth == 4:
            dtype = "int32"
        else:
            raise ValueError("invalid sample width")

        def audio_thread():
            mixer = SampleMixer(chunksize=norm_chunksize)
            try:
                stream = sounddevice.RawOutputStream(self.samplerate, channels=self.nchannels, dtype=dtype)
                stream.start()
                try:
                    while True:
                        try:
                            job = self.samp_queue.get_nowait()
                            if job is None:
                                break
                        except queue.Empty:
                            pass
                        else:
                            mixer.add_sample(job["sample"].sampledata, job["repeat"])
                        data = next(mixer.mixed_chunks)
                        stream.write(data)
                finally:
                    stream.close()
            finally:
                sounddevice.stop()

        self.output_thread = threading.Thread(target=audio_thread, name="audio-sounddevice", daemon=True)
        self.output_thread.start()

    def query_api_version(self):
        return sounddevice.get_portaudio_version()[1]


class Sounddevice(AudioApi):
    """Api to the more featureful sounddevice library (that uses portaudio) -
    using callback stream, without a separate audio output thread"""
    def __init__(self):
        super().__init__()
        global sounddevice
        import sounddevice
        if self.samplewidth == 1:
            dtype = "int8"
        elif self.samplewidth == 2:
            dtype = "int16"
        elif self.samplewidth == 3:
            dtype = "int24"
        elif self.samplewidth == 4:
            dtype = "int32"
        else:
            raise ValueError("invalid sample width")
        self._empty_sound_data = b"\0" * norm_chunksize * self.nchannels * self.samplewidth
        self.mixer = SampleMixer(chunksize=norm_chunksize)
        self.stream = sounddevice.RawOutputStream(self.samplerate, channels=self.nchannels, dtype=dtype,
            blocksize=norm_chunksize // self.nchannels // self.samplewidth, callback=self.streamcallback)
        self.stream.start()

    def query_api_version(self):
        return sounddevice.get_portaudio_version()[1]

    def play(self, sample, repeat=False):
        if sample is None:
            self.stream.stop()
        else:
            self.mixer.add_sample(sample.sampledata, repeat)

    def close(self):
        self.stream.stop()

    def streamcallback(self, outdata, frames, time, status):
        data = next(self.mixer.mixed_chunks)
        if not data:
            # no frames available, use silence
            # raise sounddevice.CallbackAbort   this will abort the stream
            assert len(outdata) == len(self._empty_sound_data)
            outdata[:] = self._empty_sound_data
        elif len(data) < len(outdata):
            # print("underflow", len(data), len(outdata))
            # underflow, pad with silence
            outdata[:len(data)] = data
            outdata[len(data):] = b"\0"*(len(outdata)-len(data))
            # raise sounddevice.CallbackStop    this will play the remaining samples and then stop the stream
        else:
            outdata[:] = data


class Winsound(AudioApi):
    """Minimally featured api for the winsound library that comes with Python on Windows."""
    def __init__(self):
        super().__init__()
        import winsound as _winsound
        global winsound
        winsound = _winsound
        self.threads = []
        self.oggdecexe = self.ensure_oggdegexe()

    @staticmethod
    def ensure_oggdegexe():
        filename = os.path.expanduser("~/.bouldercaves/oggdec.exe")
        if os.path.isfile(filename):
            return filename
        os.makedirs(os.path.expanduser("~/.bouldercaves"), exist_ok=True)
        oggdecexe = pkgutil.get_data(__name__, "sounds/oggdec.exe")
        with open(filename, "wb") as exefile:
            exefile.write(oggdecexe)
        return filename

    def play(self, sample):
        winsound.PlaySound(sample.filename, winsound.SND_ASYNC)

    def store_sample_file(self, filename, data):
        # convert the sample file to a wav file on disk.
        oggfilename = os.path.expanduser("~/.bouldercaves/")+filename
        with open(oggfilename, "wb") as oggfile:
            oggfile.write(data)
        wavfilename = os.path.splitext(oggfilename)[0] + ".wav"
        oggdeccmd = [self.oggdecexe, "--quiet", oggfilename, "-o", wavfilename]
        subprocess.call(oggdeccmd)
        os.remove(oggfilename)
        return wavfilename


class DummyAudio(AudioApi):
    """Dummy audio api that does nothing"""
    def __init__(self):
        super().__init__()

    def query_api_version(self):
        return "dummy"

    def play(self, sample, repeat=False):
        pass


class Output:
    """Plays samples to audio output device or streams them to a file."""
    def __init__(self, api=None):
        if api is None:
            api = best_api(dummy_enabled=True)
        self.audio_api = api

    def __enter__(self):
        return self

    def __exit__(self, xtype, value, traceback):
        self.close()

    def close(self):
        self.audio_api.close()

    def play_sample(self, samplename, repeat=False):
        """Play a single sample (asynchronously)."""
        global samples
        self.audio_api.play(samples[samplename], repeat=repeat)


samples = {}
output = None


def init_audio(dummy=False):
    sounds = {
        "music": "bdmusic.ogg",
        "cover": "cover.ogg",
        "crack": "crack.ogg",
        "boulder": "boulder.ogg",
        "finished": "finished.ogg",
        "explosion": "explosion.ogg",
        "extra_life": "bonus_life.ogg",
        "walk_empty": "walk_empty.ogg",
        "walk_dirt": "walk_dirt.ogg",
        "collect_diamond": "collectdiamond.ogg",
        "box_push": "box_push.ogg",
        "amoeba": "amoeba.ogg",
        "magic_wall": "magic_wall.ogg",
        "diamond1": "diamond1.ogg",
        "diamond2": "diamond2.ogg",
        "diamond3": "diamond3.ogg",
        "diamond4": "diamond4.ogg",
        "diamond5": "diamond5.ogg",
        "diamond6": "diamond6.ogg",
        "game_over": "game_over.ogg",
        "timeout1": "timeout1.ogg",
        "timeout2": "timeout2.ogg",
        "timeout3": "timeout3.ogg",
        "timeout4": "timeout4.ogg",
        "timeout5": "timeout5.ogg",
        "timeout6": "timeout6.ogg",
        "timeout7": "timeout7.ogg",
        "timeout8": "timeout8.ogg",
        "timeout9": "timeout9.ogg",
    }

    global output, samples
    if dummy:
        output = Output(DummyAudio())
    else:
        output = Output()
    if isinstance(output.audio_api, DummyAudio):
        if not dummy:
            print("No audio output available. Install 'sounddevice' or 'pyaudio' library to hear things.")
        for name, filename in sounds.items():
            samples[name] = DummySample(name)
        return

    print("Loading sound data...")
    for name, filename in sounds.items():
        data = pkgutil.get_data(__name__, "sounds/" + filename)
        if isinstance(output.audio_api, Winsound):
            # winsound needs the samples as physical WAV files on disk.
            filename = output.audio_api.store_sample_file(filename, data)
            samples[name] = DummySample(name, filename)
        else:
            samples[name] = Sample(name, data=data)
    print("Sound API used:", output.audio_api)
    if isinstance(output.audio_api, Winsound):
        print("Winsound is used as fallback. For better audio, it is recommended to install the 'sounddevice' or 'pyaudio' library instead.")


def play_sample(samplename):
    output.play_sample(samplename)


def shutdown_audio():
    if output:
        output.close()


if __name__ == "__main__":
    # data = b"0123456789"
    # chunks = chunked(data, chunksize=91, repeat=True)
    # for _ in range(200):
    #     print(next(chunks).tobytes())
    # raise SystemExit
    norm_samplerate = 22100
    init_audio()
    with Output(Sounddevice()) as output:
        print("PLAY MUSIC...", output.audio_api)
        print("CHUNK", norm_chunksize)
        output.play_sample("amoeba", repeat=True)
        time.sleep(3)
        print("PLAY ANOTHER SOUND!")
        output.play_sample("game_over", repeat=False)
        time.sleep(1)
        print("PLAY ANOTHER SOUND!")
        output.play_sample("explosion", repeat=False)
        time.sleep(4)
        print("STOP SOUND!")
        output.stop()
        time.sleep(2)
        print("SHUTDOWN!")
    time.sleep(0.5)
