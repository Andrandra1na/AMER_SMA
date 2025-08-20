<template>
  <div class="container-fluid recruiter-dashboard">
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
      <div>
        <h1 class="display-5 fw-bold mb-0">Tableau de Bord</h1>
        <p class="text-muted">Suivez l'avancement de vos campagnes de recrutement.</p>
      </div>
      <router-link to="/recruiter/create-session" class="btn btn-primary"><i class="bi bi-plus-circle-fill me-2"></i>Nouvel Entretien</router-link>
    </div>

    <div v-if="isLoading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>
    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-else>
      <!-- Cartes KPI -->
      <div class="row g-4 mb-5">
        <div class="col-md-6 col-xl-3"><div class="card kpi-card shadow-sm"><div class="card-body"><div class="kpi-icon bg-primary-subtle text-primary"><i class="bi bi-collection-fill"></i></div><div><p class="h2 fw-bolder mb-0">{{ kpis.total }}</p><div class="text-muted">Entretiens Créés</div></div></div></div></div>
        <div class="col-md-6 col-xl-3"><div class="card kpi-card shadow-sm"><div class="card-body"><div class="kpi-icon bg-warning-subtle text-warning"><i class="bi bi-hourglass-split"></i></div><div><p class="h2 fw-bolder mb-0">{{ kpis.pending }}</p><div class="text-muted">En Attente Candidat</div></div></div></div></div>
        <div class="col-md-6 col-xl-3"><div class="card kpi-card shadow-sm"><div class="card-body"><div class="kpi-icon bg-info-subtle text-info"><i class="bi bi-robot"></i></div><div><p class="h2 fw-bolder mb-0">{{ kpis.analyzing }}</p><div class="text-muted">Analyses en Cours</div></div></div></div></div>
        <div class="col-md-6 col-xl-3"><div class="card kpi-card shadow-sm"><div class="card-body"><div class="kpi-icon bg-success-subtle text-success"><i class="bi bi-eye-fill"></i></div><div><p class="h2 fw-bolder mb-0">{{ kpis.review_needed }}</p><div class="text-muted">Rapports à Examiner</div></div></div></div></div>
      </div>

      <!-- DataTable Détaillé -->
      <div class="card shadow-sm">
        <div class="card-header d-flex justify-content-between align-items-center flex-wrap gap-2">
          <h5 class="mb-0">Détail des Sessions</h5>
          <div class="col-12 col-md-4">
            <input type="text" class="form-control form-control-sm" v-model="searchValue" placeholder="Rechercher un candidat ou un poste...">
          </div>
        </div>
        <div class="card-body">
          <EasyDataTable
            :headers="headers"
            :items="sessions"
            :search-field="['candidat.nom', 'poste_vise']"
            :search-value="searchValue"
            theme-color="#005f73"
            table-class-name="custom-table"
            rows-per-page-message="Lignes par page"
            rows-of-page-separator-message="sur"
            empty-message="Aucun entretien ne correspond à votre recherche"
            buttons-pagination
          >
            <!-- Templates pour customiser l'affichage des cellules -->
            <template #item-candidat="{ candidat }">
              <div>{{ candidat.nom }}</div>
              <small class="text-muted">{{ candidat.email }}</small>
            </template>
            <template #item-date_creation="{ date_creation }">{{ new Date(date_creation).toLocaleDateString('fr-FR') }}</template>
            <template #item-statut="{ statut }">
              <span class="badge" :class="statusBadgeClass(statut)">
                <i v-if="statut === 'analyzing'" class="spinner-border spinner-border-sm me-1" style="width: 0.8rem; height: 0.8rem;"></i>
                {{ formatStatus(statut) }}
              </span>
            </template>
            <template #item-actions="item">
              <div class="d-inline-flex gap-2">
                <button v-if="item.statut === 'file_uploaded'" @click="handleStartAnalysis(item)" class="btn btn-sm btn-info text-white" title="Lancer l'analyse IA"><i class="bi bi-robot"></i></button>
                <router-link v-if="item.statut !== 'pending'" :to="{ name: 'player', params: { id: item.id } }" class="btn btn-sm btn-outline-secondary" title="Revoir la vidéo"><i class="bi bi-play-btn-fill"></i></router-link>
                <router-link v-if="['analysis_complete', 'validated'].includes(item.statut)" :to="`/report/${item.id}`" class="btn btn-sm btn-outline-success" title="Voir le rapport"><i class="bi bi-file-earmark-text-fill"></i></router-link>
                <button v-if="item.statut === 'pending'" @click="handleDeleteSession(item)" class="btn btn-sm btn-outline-danger" title="Supprimer la session"><i class="bi bi-trash-fill"></i></button>
              </div>
            </template>
          </EasyDataTable>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import * as api from '@/services/api';
import EasyDataTable from 'vue3-easy-data-table';
import 'vue3-easy-data-table/dist/style.css';

