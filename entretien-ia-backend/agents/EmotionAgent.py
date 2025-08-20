import os
import librosa
import numpy as np
import joblib
from tensorflow.keras.models import load_model

BASE_DIR = os.path.dirname(__file__)
CNN_MODEL_PATH = os.path.join(BASE_DIR, '..', 'models', 'emotion_cnn_model.h5')
LABEL_ENCODER_PATH = os.path.join(BASE_DIR, '..', 'models', 'emotion_label_encoder.joblib')

class EmotionAgent:
    def __init__(self, sample_rate=22050):
        self.sr = sample_rate
        self.cnn_model = None
        self.label_encoder = None
        print("EmotionAgent initialisé.")

    def _load_model(self):
        if self.cnn_model and self.label_encoder:
            return
            
        print("Chargement du modèle de détection d'émotions CNN...")
        if not os.path.exists(CNN_MODEL_PATH) or not os.path.exists(LABEL_ENCODER_PATH):
            raise FileNotFoundError(f"Modèle CNN ou LabelEncoder non trouvé. Veuillez d'abord entraîner le modèle avec le script 'train_emotion_cnn.py'.")
        
        try:
            self.cnn_model = load_model(CNN_MODEL_PATH)
            self.label_encoder = joblib.load(LABEL_ENCODER_PATH)
            print("Modèle CNN et LabelEncoder prêts.")
        except Exception as e:
            print(f"ERREUR lors du chargement du modèle CNN : {e}")

    def extract_mel_spectrogram(self, audio_path: str, max_pad_len=174) -> np.ndarray:
        """
        Extrait le spectrogramme Mel (notre "image" audio) et le normalise en taille.
        """
        if not os.path.exists(audio_path):
            print(f"ERREUR (EmotionAgent): Fichier non trouvé {audio_path}")
            return None
            
        try:
            y, sr = librosa.load(audio_path, sr=self.sr)
            
            mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
            log_mel_spec = librosa.power_to_db(mel_spec, ref=np.max)
            
            # Padding ou troncature pour avoir une taille fixe pour le CNN
            if log_mel_spec.shape[1] > max_pad_len:
                log_mel_spec = log_mel_spec[:, :max_pad_len]
            else:
                pad_width = max_pad_len - log_mel_spec.shape[1]
                log_mel_spec = np.pad(log_mel_spec, pad_width=((0, 0), (0, pad_width)), mode='constant')
            
            return log_mel_spec

        except Exception as e:
            print(f"ERREUR (EmotionAgent) lors de l'extraction du spectrogramme de {audio_path}: {e}")
            return None

    def predict_emotion(self, audio_path: str) -> dict:
        self._load_model()
        if not self.cnn_model or not self.label_encoder:
            return {"dominant_emotion": "erreur_modele", "scores": {}}

        spectrogram = self.extract_mel_spectrogram(audio_path)
        if spectrogram is None:
            return {"dominant_emotion": "erreur_extraction", "scores": {}}

        # Préparer les données pour le modèle (batch de 1, 1 canal de couleur)
        spectrogram = np.expand_dims(spectrogram, axis=0)
        spectrogram = np.expand_dims(spectrogram, axis=-1)
        
        try:
            probabilities = self.cnn_model.predict(spectrogram)[0]
            predicted_index = np.argmax(probabilities)
            dominant_emotion = self.label_encoder.inverse_transform([predicted_index])[0]
            scores = {label: float(prob) for label, prob in zip(self.label_encoder.classes_, probabilities)}
            
            return {"dominant_emotion": dominant_emotion, "scores": scores}
        except Exception as e:
            print(f"ERREUR lors de la prédiction d'émotion : {e}")
            return {"dominant_emotion": "erreur_prediction", "scores": {}}

    @staticmethod
    def get_emotion_label_from_filename(filename: str) -> str:
        try:
            emotion_code = int(filename.split('-')[2])
            emotion_map = {1: "neutre", 2: "calme", 3: "heureux", 4: "triste", 5: "colère", 6: "peur", 7: "dégoût", 8: "surpris"}
            return emotion_map.get(emotion_code)
        except (IndexError, ValueError):
            return None

if __name__ == '__main__':
    print("--- DÉBUT DU TEST DE L'AGENT ÉMOTIONNEL (PRÉDICTION CNN) ---")
    emotion_agent = EmotionAgent()
    
    test_file_path = "data/datasets/RAVDESS/Actor_01/03-01-01-01-02-01-01.wav" # Fichier marqué neutre
    
    if os.path.exists(test_file_path):
        expected_emotion = emotion_agent.get_emotion_label_from_filename(os.path.basename(test_file_path))
        print(f"Analyse du fichier de test : {os.path.basename(test_file_path)}")
        print(f"Émotion attendue : {expected_emotion.upper()}")

        prediction_result = emotion_agent.predict_emotion(test_file_path)
        
        if prediction_result and prediction_result['scores']:
            print("\n--- RÉSULTAT DE LA PRÉDICTION ---")
            print(f"Émotion dominante prédite : {prediction_result['dominant_emotion'].upper()}")
            print("\nScores de probabilité par émotion :")
            sorted_scores = sorted(prediction_result['scores'].items(), key=lambda item: item[1], reverse=True)
            for emotion, score in sorted_scores:
                print(f"- {emotion.capitalize():<10}: {score * 100:.2f}%")
    else:
        print(f"!!! Fichier de test non trouvé : {test_file_path}")