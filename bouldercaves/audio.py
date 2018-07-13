"""
Various audio output options. Here the specific audio library code is located.
Supported audio output libraries:
- pyaudio
- sounddevice (both thread+blocking stream, and nonblocking callback stream variants)

It can play multiple samples at the same time via real-time mixing, and you can
loop samples as well without noticable overhead (great for continous effects or music)
Wav (PCM) files and .ogg files can be loaded (requires oggdec from the
vorbis-tools package to decode those)

High level api functions:
  init_audio
  play_sample
  silence_audio
  shutdown_audio

Written by Irmen de Jong (irmen@razorvine.net)
License: GNU GPL 3.0, see LICENSE
"""

import audioop
import pkgutil
import queue
import threading
import time
import tempfile
from collections import defaultdict
from typing import Generator, Union, Dict, Tuple, Any
from .synthesizer import params as synth_params
from .synthesizer import sample
from .synthesizer.tools import streaming


__all__ = ["init_audio", "play_sample", "silence_audio", "shutdown_audio"]


# stubs for optional audio library modules:
sounddevice = None
pyaudio = None
norm_chunk_duration = 1 / 50     # seconds

# audio parameters
synth_params.norm_samplerate = 22050
streaming.AudiofileToWavStream.ffprobe_executable = ""  # force use of oggdec instead of ffmpeg
streaming.AudiofileToWavStream.ffmpeg_executable = ""  # force use of oggdec instead of ffmpeg


def best_api():
    try:
        return Sounddevice()
    except ImportError:
        try:
            return SounddeviceThread()
        except ImportError:
            try:
                return PyAudio()
            except ImportError:
                raise Exception("no suitable audio output api available") from None


class SampleMixer:
    """
    Real-time audio sample mixer. Simply adds a number of samples, clipping if values become too large.
    Produces (via a generator method) chunks of audio stream data to be fed to the sound output stream.
    """
    def __init__(self, chunksize: int) -> None:
        self.active_samples = {}   # type: Dict[int, Tuple[str, Generator[memoryview, None, None]]]
        self.sample_counts = defaultdict(int)  # type: Dict[str, int]
        self.chunksize = chunksize
        self.mixed_chunks = self.chunks()
        self.add_lock = threading.Lock()
        self._sid = 0
        self.sample_limits = defaultdict(int)  # type: Dict[str, int]

    def add_sample(self, sample: sample.Sample, repeat: bool=False, sid: int=None) -> Union[int, None]:
        if not self.allow_sample(sample, repeat):
            return None
        with self.add_lock:
            sample_chunks = sample.chunked_frame_data(chunksize=self.chunksize, repeat=repeat)
            self._sid += 1
            sid = sid or self._sid
            self.active_samples[sid] = (sample.name, sample_chunks)
            self.sample_counts[sample.name] += 1
            return sid

    def allow_sample(self, sample: sample.Sample, repeat: bool=False) -> bool:
        if repeat and self.sample_counts[sample.name] >= 1:  # don't allow more than one repeating sample
            return False
        max_samples = self.sample_limits[sample.name] or 4
        if self.sample_counts[sample.name] >= max_samples:  # same sample max 4 times simultaneously
            return False
        if sum(self.sample_counts.values()) >= 8:  # mixing max 8 samples simultaneously
            return False
        return True

    def clear_sources(self) -> None:
        # clears all sources
        with self.add_lock:
            self.active_samples.clear()
            self.sample_counts.clear()

    def clear_source(self, sid_or_name: Union[int, str]) -> None:
        # clear a single sample source by its sid or all sources with the sample name
        if isinstance(sid_or_name, int):
            self.remove_sample(sid_or_name)
        else:
            with self.add_lock:
                active_samples = list(self.active_samples.items())
            for sid, (name, _) in active_samples:
                if name == sid_or_name:
                    self.remove_sample(sid)

    def chunks(self) -> Generator[memoryview, None, None]:
        silence = b"\0" * self.chunksize
        while True:
            chunks_to_mix = []
            with self.add_lock:
                active_samples = list(self.active_samples.items())
            for i, (name, s) in active_samples:
                try:
                    chunk = next(s)
                    if len(chunk) > self.chunksize:
                        raise ValueError("chunk from sample is larger than chunksize from mixer")
                    if len(chunk) < self.chunksize:
                        # pad the chunk with some silence
                        chunk = memoryview(chunk.tobytes() + silence[:self.chunksize - len(chunk)])
                    chunks_to_mix.append(chunk)
                except StopIteration:
                    self.remove_sample(i)
            chunks_to_mix = chunks_to_mix or [memoryview(silence)]
            assert all(len(c) == self.chunksize for c in chunks_to_mix)
            mixed = chunks_to_mix[0]
            if len(chunks_to_mix) > 1:
                for to_mix in chunks_to_mix[1:]:
                    mixed = audioop.add(mixed, to_mix, synth_params.norm_nchannels)
                mixed = memoryview(mixed)
            yield mixed

    def remove_sample(self, sid: int) -> None:
        with self.add_lock:
            name = self.active_samples[sid][0]
            del self.active_samples[sid]
            self.sample_counts[name] -= 1

    def set_limit(self, samplename: str, max_simultaneously: int) -> None:
        self.sample_limits[samplename] = max_simultaneously


