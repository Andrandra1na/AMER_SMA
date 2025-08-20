<template>
  <div class="report-page">
    <div v-if="isLoading" class="d-flex justify-content-center align-items-center" style="min-height: 70vh;">
      <div class="text-center">
        <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status"></div>
        <h3 class="mt-3">Génération du rapport d'analyse IA...</h3>
        <p class="text-muted">Cela peut prendre un instant.</p>
      </div>
    </div>

    <div v-else-if="error" class="alert alert-danger col-md-8 mx-auto">
      <h4 class="alert-heading"><i class="bi bi-exclamation-triangle-fill me-2"></i>Erreur de Chargement du Rapport</h4>
      <p>{{ error }}</p>
      <hr>
      <p class="mb-0">Veuillez vérifier que l'analyse pour cette session est bien terminée ou contacter un administrateur.</p>
    </div>

    <!-- ====================================================== -->
    <!-- SECTION 2 : AFFICHAGE DU RAPPORT COMPLET               -->
    <!-- ====================================================== -->
    <div v-else-if="report">
      <div class="report-header card shadow-sm mb-4">
        <div class="card-body p-4">
          <div class="row align-items-center">
            <!-- Section Titre et Candidat -->
            <div class="col-lg-6">
              <h1 class="display-5 fw-bold mb-1">Rapport d'Analyse</h1>
              <p class="fs-4 text-muted mb-2">
                Candidat : <strong>{{ report.session_info.candidat_nom }}</strong>
              </p>
            </div>
            <!-- Section Infos Clés -->
            <div class="col-lg-6">
              <div class="d-flex flex-column align-items-lg-end">
                <p class="mb-1"><strong>Poste Visé :</strong> {{ report.session_info.poste_vise }}</p>
                <p class="mb-2"><strong>Date de l'entretien :</strong> {{ report.session_info.date }}</p>
                <!-- Groupe de boutons d'action -->
                <div class="actions-group">
                  <router-link :to="`/player/${sessionId}`" class="btn btn-sm btn-outline-secondary"><i class="bi bi-play-btn-fill me-2"></i>Revoir la Vidéo</router-link>
                  <button @click="exportToPDF" class="btn btn-sm btn-primary ms-2"><i class="bi bi-download me-2"></i>Exporter en PDF</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Le conteneur global qui sera capturé pour l'export PDF -->
      <div id="export-container">
        <!-- En-tête spécifique pour le PDF, caché par défaut sur la page web -->
        <div class="pdf-header d-none">
          <h2 class="fw-bold">Rapport d'Évaluation - Entretien</h2>
          <hr>
          <div class="row">
            <div class="col-6"><strong>Candidat :</strong> {{ report.session_info.candidat_nom }}</div>
            <div class="col-6"><strong>Poste Visé :</strong> {{ report.session_info.poste_vise }}</div>
            <div class="col-6"><strong>Date :</strong> {{ report.session_info.date }}</div>
            <div class="col-6"><strong>ID Session :</strong> {{ report.session_info.id }}</div>
          </div>
          <hr style="margin-top: 1rem; margin-bottom: 2rem;">
        </div>

        <!-- Contenu principal du rapport -->
        <div id="report-content" class="p-3 p-md-4 bg-white rounded-3">

          <!-- ====================================================== -->
          <!--  BANNIÈRE DE QUALIFICATION ET RÉSUMÉ IA       -->
          <!-- ====================================================== -->
          <div class="card text-center mb-5 qualification-card" :class="qualification.bgClass">
            <div class="card-body">
              <i :class="qualification.icon" class="display-3"></i>
              <h2 class="card-title mt-2">{{ qualification.title }}</h2>
              <p class="lead">{{ qualification.text }}</p>
            </div>
          </div>

          <div class="row g-4 mb-5 row-cols-1 row-cols-lg-2">
            <div class="col-lg-7">
              <h3 class="fw-bold"><i class="bi bi-lightbulb-fill me-2 text-primary"></i>Résumé et Recommandation de l'IA</h3>
              <div class="card h-100"><div class="card-body"><p>{{ aiSummary }}</p></div></div>
            </div>
            <div class="col-lg-5">
              <h3 class="fw-bold"><i class="bi bi-exclamation-triangle-fill me-2 text-danger" v-if="redFlags.length > 0"></i>Points de Vigilance</h3>
              <div class="card h-100"><div class="card-body">
                <ul v-if="redFlags.length > 0" class="list-unstyled mb-0">
                  <li v-for="(flag, index) in redFlags" :key="index" class="mb-2"><i class="bi bi-flag-fill text-danger me-2"></i>{{ flag }}</li>
                </ul>
                <p v-else class="text-muted mb-0"><i class="bi bi-check-circle-fill text-success me-2"></i>Aucun point de vigilance majeur détecté par l'IA.</p>
              </div></div>
            </div>
          </div>
          <!-- ====================================================== -->
          <!-- NOUVEAU : CARTE DE PROFIL COMPORTEMENTAL             -->
          <!-- ====================================================== -->
          <h3 class="fw-bold mt-5 mb-3"><i class="bi bi-person-bounding-box me-2 text-primary"></i>Profil de Communication Détecté</h3>
          <div class="card shadow-sm mb-5">
            <div class="card-body p-4 d-flex align-items-center">
              <div class="profile-icon me-4">
                <i :class="communicationProfile.icon"></i>
              </div>
              <div class="profile-text">
                <h4 class="card-title fw-bold">{{ communicationProfile.title }}</h4>
                <p class="card-text text-muted mb-0">{{ communicationProfile.description }}</p>
              </div>
            </div>
          </div>

          <!-- Sous-section 2.1 : Synthèse et Score Global -->
          <div class="row g-4 mb-5 align-items-center">
            <div class="col-lg-4 text-center">
              <h3 class="fw-bold">Score Global</h3>
              <div class="svg-score-container mx-auto">
                <svg viewBox="0 0 36 36" class="circular-chart"><path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" /><path class="circle" :stroke-dasharray="`${globalScore}, 100`" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" /></svg>
                <div class="score-text"><span class="score-value">{{ globalScore }}</span><small class="score-total">/ 100</small></div>
              </div>
              <p class="fs-5 mt-2 fw-bold" :style="{ color: globalScoreColor }">{{ globalScoreText }}</p>
            </div>
            <div class="col-lg-8">
              <h3 class="fw-bold">Synthèse des Compétences</h3>
              <div class="card shadow-sm"><div class="card-body" style="height: 400px;"><ScoreChart v-if="chartScores" :scores="chartScores" /></div></div>
            </div>
          </div>

          <!-- Sous-section 2.2 : Analyse Détaillée -->
          <h3 class="fw-bold mt-5 mb-4"><i class="bi bi-zoom-in me-2 text-primary"></i>Analyse de la Performance</h3>

          <!-- Première ligne avec 4 cartes -->
          <div class="row row-cols-1 row-cols-md-2 row-cols-xl-4 g-4 mb-4">
            <div class="col">
              <div class="card h-100 metric-card">
                <div class="card-body text-center">
                  <div class="metric-icon"><i class="bi bi-chat-left-quote-fill"></i>
                  </div>
                  <h6 class="card-subtitle mb-2 text-muted">Pertinence</h6>
                  <p class="card-text fs-2 fw-bold">{{ formattedScores.relevance }}<span class="fs-6">/100</span></p>
                  <small>Capacité à répondre à la question.</small>
                </div>
              </div>
            </div>
            <div class="col">
              <div class="card h-100 metric-card">
                <div class="card-body text-center">
                  <div class="metric-icon"><i class="bi bi-spellcheck"></i>
                  </div>
                  <h6 class="card-subtitle mb-2 text-muted">Clarté</h6>
                  <p class="card-text fs-2 fw-bold">{{ formattedScores.grammar }}<span class="fs-6">/100</span></p>
                  <small>Qualité de la grammaire.</small>
                </div>
              </div>
            </div>
            <div class="col">
              <div class="card h-100 metric-card">
                <div class="card-body text-center">
                  <div class="metric-icon"><i class="bi bi-eye-fill"></i></div>
                  <h6 class="card-subtitle mb-2 text-muted">Contact Visuel</h6>
                  <p class="card-text fs-2 fw-bold">{{ globalGazeContact.toFixed(0) }}<span class="fs-6">%</span></p>
                  <small>Temps passé à regarder la caméra.</small>
                </div>
              </div>
            </div>
            <div class="col">
                <div class="card h-100 metric-card">
                  <div class="card-body text-center">
                    <div class="metric-icon"><i :class="emotionIcon"></i></div>
                    <h6 class="card-subtitle mb-2 text-muted">Émotion Dominante</h6>
                    <p class="card-text fs-2 fw-bold text-capitalize">{{ report.emotion_scores.dominant_emotion || 'N/A' }}</p>
                    <small>Ambiance générale de la voix.</small>
                  </div>
                </div>
            </div>
          </div>

          <!-- Deuxième ligne avec 2 cartes, centrées sur les grands écrans -->
          <div class="row row-cols-1 row-cols-md-2 g-4 justify-content-center">
              <div class="col">
                <div class="card h-100 metric-card"><div class="card-body text-center"><div class="metric-icon"><i class="bi bi-speedometer2"></i></div><h6 class="card-subtitle mb-2 text-muted">Débit de Parole</h6><p class="card-text fs-2 fw-bold">{{ report.vocal_analysis.speech_rate?.toFixed(0) }}</p><small class="text-muted">mots par minute</small></div></div>
              </div>
              <div class="col">
                <div class="card h-100 metric-card"><div class="card-body text-center"><div class="metric-icon"><i class="bi bi-pause-btn-fill"></i></div><h6 class="card-subtitle mb-2 text-muted">Fluidité</h6><p class="card-text fs-2 fw-bold">{{ report.vocal_analysis.pause_count ?? 'N/A' }}</p><small class="text-muted">pauses > 0.5s</small></div></div>
              </div>
          </div>

          <h4 class="fw-bold mt-5 mb-3"><i class="bi bi-graph-up me-2"></i>Comportement Visuel par Question</h4>

          <!-- Carte contenant la description ET le graphique -->
          <div class="card shadow-sm mb-5">
            <div class="card-body">
              <p class="text-muted small">
                Ce graphique montre la répartition du regard du candidat en pourcentage du temps de réponse pour chaque question. Le "Contact Visuel" est un indicateur clé d'engagement et de confiance.
              </p>
              <div style="height: 350px;">
                <Bar v-if="gazeByQuestionChartData" :data="gazeByQuestionChartData" :options="gazeChartOptions" />
              </div>
            </div>
          </div>

          <!-- Sous-section 2.3 : Analyse par Question -->
          <h3 class="fw-bold mt-5 mb-3"><i class="bi bi-patch-question-fill me-2 text-primary"></i>Détail par Question</h3>
          <div class="accordion" id="accordionAnswers">
            <div v-for="(answer, index) in report.detailed_answers" :key="answer.question_id" class="accordion-item">
              <h2 class="accordion-header">
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" :data-bs-target="'#collapse'+index"><strong>Q{{ index + 1 }}: {{ answer.question_intitule }}</strong></button>
              </h2>
              <div :id="'collapse'+index" class="accordion-collapse collapse">
                <div class="accordion-body"><p><strong>Transcription de la réponse :</strong></p><blockquote class="blockquote fst-italic bg-light p-3 rounded">"{{ answer.transcription || 'Aucune réponse détectée pour cette section.' }}"</blockquote>
                  <hr>
                  <div class="row">
                    <div class="col-md-6">
                      <strong>Score de Pertinence :</strong> <span class="badge fs-6" :class="scoreBadge(answer.score_pertinence)">{{ (answer.score_pertinence * 100).toFixed(0) }} / 100</span>
                    </div>
                    <div class="col-md-6"><strong>Score de Grammaire :</strong> <span class="badge fs-6" :class="scoreBadge(answer.score_grammaire)">{{ (answer.score_grammaire * 100).toFixed(0) }} / 100</span>
                    </div>
                  </div>

                  <!-- --- NOUVELLE SECTION : EXPLICATION RAG --- -->
                    <div v-if="answer.pertinence_explication" class="mt-3 alert alert-info small">
                      <strong class="d-block mb-1"><i class="bi bi-robot me-2"></i>Justification de l'IA (RAG) :</strong>
                      {{ answer.pertinence_explication }}
                    </div>

                </div>
              </div>
            </div>
          </div>

                <!-- ====================================================== -->
                <!--  SECTION DE VALIDATION POUR LE RECRUTEUR      -->
                <!-- ====================================================== -->

      <div v-if="authStore.userRole === 'recruteur' || authStore.userRole === 'admin'" class="mt-5">
        <hr>
        <h3 class="fw-bold mt-5 mb-3"><i class="bi bi-pencil-square me-2 text-primary"></i>Zone de Validation RH</h3>

        <!-- Affiche le commentaire si déjà validé -->
        <div v-if="report.validation_info?.validated" class="card bg-light border-success">
          <div class="card-body">
            <h5 class="card-title text-success"><i class="bi bi-check-circle-fill me-2"></i>Rapport Validé</h5>
            <p class="card-text mb-1"><strong>Commentaire :</strong></p>
            <blockquote class="blockquote mb-0 fst-italic">"{{ report.validation_info.commentaire_rh }}"</blockquote>
          </div>
        </div>

        <!-- Affiche le formulaire si non validé -->
        <div v-else class="card">
          <div class="card-body">
            <h5 class="card-title">Ajouter un commentaire et finaliser</h5>
            <form @submit.prevent="handleValidation">
              <div class="mb-3">
                <textarea v-model="commentaire" class="form-control" rows="4" required></textarea>
              </div>
              <button type="submit" class="btn btn-success" :disabled="isSubmittingValidation">
                <span v-if="isSubmittingValidation" class="spinner-border spinner-border-sm me-2"></span>
                Valider le Rapport
              </button>
              <p v-if="validationError" class="text-danger mt-2">{{ validationError }}</p>
            </form>
          </div>
        </div>
      </div>
              </div>
            </div>
          </div>
        </div>
      </template>

