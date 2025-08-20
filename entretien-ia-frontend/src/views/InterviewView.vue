<template>
  <div class="interview-page">
    <!-- 1. État de Chargement Initial -->
    <div v-if="isLoading" class="text-center py-5">
      <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;"></div>
      <p class="mt-3 text-muted fs-5">Préparation de votre session d'entretien...</p>
    </div>

    <!-- 2. État d'Erreur -->
    <div v-else-if="error" class="alert alert-danger col-md-8 mx-auto">
        <h4 class="alert-heading">Une erreur est survenue</h4>
        <p>{{ error }}</p>
        <p>Veuillez réessayer ou contacter le support.</p>
    </div>

    <!-- 3. État Final (Entretien Soumis) -->
    <div v-else-if="isSessionFinished" class="alert alert-success text-center col-md-8 mx-auto">
      <h4><i class="bi bi-check-circle-fill me-2"></i>Entretien Terminé et Soumis</h4>
      <p>Merci pour votre participation ! Votre enregistrement va maintenant être analysé par notre IA.</p>
      <p>Vous pouvez consulter le statut de l'analyse sur votre tableau de bord.</p>
      <div class="d-flex justify-content-center gap-2 mt-3">
          <router-link :to="`/player/${sessionId}`" class="btn btn-primary">Revoir ma soumission</router-link>
          <router-link to="/candidate/dashboard" class="btn btn-secondary">Retour au Tableau de Bord</router-link>
      </div>
    </div>

    <!-- 4. Interface Principale de l'Entretien -->
    <div v-else class="row g-5">
      <!-- Colonne de Gauche : Questions et Instructions -->
      <div class="col-lg-5">
        <div class="sticky-top" style="top: 100px;">
          <!-- NOUVEAU : Barre de progression -->
          <div class="progress mb-3" style="height: 10px;">
            <div class="progress-bar" role="progressbar" :style="{ width: progressPercentage + '%' }" :aria-valuenow="progressPercentage" aria-valuemin="0" aria-valuemax="100"></div>
          </div>

          <p class="text-muted fw-bold">Question {{ currentQuestionIndex + 1 }} / {{ questions.length }}</p>
          <div class="card bg-light border-0 shadow-sm">
            <div class="card-body p-4">
              <h3 class="card-title fw-bold">{{ currentQuestion.intitule }}</h3>
              <span class="badge bg-primary-subtle text-primary-emphasis rounded-pill mt-2">{{ currentQuestion.category }}</span>
            </div>
          </div>
          <!-- Navigation -->
          <div class="d-flex justify-content-between mt-4">
            <button @click="changeQuestion('prev')" class="btn btn-outline-secondary" :disabled="currentQuestionIndex === 0"><i class="bi bi-arrow-left"></i> Précédente</button>
            <button @click="changeQuestion('next')" class="btn btn-outline-secondary" :disabled="isLastQuestion">Suivante <i class="bi bi-arrow-right"></i></button>
          </div>
          <!-- NOUVEAU : Conseil contextuel -->
          <div class="alert alert-info mt-4 small p-2 text-center">
            <i class="bi bi-lightbulb-fill me-2"></i><strong>Conseil :</strong> Regardez la caméra pour un meilleur contact visuel.
          </div>
        </div>
      </div>
      <!-- Colonne de Droite : Vidéo et Actions -->
      <div class="col-lg-7">
        <InterviewBox ref="interviewBox" />

        <!-- Écran de Revue après une tentative -->
        <div v-if="uploadSuccess" class="text-center mt-4 animate__animated animate__fadeIn">
            <div class="alert alert-info">
                <h4 class="alert-heading"><i class="bi bi-camera-video-fill me-2"></i>Tentative Enregistrée !</h4>
                <p v-if="tentativesRestantes > 0">Il vous reste <strong>{{ tentativesRestantes }}</strong> tentative(s). Vous pouvez revoir votre vidéo, recommencer, ou soumettre cette version.</p>
                <p v-else>Vous avez utilisé toutes vos tentatives. Veuillez soumettre cette dernière version.</p>
            </div>
            <div class="d-flex justify-content-center flex-wrap gap-3">
                 <router-link :to="`/player/${sessionId}`" class="btn btn-secondary"><i class="bi bi-play-btn-fill me-2"></i>Revoir ma tentative</router-link>
                 <button v-if="tentativesRestantes > 0" @click="resetForNewAttempt" class="btn btn-warning"><i class="bi bi-arrow-counterclockwise me-2"></i>Utiliser une autre tentative</button>
                 <button @click="handleSubmit" class="btn btn-success" :disabled="isSubmitting">
                    <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2"></span>
                    <i v-else class="bi bi-send-check-fill me-2"></i>
                    Soumettre cette version définitivement
                 </button>
            </div>
        </div>

        <!-- Vue initiale pour enregistrer -->
        <div v-else class="text-center mt-4">
          <button v-if="!isRecording" @click="handleStart" class="btn btn-primary btn-lg" style="min-width: 300px;" :disabled="!isMediaReady">
            Démarrer (Tentative {{ tentativesRealisees + 1 }}/{{ nombreTentatives }})
          </button>
          <button v-else @click="handleStopAndUpload" class="btn btn-danger btn-lg" style="min-width: 300px;" :disabled="isUploading">
            <span v-if="isUploading" class="spinner-border spinner-border-sm me-2"></span>
            {{ isUploading ? 'Traitement...' : "Terminer cette tentative" }}
          </button>
        </div>
        <div v-if="statusMessage" class="alert mt-3 text-center" :class="statusClass">{{ statusMessage }}</div>
      </div>
    </div>

    <!-- NOUVEAU : Modale de Briefing -->
    <div class="modal fade" id="briefingModal" tabindex="-1" aria-hidden="true" data-bs-backdrop="static" data-bs-keyboard="false">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header border-0">
            <h5 class="modal-title fw-bold"><i class="bi bi-info-circle-fill me-2"></i>Instructions pour votre Entretien</h5>
          </div>
          <div class="modal-body">
            <p>Bienvenue dans votre session d'entretien en différé. Voici quelques points importants :</p>
            <ul class="list-group list-group-flush">
              <li class="list-group-item"><i class="bi bi-card-checklist me-2 text-primary"></i>Vous aurez <strong>{{ questions.length }} questions</strong> à répondre.</li>
              <li class="list-group-item"><i class="bi bi-arrow-repeat me-2 text-primary"></i>Vous disposez de <strong>{{ nombreTentatives }} tentatives</strong> au total pour enregistrer votre meilleure prestation.</li>
              <li class="list-group-item"><i class="bi bi-camera-video me-2 text-primary"></i>L'ensemble de vos réponses sera enregistré en <strong>une seule vidéo</strong> par tentative.</li>
            </ul>
            <p class="fw-bold mt-4">Nos conseils pour réussir :</p>
            <ul class="list-unstyled small text-muted">
              <li><i class="bi bi-check-lg text-success"></i> Installez-vous dans un endroit calme et bien éclairé.</li>
              <li><i class="bi bi-check-lg text-success"></i> Essayez de regarder directement la caméra.</li>
              <li><i class="bi bi-check-lg text-success"></i> Parlez de manière claire et naturelle.</li>
            </ul>
            <p class="mt-4">Êtes-vous prêt(e) à commencer ?</p>
          </div>
          <div class="modal-footer border-0">
            <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Je suis prêt(e)</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import InterviewBox from '@/components/InterviewBox.vue';
