"""
Various audio output options. Here the specific audio library code is located.
Supported audio output libraries:
- pyaudio
- sounddevice (both thread+blocking stream, and nonblocking callback stream variants)
- winsound (limited capabilities)

It can play multiple samples at the same time via real-time mixing, and you can
loop samples as well without noticable overhead (great for continous effects or music)

Written by Irmen de Jong (irmen@razorvine.net) - License: MIT open-source.
"""

import audioop      # type: ignore
import queue
import threading
import tempfile
import time
import os
from collections import defaultdict
from typing import Generator, Union, Dict, Tuple, Any, List, Callable
from .import params
from .sample import Sample


__all__ = ["Output", "best_api"]


# stubs for optional audio library modules:
sounddevice = None
pyaudio = None
winsound = None


def best_api(samplerate=0, samplewidth=0, nchannels=0, chunkduration=0, mixing="mix", queue_size=100):
    if mixing not in ("mix", "sequential"):
        raise ValueError("invalid mix mode, must be mix or sequential")
    if mixing == "mix":
        candidates = [Sounddevice_Mix, SounddeviceThread_Mix, PyAudio_Mix]
    else:
        candidates = [SounddeviceThread_Seq, PyAudio_Seq, Winsound_Seq]
    for candidate in candidates:
        try:
            if mixing == "mix":
                return candidate(samplerate, samplewidth, nchannels, chunkduration)
            else:
                return candidate(samplerate, samplewidth, nchannels, chunkduration, queue_size)
        except ImportError:
            continue
    raise Exception("no supported audio output api available")


class RealTimeMixer:
    """
    Real-time audio sample mixer. Samples are played as soon as they're added into the mix.
    Simply adds a number of samples, clipping if values become too large.
    Produces (via a generator method) chunks of audio stream data to be fed to the sound output stream.
    """
    def __init__(self, chunksize: int, all_played_callback: Callable=None) -> None:
        self.chunksize = chunksize
        self.all_played_callback = all_played_callback or (lambda: None)
        self.add_lock = threading.Lock()
        self.chunks_mixed = 0
        self._sid = 0
        self.active_samples = {}   # type: Dict[int, Tuple[str, int, Generator[memoryview, None, None]]]
        self.sample_counts = defaultdict(int)  # type: Dict[str, int]
        self.sample_limits = defaultdict(lambda: 9999999)  # type: Dict[str, int]

    def add_sample(self, sample: Sample, repeat: bool=False, sid: int=None, chunks_delay: int=0) -> Union[int, None]:
        if not self.allow_sample(sample, repeat):
            return None
        with self.add_lock:
            sample_chunks = sample.chunked_frame_data(chunksize=self.chunksize, repeat=repeat)
            self._sid += 1
            sid = sid or self._sid
            self.active_samples[sid] = (sample.name, self.chunks_mixed+chunks_delay, sample_chunks)
            self.sample_counts[sample.name] += 1
            return sid

    def allow_sample(self, sample: Sample, repeat: bool=False) -> bool:
        if repeat and self.sample_counts[sample.name] >= 1:  # don't allow more than one repeating sample
            return False
        if not sample.name:
            return True     # samples without a name can't be checked
        return self.sample_counts[sample.name] < self.sample_limits[sample.name]

    def determine_samples_to_mix(self) -> List[Tuple[int, Tuple[str, Generator[memoryview, None, None]]]]:
        active = []
        with self.add_lock:
            for sid, (name, mix_after_chunk, sample) in self.active_samples.items():
                if mix_after_chunk <= self.chunks_mixed:
                    active.append((sid, (name, sample)))
        return active

    def clear_sources(self) -> None:
        # clears all sources
        with self.add_lock:
            self.active_samples.clear()
            self.sample_counts.clear()
            self.all_played_callback()

    def clear_source(self, sid_or_name: Union[int, str]) -> None:
        # clear a single sample source by its sid or all sources with the sample name
        if isinstance(sid_or_name, int):
            self.remove_sample(sid_or_name)
        else:
            active_samples = self.determine_samples_to_mix()
            for sid, (name, _) in active_samples:
                if name == sid_or_name:
                    self.remove_sample(sid)

    def chunks(self) -> Generator[memoryview, None, None]:
        silence = b"\0" * self.chunksize
        while True:
            chunks_to_mix = []
            active_samples = self.determine_samples_to_mix()
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
            chunks_to_mix = chunks_to_mix or [silence]      # type: ignore
            assert all(len(c) == self.chunksize for c in chunks_to_mix)
            mixed = chunks_to_mix[0]
            if len(chunks_to_mix) > 1:
                for to_mix in chunks_to_mix[1:]:
                    mixed = audioop.add(mixed, to_mix, params.norm_nchannels)
                mixed = memoryview(mixed)
            self.chunks_mixed += 1
            yield mixed

    def remove_sample(self, sid: int) -> None:
        with self.add_lock:
            name = self.active_samples[sid][0]
            del self.active_samples[sid]
            self.sample_counts[name] -= 1
            if not self.active_samples:
                self.all_played_callback()

    def set_limit(self, samplename: str, max_simultaneously: int) -> None:
        self.sample_limits[samplename] = max_simultaneously


