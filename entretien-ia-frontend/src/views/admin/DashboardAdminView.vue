<template>
  <div class="container-fluid admin-dashboard">
    <h1 class="display-5 fw-bold mb-4">Tableau de Bord Administrateur</h1>

    <div v-if="isLoading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>
    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-else-if="stats">
      <!-- Cartes KPI Globales -->
      <div class="row g-4 mb-5">
        <div class="col-md-6 col-xl-3"><div class="card kpi-card shadow-sm"><div class="card-body"><div class="kpi-icon bg-primary-subtle text-primary"><i class="bi bi-people-fill"></i></div><div><p class="h2 fw-bolder mb-0">{{ stats.kpis.total_users }}</p><div class="text-muted">Utilisateurs Inscrits</div></div></div></div></div>
        <div class="col-md-6 col-xl-3"><div class="card kpi-card shadow-sm"><div class="card-body"><div class="kpi-icon bg-info-subtle text-info"><i class="bi bi-briefcase-fill"></i></div><div><p class="h2 fw-bolder mb-0">{{ stats.kpis.total_recruiters }}</p><div class="text-muted">Comptes Recruteur</div></div></div></div></div>
        <div class="col-md-6 col-xl-3"><div class="card kpi-card shadow-sm"><div class="card-body"><div class="kpi-icon bg-success-subtle text-success"><i class="bi bi-camera-reels-fill"></i></div><div><p class="h2 fw-bolder mb-0">{{ stats.kpis.total_sessions }}</p><div class="text-muted">Entretiens Passés</div></div></div></div></div>
        <div class="col-md-6 col-xl-3"><div class="card kpi-card shadow-sm"><div class="card-body"><div class="kpi-icon bg-secondary-subtle text-secondary"><i class="bi bi-card-checklist"></i></div><div><p class="h2 fw-bolder mb-0">{{ stats.kpis.total_questions }}</p><div class="text-muted">Questions en BDD</div></div></div></div></div>
      </div>

      <!-- Graphiques Avancés -->
      <div class="row g-4 mb-5">
        <div class="col-lg-5">
          <div class="card shadow-sm h-100">
            <div class="card-body">
              <h5 class="card-title fw-bold">Répartition des Rôles</h5>
              <div style="height: 350px;"><Pie v-if="roleChartData.datasets[0].data.length" :data="roleChartData" :options="chartOptions.pie" /></div>
            </div>
          </div>
        </div>
        <div class="col-lg-7">
          <div class="card shadow-sm h-100">
            <div class="card-body">
              <h5 class="card-title fw-bold">Activité de la Plateforme (30 derniers jours)</h5>
              <div style="height: 350px;"><Bar v-if="activityChartData.datasets[0].data.length" :data="activityChartData" :options="chartOptions.bar" /></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Raccourcis et DataTable des Dernières Activités -->
      <div class="row g-4">
        <div class="col-lg-4">
            <h3 class="fw-bold mb-3">Panneau de Contrôle</h3>
            <div class="list-group shadow-sm">
                <router-link to="/admin/users" class="list-group-item list-group-item-action d-flex align-items-center"><i class="bi bi-people-fill fs-4 me-3"></i><div><span class="fw-bold">Gestion des Utilisateurs</span><br><small class="text-muted">Créer, modifier et gérer les comptes.</small></div></router-link>
                <router-link to="/admin/questions" class="list-group-item list-group-item-action d-flex align-items-center"><i class="bi bi-card-checklist fs-4 me-3"></i><div><span class="fw-bold">Supervision des Questions</span><br><small class="text-muted">Modérer la bibliothèque de questions.</small></div></router-link>
                <router-link to="/admin/export" class="list-group-item list-group-item-action d-flex align-items-center"><i class="bi bi-file-earmark-arrow-down-fill fs-4 me-3"></i><div><span class="fw-bold">Export des Données</span><br><small class="text-muted">Télécharger les résultats des entretiens.</small></div></router-link>
            </div>
        </div>
        <div class="col-lg-8">
            <h3 class="fw-bold mb-3">Flux des Dernières Sessions</h3>
            <div class="card shadow-sm">
                <div class="card-body">
                    <EasyDataTable
                        :headers="headers"
                        :items="stats.latest_sessions"
                        theme-color="#005f73"
                        table-class-name="custom-table"
                        :rows-per-page="5"
                        empty-message="Aucune session n'a encore été créée."
                        buttons-pagination
                    >
                        <template #item-date="{ date }">{{ new Date(date).toLocaleDateString('fr-FR') }}</template>
                        <template #item-statut="{ statut }"><span class="badge" :class="statusBadgeClass(statut)">{{ formatStatus(statut) }}</span></template>
                        <template #item-note_globale="{ note_globale }">
                          <span v-if="note_globale !== null" class="badge" :class="scoreBadge(note_globale, 100)">{{ note_globale.toFixed(0) }} / 100</span>
                          <span v-else class="text-muted small">En attente</span>
                        </template>
                        <template #item-actions="item">
                          <router-link v-if="['analysis_complete', 'validated'].includes(item.statut)" :to="`/report/${item.id}`" class="btn btn-sm btn-outline-primary">Voir Rapport</router-link>
                        </template>
                    </EasyDataTable>
                </div>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import * as api from '@/services/api';
