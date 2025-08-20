<template>
  <div class="container-fluid candidate-dashboard">
    <!-- 1. État de Chargement -->
    <div v-if="isLoading" class="text-center py-5">
      <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
        <span class="visually-hidden">Chargement...</span>
      </div>
      <p class="mt-3 text-muted">Chargement de votre espace personnel...</p>
    </div>

    <!-- 2. État d'Erreur -->
    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

    <!-- 3. Contenu Principal du Dashboard -->
    <div v-else-if="dashboardData">
      <!-- En-tête d'accueil -->
      <h1 class="display-5 fw-bold mb-2">Bienvenue, {{ dashboardData.nom_candidat }} !</h1>
      <p class="lead text-muted mb-5">Suivez ici vos entretiens et analysez vos performances.</p>

      <!-- Section des entretiens en attente -->
      <div v-if="dashboardData.pending_sessions.length > 0" class="mb-5">
        <h3 class="mb-3"><i class="bi bi-camera-reels-fill me-2 text-primary"></i>Entretien à Réaliser</h3>
        <div v-for="session in dashboardData.pending_sessions" :key="session.id" class="card shadow-sm mb-3 animate__animated animate__fadeInUp">
          <div class="card-body p-4 d-flex justify-content-between align-items-center flex-wrap gap-3">
            <div>
              <h5 class="card-title mb-1">Entretien pour le poste de :</h5>
              <p class="h4 fw-bold text-primary mb-0">{{ session.poste_vise }}</p>
              <small class="text-muted">Assigné le {{ session.date_creation }}</small>
            </div>
            <router-link :to="{ name: 'interview', params: { sessionId: session.id } }" class="btn btn-primary btn-lg">
              <i class="bi bi-play-circle-fill me-2"></i>Commencer l'Entretien
            </router-link>
          </div>
        </div>
      </div>
      <div v-else class="alert alert-success mb-5">
        <h4 class="alert-heading"><i class="bi bi-check-circle-fill me-2"></i>Tout est à jour !</h4>
        <p>Vous n'avez aucun entretien en attente pour le moment.</p>
      </div>

      <!-- Section des Performances et de l'Historique -->
      <h3 class="mt-5 mb-4"><i class="bi bi-bar-chart-line-fill me-2 text-primary"></i>Vos Performances Passées</h3>

      <div v-if="dashboardData.completed_sessions.length > 0">
        <!-- Cartes KPI avec les moyennes globales -->
        <div class="row g-4 mb-4">
          <div class="col-lg-4 col-md-6">
            <div class="card kpi-card shadow-sm h-100" v-tooltip="'Cette note est la moyenne pondérée de toutes vos performances.'">
              <div class="card-body"><i class="bi bi-clipboard2-data-fill"></i><div><p class="h3 fw-bolder mb-0">{{ (globalStats.avg_global_score).toFixed(0) }}<span class="fs-6">/100</span></p><div class="text-muted">Score Global Moyen</div></div></div>
            </div>
          </div>
          <div class="col-lg-4 col-md-6">
            <div class="card kpi-card shadow-sm h-100" v-tooltip="'Votre capacité moyenne à répondre de manière ciblée aux questions.'">
              <div class="card-body"><i class="bi bi-bullseye text-primary"></i><div><p class="h3 fw-bolder mb-0">{{ (globalStats.avg_relevance_score * 100).toFixed(0) }}<span class="fs-6">%</span></p><div class="text-muted">Pertinence Moyenne</div></div></div>
            </div>
          </div>
          <div class="col-lg-4 col-md-12">
            <div class="card kpi-card shadow-sm h-100" v-tooltip="'La qualité moyenne de votre grammaire et de votre syntaxe.'">
              <div class="card-body"><i class="bi bi-spellcheck text-success"></i><div><p class="h3 fw-bolder mb-0">{{ (globalStats.avg_grammar_score * 100).toFixed(0) }}<span class="fs-6">%</span></p><div class="text-muted">Clarté Moyenne</div></div></div>
            </div>
          </div>
        </div>

        <!-- DataTable pour l'historique détaillé -->
        <div class="card shadow-sm">
          <div class="card-header d-flex justify-content-between align-items-center flex-wrap">
            <h5 class="mb-0">Historique Détaillé de vos Entretiens</h5>
            <div class="col-12 col-md-4 mt-2 mt-md-0">
              <input type="text" class="form-control form-control-sm" v-model="searchValue" placeholder="Rechercher par poste...">
            </div>
          </div>
          <div class="card-body">
            <EasyDataTable
              :headers="headers"
              :items="dashboardData.completed_sessions"
              :search-value="searchValue"
              theme-color="#005f73"
              table-class-name="custom-table"
              rows-per-page-message="Lignes par page"
              rows-of-page-separator-message="sur"
              empty-message="Aucun entretien ne correspond à votre recherche"
              buttons-pagination
            >
              <template #item-date="{ date }">{{ new Date(date).toLocaleDateString('fr-FR') }}</template>
              <template #item-global_score="{ global_score }">
                <div v-if="global_score !== null" class="score-cell">
                  <span class="score-value">{{ global_score.toFixed(0) }}</span>
                  <div class="progress" style="height: 5px; width: 80px;">
                    <div class="progress-bar" :class="scoreBadge(global_score, 100)" :style="{ width: global_score + '%' }"></div>
                  </div>
                </div>
                <span v-else class="text-muted">N/A</span>
              </template>
              <template #item-dominant_emotion="{ dominant_emotion }">
                <span :title="dominant_emotion" class="text-capitalize d-flex align-items-center">
                  <i :class="emotionIcon(dominant_emotion)" class="me-2 fs-5"></i>
                  {{ dominant_emotion }}
                </span>
              </template>
              <template #item-statut="{ statut }">
                <span class="badge" :class="statusBadgeClass(statut)">
                  <i v-if="statut === 'analyzing'" class="spinner-border spinner-border-sm me-1" style="width: 0.8rem; height: 0.8rem;"></i>
                  {{ formatStatus(statut) }}
                </span>
              </template>
              <template #item-actions="item">
                <div class="d-flex justify-content-end">
                  <router-link :to="`/feedback/${item.id}`" class="btn btn-sm btn-primary">
                    <i class="bi bi-eye-fill"></i> Voir Bilan
                  </router-link>
                </div>
              </template>
            </EasyDataTable>
          </div>
        </div>
      </div>
       <div v-else class="text-center p-5 bg-light rounded">
          <h4>Vos statistiques de performance apparaîtront ici.</h4>
          <p class="text-muted">Passez votre premier entretien pour débloquer votre analyse personnalisée.</p>
       </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import * as api from '@/services/api';
