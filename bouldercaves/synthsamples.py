"""
Synthesized samples.

Written by Irmen de Jong (irmen@razorvine.net) - License: GNU GPL 3.0, see LICENSE
"""

import time
import random
import itertools
from typing import Callable, Generator
from .synthplayer import params as synth_params
from .synthplayer.sample import Sample
from .synthplayer.oscillators import *
from . import audio


_sidfreq = 985248.0 / 16777216.0


class NoteFinished(Exception):
    pass


def sample_from_osc(osc: Oscillator) -> Sample:
    s = Sample.from_oscillator(osc, 5)     # 5 seconds is the maximum it will be.
    return s.stereo()


class TitleMusic(Sample):
    # The title music. It is generated real-time while being played.
    # notes and frequencies taken from https://www.elmerproductions.com/sp/peterb/sounds.html#Theme%20tune
    title_music = [
        (22, 34), (29, 38), (34, 41), (37, 46), (20, 36), (31, 39), (32, 41), (39, 48),
        (18, 42), (18, 44), (30, 46), (18, 49), (32, 44), (51, 55), (33, 45), (49, 53),
        (22, 34), (22, 46), (22, 29), (22, 36), (20, 32), (20, 48), (20, 36), (20, 32),
        (22, 34), (22, 46), (22, 29), (22, 36), (30, 42), (30, 58), (30, 46), (30, 42),
        (20, 44), (20, 44), (20, 27), (20, 34), (28, 40), (28, 56), (28, 44), (28, 40),
        (17, 29), (41, 45), (17, 31), (41, 46), (15, 39), (15, 39), (22, 51), (22, 39),
        (22, 46), (22, 46), (22, 46), (22, 46), (34, 46), (34, 46), (22, 46), (22, 46),
        (20, 46), (20, 46), (20, 46), (20, 46), (32, 46), (32, 46), (20, 46), (20, 46),
        (22, 46), (50, 46), (22, 46), (51, 46), (34, 46), (50, 46), (22, 46), (51, 46),
        (20, 46), (50, 46), (20, 46), (51, 46), (32, 44), (48, 44), (20, 44), (49, 44),
        (22, 46), (22, 58), (22, 46), (53, 56), (34, 46), (34, 55), (22, 46), (49, 53),
        (20, 44), (20, 56), (20, 44), (20, 56), (32, 44), (32, 51), (20, 44), (20, 56),
        (22, 46), (50, 46), (22, 46), (51, 46), (34, 46), (50, 46), (22, 46), (51, 46),
        (20, 46), (50, 46), (20, 46), (51, 46), (32, 44), (48, 44), (20, 44), (49, 44),
        (46, 50), (41, 46), (38, 41), (34, 38), (44, 48), (39, 44), (36, 39), (20, 32),
        (53, 50), (50, 46), (46, 41), (41, 38), (39, 48), (36, 44), (32, 39), (20, 32)
    ]

    music_freq_table = [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        732, 778, 826, 876, 928, 978, 1042, 1100, 1170, 1238, 1312, 1390, 1464, 1556,
        1652, 1752, 1856, 1956, 2084, 2200, 2340, 2476, 2624, 2780, 2928, 3112, 3304,
        3504, 3712, 3912, 4168, 4400, 4680, 4952, 5248, 5560, 5856, 6224, 6608, 7008,
        7424, 7824, 8336, 8800, 9360, 9904, 10496, 11120, 11712
    ]

    adsr_times = (0.001, 0.001, 0.145, 0.01)

    def __init__(self) -> None:
        super().__init__(name="music")

    @property
    def duration(self):
        # set the duration to a quite precise approximation of the length of the synthesized song:
        return sum(self.adsr_times) * len(self.title_music) + 0.005

    def chunked_frame_data(self, chunksize: int, repeat: bool=False,
                           stopcondition: Callable[[], bool]=lambda: False) -> Generator[memoryview, None, None]:
        notes = itertools.cycle(self.title_music) if repeat else iter(self.title_music)
        attack, decay, sustain, release = self.adsr_times

        num_frames = chunksize // synth_params.norm_samplewidth // synth_params.norm_nchannels
        sample_residue = Sample(None, nchannels=2)
        for v1, v2 in notes:
            if stopcondition():
                break
            vf1 = self.music_freq_table[v1]
            vf2 = self.music_freq_table[v2]
            osc1 = FastTriangle(vf1 * _sidfreq, amplitude=0.5)
            osc2 = FastTriangle(vf2 * _sidfreq, amplitude=0.5)
            f1 = EnvelopeFilter(osc1, attack, decay, sustain, 1.0, release, stop_at_end=True)
            f2 = EnvelopeFilter(osc2, attack, decay, sustain, 1.0, release, stop_at_end=True)
            sample1 = Sample.from_oscillator(f1, 1, synth_params.norm_samplerate)       # length is max. 1 second
            sample2 = Sample.from_oscillator(f2, 1, synth_params.norm_samplerate)       # length is max. 1 second
            sample_residue.join(sample1.stereo_mix(sample2, "R"))
            while len(sample_residue) >= num_frames:
                yield sample_residue.view_frame_data()[:chunksize]
                sample_residue = Sample.from_raw_frames(sample_residue.view_frame_data()[chunksize:],
                                                        sample_residue.samplewidth, sample_residue.samplerate, sample_residue.nchannels)
        if len(sample_residue):
            yield sample_residue.view_frame_data()


