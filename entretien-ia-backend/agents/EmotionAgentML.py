import os
import librosa
import numpy as np
import joblib


BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, '..', 'models', 'emotion_model.joblib')
SCALER_PATH = os.path.join(BASE_DIR, '..', 'models', 'emotion_scaler.joblib')

class EmotionAgent:
    """
    Agent spécialisé dans l'analyse et la détection des émotions
    à partir des caractéristiques vocales.
    """
    def __init__(self, sample_rate=22050, n_mfcc=40):
        """
        Initialise l'agent avec les paramètres pour l'extraction de features.
        """
        self.sr = sample_rate
        self.n_mfcc = n_mfcc
        # Initialisation paresseuse (lazy loading) du modèle et du scaler
        self.model = None
        self.scaler = None
        print("EmotionAgent initialisé.")

    def _load_model_and_scaler(self):
        """
        Charge le modèle de classification et le scaler de mise à l'échelle
        depuis le disque. Ne le fait qu'une seule fois.
        """
        if self.model and self.scaler:
            return
            
        print("Chargement du modèle de détection d'émotions et du scaler...")
        if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
            raise FileNotFoundError(f"Modèle ({MODEL_PATH}) ou scaler ({SCALER_PATH}) non trouvé. Veuillez d'abord entraîner le modèle avec le script 'train_emotion_model.py'.")
        
        try:
            self.model = joblib.load(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            print("Modèle et scaler prêts.")
        except Exception as e:
            print(f"ERREUR lors du chargement du modèle ou du scaler : {e}")

    def extract_features(self, audio_path: str) -> np.ndarray:
        """
        Charge un fichier audio et extrait un ensemble enrichi de caractéristiques acoustiques
        (MFCC, Chroma, Mel-spectrogram, Contraste Spectral).
        """
        if not os.path.exists(audio_path):
            print(f"ERREUR (EmotionAgent): Fichier non trouvé {audio_path}")
            return None
            
        try:
            y, sr = librosa.load(audio_path, sr=self.sr)
            
            # 1. MFCC
            mfccs = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.n_mfcc).T, axis=0)
            
            # 2. Chroma
            chroma = np.mean(librosa.feature.chroma_stft(y=y, sr=sr).T, axis=0)
            
            # 3. Mel-spectrogram
            mel = np.mean(librosa.feature.melspectrogram(y=y, sr=sr).T, axis=0)
            
            # 4. Contraste Spectral
            contrast = np.mean(librosa.feature.spectral_contrast(y=y, sr=sr).T, axis=0)
            
            # On combine toutes ces caractéristiques en un seul grand vecteur
            combined_features = np.hstack((mfccs, chroma, mel, contrast))

            return combined_features

        except Exception as e:
            print(f"ERREUR (EmotionAgent) lors de l'extraction des features de {audio_path}: {e}")
            return None

    def predict_emotion(self, audio_path: str) -> dict:
        """
        Prédit l'émotion dominante et les probabilités pour chaque émotion
        à partir d'un fichier audio.
        """
        self._load_model_and_scaler()
        if not self.model or not self.scaler:
            return {"dominant_emotion": "erreur_chargement_modele", "scores": {}}

        # 1. Extraire les features de l'audio d'entrée
        features = self.extract_features(audio_path)
        if features is None:
            return {"dominant_emotion": "erreur_extraction_features", "scores": {}}

        # 2. Appliquer la même mise à l'échelle que sur les données d'entraînement
        # Le scaler s'attend à un tableau 2D, donc on reshape le vecteur [features]
        features_scaled = self.scaler.transform([features])
        
        # 3. Faire la prédiction sur les données mises à l'échelle
        try:
            dominant_emotion = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            scores = {emotion: prob for emotion, prob in zip(self.model.classes_, probabilities)}
            
            return {
                "dominant_emotion": dominant_emotion,
                "scores": scores
            }
        except Exception as e:
            print(f"ERREUR lors de la prédiction d'émotion : {e}")
            return {"dominant_emotion": "erreur_prediction", "scores": {}}

    @staticmethod
    def get_emotion_label_from_filename(filename: str) -> str:
        """Utilitaire pour le dataset RAVDESS."""
        try:
            emotion_code = int(filename.split('-')[2])
            emotion_map = {
                1: "neutre", 2: "calme", 3: "heureux", 4: "triste",
                5: "colère", 6: "peur", 7: "dégoût", 8: "surpris"
            }
            return emotion_map.get(emotion_code, "inconnu")
        except (IndexError, ValueError):
            return "inconnu"

# --- Bloc de test pour valider la prédiction ---
if __name__ == '__main__':
    print("--- DÉBUT DU TEST DE L'AGENT ÉMOTIONNEL (PRÉDICTION) ---")
    
    # On crée une instance de l'agent
    emotion_agent = EmotionAgent()
    
    # Chemin vers le dataset. Assurez-vous qu'il est correct depuis la racine du projet backend.
    ravdess_path = "data/datasets/RAVDESS/Actor_05/"
    
    if os.path.exists(ravdess_path):
        test_files = [f for f in os.listdir(ravdess_path) if f.endswith('.wav')]
        if test_files:
            # On prend un fichier au hasard pour le tester
            test_file_name = test_files[7]
            test_file_path = os.path.join(ravdess_path, test_file_name)
            
            expected_emotion = emotion_agent.get_emotion_label_from_filename(test_file_name)
            print(f"\nAnalyse du fichier de test : {test_file_name}")
            print(f"Émotion attendue (d'après le nom du fichier) : {expected_emotion.upper()}")

            # On appelle la méthode de prédiction
            prediction_result = emotion_agent.predict_emotion(test_file_path)
            
            if prediction_result and prediction_result['scores']:
                print("\n--- RÉSULTAT DE LA PRÉDICTION ---")
                print(f"Émotion dominante prédite : {prediction_result['dominant_emotion'].upper()}")
                print("\nScores de probabilité par émotion :")
                # On trie les scores pour un affichage plus clair
                sorted_scores = sorted(prediction_result['scores'].items(), key=lambda item: item[1], reverse=True)
                for emotion, score in sorted_scores:
                    print(f"- {emotion.capitalize():<10}: {score * 100:.2f}%")
            else:
                print("--- ÉCHEC DE LA PRÉDICTION ---")
    else:
        print(f"!!! ATTENTION : Dossier du dataset RAVDESS non trouvé à l'emplacement : {ravdess_path}")
        print("Veuillez télécharger le dataset et le placer dans le bon dossier.")

    print("\n--- FIN DU TEST ---")