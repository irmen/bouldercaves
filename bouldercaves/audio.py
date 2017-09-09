"""
Various audio output options. Here the specific audio library code is located.
Supported audio output libraries:
- pyaudio
- sounddevice (both thread+blocking stream, and nonblocking callback stream variants)
- winsound

It can play multiple samples at the same time via real-time mixing, and you can
loop samples as well without noticable overhead (great for continous effects or music)
Wav (PCM) files and .ogg files can be loaded (requires oggdec from the
vorbis-tools package to decode those)

High level api functions:
  init_audio
  play_sample
  silence_audio
  shutdown_audio

Written by Irmen de Jong (irmen@razorvine.net) - License: MIT open-source.
"""

import audioop   # type: ignore
import io
import math
import os
import pkgutil
import queue
import subprocess
import tempfile
import threading
import time
import wave
from typing import BinaryIO, ByteString, Callable, Generator, List, Union


__all__ = ["init_audio", "play_sample", "silence_audio", "shutdown_audio"]


# stubs for optional audio library modules:
sounddevice = None
pyaudio = None
winsound = None

norm_samplerate = 44100
norm_samplewidth = 2
norm_channels = 2
norm_chunk_duration = 1 / 50     # seconds


def best_api(dummy_enabled: bool=False):
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
    """A stereo sample of raw PCM audio data. Uncompresses .ogg to PCM if needed."""
    def __init__(self, name: str, filename: str=None, filedata: bytes=None, pcmdata: bytes=None) -> None:
        self.duration = 0.0
        self.name = name
        self.filename = filename
        if pcmdata is not None:
            self.sampledata = pcmdata
            self.duration = len(self.sampledata) // norm_channels // norm_samplewidth / norm_samplerate
            return
        if filename:
            inputfile = open(filename, "rb")
        else:
            inputfile = io.BytesIO(filedata)
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

    def append(self, othersample: 'Sample'):
        self.duration += othersample.duration
        self.sampledata += othersample.sampledata

    def save_wav(self, filename):
        with wave.open(filename, "wb") as out:
            out.setparams((norm_channels, norm_samplewidth, norm_samplerate, 0, "NONE", "not compressed"))
            out.writeframes(self.sampledata)

    @classmethod
    def convertformat(cls, stream: BinaryIO) -> BinaryIO:
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

    def chunked_data(self, chunksize: int, repeat: bool=False,
                     stopcondition: Callable[[], bool]=lambda: False) -> Generator[memoryview, None, None]:
        if repeat:
            # continuously repeated
            bdata = self.sampledata
            if len(bdata) < chunksize:
                bdata = bdata * math.ceil(chunksize / len(bdata))
            length = len(bdata)
            bdata += bdata[:chunksize]
            mdata = memoryview(bdata)
            i = 0
            while not stopcondition():
                yield mdata[i: i + chunksize]
                i = (i + chunksize) % length
        else:
            # one-shot
            mdata = memoryview(self.sampledata)
            i = 0
            while i < len(mdata) and not stopcondition():
                yield mdata[i: i + chunksize]
                i += chunksize


class DummySample(Sample):
    def __init__(self, name: str, filename: str=None, duration: float=0.0) -> None:
        self.name = name
        self.filename = filename
        self.duration = duration
        self.sampledata = b""


class SampleMixer:
    """
    Real-time audio sample mixer. Simply adds a number of samples, clipping if values become too large.
    Produces (via a generator method) chunks of audio stream data to be fed to the sound output stream.
    """
    def __init__(self, chunksize: int) -> None:
        self.active_samples = []   # type: List[Generator[memoryview, None, None]]
        self.chunksize = chunksize
        self.mixed_chunks = self.chunks()

    def add_sample(self, sample: Sample, repeat: bool=False) -> None:
        sample_chunks = sample.chunked_data(chunksize=self.chunksize, repeat=repeat)
        self.active_samples.append(sample_chunks)

    def clear_sources(self) -> None:
        self.active_samples.clear()

    def chunks(self) -> Generator[memoryview, None, None]:
        silence = b"\0" * self.chunksize
        while True:
            chunks_to_mix = []
            for s in list(self.active_samples):
                try:
                    chunk = next(s)
                    if len(chunk) < self.chunksize:
                        # pad the chunk with some silence
                        chunk = memoryview(chunk.tobytes() + silence[:self.chunksize - len(chunk)])
                    chunks_to_mix.append(chunk)
                except StopIteration:
                    self.active_samples.remove(s)
            chunks_to_mix = chunks_to_mix or [memoryview(silence)]
            assert all(len(c) == self.chunksize for c in chunks_to_mix)
            mixed = chunks_to_mix[0]
            if len(chunks_to_mix) > 1:
                for to_mix in chunks_to_mix[1:]:
                    mixed = audioop.add(mixed, to_mix, norm_channels)
                mixed = memoryview(mixed)
            yield mixed


class AudioApi:
    """Base class for the various audio APIs."""
    def __init__(self) -> None:
        self.samplerate = norm_samplerate
        self.samplewidth = norm_samplewidth
        self.nchannels = norm_channels
        self.chunkduration = norm_chunk_duration
        self.samp_queue = queue.Queue(maxsize=100)    # type: ignore

    def __str__(self) -> str:
        api_ver = self.query_api_version()
        if api_ver and api_ver != "unknown":
            return self.__class__.__name__ + ", " + self.query_api_version()
        else:
            return self.__class__.__name__

    def chunksize(self) -> int:
        return int(self.samplerate * self.samplewidth * self.nchannels * self.chunkduration)

    def play(self, sample: Sample, repeat: bool=False) -> None:
        self.samp_queue.put({"sample": sample, "repeat": repeat})

    def silence(self) -> None:
        self.samp_queue.put("silence")

    def close(self) -> None:
        self.samp_queue.put("stop")

    def query_api_version(self) -> str:
        return "unknown"


