"""
Synthesized samples.

Written by Irmen de Jong (irmen@razorvine.net) - License: MIT open-source.
"""

import time
import audioop
import array
import random
import itertools
from typing import Callable, Generator
from .synth import FastTriangle, WhiteNoise, Linear, Triangle, SquareH, EnvelopeFilter, AmpModulationFilter, note_freq
from . import audio


_sidfreq = 985248.0 / 16777216.0


def sample_from_osc(osc, raw=False, chunksize=0):
    scale = 2 ** (audio.norm_samplewidth * 8 - 1) - 1
    sounddata = array.array('h')
    if chunksize:
        try:
            for _ in range(chunksize):
                sounddata.append(int(scale * next(osc)))
        except StopIteration:
            pass
    else:
        for v in osc:
            sounddata.append(int(scale * v))
    sounddata = sounddata.tobytes()
    if len(sounddata) == 0:
        raise StopIteration
    if raw:
        return sounddata
    sounddata = audioop.tostereo(sounddata, audio.norm_samplewidth, 1, 1)
    return audio.Sample("sample", pcmdata=sounddata)


class TitleMusic(audio.Sample):
    # The title music. It is generated real-time while being played.
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
        super().__init__("music", pcmdata=b"")
        # set the duration to a quite precise approximation of the length of the synthesized song:
        self.duration = len(self.title_music) * sum(self.adsr_times) + 0.005

    def chunked_data(self, chunksize: int, repeat: bool=False,
                     stopcondition: Callable[[], bool]=lambda: False) -> Generator[memoryview, None, None]:
        notes = self.title_music
        if repeat:
            notes = itertools.cycle(notes)
        attack, decay, sustain, release = self.adsr_times

        class NoteFinished(Exception):
            pass

        samplebuffer = b""
        for v1, v2 in notes:
            if stopcondition():
                break
            vf1 = self.music_freq_table[v1]
            vf2 = self.music_freq_table[v2]
            osc1 = FastTriangle(vf1 * _sidfreq, amplitude=0.5, samplerate=audio.norm_samplerate)
            osc2 = FastTriangle(vf2 * _sidfreq, amplitude=0.5, samplerate=audio.norm_samplerate)
            f1 = EnvelopeFilter(osc1, attack, decay, sustain, 1.0, release, stop_at_end=True)
            f2 = EnvelopeFilter(osc2, attack, decay, sustain, 1.0, release, stop_at_end=True)
            osc_chunksize = chunksize // audio.norm_samplewidth // audio.norm_channels
            f1_i = iter(f1)
            f2_i = iter(f2)

            def render_chunk():
                try:
                    sample1 = sample_from_osc(f1_i, True, chunksize=osc_chunksize)
                    sample2 = sample_from_osc(f2_i, True, chunksize=osc_chunksize)
                except StopIteration:
                    raise NoteFinished
                else:
                    sample1 = audioop.tostereo(sample1, audio.norm_samplewidth, 1, 0)
                    sample2 = audioop.tostereo(sample2, audio.norm_samplewidth, 0, 1)
                    sample1 = audioop.add(sample1, sample2, audio.norm_samplewidth)
                    return sample1

            while True:
                # render this note in chunks of the asked size
                try:
                    while len(samplebuffer) < chunksize:
                        # fill up the sample buffer so we have at least one full chunk
                        chunk = render_chunk()
                        samplebuffer += chunk
                except NoteFinished:
                    # go to next note
                    break

                if samplebuffer:
                    chunk = samplebuffer[:chunksize]
                    samplebuffer = samplebuffer[chunksize:]
                    assert len(chunk) == chunksize
                    yield memoryview(chunk)
                else:
                    break
        if samplebuffer:
            yield memoryview(samplebuffer)


class Amoeba(audio.Sample):
    def __init__(self) -> None:
        super().__init__("amoeba", pcmdata=b"")
        for _ in range(1, 200):
            freq = random.randint(0x0800, 0x1200)
            osc = FastTriangle(freq * _sidfreq, amplitude=0.75, samplerate=audio.norm_samplerate)
            filtered = EnvelopeFilter(osc, 0.024, 0.006, 0.0, 0.5, 0.003, stop_at_end=True)
            self.append(sample_from_osc(filtered))


class MagicWall(audio.Sample):
    def __init__(self) -> None:
        super().__init__("magicwall", pcmdata=b"")
        for _ in range(1, 200):
            freq = random.randint(0x8600, 0x9f00)
            freq &= 0b0001100100000000
            freq |= 0b1000011000000000
            osc = FastTriangle(freq * _sidfreq, amplitude=0.4, samplerate=audio.norm_samplerate)
            filtered = EnvelopeFilter(osc, 0.002, 0.008, 0.0, 0.6, 0.03, stop_at_end=True)
            self.append(sample_from_osc(filtered))