class AudioApi:
    """Base class for the various audio APIs."""
    def __init__(self, samplerate: int=0, samplewidth: int=0, nchannels: int=0,
                 chunkduration: float=0.0, queue_size: int=100) -> None:
        self.samplerate = samplerate or params.norm_samplerate
        self.samplewidth = samplewidth or params.norm_samplewidth
        self.nchannels = nchannels or params.norm_nchannels
        self.chunkduration = chunkduration or params.norm_chunk_duration
        self.supports_streaming = True
        self.all_played = threading.Event()
        self.playing_callback = None
        self.queue_size = queue_size
        self.mixer = RealTimeMixer(self.chunksize(), self._all_played_callback)
        # the actual playback of the samples from the queue is done in the various subclasses

    def __str__(self) -> str:
        api_ver = self.query_api_version()
        if api_ver and api_ver != "unknown":
            return self.__class__.__name__ + ", " + self.query_api_version()
        else:
            return self.__class__.__name__

    def chunksize(self) -> int:
        return int(self.samplerate * self.samplewidth * self.nchannels * self.chunkduration)

    def play(self, sample: Sample, repeat: bool=False, chunks_delay: int=0) -> int:
        self.all_played.clear()
        return self.mixer.add_sample(sample, repeat, chunks_delay=chunks_delay) or 0

    def silence(self) -> None:
        self.mixer.clear_sources()
        self.all_played.set()

    def stop(self, sid_or_name: Union[int, str]) -> None:
        self.mixer.clear_source(sid_or_name)

    def set_sample_play_limit(self, samplename: str, max_simultaneously: int) -> None:
        self.mixer.set_limit(samplename, max_simultaneously)

    def close(self) -> None:
        self.silence()

    def query_api_version(self) -> str:
        return "unknown"

    def query_apis(self) -> List[Dict]:
        return []

    def query_devices(self) -> List[Dict]:
        return []

    def query_device_details(self, device=None, kind=None) -> Any:
        raise NotImplementedError("not available for this audio API")

    def wait_all_played(self):
        self.all_played.wait()

    def still_playing(self) -> bool:
        return not self.all_played.is_set()

    def register_notify_played(self, callback):
        self.playing_callback = callback

    def _all_played_callback(self):
        self.all_played.set()