import * as api from '@/services/api';
import { Modal } from 'bootstrap';

const props = defineProps({ sessionId: { type: [String, Number], required: true } });
const router = useRouter();

const isLoading = ref(true);
const error = ref('');
const questions = ref([]);
const session = ref(null);
const currentQuestionIndex = ref(0);
const interviewBox = ref(null);
const isRecording = ref(false);
const isUploading = ref(false);
const isSubmitting = ref(false);
const statusMessage = ref('');
const statusType = ref('info');
const uploadSuccess = ref(false);
const questionEvents = ref([]);

const nombreTentatives = computed(() => session.value?.nombre_tentatives || 0);
const tentativesRealisees = computed(() => session.value?.tentatives_realisees || 0);
const tentativesRestantes = computed(() => Math.max(0, nombreTentatives.value - tentativesRealisees.value));
const isSessionFinished = computed(() => session.value?.statut !== 'pending');
const currentQuestion = computed(() => questions.value[currentQuestionIndex.value] || {});
const isLastQuestion = computed(() => currentQuestionIndex.value >= questions.value.length - 1);
const statusClass = computed(() => `alert-${statusType.value}`);
const isMediaReady = computed(() => interviewBox.value?.mediaReady);
const progressPercentage = computed(() => {
  if (questions.value.length === 0) return 0;
  return ((currentQuestionIndex.value + 1) / questions.value.length) * 100;
});