class RealtimeSynthesizedSample(Sample):
    def __init__(self, name: str) -> None:
        super().__init__(name=name)

    def chunked_frame_data(self, chunksize: int, repeat: bool=False,
                           stopcondition: Callable[[], bool]=lambda: False) -> Generator[memoryview, None, None]:
        raise NotImplementedError("subclass should implement this")

    def render_samples(self, osc: Oscillator, samplebuffer: bytes,
                       sample_chunksize: int, stopcondition: Callable[[], bool]=lambda: False,
                       return_remaining_buffer: bool=False) -> Generator[memoryview, None, bytes]:
        num_frames = sample_chunksize // synth_params.norm_samplewidth // synth_params.norm_nchannels
        while not stopcondition():
            # render this sample in chunks of the asked size
            try:
                while len(samplebuffer) < sample_chunksize:
                    # fill up the sample buffer so we have at least one full chunk
                    print("NUM_FRAMES", num_frames)  # XXX
                    sample = sample_from_osc(osc)
                    print(sample, len(sample))
                    samplebuffer += sample.view_frame_data()    # type: ignore
            except NoteFinished:
                # go to next sample
                break
            if samplebuffer:
                chunk = samplebuffer[:sample_chunksize]
                samplebuffer = samplebuffer[sample_chunksize:]
                assert len(chunk) == sample_chunksize
                yield memoryview(chunk)
            else:
                break
        if return_remaining_buffer:
            return samplebuffer
        yield memoryview(samplebuffer)
        return samplebuffer


class Amoeba(RealtimeSynthesizedSample):
    def __init__(self) -> None:
        super().__init__(name="amoeba")

    def chunked_frame_data(self, chunksize: int, repeat: bool=False,
                           stopcondition: Callable[[], bool]=lambda: False) -> Generator[memoryview, None, None]:
        assert repeat, "amoeba is a repeating sound"
        samplebuffer = b""
        while not stopcondition():
            freq = random.randint(0x0800, 0x1200)
            osc = FastTriangle(freq * _sidfreq, amplitude=0.75)
            filtered = EnvelopeFilter(osc, 0.024, 0.006, 0.0, 0.5, 0.003, stop_at_end=True)
            samplebuffer = yield from self.render_samples(filtered, samplebuffer, chunksize, return_remaining_buffer=True)


class MagicWall(RealtimeSynthesizedSample):
    def __init__(self) -> None:
        super().__init__(name="magic_wall")

    def chunked_frame_data(self, chunksize: int, repeat: bool=False,
                           stopcondition: Callable[[], bool]=lambda: False) -> Generator[memoryview, None, None]:
        assert repeat, "magic_wall is a repeating sound"
        samplebuffer = b""
        while not stopcondition():
            freq = random.randint(0x8600, 0x9f00)
            freq &= 0b0001100100000000
            freq |= 0b1000011000000000
            osc = FastTriangle(freq * _sidfreq, amplitude=0.4)
            filtered = EnvelopeFilter(osc, 0.002, 0.008, 0.0, 0.6, 0.03, stop_at_end=True)
            samplebuffer = yield from self.render_samples(filtered, samplebuffer, chunksize, return_remaining_buffer=True)


class Cover(RealtimeSynthesizedSample):
    def __init__(self) -> None:
        super().__init__(name="cover")

    def chunked_frame_data(self, chunksize: int, repeat: bool=False,
                           stopcondition: Callable[[], bool]=lambda: False) -> Generator[memoryview, None, None]:
        assert repeat, "cover is a repeating sound"
        samplebuffer = b""
        while not stopcondition():
            freq = random.randint(0x6000, 0xd800)
            osc = FastTriangle(freq * _sidfreq, amplitude=0.7)
            filtered = EnvelopeFilter(osc, 0.002, 0.02, 0.0, 0.5, 0.02, stop_at_end=True)
            samplebuffer = yield from self.render_samples(filtered, samplebuffer, chunksize, return_remaining_buffer=True)