class Sounddevice_Mix(AudioApi):
    """Api to the more featureful sounddevice library (that uses portaudio) -
    using callback stream, without a separate audio output thread"""
    def __init__(self, samplerate: int=0, samplewidth: int=0, nchannels: int=0, chunkduration: float=0.0) -> None:
        super().__init__(samplerate, samplewidth, nchannels, chunkduration, 0)
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
        self._empty_sound_data = b"\0" * self.chunksize()
        self.mixed_chunks = self.mixer.chunks()
        self.stream = sounddevice.RawOutputStream(self.samplerate, channels=self.nchannels, dtype=dtype,        # type: ignore
                                                  blocksize=self.chunksize() // self.nchannels // self.samplewidth,
                                                  callback=self.streamcallback)
        self.stream.start()

    def query_api_version(self):
        return sounddevice.get_portaudio_version()[1]

    def query_apis(self):
        return list(sounddevice.query_hostapis())

    def query_devices(self):
        return list(sounddevice.query_devices())

    def query_device_details(self, device=None, kind=None):
        return sounddevice.query_devices(device, kind)

    def close(self):
        super().close()
        self.stream.stop()

    def streamcallback(self, outdata, frames, time, status):
        data = next(self.mixed_chunks)
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
        if self.playing_callback:
            sample = Sample.from_raw_frames(outdata[:], self.samplewidth, self.samplerate, self.nchannels)
            self.playing_callback(sample)


class SounddeviceThread_Mix(AudioApi):
    """Api to the more featureful sounddevice library (that uses portaudio) -
    using blocking streams with an audio output thread"""
    def __init__(self, samplerate: int=0, samplewidth: int=0, nchannels: int=0, chunkduration: float=0.0) -> None:
        super().__init__(samplerate, samplewidth, nchannels, chunkduration, 0)
        global sounddevice
        import sounddevice      # type: ignore
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
            mixed_chunks = self.mixer.chunks()
            stream = sounddevice.RawOutputStream(self.samplerate, channels=self.nchannels, dtype=dtype)
            stream.start()
            thread_ready.set()
            try:
                silence = b"\0" * self.chunksize()
                while True:
                    data = next(mixed_chunks) or silence
                    stream.write(data)
                    if len(data) < self.chunksize():
                        stream.write(silence[:self.chunksize()-len(data)])
                    if self.playing_callback:
                        sample = Sample.from_raw_frames(data, self.samplewidth, self.samplerate, self.nchannels)
                        self.playing_callback(sample)
            finally:
                stream.stop()
                stream.close()

        self.output_thread = threading.Thread(target=audio_thread, name="audio-sounddevice", daemon=True)
        self.output_thread.start()
        thread_ready.wait()

    def query_api_version(self):
        return sounddevice.get_portaudio_version()[1]

    def query_apis(self):
        return list(sounddevice.query_hostapis())

    def query_devices(self):
        return list(sounddevice.query_devices())

    def query_device_details(self, device=None, kind=None):
        return sounddevice.query_devices(device, kind)


class SounddeviceThread_Seq(AudioApi):
    """Api to the more featureful sounddevice library (that uses portaudio) -
    using blocking streams with an audio output thread"""
    def __init__(self, samplerate: int=0, samplewidth: int=0, nchannels: int=0,
                 chunkduration: float=0.0, queue_size: int=100) -> None:
        super().__init__(samplerate, samplewidth, nchannels, chunkduration, queue_size)
        global sounddevice
        import sounddevice      # type: ignore
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
        del self.mixer
        self.command_queue = queue.Queue(maxsize=queue_size)        # type: queue.Queue[Dict[str, Any]]

        def audio_thread():
            stream = sounddevice.RawOutputStream(self.samplerate, channels=self.nchannels, dtype=dtype)
            stream.start()
            thread_ready.set()
            try:
                while True:
                    data = b""
                    try:
                        command = self.command_queue.get(timeout=0.2)
                        if command is None or command["action"] == "stop":
                            break
                        elif command["action"] == "play":
                            data = command["sample"].view_frame_data() or b""
                    except queue.Empty:
                        self.all_played.set()
                        data = b""
                    if data:
                        stream.write(data)
                        if self.playing_callback:
                            sample = Sample.from_raw_frames(data, self.samplewidth, self.samplerate, self.nchannels)
                            self.playing_callback(sample)
            finally:
                self.all_played.set()
                stream.stop()
                stream.close()

        self.output_thread = threading.Thread(target=audio_thread, name="audio-sounddevice-seq", daemon=True)
        self.output_thread.start()
        thread_ready.wait()

    def play(self, sample: Sample, repeat: bool=False, chunks_delay: int=0) -> int:
        self.all_played.clear()
        self.command_queue.put({"action": "play", "sample": sample})
        return 0

    def silence(self) -> None:
        try:
            while True:
                self.command_queue.get(block=False)
        except queue.Empty:
            pass
        self.all_played.set()

    def stop(self, sid_or_name: Union[int, str]) -> None:
        raise NotImplementedError("sequential play mode doesn't support stopping individual samples")

    def close(self) -> None:
        super().close()
        self.command_queue.put({"action": "stop"})

    def set_sample_play_limit(self, samplename: str, max_simultaneously: int) -> None:
        raise NotImplementedError("sequential play mode doesn't support setting sample limits")

    def query_api_version(self):
        return sounddevice.get_portaudio_version()[1]

    def query_apis(self):
        return list(sounddevice.query_hostapis())

    def query_devices(self):
        return list(sounddevice.query_devices())

    def query_device_details(self, device=None, kind=None):
        return sounddevice.query_devices(device, kind)


