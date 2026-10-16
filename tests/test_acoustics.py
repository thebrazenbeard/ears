import unittest
import numpy as np
from ears.acoustics import analyze_pcm


class AcousticTests(unittest.TestCase):
    def test_silence_retains_no_pitch_or_voice_claim(self):
        frames = analyze_pcm(np.zeros(4096), 16000, frame_size=1024, hop_size=512)
        self.assertEqual(len(frames), 7)
        self.assertTrue(all(f.f0_hz is None and not f.voiced_candidate for f in frames))
        self.assertTrue(all(f.rms == 0 for f in frames))

    def test_tone_is_tonal_and_has_candidate_harmonics(self):
        sr = 16000
        time = np.arange(sr) / sr
        wave = sum(0.5 / n * np.sin(2 * np.pi * 200 * n * time) for n in range(1, 5))
        frames = analyze_pcm(wave, sr, frame_size=2048, hop_size=1024)
        self.assertGreater(frames[2].harmonic_ratio, 0.5)
        self.assertLess(frames[2].spectral_flatness, 0.2)
        self.assertTrue(frames[2].f0_candidates_hz)

    def test_transient_flux_and_timestamp(self):
        signal = np.zeros(4096)
        signal[2048] = 1.0
        frames = analyze_pcm(signal, 16000, frame_size=1024, hop_size=512)
        self.assertAlmostEqual(frames[0].time_seconds, 0.032)
        self.assertGreater(max(f.spectral_flux for f in frames), 0)

    def test_invalid_audio_rejected(self):
        with self.assertRaises(ValueError):
            analyze_pcm(np.ones((2, 1024)), 16000)
        with self.assertRaises(ValueError):
            analyze_pcm([float("nan")] * 1024, 16000)
        with self.assertRaises(ValueError):
            analyze_pcm(np.ones(1024), 800)


if __name__ == "__main__":
    unittest.main()
