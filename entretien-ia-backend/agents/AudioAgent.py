import librosa
import numpy as np
import torch
import torchaudio
import os

class AudioAgent:
    def __init__(self, sample_rate=16000, pause_threshold=0.5):
        print("Initialisation de AudioAgent avec Silero-VAD...")
        self.sr = sample_rate
        self.pause_threshold = pause_threshold
        
        try:
            self.model, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False
            )
            print("AudioAgent initialisé avec succès.")
        except Exception as e:
            self.model = None
            print(f"ERREUR FATALE: Impossible de charger le modèle Silero-VAD. L'analyse vocale sera désactivée. Erreur: {e}")

    def analyze_audio_chunk(self, audio_chunk_tensor: torch.Tensor, transcription_chunk: str) -> dict:
        """
        Analyse un segment audio (tenseur PyTorch) au lieu d'un fichier complet.
        C'est la méthode principale pour l'analyse par réponse.
        """
        if not self.model:
            return self._default_results()
        
        try:
            # === ÉTAPE 1 : OBTENIR LES DURÉES ===
            total_duration_seconds = audio_chunk_tensor.shape[1] / self.sr
            if total_duration_seconds < 1.0: return self._default_results()

            # === ÉTAPE 2 : DÉTECTION VAD SUR LE SEGMENT ===
            (get_speech_timestamps, *_) = self.utils
            speech_timestamps = get_speech_timestamps(audio_chunk_tensor, self.model, sampling_rate=self.sr)
            if not speech_timestamps: return self._default_results()
            
            # === ÉTAPE 3 : CALCUL DES MÉTRIQUES SUR LE SEGMENT ===
            word_count = len(transcription_chunk.strip().split())
            speech_duration_seconds = sum([ts['end'] - ts['start'] for ts in speech_timestamps]) / self.sr
            if speech_duration_seconds < 0.5: return self._default_results()

            speech_rate = word_count / (speech_duration_seconds / 60)
            
            pauses = [ (speech_timestamps[i+1]['start'] - speech_timestamps[i]['end']) / self.sr 
                       for i in range(len(speech_timestamps) - 1) 
                       if (speech_timestamps[i+1]['start'] - speech_timestamps[i]['end']) / self.sr > self.pause_threshold ]
            
            pause_count = len(pauses)
            average_pause_duration = np.mean(pauses) if pauses else 0.0
            
            y_mono_numpy = audio_chunk_tensor.squeeze().numpy()
            pitches, _ = librosa.piptrack(y=y_mono_numpy, sr=self.sr, fmin=75, fmax=400)
            valid_pitches = pitches[pitches > 0]
            pitch_mean = np.mean(valid_pitches) if len(valid_pitches) > 0 else 0.0
            pitch_std = np.std(valid_pitches) if len(valid_pitches) > 0 else 0.0
            
            fluency_score = self._calculate_fluency_score(speech_duration_seconds, total_duration_seconds, pause_count, average_pause_duration)

            return {
                "speech_rate": float(round(speech_rate, 2)),
                "pause_count": int(pause_count),
                "average_pause_duration": float(round(average_pause_duration, 2)),
                "pitch_mean": float(round(pitch_mean, 2)),
                "pitch_std": float(round(pitch_std, 2)),
                "fluency_score": float(round(fluency_score, 2))
            }
        except Exception as e:
            print(f" ERREUR critique dans analyze_audio_chunk : {e}")
            return self._default_results()

    def analyze_speech_vocal_characteristics(self, audio_path: str, transcription: str) -> dict:
        """
        Analyse un fichier audio complet pour extraire des métriques vocales globales.
        Cette méthode est maintenant un "wrapper" qui charge le fichier et appelle analyze_audio_chunk.
        """
        if not self.model:
            return self._default_results()
        try:
            wav, sr = torchaudio.load(audio_path)
            if sr != self.sr: wav = torchaudio.transforms.Resample(sr, self.sr)(wav)
            if wav.shape[0] > 1: wav = torch.mean(wav, dim=0, keepdim=True)
            wav = wav.float()
            
            return self.analyze_audio_chunk(wav, transcription)

        except Exception as e:
            print(f" ERREUR critique dans analyze_speech_vocal_characteristics : {e}")
            return self._default_results()

    def _calculate_fluency_score(self, speech_duration, total_duration, pause_count, avg_pause_duration):
        if total_duration == 0: return 0
        speech_ratio_score = (speech_duration / total_duration) * 100
        pause_count_penalty = min(25, pause_count * 1.5)
        pause_duration_penalty = min(25, avg_pause_duration * 5)
        final_score = max(0, speech_ratio_score - pause_count_penalty - pause_duration_penalty)
        return final_score

    def _default_results(self):
        return {
            "speech_rate": 0.0, "pause_count": 0, "average_pause_duration": 0.0,
            "pitch_mean": 0.0, "pitch_std": 0.0, "fluency_score": 0.0
        }

if __name__ == '__main__':
    test_audio = "data/datasets/RAVDESS/Actor_01/03-01-01-01-01-01-01.wav"
    test_transcription = ("Kids are talking by the door")

    if os.path.exists(test_audio):
        agent = AudioAgent()
        if agent.model:
            result = agent.analyze_speech_vocal_characteristics(test_audio, test_transcription)
            print("\n--- RÉSULTATS DE L'ANALYSE VOCALE GLOBALE (VAD) ---")
            for key, value in result.items():
                print(f" {key.replace('_', ' ').capitalize():<25}: {value}")
    else:
        print(f" Fichier de test introuvable : {test_audio}")