class PyAudio_Mix(AudioApi):
    """Api to the somewhat older pyaudio library (that uses portaudio)"""
    def __init__(self, samplerate: int=0, samplewidth: int=0, nchannels: int=0, chunkduration: float=0.0) -> None:
        super().__init__(samplerate, samplewidth, nchannels, chunkduration, 0)
        global pyaudio
        import pyaudio      # type: ignore
        thread_ready = threading.Event()

        def audio_thread():
            audio = pyaudio.PyAudio()
            try:
                mixed_chunks = self.mixer.chunks()
                audio_format = audio.get_format_from_width(self.samplewidth) if self.samplewidth != 4 else pyaudio.paInt32
                stream = audio.open(format=audio_format, channels=self.nchannels, rate=self.samplerate, output=True)
                thread_ready.set()
                try:
                    silence = b"\0" * self.chunksize()
                    while True:
                        data = next(mixed_chunks) or silence
                        if isinstance(data, memoryview):
                            data = data.tobytes()   # PyAudio stream can't deal with memoryview
                        stream.write(data)
                        if len(data) < self.chunksize():
                            stream.write(silence[:self.chunksize()-len(data)])
                        if self.playing_callback:
                            sample = Sample.from_raw_frames(data, self.samplewidth, self.samplerate, self.nchannels)
                            self.playing_callback(sample)
                finally:
                    stream.close()
            finally:
                audio.terminate()

        outputter = threading.Thread(target=audio_thread, name="audio-pyaudio", daemon=True)
        outputter.start()
        thread_ready.wait()

    def query_api_version(self):
        return pyaudio.get_portaudio_version_text()

    def query_devices(self):
        audio = pyaudio.PyAudio()
        try:
            num_devices = audio.get_device_count()
            info = [audio.get_device_info_by_index(i) for i in range(num_devices)]
            return info
        finally:
            audio.terminate()

    def query_apis(self):
        audio = pyaudio.PyAudio()
        try:
            num_apis = audio.get_host_api_count()
            info = [audio.get_host_api_info_by_index(i) for i in range(num_apis)]
            return info
        finally:
            audio.terminate()