<script setup>
import { useAuthStore } from '@/stores/auth';
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import * as api from '@/services/api';
import ScoreChart from '@/components/ScoreChart.vue';
import { useReportCalculations } from '@/composables/useReportCalculations.js';
import { Bar } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';


ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

const route = useRoute();
const report = ref(null);
const isLoading = ref(true);
const error = ref('');
const sessionId = route.params.id;
const authStore = useAuthStore();


const {
    globalScore, qualification, communicationProfile,
    chartScores, formattedScores, aiSummary, redFlags,
    globalScoreStyle, globalScoreText, globalScoreColor,
    globalGazeContact,
    gazeByQuestionChartData
} = useReportCalculations(report);

const commentaire = ref('');
const isSubmittingValidation = ref(false);
const validationError = ref('');

const gazeChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { position: 'top' },
        title: { display: true, text: 'Répartition du regard en % du temps de réponse' }
    },
    scales: {
        x: { stacked: true }, // Les barres sont empilées
        y: { stacked: true, max: 100, title: { display: true, text: '%' } }
    }
};


// --- CYCLE DE VIE ---
onMounted(async () => {
  try {
    const response = await api.getReport(sessionId);
    report.value = response.data;

    console.log("Données du rapport reçues par le frontend:", report.value);
    console.log("Détail de la première réponse:", report.value.detailed_answers[0]);

    if (report.value?.validation_info?.validated) {
        commentaire.value = report.value.validation_info.commentaire_rh;
    }
  } catch (err) {
    error.value = "Impossible de charger le rapport.";
  } finally {
    isLoading.value = false;
  }
});