class AudioApi:
    """Base class for the various audio APIs."""
    def __init__(self) -> None:
        self.samplerate = synth_params.norm_samplerate
        self.samplewidth = synth_params.norm_samplewidth
        self.nchannels = synth_params.norm_nchannels
        self.chunkduration = norm_chunk_duration
        self.samp_queue = queue.Queue(maxsize=100)      # type: queue.Queue[Union[Tuple[str, int], str, Dict[str, Any]]]

    def __str__(self) -> str:
        api_ver = self.query_api_version()
        if api_ver and api_ver != "unknown":
            return self.__class__.__name__ + ", " + self.query_api_version()
        else:
            return self.__class__.__name__

    def chunksize(self) -> int:
        return int(self.samplerate * self.samplewidth * self.nchannels * self.chunkduration)

    def play(self, sample: sample.Sample, repeat: bool=False) -> int:
        job = {"sample": sample, "repeat": repeat}
        job_id = id(job)
        job["id"] = job_id
        self.samp_queue.put(job)
        return job_id

    def silence(self) -> None:
        self.samp_queue.put("silence")

    def close(self) -> None:
        self.samp_queue.put("stop")

    def stop(self, sid: int) -> None:
        self.samp_queue.put(("stopsample", sid))

    def query_api_version(self) -> str:
        return "unknown"

    def set_sample_play_limit(self, samplename: str, max_simultaneously: int) -> None:
        pass


class PyAudio(AudioApi):
    """Api to the somewhat older pyaudio library (that uses portaudio)"""
    def __init__(self):
        super().__init__()
        global pyaudio
        import pyaudio
        thread_ready = threading.Event()

        def audio_thread():
            audio = pyaudio.PyAudio()
            self.mixer = SampleMixer(chunksize=self.chunksize())
            try:
                audio_format = audio.get_format_from_width(self.samplewidth) if self.samplewidth != 4 else pyaudio.paInt32
                stream = audio.open(format=audio_format, channels=self.nchannels, rate=self.samplerate, output=True)
                thread_ready.set()
                try:
                    while True:
                        try:
                            job = self.samp_queue.get_nowait()
                            if job == "stop":
                                break
                            elif job == "silence":
                                self.mixer.clear_sources()
                                continue
                            elif isinstance(job, tuple):
                                if job[0] == "stopsample":
                                    self.mixer.clear_source(job[1])
                                continue
                        except queue.Empty:
                            pass
                        else:
                            self.mixer.add_sample(job["sample"], job["repeat"], job["id"])
                        data = next(self.mixer.mixed_chunks)
                        if isinstance(data, memoryview):
                            data = data.tobytes()   # PyAudio stream can't deal with memoryview
                        stream.write(data)
                finally:
                    stream.close()
            finally:
                audio.terminate()

        outputter = threading.Thread(target=audio_thread, name="audio-pyaudio", daemon=True)
        outputter.start()
        thread_ready.wait()

    def query_api_version(self):
        return pyaudio.get_portaudio_version_text()

    def set_sample_play_limit(self, samplename: str, max_simultaneously: int) -> None:
        self.mixer.set_limit(samplename, max_simultaneously)


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
        thread_ready = threading.Event()

        def audio_thread():
            self.mixer = SampleMixer(chunksize=self.chunksize())
            try:
                stream = sounddevice.RawOutputStream(self.samplerate, channels=self.nchannels, dtype=dtype)
                stream.start()
                thread_ready.set()
                try:
                    while True:
                        try:
                            job = self.samp_queue.get_nowait()
                            if job == "stop":
                                break
                            elif job == "silence":
                                self.mixer.clear_sources()
                                continue
                            elif isinstance(job, tuple):
                                if job[0] == "stopsample":
                                    self.mixer.clear_source(job[1])
                                continue
                        except queue.Empty:
                            pass
                        else:
                            self.mixer.add_sample(job["sample"], job["repeat"], job["id"])
                        data = next(self.mixer.mixed_chunks)
                        stream.write(data)
                finally:
                    stream.close()
            finally:
                sounddevice.stop()

        self.output_thread = threading.Thread(target=audio_thread, name="audio-sounddevice", daemon=True)
        self.output_thread.start()
        thread_ready.wait()

    def query_api_version(self):
        return sounddevice.get_portaudio_version()[1]

    def set_sample_play_limit(self, samplename: str, max_simultaneously: int) -> None:
        self.mixer.set_limit(samplename, max_simultaneously)


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
        return self.mixer.add_sample(sample, repeat)

    def silence(self):
        self.mixer.clear_sources()

    def stop(self, sid: int) -> None:
        self.mixer.clear_source(sid)

    def set_sample_play_limit(self, samplename: str, max_simultaneously: int) -> None:
        self.mixer.set_limit(samplename, max_simultaneously)

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