// --- États ---
const sessions = ref([]);
const kpis = ref({ total: 0, pending: 0, analyzing: 0, review_needed: 0 });
const isLoading = ref(true);
const error = ref('');
const searchValue = ref('');

let pollingInterval = null;

// --- Configuration DataTable ---
const headers = [
  { text: "Candidat", value: "candidat.nom", sortable: true }, // On peut trier par nom de candidat
  { text: "Poste Visé", value: "poste_vise", sortable: true },
  { text: "Date Création", value: "date_creation", sortable: true },
  { text: "Statut", value: "statut", align: 'center' },
  { text: "Actions", value: "actions", align: 'end' },
];

// --- Cycle de vie ---
const fetchDashboardData = async (isPolling = false) => {
  if (!isPolling) isLoading.value = true;
  try {
    const response = await api.getRecruiterDashboardData();
    sessions.value = response.data.sessions;
    kpis.value = response.data.kpis;

    // --- DÉBUT DE LA LOGIQUE DE POLLING ---
    const isAnySessionAnalyzing = sessions.value.some(s => s.statut === 'analyzing');

    if (isAnySessionAnalyzing && !pollingInterval) {
      // S'il y a une analyse en cours et que le polling n'est pas déjà actif, on le démarre.
      startPolling();
    } else if (!isAnySessionAnalyzing && pollingInterval) {
      // S'il n'y a plus d'analyse en cours, on arrête le polling.
      stopPolling();
    }
    // --- FIN DE LA LOGIQUE DE POLLING ---

  } catch (err) {
    error.value = "Erreur lors du chargement de votre tableau de bord.";
    console.error(err);
    stopPolling(); // On arrête aussi en cas d'erreur
  } finally {
    if (!isPolling) isLoading.value = false;
  }
};

onMounted(fetchDashboardData);

const startPolling = () => {
    console.log("Démarrage du polling pour vérifier les statuts d'analyse...");
    // On vérifie le statut toutes les 5 secondes (5000 millisecondes)
    pollingInterval = setInterval(() => {
        console.log("Polling... Vérification des statuts.");
        fetchDashboardData(true); // 'true' pour ne pas montrer le loader à chaque fois
    }, 5000);
};

const stopPolling = () => {
    if (pollingInterval) {
        console.log("Arrêt du polling.");
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
};

// --- Méthodes d'Action ---
const handleStartAnalysis = async (session) => {
  if (!confirm(`Lancer l'analyse pour ${session.candidat.nom} ?`)) return;

  session.statut = 'analyzing'; // Mise à jour optimiste

  try {
    await api.startAnalysis(session.id);
    // Après avoir lancé l'analyse, on démarre le polling
    startPolling();
  } catch (err) {
    alert("Erreur lors du lancement de l'analyse.");
    session.statut = 'file_uploaded';
  }
};

const handleDeleteSession = async (session) => {
  if (!confirm(`Supprimer la session pour ${session.candidat.nom} ?`)) return;
  try {
    await api.deleteSession(session.id);
    // On retire l'élément de la liste pour une mise à jour immédiate
    sessions.value = sessions.value.filter(s => s.id !== session.id);
  } catch (err) {
    alert("Erreur lors de la suppression.");
  }
};

// --- Fonctions Utilitaires d'UI ---
const formatStatus = (status) => {
  const statusMap = {
    'pending': 'En attente',
    'file_uploaded': 'Prêt pour analyse',
    'analyzing': 'Analyse en cours',
    'analysis_complete': 'Rapport prêt',
    'analysis_failed': 'Échec analyse',
    'validated': 'Validé'
  };
  return statusMap[status] || status;
};

const statusBadgeClass = (status) => {
  const classMap = {
    'pending': 'bg-warning text-dark',
    'file_uploaded': 'bg-info text-dark',
    'analyzing': 'bg-primary',
    'analysis_complete': 'bg-success',
    'analysis_failed': 'bg-danger',
    'validated': 'bg-dark'
  };
  return classMap[status] || 'bg-secondary';
};
</script>

<style>
/* Style global pour surcharger la DataTable */
.custom-table {
  --easy-table-border: 1px solid var(--border-color);
  --easy-table-header-background-color: var(--bg-color);
  --easy-table-header-font-color: var(--text-dark);
  --easy-table-body-row-hover-background-color: #e9ecef;
    /* Police pour le corps du tableau (les lignes de données) */
  --easy-table-body-row-font-size: 14px; /* Augmente la taille par défaut (12px) */
  --easy-table-header-font-size: 15px; /* Rend l'en-tête légèrement plus grand */
  --easy-table-header-font-color: var(--text-dark);
}
</style>

<style scoped>
/* Styles spécifiques au dashboard */
.kpi-card .card-body { display: flex; align-items: center; gap: 1rem; }
.kpi-icon { font-size: 2rem; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.kpi-card .h2 { font-size: 2.5rem; }
</style>
