<template>
  <div class="container-fluid question-manager-page">
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
      <h1 class="display-5 fw-bold">Bibliothèque de Questions</h1>
      <!-- Le bouton est désactivé si on n'est pas sur l'onglet "Mes Questions" -->
      <button class="btn btn-primary" @click="openModalForCreate" :disabled="activeTab !== 'my-questions'">
        <i class="bi bi-plus-circle-fill me-2"></i>Nouvelle Question
      </button>
    </div>

    <!-- NOUVEAU : Système d'onglets de navigation -->
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <a class="nav-link" :class="{ active: activeTab === 'my-questions' }" href="#" @click.prevent="activeTab = 'my-questions'">
          Mes Questions Personnalisées
        </a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{ active: activeTab === 'all-questions' }" href="#" @click.prevent="activeTab = 'all-questions'">
          Bibliothèque Complète
        </a>
      </li>
    </ul>

    <!-- Contenu de l'onglet "Mes Questions" -->
    <div v-if="activeTab === 'my-questions'">
      <!-- Cartes KPI pour "Mes Questions" -->
      <div v-if="!isLoading.my" class="row g-4 mb-4">
        <div class="col-md-4"><div class="card kpi-card shadow-sm"><div class="card-body"><i class="bi bi-collection-fill"></i><div><p class="h3 fw-bolder mb-0">{{ myStats.total }}</p><div class="text-muted">Mes Questions Créées</div></div></div></div></div>
        <div class="col-md-4"><div class="card kpi-card shadow-sm"><div class="card-body"><i class="bi bi-tags-fill text-info"></i><div><p class="h3 fw-bolder mb-0">{{ myStats.categories }}</p><div class="text-muted">Catégories Uniques</div></div></div></div></div>
        <div class="col-md-4"><div class="card kpi-card shadow-sm"><div class="card-body"><i class="bi bi-flag-fill text-warning"></i><div><p class="h3 fw-bolder mb-0">{{ myStats.flagged }}</p><div class="text-muted">Questions Signalées</div></div></div></div></div>
      </div>

      <div class="card shadow-sm">
        <div class="card-header bg-light d-flex justify-content-between align-items-center flex-wrap">
          <h5 class="mb-0">Liste de vos questions</h5>
          <div class="col-12 col-md-4 mt-2 mt-md-0">
            <input type="text" class="form-control form-control-sm" v-model="mySearchValue" placeholder="Rechercher dans mes questions...">
          </div>
        </div>
        <div class="card-body">
          <EasyDataTable
            :headers="myQuestionsHeaders"
            :items="myQuestions"
            :search-value="mySearchValue"
            :loading="isLoading.my"
            empty-message="Vous n'avez pas encore créé de question."
            theme-color="#005f73" table-class-name="custom-table" buttons-pagination>
            <template #item-intitule="{ intitule, signalement_admin, commentaire_admin, ideal_answer }">
                <div class="d-flex align-items-center">
                <span v-if="signalement_admin" class="me-2" :title="`Signalée: ${commentaire_admin || 'Aucun commentaire'}`"><i class="bi bi-exclamation-triangle-fill text-warning"></i></span>
                <span>{{ intitule }}</span>
                <i v-if="ideal_answer" class="bi bi-info-circle-fill text-muted ms-2 small" :title="`Réponse idéale: ${ideal_answer}`"></i>
                </div>
            </template>
            <template #item-category="{ category }"><span class="badge bg-secondary">{{ category }}</span></template>
            <template #item-role_target="{ role_target }">{{ role_target || '-' }}</template>
            <template #item-difficulty="{ difficulty }"><span v-if="difficulty" class="badge" :class="difficultyBadge(difficulty)">{{ difficulty }}</span><span v-else>-</span></template>
            <template #item-actions="question">
                <div class="d-inline-flex gap-2">
                <button class="btn btn-sm btn-outline-secondary" @click="openModalForEdit(question)" :disabled="question.signalement_admin" title="Modifier"><i class="bi bi-pencil-fill"></i></button>
                <button class="btn btn-sm btn-outline-danger" @click="handleDelete(question)" title="Supprimer"><i class="bi bi-trash-fill"></i></button>
                </div>
            </template>
          </EasyDataTable>
        </div>
      </div>
    </div>

    <!-- Contenu de l'onglet "Toutes les Questions" -->
    <div v-if="activeTab === 'all-questions'">
       <div class="card shadow-sm">
        <div class="card-header bg-light d-flex justify-content-between align-items-center">
            <h5 class="mb-0">Bibliothèque complète de l'entreprise</h5>
            <input type="text" class="form-control form-control-sm w-25" v-model="allSearchValue" placeholder="Rechercher...">
        </div>
        <div class="card-body">
            <EasyDataTable
              :headers="allQuestionsHeaders"
              :items="allQuestions"
              :search-field="['intitule', 'category', 'auteur', 'role_target']"
              :search-value="allSearchValue"
              :loading="isLoading.all"
              empty-message="Aucune question trouvée dans la bibliothèque."
              theme-color="#005f73" table-class-name="custom-table" buttons-pagination>
               <template #item-intitule="{ intitule, signalement_admin }">
                <span v-if="signalement_admin" class="me-2 text-warning" title="Signalée par un admin"><i class="bi bi-flag-fill"></i></span>
                {{ intitule }}
              </template>
              <template #item-difficulty="{ difficulty }">
                <span v-if="difficulty" class="badge" :class="difficultyBadge(difficulty)">{{ difficulty }}</span>
              </template>
              <template #item-source_type="{ source_type }">
                <span v-if="source_type" class="badge bg-info text-dark">{{ source_type }}</span>
              </template>
              <template #item-experience_level="{ experience_level }">
                <span v-if="experience_level" class="badge bg-light text-dark">{{ experience_level }}</span>
              </template>
            </EasyDataTable>
        </div>
      </div>
    </div>

    <QuestionModal :question="selectedQuestion" @questionSaved="handleSave" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import * as api from '@/services/api';