class Cover(audio.Sample):
    def __init__(self) -> None:
        super().__init__("cover", pcmdata=b"")
        for _ in range(1, 100):
            freq = random.randint(0x6000, 0xd800)
            osc = FastTriangle(freq * _sidfreq, amplitude=0.7, samplerate=audio.norm_samplerate)
            filtered = EnvelopeFilter(osc, 0.002, 0.02, 0.0, 0.5, 0.02, stop_at_end=True)
            self.append(sample_from_osc(filtered))


class Finished(audio.Sample):
    def __init__(self) -> None:
        super().__init__("finished", pcmdata=b"")
        for n in range(0, 180):
            freq = 0x8000 - n * 180
            osc = FastTriangle(freq * _sidfreq, amplitude=0.8, samplerate=audio.norm_samplerate)
            filtered = EnvelopeFilter(osc, 0.002, 0.004, 0.0, 0.6, 0.02, stop_at_end=True)
            self.append(sample_from_osc(filtered))


class ExtraLife(audio.Sample):
    def __init__(self) -> None:
        super().__init__("extra_life", pcmdata=b"")
        for n in range(0, 16):
            freq = 0x1400 + n * 1024
            osc = FastTriangle(freq * _sidfreq, amplitude=0.8, samplerate=audio.norm_samplerate)
            filtered = EnvelopeFilter(osc, 0.002, 0.024, 0.0, 0.6, 0.03, stop_at_end=True)
            self.append(sample_from_osc(filtered))


class GameOver(audio.Sample):
    def __init__(self) -> None:
        super().__init__("game_over", pcmdata=b"")
        fm = Linear(0, -2.3e-5, samplerate=audio.norm_samplerate).generator()
        osc = Triangle(1567.98174, fm_lfo=fm, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.1, 0.3, 1.5, 1.0, 0.07, stop_at_end=True)
        ampmod = SquareH(10, 9, amplitude=0.5, bias=0.5, samplerate=audio.norm_samplerate).generator()
        filtered = AmpModulationFilter(filtered, ampmod)
        self.append(sample_from_osc(filtered))


class WalkDirt(audio.Sample):
    def __init__(self) -> None:
        super().__init__("walk_dirt", pcmdata=b"")
        osc = WhiteNoise(0x8500, amplitude=0.3, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.034, 0.006, 0.0, 0.5, 0.008, stop_at_end=True)
        self.append(sample_from_osc(filtered))


class WalkEmpty(audio.Sample):
    def __init__(self) -> None:
        super().__init__("walk_empty", pcmdata=b"")
        osc = WhiteNoise(0x1200, amplitude=0.2, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.034, 0.006, 0.0, 0.5, 0.008, stop_at_end=True)
        self.append(sample_from_osc(filtered))


class Explosion(audio.Sample):
    def __init__(self) -> None:
        super().__init__("explosion", pcmdata=b"")
        osc = WhiteNoise(0x1432, amplitude=0.8, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.008, 0.1, 0.0, 0.5, 1.5, stop_at_end=True)
        self.append(sample_from_osc(filtered))


class CollectDiamond(audio.Sample):
    def __init__(self) -> None:
        super().__init__("collect_diamond", pcmdata=b"")
        osc = FastTriangle(0x1478 * _sidfreq, amplitude=0.99, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.002, 0.006, 0.0, 0.7, 0.65, stop_at_end=True)
        self.append(sample_from_osc(filtered))


class Boulder(audio.Sample):
    def __init__(self) -> None:
        super().__init__("boulder", pcmdata=b"")
        osc = WhiteNoise(0x0932, amplitude=0.8, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.08, 0.08, 0.0, 0.4, 0.65, stop_at_end=True)
        self.append(sample_from_osc(filtered))


class Crack(audio.Sample):
    def __init__(self) -> None:
        super().__init__("crack", pcmdata=b"")
        osc = WhiteNoise(0x2F32, amplitude=0.8, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.008, 0.075, 0.0, 0.4, 0.65, stop_at_end=True)
        self.append(sample_from_osc(filtered))


class BoxPush(audio.Sample):
    def __init__(self) -> None:
        super().__init__("boxpush", pcmdata=b"")
        osc = WhiteNoise(2637, amplitude=0.6, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.2, 0.2, 0.0, 0.25, 0, stop_at_end=True)
        self.append(sample_from_osc(filtered))


class Diamond(audio.Sample):
    def __init__(self) -> None:
        super().__init__("diamond", pcmdata=b"")

    def chunked_data(self, chunksize: int, repeat: bool=False,
                     stopcondition: Callable[[], bool]=lambda: False) -> Generator[memoryview, None, None]:
        # generate a new random diamond sound
        begin = time.perf_counter()
        freq = random.randint(0x8600, 0xfeff)
        print("new diamond sound", freq)  # XXX
        freq &= 0b0111100011111111
        freq |= 0b1000011000000000
        osc = FastTriangle(freq * _sidfreq, amplitude=0.7, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.002, 0.006, 0.0, 0.7, 0.6, stop_at_end=True)
        sample = sample_from_osc(filtered)
        print("samp took", time.perf_counter() - begin)   # XXX
        self.duration = sample.duration
        self.sampledata = sample.sampledata
        return super().chunked_data(chunksize, repeat, stopcondition)


