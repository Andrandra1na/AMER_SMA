<template>
  <div class="container-fluid all-questions-page">
    <h1 class="display-5 fw-bold mb-4">Supervision de la Bibliothèque de Questions</h1>

    <div v-if="!isLoading" class="row g-4 mb-4">
      <div class="col-md-4"><div class="card kpi-card shadow-sm"><div class="card-body"><i class="bi bi-collection-fill"></i><div><p class="h3 fw-bolder mb-0">{{ stats.total }}</p><div class="text-muted">Questions Totales</div></div></div></div></div>
      <div class="col-md-4"><div class="card kpi-card shadow-sm"><div class="card-body"><i class="bi bi-person-workspace text-info"></i><div><p class="h3 fw-bolder mb-0">{{ stats.recruiter_created }}</p><div class="text-muted">Créées par les Recruteurs</div></div></div></div></div>
      <div class="col-md-4"><div class="card kpi-card shadow-sm"><div class="card-body"><i class="bi bi-flag-fill text-danger"></i><div><p class="h3 fw-bolder mb-0">{{ stats.flagged }}</p><div class="text-muted">Questions Signalées</div></div></div></div></div>
    </div>

    <div class="card shadow-sm">
      <div class="card-header bg-light d-flex justify-content-between align-items-center flex-wrap gap-2">
        <h5 class="mb-0">Liste Complète des Questions</h5>
        <input type="text" class="form-control form-control-sm w-25" v-model="searchValue" placeholder="Rechercher...">
      </div>
      <div class="card-body">
        <EasyDataTable
          :headers="headers"
          :items="questions"
          :search-field="['intitule', 'auteur', 'category']"
          :search-value="searchValue"
          :loading="isLoading"
          :rows-per-page="10"
          theme-color="#005f73"
          table-class-name="custom-table"
          buttons-pagination show-index>

          <template #item-intitule="{ intitule, signalement_admin }">
            <span v-if="signalement_admin" class="me-2 text-danger" title="Question signalée"><i class="bi bi-flag-fill"></i></span>
            {{ intitule }}
          </template>
          <template #item-auteur="{ auteur }">
            <span class="badge" :class="auteur === 'Par Défaut' ? 'bg-primary' : 'bg-secondary'">{{ auteur }}</span>
          </template>

          <template #item-actions="question">
            <div class="d-inline-flex gap-2">

              <!-- Actions pour les questions PAR DÉFAUT -->
              <!-- On se base sur recruteur_id qui est soit un nombre, soit null. -->
              <template v-if="question.recruteur_id === null">
                <button class="btn btn-sm btn-outline-secondary" @click="openModalForEditDefault(question)" title="Modifier la question par défaut"><i class="bi bi-pencil-fill"></i></button>
                <button class="btn btn-sm btn-outline-danger" @click="handleDeleteDefault(question)" title="Supprimer la question par défaut"><i class="bi bi-trash-fill"></i></button>
              </template>

              <!-- Action pour les questions de RECRUTEURS -->
              <button class="btn btn-sm btn-outline-warning" @click="openSignalModal(question)" title="Gérer le signalement">
                <i class="bi bi-flag-fill"></i> Gérer
              </button>
            </div>
          </template>
          <!-- === FIN DE LA CORRECTION === -->
        </EasyDataTable>
      </div>
    </div>

    <QuestionModal v-if="isModalActive.question" :question="selectedQuestion" @questionSaved="handleSaveDefault" />
    <SignalModal v-if="isModalActive.signal" :question="selectedQuestion" @signalSaved="handleSignal" />
  </div>
</template>


<script setup>
import { ref, onMounted, computed, reactive } from 'vue';
import * as api from '@/services/api';
import QuestionModal from '@/components/QuestionModal.vue';
import SignalModal from '@/components/SignalModal.vue';
import { Modal } from 'bootstrap';
import EasyDataTable from 'vue3-easy-data-table';
import 'vue3-easy-data-table/dist/style.css';

// --- États ---
const questions = ref([]);
const isLoading = ref(true);
const error = ref('');
const selectedQuestion = ref(null);
const searchValue = ref('');
const isModalActive = reactive({ question: false, signal: false });

// --- Configuration DataTable ---
const headers = [
  { text: "Intitulé", value: "intitule", sortable: true, width: 35 },
  { text: "Auteur", value: "auteur", sortable: true },
  { text: "Catégorie", value: "category", sortable: true },
  { text: "Phase", value: "phase", sortable: true },
  { text: "Poste Ciblé", value: "role_target", sortable: true },
  { text: "Difficulté", value: "difficulty", sortable: true, align: 'center' },
  { text: "Actions", value: "actions", align: 'end', width: 150 },
];

// --- Cycle de vie et KPIs ---
const fetchAllQuestions = async () => {
  isLoading.value = true;
  try {
    const response = await api.getAllQuestions();
    questions.value = response.data;
  } catch (err) {
    error.value = "Erreur de chargement.";
  } finally {
    isLoading.value = false;
  }
};
onMounted(fetchAllQuestions);

const stats = computed(() => {
  const total = questions.value.length;
  const flagged = questions.value.filter(q => q.signalement_admin).length;
  const recruiter_created = questions.value.filter(q => q.recruteur_id !== null).length;
  return { total, flagged, recruiter_created };
});

// --- Logique des Modales et du CRUD ---
const openModalForCreateDefault = () => {
    selectedQuestion.value = null;
    isModalActive.question = true;
    setTimeout(() => Modal.getOrCreateInstance('#questionModal').show(), 0);
};

const openModalForEditDefault = (question) => {
    selectedQuestion.value = { ...question };
    isModalActive.question = true;
    setTimeout(() => Modal.getOrCreateInstance('#questionModal').show(), 0);
};

const openSignalModal = (question) => {
    selectedQuestion.value = { ...question };
    isModalActive.signal = true;
    setTimeout(() => Modal.getOrCreateInstance('#signalModal').show(), 0);
};

const handleSaveDefault = async (questionData) => {
    try {
        if (questionData.id) {
            await api.updateDefaultQuestion(questionData.id, questionData);
        } else {
            await api.createDefaultQuestion(questionData);
        }
        await fetchAllQuestions();
    } catch (err) { alert("Une erreur est survenue."); }
    finally { isModalActive.question = false; }
};

const handleDeleteDefault = async (question) => {
    if (confirm(`Supprimer la question par défaut : "${question.intitule}" ?`)) {
        try {
            await api.deleteDefaultQuestion(question.id);
            await fetchAllQuestions();
        } catch (err) { alert("Une erreur est survenue."); }
    }
};

const handleSignal = async (signalData) => {
    try {
        await api.signalQuestion(signalData.questionId, signalData);
        await fetchAllQuestions();
    } catch (err) { alert("Une erreur est survenue."); }
    finally { isModalActive.signal = false; }
};
</script>

<style>
.custom-table {
  --easy-table-border: 1px solid var(--border-color);
  --easy-table-header-font-size: 14px;
  --easy-table-header-background-color: var(--bg-color);
  --easy-table-header-font-color: var(--text-dark);
  --easy-table-body-row-hover-background-color: #e9ecef;
}
</style>

<style scoped>
.kpi-card .card-body { display: flex; align-items: center; gap: 1.5rem; }
.kpi-card i { font-size: 2.5rem; }
.kpi-card .h3 { font-size: 2rem; }
.table-danger {
    --bs-table-bg: var(--bs-danger-bg-subtle);
    --bs-table-border-color: var(--bs-danger-border-subtle);
    --bs-table-hover-bg: var(--bs-danger-bg-subtle);
}
</style>
