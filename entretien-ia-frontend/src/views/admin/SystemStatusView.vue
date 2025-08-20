<template>
  <div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h1 class="display-5 fw-bold">Centre de Contrôle Qualité</h1>
      <div class="d-flex gap-2">
        <a
          v-if="lastReport"
          :href="htmlReportUrl"
          target="_blank"
          class="btn btn-outline-secondary"
        >
          <i class="bi bi-file-earmark-text-fill me-2"></i>Voir le Rapport HTML Détaillé
        </a>
            <button @click="runTests" class="btn btn-primary" :disabled="isLoading">
                <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
                {{ isLoading ? 'Tests en cours...' : 'Relancer les Tests' }}
            </button>
        </div>
    </div>

    <div v-if="pageLoading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>
    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-else-if="lastReport">
      <p class="text-muted">Dernière vérification effectuée le: {{ new Date(lastReport.created_at).toLocaleString('fr-FR') }}</p>
      <!-- Cartes de Résumé -->
      <div class="row g-4 mb-4">
        <div class="col-md-4"><div class="card text-center shadow-sm" :class="globalStatus.borderClass">
            <div class="card-body p-4"><p class="h1" :class="globalStatus.textClass"><i :class="globalStatus.icon"></i></p><h5 class="card-title mt-2">{{ globalStatus.text }}</h5></div></div></div>
        <div class="col-md-4"><div class="card text-center shadow-sm"><div class="card-body p-4"><p class="h1">{{ lastReport.summary.total || 0 }}</p><h5 class="card-title">Tests Exécutés</h5></div></div></div>
        <div class="col-md-4"><div class="card text-center shadow-sm"><div class="card-body p-4"><p class="h1">{{ (lastReport.duration || 0).toFixed(2) }}s</p><h5 class="card-title">Durée d'Exécution</h5></div></div></div>
      </div>

      <!-- Tableau des résultats détaillés -->
      <div class="card shadow-sm">
        <div class="card-header"><h5 class="mb-0">Résultats Détaillés du Dernier Lancement</h5></div>
        <div class="list-group list-group-flush">
          <div v-for="test in lastReport.tests" :key="test.nodeid" class="list-group-item">
            <div class="d-flex w-100 justify-content-between">
              <h6 class="mb-1 fw-bold">{{ formatTestName(test.nodeid) }}</h6>
              <span class="badge" :class="test.outcome === 'passed' ? 'bg-success' : 'bg-danger'">{{ test.outcome.toUpperCase() }}</span>
            </div>
            <p class="mb-1 small text-muted">{{ getTestFile(test.nodeid) }}</p>
            <pre v-if="test.outcome === 'failed'" class="bg-light p-2 rounded small mt-2"><code>{{ test.longrepr.reprcrash.message }}</code></pre>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="alert alert-info">Aucun rapport de test n'a encore été généré. Cliquez sur "Relancer les Tests" pour effectuer la première vérification.</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import * as api from '@/services/api';

const authStore = useAuthStore();
const backendUrl = 'http://localhost:5000';

const pageLoading = ref(true);
const isLoading = ref(false); // Pour le bouton
const lastReport = ref(null);
const error = ref('');

const htmlReportUrl = computed(() => {
    // On s'assure que le token existe avant de construire l'URL
    if (authStore.token) {
        return `${backendUrl}/api/admin/system-status/html-report?jwt=${authStore.token}`;
    }
    // Si pas de token, le lien ne mènera nulle part (sécurité)
    return '#';
});

const fetchLatestReport = async () => {
    try {
        const response = await api.getLatestSystemStatus();
        lastReport.value = response.data;
    } catch (err) {
        if (err.response?.status === 404) {
            console.log("Aucun rapport précédent trouvé.");
        } else {
            error.value = "Impossible de charger le dernier statut du système.";
        }
    }
};

onMounted(async () => {
    await fetchLatestReport();
    pageLoading.value = false;
});

const runTests = async () => {
  isLoading.value = true;
  error.value = '';
  try {
    const response = await api.runSystemTests();
    lastReport.value = response.data;
  } catch (err) {
    error.value = "Une erreur est survenue lors de l'exécution des tests.";
  } finally {
    isLoading.value = false;
  }
};

const globalStatus = computed(() => {
    if (!lastReport.value?.summary) return { text: 'Inconnu', icon: 'bi bi-question-circle', textClass: 'text-muted', borderClass: ''};
    const failedCount = lastReport.value.summary.failed || 0;
    if (failedCount > 0) {
        return { text: 'ERREUR DÉTECTÉE', icon: 'bi bi-x-octagon-fill', textClass: 'text-danger', borderClass: 'border-danger'};
    }
    return { text: 'SYSTÈME OPÉRATIONNEL', icon: 'bi bi-check-circle-fill', textClass: 'text-success', borderClass: 'border-success'};
});

const formatTestName = (nodeid) => nodeid.split('::')[1]?.replace(/\[.*?\]/, '') || nodeid;
const getTestFile = (nodeid) => nodeid.split('::')[0];
</script>

<style scoped>
.kpi-icon { font-size: 2rem; }
</style>
