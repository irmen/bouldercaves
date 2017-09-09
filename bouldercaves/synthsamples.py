"""
Synthesized samples.

Written by Irmen de Jong (irmen@razorvine.net) - License: MIT open-source.
"""

import time
import audioop
import array
from . import audio
from .synth import WaveSynth, FastTriangle, WhiteNoise, FastSine, EnvelopeFilter, note_freq


_title_music = [
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

_music_freq_table = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    732, 778, 826, 876, 928, 978, 1042, 1100, 1170, 1238, 1312, 1390, 1464, 1556,
    1652, 1752, 1856, 1956, 2084, 2200, 2340, 2476, 2624, 2780, 2928, 3112, 3304,
    3504, 3712, 3912, 4168, 4400, 4680, 4952, 5248, 5560, 5856, 6224, 6608, 7008,
    7424, 7824, 8336, 8800, 9360, 9904, 10496, 11120, 11712
]


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
    sidfreq = 985248.0 / 16777216.0
    audio.norm_samplerate = 44100

    def make_sample(osc, raw=False):
        scale = 2 ** (audio.norm_samplewidth * 8 - 1) - 1
        wave = osc.generator()
        sounddata = array.array('h')
        while True:
            try:
                sounddata.append(int(scale*next(wave)))
            except StopIteration:
                break
        sounddata = sounddata.tobytes()
        if raw:
            return sounddata
        sounddata = audioop.tostereo(sounddata, audio.norm_samplewidth, 1, 1)
        return audio.Sample("test", pcmdata=sounddata)

    api = audio.best_api()
    import random

    # ------ explosion
    print("Explosion")
    osc = WhiteNoise(0x1432, amplitude=0.8, samplerate=audio.norm_samplerate)
    filtered = EnvelopeFilter(osc, 0.008, 0.1, 0.0, 0.5, 1.5, stop_at_end=True)
    sample = make_sample(filtered)
    print(sample.duration)
    api.play(sample)
    time.sleep(sample.duration + 0.1)

    # ------ diamond
    print("Diamonds")
    freq = random.randint(0x8600, 0xfeff)
    freq &= 0b0111100011111111
    freq |= 0b1000011000000000
    osc = FastTriangle(freq * sidfreq, amplitude=0.8, samplerate=audio.norm_samplerate)
    filtered = EnvelopeFilter(osc, 0.002, 0.006, 0.0, 0.7, 0.6, stop_at_end=True)
    sample = make_sample(filtered)
    print(sample.duration)
    api.play(sample)
    time.sleep(sample.duration + 0.1)

    #---- diamond pickup
    print("Diamond pickup")
    osc = FastTriangle(0x1478 * sidfreq, amplitude=0.99, samplerate=audio.norm_samplerate)
    filtered = EnvelopeFilter(osc, 0.002, 0.006, 0.0, 0.7, 0.65, stop_at_end=True)
    sample = make_sample(filtered)
    print(sample.duration)
    api.play(sample)
    time.sleep(sample.duration + 0.1)

    # ------ boulder
    print("Boulder")
    osc = WhiteNoise(0x0932, amplitude=0.8, samplerate=audio.norm_samplerate)
    filtered = EnvelopeFilter(osc, 0.08, 0.08, 0.0, 0.4, 0.65, stop_at_end=True)
    sample = make_sample(filtered)
    print(sample.duration)
    api.play(sample)
    time.sleep(sample.duration + 0.1)

    # ------ crack
    print("Crack", sidfreq)
    osc = WhiteNoise(0x2F32, amplitude=0.8, samplerate=audio.norm_samplerate)
    filtered = EnvelopeFilter(osc, 0.008, 0.075, 0.0, 0.4, 0.65, stop_at_end=True)
    sample = make_sample(filtered)
    api.play(sample)
    time.sleep(sample.duration + 0.1)

    # ---- out of time
    print("Out of time")
    for n in range(1, 10):
        osc = FastTriangle((n*256+0x1E00) * sidfreq, amplitude=0.99, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.002, 0.2, 0.1, 0.5, 0.8, stop_at_end=True)
        sample = make_sample(filtered)
        print(sample.duration)
        api.play(sample)
        time.sleep(sample.duration + 0.1)

    # ---- uncover
    print("Uncover")
    sample = audio.Sample("cover", pcmdata=b"")
    for n in range(1, 100):
        freq = random.randint(0x6000, 0xd800)
        osc = FastTriangle(freq * sidfreq, amplitude=0.7, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.002, 0.02, 0.0, 0.5, 0.02, stop_at_end=True)
        sample.append(make_sample(filtered))
    print(sample.duration)
    api.play(sample)
    time.sleep(sample.duration)

    # ------ Amoeba
    print("Amoeba")
    for n in range(1, 100):
        freq = random.randint(0x0800, 0x1200)
        osc = FastTriangle(freq * sidfreq, amplitude=0.7, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.024, 0.006, 0.0, 0.5, 0.003, stop_at_end=True)
        sample = make_sample(filtered)
        print(sample.duration)
        api.play(sample)
        time.sleep(sample.duration)

    # ------- Magic wall
    print("Magic wall")
    for n in range(1, 100):
        freq = random.randint(0x8600, 0x9f00)
        freq &= 0b0001100100000000
        freq |= 0b1000011000000000
        osc = FastTriangle(freq * sidfreq, amplitude=0.6, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.002, 0.008, 0.0, 0.6, 0.02, stop_at_end=True)
        sample = make_sample(filtered)
        print(sample.duration)
        api.play(sample)
        time.sleep(sample.duration)

    # ---- bonus points sound
    print("Bonus points1")
    sample = audio.Sample("finished", pcmdata=b"")
    for n in range(0, 200):
        freq = 0x8000 - n * 160
        osc = FastTriangle(freq * sidfreq, amplitude=0.8, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.002, 0.004, 0.0, 0.6, 0.02, stop_at_end=True)
        sample.append(make_sample(filtered))
    print(sample.duration)
    api.play(sample)
    time.sleep(sample.duration)

    # ------ moving
    print("Move (dirt)")
    for _ in range(10):
        osc = WhiteNoise(0xa500, amplitude=0.5, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.034, 0.006, 0.0, 0.5, 0.008, stop_at_end=True)
        sample = make_sample(filtered)
        print(sample.duration)
        api.play(sample)
        time.sleep(sample.duration + 0.1)
    print("Move (space)")
    for _ in range(10):
        osc = WhiteNoise(0x1200, amplitude=0.2, samplerate=audio.norm_samplerate)
        filtered = EnvelopeFilter(osc, 0.034, 0.006, 0.0, 0.5, 0.008, stop_at_end=True)
        sample = make_sample(filtered)
        print(sample.duration)
        api.play(sample)
        time.sleep(sample.duration + 0.1)

    # ----- title music
    print("Title music")
    print("Synthesizing title tune...")
    sample = audio.Sample("music", pcmdata=b"")
    for v1, v2 in _title_music:
        vf1 = _music_freq_table[v1]
        vf2 = _music_freq_table[v2]
        osc1 = FastTriangle(vf1 * sidfreq, amplitude=0.5, samplerate=audio.norm_samplerate)
        osc2 = FastTriangle(vf2 * sidfreq, amplitude=0.5, samplerate=audio.norm_samplerate)
        f1 = EnvelopeFilter(osc1, 0.001, 0.001, 0.145, 1.0, 0.01, stop_at_end=True)
        f2 = EnvelopeFilter(osc2, 0.001, 0.001, 0.145, 1.0, 0.01, stop_at_end=True)
        sample1 = make_sample(f1, True)
        sample2 = make_sample(f2, True)
        sample1 = audioop.tostereo(sample1, audio.norm_samplewidth, 1, 0)
        sample2 = audioop.tostereo(sample2, audio.norm_samplewidth, 0, 1)
        sample1 = audioop.add(sample1, sample2, audio.norm_samplewidth)
        sample.append(audio.Sample("music", pcmdata=sample1))
    print(sample.duration)
    api.play(sample)
    time.sleep(sample.duration)

    print("CLOSING!")
    api.close()


if __name__ == "__main__":
    demo2()

