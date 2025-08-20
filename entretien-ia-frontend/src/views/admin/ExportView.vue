<template>
  <div class="container-fluid export-page">
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
      <h1 class="display-5 fw-bold">Export des Données d'Entretiens</h1>
      <!-- Le bouton d'export est maintenant contextuel aux données affichées -->
      <button class="btn btn-success" @click="handleExport" :disabled="isExporting || data.length === 0">
        <span v-if="isExporting" class="spinner-border spinner-border-sm me-2"></span>
        <i v-else class="bi bi-file-earmark-spreadsheet-fill me-2"></i>
        Exporter {{ data.length }} Lignes (CSV)
      </button>
    </div>

    <!-- Panneau de filtres -->
    <div class="card shadow-sm mb-4">
      <div class="card-body">
        <div class="row g-3 align-items-end">
          <div class="col-md-3"><label class="form-label small">Date de début</label><input type="date" class="form-control" v-model="filters.start_date"></div>
          <div class="col-md-3"><label class="form-label small">Date de fin</label><input type="date" class="form-control" v-model="filters.end_date"></div>
          <div class="col-md-4"><label class="form-label small">Poste Visé (contient)</label><input type="text" class="form-control" v-model="filters.poste_vise" @keyup.enter="fetchData"></div>
          <div class="col-md-2 d-grid"><button class="btn btn-primary w-100" @click="fetchData" :disabled="isLoading"><i class="bi bi-funnel-fill me-2"></i>Filtrer</button></div>
        </div>
      </div>
    </div>

    <!-- NOUVEAU : Cartes KPI basées sur les données filtrées -->
    <div v-if="!isLoading && data.length > 0" class="row g-4 mb-4">
        <div class="col-md-4"><div class="card kpi-card shadow-sm"><div class="card-body"><i class="bi bi-collection-fill"></i><div><p class="h3 fw-bolder mb-0">{{ data.length }}</p><div class="text-muted">Résultats Filtrés</div></div></div></div></div>
        <div class="col-md-4"><div class="card kpi-card shadow-sm"><div class="card-body"><i class="bi bi-clipboard2-data-fill text-primary"></i><div><p class="h3 fw-bolder mb-0">{{ kpis.average_score.toFixed(1) }}<span class="fs-6">/100</span></p><div class="text-muted">Note Globale Moyenne</div></div></div></div></div>
        <div class="col-md-4"><div class="card kpi-card shadow-sm"><div class="card-body"><i class="bi bi-bullseye text-success"></i><div><p class="h3 fw-bolder mb-0">{{ (kpis.average_relevance * 100).toFixed(0) }}<span class="fs-6">%</span></p><div class="text-muted">Pertinence Moyenne</div></div></div></div></div>
    </div>

    <!-- DataTable d'aperçu des données -->
    <div class="card shadow-sm">
      <div class="card-header bg-light d-flex justify-content-between align-items-center flex-wrap">
        <h5 class="mb-0">Aperçu des Données</h5>
         <div class="col-12 col-md-4 mt-2 mt-md-0">
            <input type="text" class="form-control form-control-sm" v-model="searchValue" placeholder="Rechercher dans les résultats...">
        </div>
      </div>
      <div class="card-body">
        <EasyDataTable
          :headers="headers"
          :items="data"
          :search-field="['nom_candidat', 'poste_vise']"
          :search-value="searchValue"
          :loading="isLoading"
          :rows-per-page="10"
          theme-color="#005f73"
          table-class-name="custom-table"
          rows-per-page-message="Lignes par page"
          rows-of-page-separator-message="sur"
          empty-message="Aucun résultat ne correspond à vos filtres"
          buttons-pagination
          show-index
        >
          <template #item-date_entretien="{ date_entretien }">{{ new Date(date_entretien).toLocaleDateString('fr-FR') }}</template>
          <template #item-note_globale="{ note_globale }"><span class="badge" :class="scoreBadge(note_globale, 100)">{{ note_globale?.toFixed(0) || 'N/A' }}</span></template>
          <template #item-score_pertinence_moyen="{ score_pertinence_moyen }"><span class="badge" :class="scoreBadge(score_pertinence_moyen, 1)">{{ (score_pertinence_moyen * 100)?.toFixed(0) || 'N/A' }}</span></template>
          <template #item-score_grammaire="{ score_grammaire }"><span class="badge" :class="scoreBadge(score_grammaire, 1)">{{ (score_grammaire * 100)?.toFixed(0) || 'N/A' }}</span></template>
        </EasyDataTable>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import * as api from '@/services/api';