class Finished(RealtimeSynthesizedSample):
    def __init__(self) -> None:
        super().__init__(name="finished")

    def chunked_frame_data(self, chunksize: int, repeat: bool=False,
                           stopcondition: Callable[[], bool]=lambda: False) -> Generator[memoryview, None, None]:
        assert not repeat
        samplebuffer = b""
        for n in range(0, 180):
            if stopcondition():
                break
            freq = 0x8000 - n * 180
            osc = FastTriangle(freq * _sidfreq, amplitude=0.8)
            filtered = EnvelopeFilter(osc, 0.002, 0.004, 0.0, 0.6, 0.02, stop_at_end=True)
            samplebuffer = yield from self.render_samples(filtered, samplebuffer, chunksize, return_remaining_buffer=True)
        if samplebuffer:
            yield memoryview(samplebuffer)


class ExtraLife(Sample):
    def __init__(self) -> None:
        super().__init__(name="extra_life")
        for n in range(0, 16):
            freq = 0x1400 + n * 1024
            osc = FastTriangle(freq * _sidfreq, amplitude=0.8)
            filtered = EnvelopeFilter(osc, 0.002, 0.024, 0.0, 0.6, 0.03, stop_at_end=True)
            self.join(sample_from_osc(filtered))


class GameOver(RealtimeSynthesizedSample):
    def __init__(self) -> None:
        super().__init__(name="game_over")

    def chunked_frame_data(self, chunksize: int, repeat: bool=False,
                           stopcondition: Callable[[], bool]=lambda: False) -> Generator[memoryview, None, None]:
        assert not repeat
        fm = Linear(0, -2.3e-5)
        osc = Triangle(1567.98174, fm_lfo=fm)
        filtered = EnvelopeFilter(osc, 0.1, 0.3, 1.5, 1.0, 0.07, stop_at_end=True)
        ampmod = SquareH(10, 9, amplitude=0.5, bias=0.5)
        modulated = AmpModulationFilter(filtered, ampmod)
        yield from self.render_samples(modulated, b"", chunksize, stopcondition=stopcondition)


class WalkDirt(Sample):
    def __init__(self) -> None:
        super().__init__(name="walk_dirt")
        osc = WhiteNoise(0x5000, amplitude=0.3)
        filtered = EnvelopeFilter(osc, 0.034, 0.006, 0.0, 0.5, 0.008, stop_at_end=True)
        self.join(sample_from_osc(filtered))


class WalkEmpty(Sample):
    def __init__(self) -> None:
        super().__init__(name="walk_empty")
        osc = WhiteNoise(0x1200, amplitude=0.2)
        filtered = EnvelopeFilter(osc, 0.034, 0.006, 0.0, 0.5, 0.008, stop_at_end=True)
        self.join(sample_from_osc(filtered))


class Explosion(Sample):
    def __init__(self) -> None:
        super().__init__(name="explosion")
        osc = WhiteNoise(0x1432, amplitude=0.8)
        filtered = EnvelopeFilter(osc, 0.008, 0.1, 0.0, 0.5, 1.5, stop_at_end=True)
        self.join(sample_from_osc(filtered))


class VoodooExplosion(Sample):
    def __init__(self) -> None:
        super().__init__(name="voodoo_explosion")
        osc5 = WhiteNoise(1200, amplitude=0.4)
        fm = Sine(5, 0.49, bias=0.5)
        osc4 = Sine(146.83238, 0.7, fm_lfo=fm)
        f1 = EnvelopeFilter(osc5, 0.02, 0.02, 0, 0.72, 1.5, stop_at_end=True)
        f2 = EnvelopeFilter(osc4, 0.18, 0.16, 0, 0.48, 1.2, stop_at_end=True)
        filtered = MixingFilter(f1, f2)
        self.join(sample_from_osc(filtered))


class CollectDiamond(Sample):
    def __init__(self) -> None:
        super().__init__(name="collect_diamond")
        osc = FastTriangle(0x1478 * _sidfreq, amplitude=0.8)
        filtered = EnvelopeFilter(osc, 0.002, 0.006, 0.0, 0.7, 0.65, stop_at_end=True)
        self.join(sample_from_osc(filtered))


class Boulder(Sample):
    def __init__(self) -> None:
        super().__init__(name="boulder")
        osc = WhiteNoise(0x0932, amplitude=0.8)
        filtered = EnvelopeFilter(osc, 0.08, 0.08, 0.0, 0.4, 0.65, stop_at_end=True)
        self.join(sample_from_osc(filtered))


class Crack(Sample):
    def __init__(self) -> None:
        super().__init__(name="crack")
        osc = WhiteNoise(0x2F32, amplitude=0.8)
        filtered = EnvelopeFilter(osc, 0.008, 0.075, 0.0, 0.4, 0.65, stop_at_end=True)
        self.join(sample_from_osc(filtered))


class BoxPush(Sample):
    def __init__(self) -> None:
        super().__init__(name="boxpush")
        osc = WhiteNoise(2637, amplitude=0.6)
        filtered = EnvelopeFilter(osc, 0.2, 0.2, 0.0, 0.25, 0, stop_at_end=True)
        self.join(sample_from_osc(filtered))


