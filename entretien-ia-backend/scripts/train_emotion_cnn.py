import os
import sys
import glob
import numpy as np
import joblib
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
import librosa
import audiomentations as A 

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.utils import to_categorical

# Configuration pour éviter les problèmes de mémoire sur CPU
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.EmotionAgent import EmotionAgent

BASE_DIR = os.path.dirname(__file__)
RAVDESS_DATASET_PATH = os.path.join(BASE_DIR, '..', 'data', 'datasets', 'RAVDESS')
MODELS_DIR = os.path.join(BASE_DIR, '..', 'models')
DOCS_DIR = os.path.join(BASE_DIR, '..', 'docs', 'images')
CNN_MODEL_SAVE_PATH = os.path.join(MODELS_DIR, 'emotion_cnn_model.h5')
LABEL_ENCODER_PATH = os.path.join(MODELS_DIR, 'emotion_label_encoder.joblib')
TRAINING_PLOT_PATH = os.path.join(DOCS_DIR, 'cnn_training_history.png')
CONFUSION_MATRIX_PATH = os.path.join(DOCS_DIR, 'cnn_confusion_matrix.png')

augmenter = A.Compose([
    A.AddGaussianNoise(min_amplitude=0.001, max_amplitude=0.015, p=0.5),
    A.TimeStretch(min_rate=0.8, max_rate=1.25, p=0.5),
    A.PitchShift(min_semitones=-4, max_semitones=4, p=0.5),
])

def load_and_process_data():
    emotion_agent = EmotionAgent()
    features, labels = [], []
    ravdess_files = glob.glob(os.path.join(RAVDESS_DATASET_PATH, "Actor_*", "*.wav"))
    if not ravdess_files:
        raise FileNotFoundError(f"Aucun fichier .wav trouvé dans {RAVDESS_DATASET_PATH}.")
        
    for file_path in tqdm(ravdess_files, desc="Traitement des données"):
        # 1. Donnée originale
        y, sr = librosa.load(file_path, sr=emotion_agent.sr)
        spectrogram = emotion_agent.extract_mel_spectrogram(file_path)
        emotion_label = emotion_agent.get_emotion_label_from_filename(os.path.basename(file_path))
        
        if spectrogram is not None and emotion_label is not None:
            features.append(spectrogram)
            labels.append(emotion_label)

            # 2. Donnée augmentée (on en crée une par fichier original)
            augmented_audio = augmenter(samples=y, sample_rate=sr)
            # On doit sauvegarder temporairement pour que librosa le lise
            temp_path = "temp_augmented.wav"
            import soundfile as sf
            sf.write(temp_path, augmented_audio, sr)
            augmented_spectrogram = emotion_agent.extract_mel_spectrogram(temp_path)
            if augmented_spectrogram is not None:
                features.append(augmented_spectrogram)
                labels.append(emotion_label)
    
    if os.path.exists("temp_augmented.wav"):
        os.remove("temp_augmented.wav")
        
    return np.array(features), np.array(labels)

def build_cnn_model(input_shape, num_classes):
    model = Sequential([
        Conv2D(32, (3, 3), activation='relu', input_shape=input_shape, padding='same'),
        BatchNormalization(),
        MaxPooling2D((2, 2)),
        Dropout(0.25),
        
        Conv2D(64, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        MaxPooling2D((2, 2)),
        Dropout(0.25),

        Conv2D(128, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        MaxPooling2D((2, 2)),
        Dropout(0.3),
        
        Flatten(),
        Dense(256, activation='relu'),
        BatchNormalization(),
        Dropout(0.5),
        Dense(num_classes, activation='softmax')
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), 
                  loss='categorical_crossentropy', 
                  metrics=['accuracy'])
    return model

def plot_training_history(history, path):
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(history.history['accuracy'], label='Précision (Entraînement)')
    plt.plot(history.history['val_accuracy'], label='Précision (Validation)')
    plt.title('Précision du Modèle')
    plt.xlabel('Époque')
    plt.ylabel('Précision')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'], label='Perte (Entraînement)')
    plt.plot(history.history['val_loss'], label='Perte (Validation)')
    plt.title('Perte du Modèle')
    plt.xlabel('Époque')
    plt.ylabel('Perte')
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    print(f"Graphique d'entraînement sauvegardé dans : {path}")

def train_main():
    X, y = load_and_process_data()
    if X is None: return
    print(f"\nTotal de {len(X)} échantillons (originaux + augmentés).")
    
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    y_categorical = to_categorical(y_encoded)
    
    X = np.expand_dims(X, axis=-1)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_categorical, test_size=0.2, random_state=42, stratify=y_categorical)

    model = build_cnn_model(X_train.shape[1:], y_train.shape[1])
    model.summary()
    
    early_stopping = EarlyStopping(monitor='val_accuracy', patience=15, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=0.00001)
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=100, 
        batch_size=32,
        callbacks=[early_stopping, reduce_lr]
    )

    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
    print("\n" + "="*40)
    print("--- RAPPORT D'ÉVALUATION FINAL DU MODÈLE CNN ---")
    print(f"\nPrécision finale sur l'ensemble de test : {accuracy * 100:.2f}%")
    
    y_pred_proba = model.predict(X_test)
    y_pred_labels = np.argmax(y_pred_proba, axis=1)
    y_test_labels = np.argmax(y_test, axis=1)
    
    print("\n--- Rapport de Classification Détaillé ---")
    print(classification_report(y_test_labels, y_pred_labels, target_names=label_encoder.classes_, zero_division=0))
    
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)
    
    model.save(CNN_MODEL_SAVE_PATH)
    joblib.dump(label_encoder, LABEL_ENCODER_PATH)
    print(f"\nModèle CNN et LabelEncoder sauvegardés.")
    
    plot_training_history(history, TRAINING_PLOT_PATH)
    
    cm = confusion_matrix(y_test_labels, y_pred_labels)
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=label_encoder.classes_, yticklabels=label_encoder.classes_)
    plt.title('Matrice de Confusion', fontsize=16)
    plt.ylabel('Vraie Étiquette', fontsize=12)
    plt.xlabel('Étiquette Prédite', fontsize=12)
    plt.savefig(CONFUSION_MATRIX_PATH, bbox_inches='tight')
    print(f"Matrice de confusion sauvegardée dans : {CONFUSION_MATRIX_PATH}")

if __name__ == '__main__':
    train_main()