import Papa from 'papaparse';
import EasyDataTable from 'vue3-easy-data-table';
import 'vue3-easy-data-table/dist/style.css';

// --- États ---
const data = ref([]);
const isLoading = ref(true);
const isExporting = ref(false);
const filters = ref({ start_date: '', end_date: '', poste_vise: '' });
const searchValue = ref('');

// --- Configuration DataTable ---
const headers = [
  { text: "Candidat", value: "nom_candidat", sortable: true },
  { text: "Poste Visé", value: "poste_vise", sortable: true },
  { text: "Date", value: "date_entretien", sortable: true },
  { text: "Note Globale", value: "note_globale", sortable: true, align: 'center' },
  { text: "Pertinence", value: "score_pertinence_moyen", sortable: true, align: 'center' },
  { text: "Grammaire", value: "score_grammaire", sortable: true, align: 'center' },
];

// --- Cycle de vie ---
const fetchData = async () => {
  isLoading.value = true;
  try {
    const cleanFilters = Object.fromEntries(Object.entries(filters.value).filter(([_, v]) => v));
    const response = await api.getExportPreview(cleanFilters);
    data.value = response.data;
  } catch(e) { console.error("Erreur de chargement", e); }
  finally { isLoading.value = false; }
};
onMounted(fetchData);

// --- Propriétés Calculées pour les KPIs ---
const kpis = computed(() => {
    if (data.value.length === 0) {
        return { average_score: 0, average_relevance: 0 };
    }
    const validScores = data.value.filter(item => item.note_globale !== null);
    const avg_score = validScores.length > 0 ? validScores.reduce((sum, item) => sum + item.note_globale, 0) / validScores.length : 0;

    const validRelevance = data.value.filter(item => item.score_pertinence_moyen !== null);
    const avg_relevance = validRelevance.length > 0 ? validRelevance.reduce((sum, item) => sum + item.score_pertinence_moyen, 0) / validRelevance.length : 0;

    return { average_score: avg_score, average_relevance: avg_relevance };
});

// --- Méthodes ---
const handleExport = () => {
    isExporting.value = true;
    try {
        // La DataTable ne trie que l'affichage, pas les données sources.
        // On doit donc récupérer les items triés et cherchés depuis la table si on veut un export WYSIWYG.
        // Pour la simplicité, on exporte les données filtrées par le backend.
        // Une version avancée utiliserait les données triées/recherchées de la table.
        const dataToExport = data.value.map(item => ({
            "ID Session": item.session_id,
            "Candidat": item.nom_candidat,
            "Poste Visé": item.poste_vise,
            "Date": new Date(item.date_entretien).toISOString().split('T')[0],
            "Note Globale (/100)": item.note_globale?.toFixed(2),
            "Score Pertinence (/1)": item.score_pertinence_moyen?.toFixed(2),
            "Score Grammaire (/1)": item.score_grammaire?.toFixed(2)
        }));

        const csv = Papa.unparse(dataToExport);
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.setAttribute('download', 'export_entretiens.csv');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch(e) {
        console.error("Erreur d'export CSV", e);
        alert("Une erreur est survenue lors de la génération du fichier.");
    } finally {
        isExporting.value = false;
    }
};

const scoreBadge = (score, max) => {
    if (score === null || score === undefined) return 'bg-light text-dark';
    const normalizedScore = (score / max) * 100;
    if (normalizedScore >= 80) return 'bg-success';
    if (normalizedScore >= 60) return 'bg-warning text-dark';
    return 'bg-danger';
};
</script>

<style>
.custom-table {
  --easy-table-border: 1px solid var(--border-color);
  --easy-table-header-font-size: 14px;
  --easy-table-header-background-color: var(--bg-color);
  --easy-table-header-font-color: var(--text-dark);
}
</style>

<style scoped>
.kpi-card .card-body { display: flex; align-items: center; gap: 1.5rem; }
.kpi-card i { font-size: 2.5rem; }
.kpi-card .h3 { font-size: 2rem; }
</style>