import { Pie, Bar } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement } from 'chart.js';
import EasyDataTable from 'vue3-easy-data-table';
import 'vue3-easy-data-table/dist/style.css';

ChartJS.register(Title, Tooltip, Legend, ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement);

const stats = ref(null);
const isLoading = ref(true);
const error = ref('');

// --- Configuration DataTable ---
const headers = [
  { text: "Candidat", value: "candidat_nom", sortable: true },
  { text: "Poste", value: "poste_vise", sortable: true },
  { text: "Date", value: "date", sortable: true },
  { text: "Note", value: "note_globale", sortable: true },
  { text: "Statut", value: "statut" },
  { text: "Actions", value: "actions", align: 'end' },
];

onMounted(async () => {
  try {
    const response = await api.getAdminDashboardStats();
    stats.value = response.data;
  } catch (err) {
    error.value = "Impossible de charger les statistiques de l'administrateur.";
  } finally {
    isLoading.value = false;
  }
});

const roleChartData = computed(() => {
    const roles = stats.value?.charts.role_distribution || {};
    return {
        labels: Object.keys(roles).map(r => r.charAt(0).toUpperCase() + r.slice(1)),
        datasets: [{
            data: Object.values(roles),
            backgroundColor: ['#005f73', '#0a9396', '#94d2bd'],
        }]
    };
});

const activityChartData = computed(() => {
    const activity = stats.value?.charts.daily_activity || {};
    const labels = [];
    const sessionsData = [];
    const scoresData = [];
    for (let i = 29; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        const dateString = d.toISOString().split('T')[0];
        const formattedDate = d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
        labels.push(formattedDate);
        sessionsData.push(activity[dateString]?.count || 0);
        scoresData.push(activity[dateString]?.avg_score || 0);
    }
    return {
        labels,
        datasets: [
            {
                label: 'Entretiens Passés',
                data: sessionsData,
                backgroundColor: 'rgba(0, 95, 115, 0.5)',
                borderColor: 'rgba(0, 95, 115, 1)',
                yAxisID: 'y',
                order: 2 //
            },
            {
                label: 'Score Moyen',
                data: scoresData,
                borderColor: '#FFC107',
                backgroundColor: '#FFC107',
                type: 'line',
                yAxisID: 'y1',
                tension: 0.4,
                borderWidth: 3,
                pointBackgroundColor: '#FFFFFF',
                pointBorderColor: '#FFC107',
                pointHoverRadius: 7,
                order: 1
            }
        ]
    };
});

const chartOptions = {
    pie: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } },
    bar: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'top' } },
        scales: {
            y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'Nombre d\'Entretiens' } },
            y1: { type: 'linear', display: true, position: 'right', grid: { drawOnChartArea: false }, title: { display: true, text: 'Score Moyen (/100)' }, suggestedMin: 0, suggestedMax: 100 }
        }
    }
};

// --- Fonctions Utilitaires d'UI ---
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

</script>

<style scoped>
.kpi-card .card-body { display: flex; align-items: center; gap: 1.5rem; }
.kpi-icon { font-size: 2.5rem; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.kpi-card .h2 { font-size: 2.5rem; }
.list-group-item-action:hover { background-color: var(--bg-color); }
</style>