const handleValidation = async () => {
    isSubmittingValidation.value = true;
    validationError.value = '';
    try {
        const response = await api.validateReport(sessionId, commentaire.value);
        report.value = response.data;
    } catch (err) {
        validationError.value = err.response?.data?.msg || "Erreur de validation.";
    } finally {
        isSubmittingValidation.value = false;
    }
};


const emotionIcon = computed(() => {
    const emotion = report.value?.emotion_scores?.dominant_emotion;
    switch (emotion) {
        case 'heureux': return 'bi bi-emoji-smile-fill text-success';
        case 'calme': return 'bi bi-emoji-neutral-fill text-primary';
        case 'neutre': return 'bi bi-emoji-expressionless-fill text-secondary';
        case 'surpris': return 'bi bi-emoji-surprise-fill text-info';
        case 'triste': return 'bi bi-emoji-frown-fill text-muted';
        case 'peur': return 'bi bi-emoji-dizzy-fill text-warning';
        case 'colère': return 'bi bi-emoji-angry-fill text-danger';
        case 'dégoût': return 'bi bi-emoji-dizzy-fill text-danger';
        default: return 'bi bi-question-circle-fill text-secondary';
    }
});


const scoreBadge = (score) => {
    if (score === null || score === undefined) return 'bg-secondary';
    const finalScore = score * 100;
    if (finalScore >= 85) return 'bg-success';
    if (finalScore >= 60) return 'bg-warning text-dark';
    return 'bg-danger';
};