import EasyDataTable from 'vue3-easy-data-table';
import 'vue3-easy-data-table/dist/style.css';
import BootstrapTooltip from 'bootstrap/js/dist/tooltip';

const dashboardData = ref(null);
const isLoading = ref(true);
const error = ref('');
const searchValue = ref('');

onMounted(async () => {
  try {
    const response = await api.getCandidateDashboard();
    dashboardData.value = response.data;
  } catch (err) {
    console.error("Erreur lors de la récupération du dashboard:", err);
    error.value = "Impossible de charger votre espace personnel. Veuillez réessayer plus tard.";
  } finally {
    isLoading.value = false;
  }
});

const headers = [
  { text: "Poste Visé", value: "poste_vise", sortable: true, width: 250 },
  { text: "Date", value: "date", sortable: true },
  { text: "Score Global", value: "global_score", sortable: true, align: 'center' },
  { text: "Émotion Dominante", value: "dominant_emotion", sortable: true, align: 'center' },
  { text: "Statut", value: "statut", align: 'center' },
  { text: "Actions", value: "actions", align: 'end' },
];

const globalStats = computed(() => {
  if (!dashboardData.value?.completed_sessions || dashboardData.value.completed_sessions.length === 0) {
    return { avg_global_score: 0, avg_relevance_score: 0, avg_grammar_score: 0 };
  }
  const sessions = dashboardData.value.completed_sessions;
  const validGlobalScores = sessions.filter(s => s.global_score !== null);
  const avgGlobal = validGlobalScores.length > 0 ? validGlobalScores.reduce((sum, s) => sum + s.global_score, 0) / validGlobalScores.length : 0;

  const validRelevanceScores = sessions.filter(s => s.relevance_score !== null);
  const avgRelevance = validRelevanceScores.length > 0 ? validRelevanceScores.reduce((sum, s) => sum + s.relevance_score, 0) / validRelevanceScores.length : 0;

  const validGrammarScores = sessions.filter(s => s.grammar_score !== null);
  const avgGrammar = validGrammarScores.length > 0 ? validGrammarScores.reduce((sum, s) => sum + s.grammar_score, 0) / validGrammarScores.length : 0;

  return { avg_global_score: avgGlobal, avg_relevance_score: avgRelevance, avg_grammar_score: avgGrammar };
});