class Timeout(audio.Sample):
    def __init__(self, timeout) -> None:
        super().__init__("timeout_"+str(timeout), pcmdata=b"")
        osc = FastTriangle((timeout * 256 + 0x1E00) * _sidfreq, amplitude=0.99, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.002, 0.2, 0.1, 0.5, 0.8, stop_at_end=True)
        self.append(sample_from_osc(filtered))


def demo1():
    audio.norm_samplerate = 22050
    scale = 2 ** (audio.norm_samplewidth * 8 - 1) - 1
    api = audio.best_api()
    print("Generating tones...")
    for note in ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']:
        duration = 0.5
        osc = FastTriangle(note_freq(note, 4), samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.05, 0.05, 0.1, 0.6, 0.1, stop_at_end=False)
        wave = filtered.generator()
        a = array.array('h', [int(scale*next(wave)) for _ in range(int(duration*audio.norm_samplerate))])
        sounddata = a.tobytes()
        sounddata = audioop.tostereo(sounddata, audio.norm_samplewidth, 1, 1)
        sample = audio.Sample("test", pcmdata=sounddata)
        api.play(sample)
        time.sleep(sample.duration + 0.1)
    print("CLOSING!")
    api.close()


def demo2():
    audio.norm_samplerate = 22050
    api = audio.best_api()

    # # ------ explosion
    # print("Explosion")
    # sample = Explosion()
    # api.play(sample)
    # time.sleep(sample.duration + 0.1)
    #
    # # # ------ diamond
    # print("Diamonds")
    # for _ in range(5):
    #     sample = Diamond()
    #     print(sample.duration)
    #     api.play(sample)
    #     time.sleep(sample.duration + 0.1)
    #
    # # ---- collect diamond
    # print("Collect diamond")
    # sample = CollectDiamond()
    # print(sample.duration)
    # api.play(sample)
    # time.sleep(sample.duration + 0.1)
    #
    # # ------ boulder
    # print("Boulder")
    # sample = Boulder()
    # print(sample.duration)
    # api.play(sample)
    # time.sleep(sample.duration + 0.1)
    #
    # # ------ crack
    # print("Crack", _sidfreq)
    # sample = Crack()
    # api.play(sample)
    # time.sleep(sample.duration + 0.1)

    # ---- out of time
    # print("Out of time")
    # for n in range(1, 10):
    #     sample = Timeout(n)
    #     print(sample.duration)
    #     api.play(sample)
    #     time.sleep(sample.duration + 0.1)

    # ---- uncover
    # print("Uncover")
    # sample = Cover()
    # print(sample.duration)
    # api.play(sample)
    # time.sleep(sample.duration)

    # ------ Amoeba
    # print("Amoeba")
    # sample = Amoeba()
    # print(sample.duration)
    # api.play(sample)
    # time.sleep(sample.duration)

    # ------- Magic wall
    # print("Magic wall")
    # sample = MagicWall()
    # print(sample.duration)
    # api.play(sample)
    # time.sleep(sample.duration)

    # # ---- bonus points sound
    # print("Bonus points")
    # sample = Finished()
    # print(sample.duration)
    # api.play(sample)
    # time.sleep(sample.duration)

    # ------ moving
    # print("Move (dirt)")
    # sample = WalkDirt()
    # for _ in range(10):
    #     print(sample.duration)
    #     api.play(sample)
    #     time.sleep(sample.duration + 0.1)
    # print("Move (space)")
    # sample = WalkEmpty()
    # for _ in range(10):
    #     print(sample.duration)
    #     api.play(sample)
    #     time.sleep(sample.duration + 0.1)

    # ----- box push
    # print("Box Push")
    # sample = BoxPush()
    # print(sample.duration)
    # api.play(sample)
    # time.sleep(sample.duration)

    # ----- extra life
    # print("Extra life")
    # sample = ExtraLife()
    # print(sample.duration)
    # api.play(sample)
    # time.sleep(sample.duration+0.5)

    # ----- game over
    # print("Game over")
    # sample = GameOver()
    # print(sample.duration)
    # api.play(sample)
    # time.sleep(sample.duration)

    # ----- title music
    print("Title music")
    sample = TitleMusic()
    print(sample.duration)
    api.play(sample, repeat=True)
    time.sleep(max(10, sample.duration + 0.1))

    print("CLOSING!")
    api.close()


if __name__ == "__main__":
    demo2()