class PyAudio_Seq(AudioApi):
    """Api to the somewhat older pyaudio library (that uses portaudio)"""
    def __init__(self, samplerate: int=0, samplewidth: int=0, nchannels: int=0,
                 chunkduration: float=0.0, queue_size: int=100) -> None:
        super().__init__(samplerate, samplewidth, nchannels, chunkduration, queue_size)
        global pyaudio
        import pyaudio      # type: ignore
        thread_ready = threading.Event()
        del self.mixer
        self.command_queue = queue.Queue(maxsize=queue_size)        # type: queue.Queue[Dict[str, Any]]

        def audio_thread():
            audio = pyaudio.PyAudio()
            try:
                audio_format = audio.get_format_from_width(self.samplewidth) if self.samplewidth != 4 else pyaudio.paInt32
                stream = audio.open(format=audio_format, channels=self.nchannels, rate=self.samplerate, output=True)
                thread_ready.set()
                try:
                    while True:
                        data = b""
                        try:
                            command = self.command_queue.get(timeout=0.2)
                            if command is None or command["action"] == "stop":
                                break
                            elif command["action"] == "play":
                                data = command["sample"].view_frame_data() or b""
                        except queue.Empty:
                            self.all_played.set()
                            data = b""
                        if data:
                            if isinstance(data, memoryview):
                                data = data.tobytes()    # pyaudio doesn't support memoryview objects
                            stream.write(data)
                            if self.playing_callback:
                                sample = Sample.from_raw_frames(data, self.samplewidth, self.samplerate, self.nchannels)
                                self.playing_callback(sample)
                finally:
                    self.all_played.set()
                    stream.close()
            finally:
                audio.terminate()

        outputter = threading.Thread(target=audio_thread, name="audio-pyaudio", daemon=True)
        outputter.start()
        thread_ready.wait()

    def play(self, sample: Sample, repeat: bool=False, chunks_delay: int=0) -> int:
        self.all_played.clear()
        self.command_queue.put({"action": "play", "sample": sample})
        return 0

    def silence(self) -> None:
        try:
            while True:
                self.command_queue.get(block=False)
        except queue.Empty:
            pass
        self.all_played.set()

    def stop(self, sid_or_name: Union[int, str]) -> None:
        raise NotImplementedError("sequential play mode doesn't support stopping individual samples")

    def close(self) -> None:
        super().close()
        self.command_queue.put({"action": "stop"})

    def query_api_version(self):
        return pyaudio.get_portaudio_version_text()

    def query_devices(self):
        audio = pyaudio.PyAudio()
        try:
            num_devices = audio.get_device_count()
            info = [audio.get_device_info_by_index(i) for i in range(num_devices)]
            return info
        finally:
            audio.terminate()

    def query_apis(self):
        audio = pyaudio.PyAudio()
        try:
            num_apis = audio.get_host_api_count()
            info = [audio.get_host_api_info_by_index(i) for i in range(num_apis)]
            return info
        finally:
            audio.terminate()


class Winsound_Seq(AudioApi):
    """Minimally featured api for the winsound library that comes with Python"""
    def __init__(self, samplerate: int=0, samplewidth: int=0, nchannels: int=0,
                 chunkduration: float=0.0, queue_size: int=100) -> None:
        super().__init__(samplerate, samplewidth, nchannels, chunkduration, 0)
        self.supports_streaming = False
        import winsound as _winsound        # type: ignore
        global winsound
        winsound = _winsound
        self.threads = []       # type: List[threading.Thread]
        self.played_callback = None

    def play(self, sample: Sample, repeat: bool=False, chunks_delay: int=0) -> int:
        # plays the sample in a background thread so that we can continue while the sound plays.
        # we don't use SND_ASYNC because that complicates cleaning up the temp files a lot.
        if repeat:
            raise ValueError("winsound player doesn't support repeating samples")
        if chunks_delay != 0:
            raise ValueError("winsound player doesn't support delayed playing")
        self.wait_all_played()
        t = threading.Thread(target=self._play, args=(sample,), daemon=True)
        self.threads.append(t)
        t.start()
        time.sleep(0.0005)
        return 0

    def _play(self, sample):
        with tempfile.NamedTemporaryFile(delete=False) as sample_file:
            sample.write_wav(sample_file)
            sample_file.flush()
            winsound.PlaySound(sample_file.name, winsound.SND_FILENAME)
            if self.played_callback:
                self.played_callback(sample)
        os.unlink(sample_file.name)

    def wait_all_played(self):
        while self.threads:
            t = self.threads.pop()
            t.join()

    def still_playing(self) -> bool:
        return bool(self.threads)