import QuestionModal from '@/components/QuestionModal.vue';
import { Modal } from 'bootstrap';
import EasyDataTable from 'vue3-easy-data-table';
import 'vue3-easy-data-table/dist/style.css';

// --- États ---
const activeTab = ref('my-questions');
const myQuestions = ref([]);
const allQuestions = ref([]);
const isLoading = ref({ my: true, all: true });
const error = ref('');
const selectedQuestion = ref(null);
const mySearchValue = ref('');
const allSearchValue = ref('');

// --- Configuration des colonnes pour chaque table ---
const myQuestionsHeaders = [
  { text: "Intitulé", value: "intitule", sortable: true, width: 40 },
  { text: "Catégorie", value: "category", sortable: true },
  { text: "Poste Ciblé", value: "role_target", sortable: true },
  { text: "Difficulté", value: "difficulty", sortable: true, width: 120 },
  { text: "Actions", value: "actions", align: 'end', width: 120 },
];
const allQuestionsHeaders = [
  { text: "Intitulé", value: "intitule", sortable: true, width: 40 },
  { text: "Auteur", value: "auteur", sortable: true },
  { text: "Catégorie", value: "category", sortable: true },
  { text: "Poste Ciblé", value: "role_target", sortable: true },
  { text: "Difficulté", value: "difficulty", sortable: true, align: 'center' },
  { text: "Type", value: "source_type", sortable: true, align: 'center' },
  { text: "Expérience", value: "experience_level", sortable: true, align: 'center' },
];

// --- Fonctions de chargement des données ---
const fetchMyQuestions = async () => {
    isLoading.value.my = true;
    try {
        const response = await api.getRecruiterQuestions();
        myQuestions.value = response.data;
    } catch (err) { error.value = "Erreur de chargement de vos questions."; }
    finally { isLoading.value.my = false; }
};
const fetchAllQuestions = async () => {
    isLoading.value.all = true;
    try {
        const response = await api.getAllInspirationQuestions();
        allQuestions.value = response.data;
    } catch (err) { error.value = "Erreur de chargement de la bibliothèque."; }
    finally { isLoading.value.all = false; }
};

onMounted(() => {
    fetchMyQuestions();
    fetchAllQuestions();
});

// --- Propriétés Calculées pour les KPIs ---
const myStats = computed(() => {
    const total = myQuestions.value.length;
    const flagged = myQuestions.value.filter(q => q.signalement_admin).length;
    const categories = new Set(myQuestions.value.map(q => q.category)).size;
    return { total, flagged, categories };
});

// --- Logique de la modale et du CRUD ---
const openModalForCreate = () => {
    selectedQuestion.value = null;
    Modal.getOrCreateInstance(document.getElementById('questionModal')).show();
};
const openModalForEdit = (question) => {
    selectedQuestion.value = { ...question };
    Modal.getOrCreateInstance(document.getElementById('questionModal')).show();
};
const handleSave = async (questionData) => {
    try {
        if (questionData.id) {
            await api.updateQuestion(questionData.id, questionData);
        } else {
            await api.createQuestion(questionData);
        }
        await fetchMyQuestions();
        await fetchAllQuestions();
    } catch (err) { console.error("Erreur de sauvegarde:", err); alert("Une erreur est survenue."); }
};
const handleDelete = async (question) => {
    if (confirm(`Êtes-vous sûr de vouloir supprimer la question : "${question.intitule}" ?`)) {
        try {
            await api.deleteQuestion(question.id);
            await fetchMyQuestions();
            await fetchAllQuestions();
        } catch (err) { console.error("Erreur de suppression:", err); alert("Une erreur est survenue."); }
    }
};

// --- Fonctions Utilitaires ---
const difficultyBadge = (difficulty) => {
    switch (difficulty) {
        case 'Facile': return 'bg-success';
        case 'Moyen': return 'bg-warning text-dark';
        case 'Difficile': return 'bg-danger';
        default: return 'bg-secondary';
    }
};
</script>

<style>
/* Style global pour surcharger la DataTable (non-scoped) */
.custom-table {
  --easy-table-border: 1px solid var(--border-color);
  --easy-table-header-font-size: 14px;
  --easy-table-header-background-color: var(--bg-color);
  --easy-table-header-font-color: var(--text-dark);
  --easy-table-body-row-hover-background-color: #e9ecef;
  /* Police pour le corps du tableau (les lignes de données) */
  --easy-table-body-row-font-size: 14px; /* Augmente la taille par défaut (12px) */

  /* Police pour l'en-tête du tableau */
  --easy-table-header-font-size: 15px; /* Rend l'en-tête légèrement plus grand */
  --easy-table-header-font-color: var(--text-dark);
}
</style>

<style scoped>
/* Styles spécifiques à ce composant (scoped) */
.kpi-card .card-body {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}
.kpi-card i {
  font-size: 2.5rem;
}
.kpi-card .h3 {
  font-size: 2rem;
}
.nav-link {
  cursor: pointer;
}
/* On s'assure que le surlignage des questions signalées fonctionne bien avec la DataTable */
.table-warning {
    --easy-table-body-row-background-color: var(--bs-warning-bg-subtle);
    --easy-table-body-row-hover-background-color: var(--bs-warning-bg-subtle);
}
</style>