class Output:
    """Plays samples to audio output device or streams them to a file."""
    def __init__(self, api=None):
        if api is None:
            api = best_api()
        self.audio_api = api

    def __enter__(self):
        return self

    def __exit__(self, xtype, value, traceback):
        self.close()

    def close(self):
        self.audio_api.close()

    def silence(self, sid_or_name=None):
        if sid_or_name:
            self.audio_api.stop(sid_or_name)
        else:
            self.audio_api.silence()

    def play_sample(self, samplename, repeat=False):
        """Play a single sample (asynchronously)."""
        global samples
        return self.audio_api.play(samples[samplename], repeat=repeat)

    def set_sample_play_limit(self, samplename: str, max_simultaneously: int) -> None:
        self.audio_api.set_sample_play_limit(samplename, max_simultaneously)


samples = {}    # type: Dict[str, Union[str, sample.Sample]]
output = None


def init_audio(samples_to_load, preferred_api=None) -> Output:
    global output, samples
    samples.clear()
    output = Output(preferred_api)
    if any(isinstance(smp, str) for smp, _ in samples_to_load.values()):
        print("Loading sound files...")
    for name, (filename, max_simultaneously) in samples_to_load.items():
        if isinstance(filename, sample.Sample):
            samples[name] = filename
        else:
            data = pkgutil.get_data(__name__, "sounds/" + filename)
            if data:
                with tempfile.NamedTemporaryFile() as tmp:
                    tmp.write(data)
                    tmp.flush()
                    samples[name] = sample.Sample(streaming.AudiofileToWavStream(tmp.name), name).stereo()
            else:
                raise SystemExit("corrupt package; sound data is missing")
        output.set_sample_play_limit(name, max_simultaneously)
    print("Sound API initialized:", output.audio_api)
    return output


def play_sample(samplename, repeat=False):
    return output.play_sample(samplename, repeat)


def silence_audio(sid_or_name=None):
    output.silence(sid_or_name)


def shutdown_audio():
    output.close()


if __name__ == "__main__":
    smp = sample.Sample.from_raw_frames([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 2, 44100, 1)
    chunks = smp.chunked_frame_data(chunksize=51, repeat=True)
    for _ in range(60):
        print(next(chunks).tobytes())
    output = init_audio({
        "explosion": ("explosion.ogg", 99),
        "amoeba": ("amoeba.ogg", 99),
        "game_over": ("game_over.ogg", 99)
    })
    print("PLAY SAMPLED SOUNDS...", output.audio_api)
    print("CHUNK", output.audio_api.chunksize())
    amoeba_sid = output.play_sample("amoeba", repeat=True)
    time.sleep(3)
    print("PLAY ANOTHER SOUND!")
    sid = output.play_sample("game_over", repeat=False)
    time.sleep(0.5)
    print("STOPPING AMOEBA!")
    output.silence("amoeba")
    time.sleep(0.5)
    print("PLAY ANOTHER SOUND!")
    sid = output.play_sample("explosion", repeat=True)
    time.sleep(4)
    print("STOP SOUND!")
    output.silence()
    time.sleep(2)
    print("SHUTDOWN!")
    output.close()
    time.sleep(0.5)