onMounted(async () => {
  try {
    const [sessionDetailsResponse, questionsResponse] = await Promise.all([
      api.getSessionDetails(props.sessionId),
      api.getSessionQuestions(props.sessionId)
    ]);
    session.value = sessionDetailsResponse.data;
    questions.value = questionsResponse.data;
    if (!session.value || questions.value.length === 0) {
      error.value = "Impossible de charger les données de l'entretien.";
    } else if (!isSessionFinished.value) {
      const briefingModal = new Modal(document.getElementById('briefingModal'));
      briefingModal.show();
    }
  } catch (err) {
    error.value = "Erreur critique lors du chargement de la session.";
  } finally {
    isLoading.value = false;
  }
});

const changeQuestion = (direction) => {
  let newIndex = currentQuestionIndex.value;
  if (direction === 'prev' && newIndex > 0) newIndex--;
  else if (direction === 'next' && !isLastQuestion.value) newIndex++;
  if (newIndex !== currentQuestionIndex.value) {
    currentQuestionIndex.value = newIndex;
    if (isRecording.value) recordQuestionChangeEvent();
  }
};

const recordQuestionChangeEvent = () => {
    if (!interviewBox.value) return;
    const currentQuestionId = questions.value[currentQuestionIndex.value].id;
    const timestampInSeconds = interviewBox.value.elapsedTime;
    questionEvents.value.push({ questionId: currentQuestionId, timestamp: timestampInSeconds });
};

const handleStart = () => {
  currentQuestionIndex.value = 0;
  interviewBox.value.start();
  isRecording.value = true;
  questionEvents.value = [];
  recordQuestionChangeEvent();
};

const handleStopAndUpload = async () => {
  isUploading.value = true;
  statusMessage.value = "Traitement de votre enregistrement, veuillez patienter...";
  const file = await interviewBox.value.stop();
  isRecording.value = false;
  if (!file) { isUploading.value = false; statusMessage.value = "L'enregistrement était vide."; statusType.value = 'danger'; return; }

  statusMessage.value = "Envoi de votre tentative en cours...";
  try {
    const response = await api.uploadFileWithEvents(props.sessionId, file, questionEvents.value);
    session.value.tentatives_realisees = response.data.tentatives_realisees;
    uploadSuccess.value = true;
    statusMessage.value = '';
  } catch (err) {
    statusMessage.value = err.response?.data?.msg || "Échec de l'envoi.";
    statusType.value = 'danger';
  } finally {
    isUploading.value = false;
  }
};

const resetForNewAttempt = () => {
  uploadSuccess.value = false;
  currentQuestionIndex.value = 0;
};

const handleSubmit = async () => {
    if (!confirm("Êtes-vous sûr de vouloir soumettre cette version ? Cette action est définitive.")) return;
    isSubmitting.value = true;
    statusMessage.value = "Soumission de votre entretien final...";
    statusType.value = 'info';
    try {
        await api.submitSession(props.sessionId);
        session.value.statut = 'file_uploaded';
        statusMessage.value = '';
    } catch (error) {
        statusMessage.value = error.response?.data?.msg || "Erreur lors de la soumission.";
        statusType.value = 'danger';
    } finally {
        isSubmitting.value = false;
    }
};
</script>

<style scoped>
@import 'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css';
.sticky-top { position: -webkit-sticky; position: sticky; top: 100px; }
.progress-bar {
  background-color: var(--blue-primary);
  transition: width 0.5s ease;
}
</style>