class Output:
    """Plays samples to audio output device or streams them to a file."""
    def __init__(self, samplerate=0, samplewidth=0, nchannels=0, chunkduration=0, mixing="mix", queue_size=100):
        self.samplerate = self.samplewidth = self.nchannels = 0
        self.chunkduration = 0.0
        self.audio_api = None
        self.mixing = ""
        self.queue_size = -1
        self.reset_params(samplerate, samplewidth, nchannels, chunkduration, mixing, queue_size)
        self.supports_streaming = self.audio_api.supports_streaming

    def __repr__(self):
        return "<Output at 0x{0:x}, {1:d} channels, {2:d} bits, rate {3:d}>"\
            .format(id(self), self.nchannels, 8*self.samplewidth, self.samplerate)

    @classmethod
    def for_sample(cls, sample: Sample, chunkduration: int=0, mixing: str="mix") -> 'Output':
        return cls(sample.samplerate, sample.samplewidth, sample.nchannels, chunkduration, mixing)

    def __enter__(self):
        return self

    def __exit__(self, xtype, value, traceback):
        self.close()

    def close(self):
        self.audio_api.close()

    def reset_params(self, samplerate: int, samplewidth: int, nchannels: int,
                     chunkduration: float, mixing: str, queue_size: int) -> None:
        if mixing not in ("mix", "sequential"):
            raise ValueError("invalid mix mode, must be mix or sequential")
        if self.audio_api is not None:
            if samplerate == self.samplerate and samplewidth == self.samplewidth and nchannels == self.nchannels \
                    and chunkduration == self.chunkduration and mixing == self.mixing and queue_size == self.queue_size:
                return   # nothing changed
        if self.audio_api:
            self.audio_api.close()
            self.audio_api.wait_all_played()
        self.samplerate = samplerate or params.norm_samplerate
        self.samplewidth = samplewidth or params.norm_samplewidth
        self.nchannels = nchannels or params.norm_nchannels
        self.chunkduration = chunkduration or params.norm_chunk_duration
        self.mixing = mixing
        self.queue_size = queue_size
        self.audio_api = best_api(self.samplerate, self.samplewidth, self.nchannels,
                                  self.chunkduration, self.mixing, self.queue_size)

    def play_sample(self, sample, repeat: bool=False, delay=0.0) -> int:
        """Play a single sample (asynchronously)."""
        assert sample.samplewidth == self.samplewidth
        assert sample.samplerate == self.samplerate
        assert sample.nchannels == self.nchannels
        return self.audio_api.play(sample, repeat, delay/self.chunkduration)

    def stop_sample(self, sid_or_name: Union[int, str]) -> None:
        self.audio_api.stop(sid_or_name)

    def wait_all_played(self):
        self.audio_api.wait_all_played()

    def still_playing(self) -> bool:
        return self.audio_api.still_playing()

    def normalized_samples(self, samples, global_amplification=26000):
        """Generator that produces samples normalized to 16 bit using a single amplification value for all."""
        for sample in samples:
            if sample.samplewidth != 2:
                # We can't use automatic global max amplitude because we're streaming
                # the samples individually. So use a fixed amplification value instead
                # that will be used to amplify all samples in stream by the same amount.
                sample = sample.amplify(global_amplification).make_16bit(False)
            if sample.nchannels == 1:
                sample.stereo()
            assert sample.nchannels == 2
            assert sample.samplerate == 44100
            assert sample.samplewidth == 2
            yield sample

    def stream_to_file(self, filename, samples):
        """Saves the samples after each other into one single output wav file."""
        samples = self.normalized_samples(samples, 26000)
        sample = next(samples)
        with Sample.wave_write_begin(filename, sample) as out:
            for sample in samples:
                Sample.wave_write_append(out, sample)
            Sample.wave_write_end(out)

    def silence(self):
        """Remove all pending samples to be played from the queue"""
        self.audio_api.silence()

    def register_notify_played(self, callback):
        self.audio_api.register_notify_played(callback)