const exportToPDF = async () => {
  if (!report.value) return;

  const exportButton = event.target;
  exportButton.disabled = true;
  exportButton.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Génération...`;

  try {
    // 1. On appelle notre nouvelle fonction API
    const pdfBlob = await api.downloadPdfReport(sessionId);

    // 2. On crée une URL locale pour ce fichier en mémoire (Blob)
    const url = window.URL.createObjectURL(pdfBlob);

    // 3. On crée un lien '<a>' invisible dans le document
    const link = document.createElement('a');
    link.href = url;

    // 4. On définit le nom du fichier pour le téléchargement
    const reportTitle = `Rapport_Entretien_${report.value.session_info.candidat_nom.replace(' ', '_')}.pdf`;
    link.setAttribute('download', reportTitle);

    // 5. On ajoute le lien au document, on le clique, puis on le supprime
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // 6. On libère l'URL de l'objet pour économiser la mémoire
    window.URL.revokeObjectURL(url);

  } catch (error) {
    console.error("Échec de l'export PDF:", error);
    alert("Une erreur est survenue lors de la génération du rapport PDF.");
  } finally {
    // On réactive le bouton
    exportButton.disabled = false;
    exportButton.innerHTML = `<i class="bi bi-download me-2"></i>Exporter en PDF`;
  }
};
</script>

<style scoped>
.report-page { background-color: var(--bg-color); padding: 1.5rem; }
#report-content { border: 1px solid var(--border-color); }
.svg-score-container { position: relative; width: 180px; height: 180px; }
.circular-chart { display: block; max-width: 100%; max-height: 100%; transform: rotate(-90deg); transform-origin: center center; }
.circle-bg { fill: none; stroke: #eee; stroke-width: 3.8; }
.circle { fill: none; stroke: var(--blue-primary); stroke-width: 2.8; stroke-linecap: round; animation: progress 1s ease-out forwards; }
@keyframes progress { 0% { stroke-dasharray: 0 100; } }
.score-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }
.score-value { font-size: 3.5rem; font-weight: 700; color: var(--blue-primary); line-height: 1; }
.score-total { font-size: 1.1rem; color: var(--text-muted); display: block; margin-top: -5px; }
.metric-card { transition: all 0.2s ease-in-out; border: none; }
.metric-card:hover { transform: translateY(-5px); box-shadow: 0 8px 30px rgba(0,0,0,0.08) !important; }
.metric-icon { font-size: 2.5rem; color: var(--blue-light); margin-bottom: 0.5rem; }
.progress { background-color: var(--bg-alternate); }
.accordion-button:not(.collapsed) { color: var(--text-primary); background-color: var(--bg-color); font-weight: 600; box-shadow: none; }
.accordion-item { border-color: var(--border-color); background-color: var(--surface-color); }
.pdf-header { display: none; padding: 20px; }
.pdf-render .pdf-header { display: block; padding-bottom: 10px; margin-bottom: 20px; }
.pdf-render .card, .pdf-render .accordion-item { box-shadow: none !important; border: 1px solid #ddd !important; }
.qualification-card {
    border-width: 2px;
    border-style: solid;
    border-color: currentColor;
}
</style>
