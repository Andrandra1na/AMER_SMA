<template>
  <div class="interview-box-container d-flex flex-column align-items-center">
    <div class="video-wrapper shadow-sm rounded overflow-hidden mb-4 position-relative">
      <video ref="videoPlayer" class="w-100 h-100" autoplay muted playsinline></video>
      <div v-if="isRecording" class="recording-indicator">
        <span class="recording-dot"></span> REC
      </div>
      <div v-if="isRecording" class="timer-indicator">
        {{ formattedTime }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed} from 'vue';

const videoPlayer = ref(null);
const isRecording = ref(false);
const mediaReady = ref(false);
const elapsedTime = ref(0);
let timerInterval = null;
let mediaRecorder;
let recordedChunks = [];
let stream;

const formattedTime = computed(() => {
  const minutes = Math.floor(elapsedTime.value / 60);
  const seconds = elapsedTime.value % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
});

onMounted(async () => {
  try {
    // Demande d'accès à la webcam et au microphone
    stream = await navigator.mediaDevices.getUserMedia({
      video: true,
      audio: {
        // On demande des paramètres audio de meilleure qualité si possible
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 44100
      }
    });
    // Affiche le flux vidéo dans la balise <video>
    videoPlayer.value.srcObject = stream;
    mediaReady.value = true;
  } catch (error) {
    console.error("Erreur lors de l'accès à la caméra/micro (getUserMedia):", error);
    // Le composant parent (InterviewView) gérera l'affichage de l'erreur
    // en vérifiant la valeur de 'mediaReady' via la ref.
  }
});


/**
 * Démarre l'enregistrement de la vidéo et du son.
 */
const start = () => {
  if (!mediaReady.value) {
    console.error("Média non prêt, impossible de démarrer l'enregistrement.");
    return;
  }

  isRecording.value = true;
  recordedChunks = [];
  elapsedTime.value = 0;
  timerInterval = setInterval(() => { elapsedTime.value++; }, 1000);

  // --- MODIFICATION : Options d'enregistrement de meilleure qualité ---
  const options = {
    mimeType: 'video/webm; codecs=vp9,opus',
    // On force un bitrate audio de 128kbps pour une meilleure clarté.
    // C'est une suggestion, le navigateur peut l'ignorer s'il ne la supporte pas.
    audioBitsPerSecond: 128000,
  };

  try {
    // On essaie de créer le MediaRecorder avec les options de haute qualité.
    mediaRecorder = new MediaRecorder(stream, options);
    console.log("MediaRecorder initialisé avec options haute qualité.");
  } catch (e) {
    // Si ça échoue (navigateur non compatible), on revient aux options par défaut.
    console.warn("Options d'enregistrement haute qualité non supportées, retour aux options par défaut.", e);
    mediaRecorder = new MediaRecorder(stream);
  }

  // Événement déclenché quand des données sont disponibles
  mediaRecorder.ondataavailable = (event) => {
    if (event.data.size > 0) {
      recordedChunks.push(event.data);
    }
  };

  mediaRecorder.start();
};

/**
 * Arrête l'enregistrement et retourne le fichier vidéo final.
 * @returns {Promise<File|null>} Une promesse qui se résout avec le fichier enregistré.
 */
const stop = () => {
  return new Promise((resolve) => {
    if (!mediaRecorder) {
      resolve(null);
      return;
    }
    // L'événement 'onstop' sera déclenché après l'arrêt de l'enregistrement.
    mediaRecorder.onstop = () => {
      const blob = new Blob(recordedChunks, { type: 'video/webm' });
      const file = new File([blob], `entretien.webm`, { type: 'video/webm' });
      resolve(file); // La promesse se résout avec le fichier final
    };

    // On arrête le minuteur et l'enregistrement.
    clearInterval(timerInterval);
    if (mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
    isRecording.value = false;
  });
};

// On expose les fonctions et l'état nécessaires au composant parent (InterviewView)
defineExpose({ start, stop, elapsedTime, mediaReady });
</script>

<style scoped>
.video-wrapper { width: 100%; max-width: 800px; aspect-ratio: 16 / 9; background-color: #000; border: 1px solid var(--border-color); }
video { width: 100%; height: 100%; object-fit: cover; }
.recording-indicator { position: absolute; top: 1rem; left: 1rem; background-color: rgba(0, 0, 0, 0.7); color: white; padding: 0.25rem 0.75rem; border-radius: 6px; font-weight: 500; font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem; }
.recording-dot { width: 10px; height: 10px; background-color: #dc3545; border-radius: 50%; animation: pulse 1.5s infinite; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
.timer-indicator { position: absolute; top: 1rem; right: 1rem; background-color: rgba(0, 0, 0, 0.7); color: white; padding: 0.25rem 0.75rem; border-radius: 6px; font-family: 'monospace'; font-size: 1.1rem; font-weight: bold; }
</style>
