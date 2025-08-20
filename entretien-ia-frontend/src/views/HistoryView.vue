<template>
  <div class="container-fluid history-page">
    <h1 class="display-5 fw-bold mb-4">Mon Historique d'Entretiens</h1>

    <div v-if="!isLoading && sessions.length > 0" class="row g-4 mb-4">
        <div class="col-md-6"><div class="card kpi-card shadow-sm"><div class="card-body"><i class="bi bi-collection-fill"></i><div><p class="h3 fw-bolder mb-0">{{ sessions.length }}</p><div class="text-muted">Entretiens Passés</div></div></div></div></div>
        <div class="col-md-6"><div class="card kpi-card shadow-sm"><div class="card-body"><i class="bi bi-clipboard2-data-fill text-primary"></i><div><p class="h3 fw-bolder mb-0">{{ averageScore }}<span class="fs-6">/100</span></p><div class="text-muted">Score Global Moyen</div></div></div></div></div>
    </div>

    <div v-if="isLoading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>
    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-else-if="sessions.length === 0" class="text-center p-5 bg-light rounded">
        <h4>Votre historique est vide.</h4>
        <p class="text-muted">Les entretiens que vous aurez terminés apparaîtront ici.</p>
        <router-link to="/candidate/dashboard" class="btn btn-primary">Retour au tableau de bord</router-link>
    </div>

    <div v-else class="card shadow-sm">
      <div class="card-header bg-light d-flex justify-content-between align-items-center flex-wrap">
        <h5 class="mb-0">Détail de vos entretiens</h5>
        <div class="col-12 col-md-4 mt-2 mt-md-0">
          <input type="text" class="form-control form-control-sm" v-model="searchValue" placeholder="Rechercher par poste...">
        </div>
      </div>
      <div class="card-body">
        <EasyDataTable
          :headers="headers"
          :items="sessions"
          :search-field="['poste_vise']"
          :search-value="searchValue"
          :loading="isLoading"
          :rows-per-page="5"
          theme-color="#005f73"
          table-class-name="custom-table"
          rows-per-page-message="Lignes par page"
          rows-of-page-separator-message="sur"
          empty-message="Aucun entretien ne correspond à votre recherche"
          buttons-pagination
          show-index
        >
          <!-- Templates pour customiser les colonnes -->
          <template #item-date_entretien="{ date_entretien }">{{ new Date(date_entretien).toLocaleDateString('fr-FR') }}</template>
          <template #item-statut="{ statut }">
            <span class="badge" :class="statusBadgeClass(statut)">
              <i v-if="statut === 'analyzing'" class="spinner-border spinner-border-sm me-1" style="width: 0.8rem; height: 0.8rem;"></i>
              {{ formatStatus(statut) }}
            </span>
          </template>
          <template #item-actions="item">
            <div class="d-flex justify-content-end">
              <router-link
                v-if="['analysis_complete', 'validated'].includes(item.statut)"
                :to="{ name: 'feedback', params: { id: item.id } }"
                class="btn btn-sm btn-primary"
              >
                <i class="bi bi-eye-fill"></i> Voir mon Bilan
              </router-link>
              <span v-else class="text-muted fst-italic small">Bilan bientôt disponible</span>
            </div>
          </template>
        </EasyDataTable>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import * as api from '@/services/api';
import EasyDataTable from 'vue3-easy-data-table';
import 'vue3-easy-data-table/dist/style.css';

const sessions = ref([]);
const isLoading = ref(true);
const error = ref('');
const searchValue = ref('');

const headers = [
  { text: "Poste Visé", value: "poste_vise", sortable: true },
  { text: "Date de l'entretien", value: "date_entretien", sortable: true },
  { text: "Statut de l'analyse", value: "statut", align: 'center' },
  { text: "Actions", value: "actions", align: 'end' },
];

onMounted(async () => {
  try {
    const response = await api.getSessionHistory();
    sessions.value = response.data;
  } catch (err) {
    error.value = "Erreur lors de la récupération de l'historique.";
    console.error(err);
  } finally {
    isLoading.value = false;
  }
});

const averageScore = computed(() => {
    const validScores = sessions.value.filter(s => s.global_score !== null && s.global_score !== undefined);
    if(validScores.length === 0) return 'N/A';
    const total = validScores.reduce((sum, s) => sum + s.global_score, 0);
    return (total / validScores.length).toFixed(0);
});

const formatStatus = (status) => {
    const statusMap = {
        'file_uploaded': 'Prêt pour analyse',
        'analyzing': 'Analyse en cours',
        'analysis_complete': 'Bilan disponible',
        'validated': 'Bilan disponible',
        'analysis_failed': 'Échec de l\'analyse'
    };
    return statusMap[status] || status;
};

const statusBadgeClass = (status) => {
    const classMap = {
        'analysis_complete': 'bg-success',
        'validated': 'bg-success',
        'analyzing': 'bg-info text-dark',
        'analysis_failed': 'bg-danger',
    };
    return classMap[status] || 'bg-secondary';
};
</script>

<style>
.custom-table {
  --easy-table-border: 1px solid var(--border-color);
  --easy-table-header-font-size: 14px;
  --easy-table-header-background-color: var(--bg-color);
  
}
</style>

<style scoped>
.kpi-card .card-body { display: flex; align-items: center; gap: 1.5rem; }
.kpi-card i { font-size: 2.5rem; }
.kpi-card .h3 { font-size: 2rem; }
</style>