class Diamond(RealtimeSynthesizedSample):
    def __init__(self) -> None:
        super().__init__(name="diamond")

    def chunked_frame_data(self, chunksize: int, repeat: bool=False,
                           stopcondition: Callable[[], bool]=lambda: False) -> Generator[memoryview, None, None]:
        # generate a new random diamond sound everytime this is played
        freq = random.randint(0x8600, 0xfeff)
        freq &= 0b0111100011111111
        freq |= 0b1000011000000000
        osc = FastTriangle(freq * _sidfreq, amplitude=0.7)
        filtered = EnvelopeFilter(osc, 0.002, 0.006, 0.0, 0.7, 0.6, stop_at_end=True)
        yield from self.render_samples(filtered, b"", chunksize, stopcondition=stopcondition)


class Timeout(Sample):
    def __init__(self, timeout: int) -> None:
        super().__init__(name="timeout_" + str(timeout))
        self._timeout = timeout
        osc = FastTriangle((timeout * 256 + 0x1E00) * _sidfreq, amplitude=0.99)
        filtered = EnvelopeFilter(osc, 0.002, 0.2, 0.1, 0.5, 0.8, stop_at_end=True)
        self.join(sample_from_osc(filtered))

    def copy(self) -> 'Timeout':
        cpy = Timeout(self._timeout)
        cpy.copy_from(self)
        return cpy


class Slime(Sample):
    def __init__(self) -> None:
        super().__init__(name="slime")
        fm = FastTriangle(5, 0.5)
        osc = Sine(261.62556, 0.25, fm_lfo=fm)
        filtered = EnvelopeFilter(osc, 0, 0, 0, 1, 0.41, stop_at_end=True)
        self.join(sample_from_osc(filtered))


def demo():
    api = audio.best_api()

    # ----- slime
    print("Slime")
    sample = Slime()
    api.play(sample)
    time.sleep(sample.duration + 0.1)

    # ------ explosion
    print("Explosion")
    sample = Explosion()
    api.play(sample)
    time.sleep(sample.duration + 0.1)

    # ------ voodoo explosion
    print("Voodoo Explosion")
    sample = VoodooExplosion()
    api.play(sample)
    time.sleep(sample.duration + 0.1)

    # ------ diamond
    print("Diamonds")
    for _ in range(10):
        sample = Diamond()
        api.play(sample)
        time.sleep(0.3)

    # ---- collect diamond
    print("Collect diamond")
    sample = CollectDiamond()
    api.play(sample)
    time.sleep(sample.duration + 0.1)

    # ------ boulder
    print("Boulder")
    sample = Boulder()
    api.play(sample)
    time.sleep(sample.duration + 0.1)

    # ------ crack
    print("Crack")
    sample = Crack()
    api.play(sample)
    time.sleep(sample.duration + 0.1)

    # ---- out of time
    print("Out of time")
    for n in range(1, 10):
        sample = Timeout(n)
        api.play(sample)
        time.sleep(sample.duration + 0.02)

    # ---- (un)cover
    print("(Un)cover")
    sample = Cover()
    api.play(sample, repeat=True)
    time.sleep(max(4, sample.duration + 0.5))
    api.silence()

    # ------ Amoeba
    print("Amoeba")
    sample = Amoeba()
    api.play(sample, repeat=True)
    time.sleep(max(4, sample.duration + 0.5))
    api.silence()

    # ------- Magic wall
    print("Magic wall")
    sample = MagicWall()
    api.play(sample, repeat=True)
    time.sleep(max(4, sample.duration + 0.5))
    api.silence()

    # ------ moving
    print("Move (dirt)")
    sample = WalkDirt()
    for _ in range(10):
        api.play(sample)
        time.sleep(sample.duration + 0.1)
    print("Move (space)")
    sample = WalkEmpty()
    for _ in range(10):
        api.play(sample)
        time.sleep(sample.duration + 0.1)

    # ----- box push
    print("Box Push")
    sample = BoxPush()
    api.play(sample)
    time.sleep(sample.duration)

    # ----- extra life
    print("Extra life")
    sample = ExtraLife()
    api.play(sample)
    time.sleep(sample.duration + 0.5)

    # ----- game over
    print("Game over")
    sample = GameOver()
    api.play(sample)
    time.sleep(max(3, sample.duration + 0.5))

    # ----- finished
    print("Finished")
    sample = Finished()
    api.play(sample)
    time.sleep(max(5, sample.duration + 0.5))

    # ----- title music
    print("Title music")
    sample = TitleMusic()
    api.play(sample, repeat=True)
    time.sleep(min(5, sample.duration + 0.1))

    print("CLOSING!")
    api.close()


if __name__ == "__main__":
    demo()