class PyAudio(AudioApi):
    """Api to the somewhat older pyaudio library (that uses portaudio)"""
    def __init__(self):
        super().__init__()
        global pyaudio
        import pyaudio

        def audio_thread():
            audio = pyaudio.PyAudio()
            mixer = SampleMixer(chunksize=self.chunksize())
            try:
                audio_format = audio.get_format_from_width(self.samplewidth) if self.samplewidth != 4 else pyaudio.paInt32
                stream = audio.open(format=audio_format, channels=self.nchannels, rate=self.samplerate, output=True)
                try:
                    while True:
                        try:
                            job = self.samp_queue.get_nowait()
                            if job == "stop":
                                break
                            elif job == "silence":
                                mixer.clear_sources()
                                continue
                        except queue.Empty:
                            pass
                        else:
                            mixer.add_sample(job["sample"], job["repeat"])
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
            mixer = SampleMixer(chunksize=self.chunksize())
            try:
                stream = sounddevice.RawOutputStream(self.samplerate, channels=self.nchannels, dtype=dtype)
                stream.start()
                try:
                    while True:
                        try:
                            job = self.samp_queue.get_nowait()
                            if job == "stop":
                                break
                            elif job == "silence":
                                mixer.clear_sources()
                                continue
                        except queue.Empty:
                            pass
                        else:
                            mixer.add_sample(job["sample"], job["repeat"])
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
        del self.samp_queue
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
        self._empty_sound_data = b"\0" * self.chunksize() * self.nchannels * self.samplewidth
        self.mixer = SampleMixer(chunksize=self.chunksize())
        self.stream = sounddevice.RawOutputStream(self.samplerate, channels=self.nchannels, dtype=dtype,
                                                  blocksize=self.chunksize() // self.nchannels // self.samplewidth, callback=self.streamcallback)
        self.stream.start()

    def query_api_version(self):
        return sounddevice.get_portaudio_version()[1]

    def play(self, sample, repeat=False):
        self.mixer.add_sample(sample, repeat)

    def silence(self):
        self.mixer.clear_sources()

    def close(self):
        self.silence()
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
            outdata[len(data):] = b"\0" * (len(outdata) - len(data))
            # raise sounddevice.CallbackStop    this will play the remaining samples and then stop the stream
        else:
            outdata[:] = data


class Winsound(AudioApi):
    """Minimally featured api for the winsound library that comes with Python on Windows."""
    def __init__(self):
        super().__init__()
        del self.samp_queue
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

    def play(self, sample, repeat=False):
        # winsound.SND_NOSTOP doesn't seem to work.
        option = winsound.SND_ASYNC
        if repeat:
            option |= winsound.SND_LOOP
        winsound.PlaySound(sample.filename, option)

    def silence(self):
        winsound.PlaySound(None, winsound.SND_PURGE)

    def close(self):
        self.silence()

    def store_sample_file(self, filename, data):
        # convert the sample file to a wav file on disk.
        oggfilename = os.path.expanduser("~/.bouldercaves/") + filename
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

    def silence(self):
        self.audio_api.silence()

    def play_sample(self, samplename, repeat=False):
        """Play a single sample (asynchronously)."""
        global samples
        self.audio_api.play(samples[samplename], repeat=repeat)


samples = {}
output = None


def init_audio(samples_to_load, dummy=False):
    global output, samples
    if dummy:
        output = Output(DummyAudio())
    else:
        output = Output()
    if isinstance(output.audio_api, DummyAudio):
        if not dummy:
            print("No audio output available. Install 'sounddevice' or 'pyaudio' library to hear things.")
        for name, filename in samples_to_load.items():
            samples[name] = DummySample(name)
        return
    print("Loading sound data...")
    for name, filename in samples_to_load.items():
        if isinstance(filename, Sample):
            samples[name] = filename
        else:
            data = pkgutil.get_data(__name__, "sounds/" + filename)
            if isinstance(output.audio_api, Winsound):
                # winsound needs the samples as physical WAV files on disk.
                filename = output.audio_api.store_sample_file(filename, data)
                samples[name] = DummySample(name, filename)
            else:
                samples[name] = Sample(name, filedata=data)
    print("Sound API initialized:", output.audio_api)
    if isinstance(output.audio_api, Winsound):
        print("Winsound is used as fallback. For better audio, it is recommended to install the 'sounddevice' or 'pyaudio' library instead.")


def play_sample(samplename, repeat=False):
    output.play_sample(samplename, repeat)


def silence_audio():
    output.silence()


def shutdown_audio():
    output.close()


if __name__ == "__main__":
    sample = Sample("test", pcmdata=b"0123456789")
    chunks = sample.chunked_data(chunksize=51, repeat=True)
    for _ in range(60):
        print(next(chunks).tobytes())
    norm_samplerate = 22050
    init_audio({
        "explosion": "explosion.ogg",
        "amoeba": "amoeba.ogg",
        "game_over": "game_over.ogg",
    })
    with Output(Sounddevice()) as output:
        print("PLAY MUSIC...", output.audio_api)
        print("CHUNK", output.audio_api.chunksize())
        output.play_sample("amoeba", repeat=True)
        time.sleep(3)
        print("PLAY ANOTHER SOUND!")
        output.play_sample("game_over", repeat=False)
        time.sleep(1)
        print("PLAY ANOTHER SOUND!")
        output.play_sample("explosion", repeat=True)
        time.sleep(4)
        print("STOP SOUND!")
        output.silence()
        time.sleep(2)
        print("SHUTDOWN!")
    time.sleep(0.5)
