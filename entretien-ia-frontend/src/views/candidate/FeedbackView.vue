<template>
  <div class="feedback-page">
    <div v-if="isLoading" class="text-center py-5">
      <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;"></div>
      <h3 class="mt-3">Calcul de votre bilan de compétences...</h3>
    </div>
    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-else-if="report">
      <div class="text-center p-4 p-md-5 mb-5 rounded-3" :class="finalVerdictForCandidate.bgClass">
        <i :class="finalVerdictForCandidate.icon" class="display-1" style="font-size: 4rem;"></i>
        <h1 class="display-4 fw-bold mt-3">{{ finalVerdictForCandidate.title }}</h1>
        <p class="lead col-lg-8 mx-auto">{{ finalVerdictForCandidate.text }}</p>
        <h2 class="fw-bolder">Votre note indicative : {{ globalScore }}/100</h2>
      </div>

      <div class="row g-5">
        <!-- Colonne de gauche -->
        <div class="col-lg-7">
          <h3 class="mb-4 fw-bold">Votre Profil de Communication Visuel</h3>
          <div class="card shadow-sm mb-5">
            <div class="card-body" style="height: 400px;">
              <ScoreChart v-if="chartScores" :scores="chartScores" />
            </div>
          </div>

          <h3 class="mb-4 fw-bold">Analyse de vos Compétences</h3>
          <div class="card shadow-sm mb-5">
            <div class="list-group list-group-flush">
              <div class="list-group-item p-3 d-flex align-items-center">
                  <div class="competency-icon bg-primary-subtle text-primary-emphasis me-3"><i class="bi bi-bullseye"></i></div>
                  <div class="flex-grow-1">
                      <h5 class="fw-bold mb-0">Pertinence & Structure</h5>
                      <p class="text-muted mb-0">Votre capacité à répondre aux questions.</p>
                  </div>
                  <span class="badge rounded-pill fs-4 bg-primary">{{ competenceScores.relevance }}/5</span>
              </div>
              <div class="list-group-item p-3 d-flex align-items-center">
                  <div class="competency-icon bg-success-subtle text-success-emphasis me-3"><i class="bi bi-mic-fill"></i></div>
                  <div class="flex-grow-1">
                      <h5 class="fw-bold mb-0">Clarté & Élocution</h5>
                      <p class="text-muted mb-0">La fluidité et la qualité de votre discours.</p>
                  </div>
                  <span class="badge rounded-pill fs-4 bg-success">{{ competenceScores.clarity }}/5</span>
              </div>
              <div class="list-group-item p-3 d-flex align-items-center">
                  <div class="competency-icon bg-warning-subtle text-warning-emphasis me-3"><i class="bi bi-emoji-smile-fill"></i></div>
                  <div class="flex-grow-1">
                      <h5 class="fw-bold mb-0">Engagement & Confiance</h5>
                      <p class="text-muted mb-0">L'énergie transmise par votre voix.</p>
                  </div>
                  <span class="badge rounded-pill fs-4 bg-warning text-dark">{{ competenceScores.engagement }}/5</span>
              </div>
            </div>
          </div>

          <div class="row g-4">
            <div class="col-md-6">
              <div class="card h-100 bg-warning-subtle text-dark border-0">
                  <div class="card-body">
                      <h5 class="card-title">
                          <i :class="improvementTip.icon" class="me-2"></i>
                          {{ improvementTip.title }}
                      </h5>
                      <p class="small">{{ improvementTip.text }}</p>
                  </div>
              </div>
  </div>
              </div>
        </div>
        <!-- Colonne de droite -->
        <div class="col-lg-5">
            <div class="sticky-top" style="top: 100px;">
                <h4 class="fw-bold text-center mb-3">Revoir votre prestation</h4>
                <div class="video-wrapper shadow rounded overflow-hidden">
                    <video v-if="videoUrl" :src="videoUrl" controls controlsList="nodownload" class="w-100"></video>
                </div>
                 <div class="text-center mt-3"><router-link to="/candidate/dashboard" class="btn btn-outline-secondary"><i class="bi bi-arrow-left me-2"></i>Retour au Tableau de bord</router-link></div>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import * as api from '@/services/api';
import ScoreChart from '@/components/ScoreChart.vue';
import { useReportCalculations } from '@/composables/useReportCalculations.js';

// --- INITIALISATION ---
const route = useRoute();
const authStore = useAuthStore();
const report = ref(null);
const isLoading = ref(true);
const error = ref('');
const sessionId = route.params.id;

// --- On instancie le composable ---
const {
    globalScore,
    finalVerdictForCandidate,
    competenceScores,
    improvementTip,
    bestAnswer,
    chartScores,
    videoUrl

} = useReportCalculations(report);

onMounted(async () => {
  try {
    const response = await api.getReport(sessionId);
    report.value = response.data;
  } catch (err) {
    error.value = "Impossible de charger votre feedback.";
  } finally {
    isLoading.value = false;
  }
});



</script>


<style scoped>
.feedback-page { padding: 2rem; }
.competency-icon { width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; }
.list-group-item { background-color: transparent; }
.video-wrapper { aspect-ratio: 16 / 9; background-color: #000; border: 1px solid var(--border-color); }
video { width: 100%; height: 100%; object-fit: cover; }
.sticky-top { top: 100px; }
</style>