// --- Fonctions Utilitaires fournies ---
const formatStatus = (status) => {
  const statusMap = {
    'file_uploaded': 'Prêt pour analyse',
    'analyzing': 'Analyse en cours',
    'analysis_complete': 'Bilan prêt',
    'validated': 'Bilan consulté',
    'analysis_failed': 'Échec de l\'analyse'
  };
  return statusMap[status] || status;
};

const statusBadgeClass = (status) => {
  const classMap = {
    'file_uploaded': 'bg-secondary',
    'analyzing': 'bg-primary',
    'analysis_complete': 'bg-success',
    'validated': 'bg-dark',
    'analysis_failed': 'bg-danger'
  };
  return classMap[status] || 'bg-light text-dark';
};

// --- Autres Fonctions Utilitaires ---
const scoreBadge = (score, max) => {
    if (score === null || score === undefined) return 'bg-secondary';
    const normalizedScore = (score / max) * 100;
    if (normalizedScore >= 80) return 'bg-success';
    if (normalizedScore >= 60) return 'bg-warning';
    return 'bg-danger';
};

const emotionIcon = (emotion) => {
    const iconMap = {
        'heureux': 'bi bi-emoji-smile text-success',
        'calme': 'bi bi-emoji-neutral text-primary',
        'neutre': 'bi bi-emoji-expressionless text-secondary',
        'surpris': 'bi bi-emoji-surprise text-info',
        'triste': 'bi bi-emoji-frown text-muted',
        'peur': 'bi bi-emoji-dizzy text-warning',
        'colère': 'bi bi-emoji-angry text-danger',
        'dégoût': 'bi bi-emoji-dizzy text-danger'
    };
    return iconMap[emotion] || 'bi bi-question-circle';
};

const vTooltip = {
  mounted: (el, binding) => {
    new BootstrapTooltip(el, { title: binding.value, placement: 'top', trigger: 'hover', html: true });
  }
};
</script>

<style>
/* Style global pour surcharger vue3-easy-data-table */
.custom-table {
  --easy-table-border: 1px solid var(--border-color);
  --easy-table-header-font-size: 14px;
  --easy-table-header-background-color: var(--bg-color);
  --easy-table-header-font-color: var(--text-dark);
  

}
</style>

<style scoped>
@import 'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css';
.card { transition: all 0.2s ease-in-out; }
.card:hover { transform: translateY(-5px); box-shadow: 0 8px 30px rgba(0,0,0,0.08) !important; }
.score-cell { display: flex; align-items: center; justify-content: center; gap: 8px; }
.score-value { font-weight: 600; width: 40px; }
.kpi-card .card-body { display: flex; align-items: center; gap: 1.5rem; }
.kpi-card i { font-size: 2.5rem; }
.kpi-card .h3 { font-size: 2rem; }
</style>
