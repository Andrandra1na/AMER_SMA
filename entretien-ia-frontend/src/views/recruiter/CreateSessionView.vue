<template>
  <div class="container" style="max-width: 800px;">
    <div class="text-center mb-5">
      <h1 class="display-5 fw-bold">Créer un Nouvel Entretien</h1>
      <p class="text-muted">Configurez une session d'entretien en 3 étapes simples.</p>
    </div>

    <div class="card p-4 shadow-sm">
      <div v-if="isLoadingInitialData" class="text-center py-5">
        <div class="spinner-border text-primary"></div>
        <p class="mt-2">Chargement des données de configuration...</p>
      </div>
      <form v-else @submit.prevent="handleCreateSession">

        <!-- === ÉTAPE 1 : INFORMATIONS GÉNÉRALES === -->
        <h5 class="mb-3 fw-bold"><span class="step-circle">1</span> Informations Générales</h5>
        <div class="row g-3">
          <div class="col-md-6">
            <label for="candidate" class="form-label">Candidat<span class="text-danger">*</span></label>
            <select id="candidate" class="form-select" v-model="form.candidate_id" required>
              <option disabled :value="null">Sélectionnez un candidat</option>
              <option v-for="c in candidates" :key="c.id" :value="c.id">{{ c.nom }} ({{ c.email }})</option>
            </select>
          </div>
          <div class="col-md-6">
            <label for="poste" class="form-label">Poste Visé<span class="text-danger">*</span></label>
            <input type="text" id="poste" class="form-control" v-model="form.poste_vise" placeholder="Ex: Développeur Fullstack" required>
          </div>
        </div>
        <hr class="my-4">

        <!-- === ÉTAPE 2 : SÉLECTION DES COMPÉTENCES === -->
        <h5 class="mb-3 fw-bold"><span class="step-circle">2</span> Compétences à Évaluer<span class="text-danger">*</span></h5>
        <p class="text-muted small">Sélectionnez entre 2 et 4 compétences clés. Le système choisira automatiquement les questions les plus pertinentes pour chaque compétence.</p>
        <div class="competencies-grid">
          <div v-for="comp in availableCompetencies" :key="comp" class="form-check">
            <input class="form-check-input" type="checkbox" :id="'comp-' + comp" :value="comp" v-model="form.competences" :disabled="form.competences.length >= 4 && !form.competences.includes(comp)">
            <label class="form-check-label" :for="'comp-' + comp">{{ comp }}</label>
          </div>
        </div>
        <hr class="my-4">

        <!-- === ÉTAPE 3 : PROFIL DE NOTATION IA === -->
        <h5 class="mb-3 fw-bold"><span class="step-circle">3</span> Profil de Notation IA<span class="text-danger">*</span></h5>
        <label for="profile" class="form-label">Comment l'IA doit-elle pondérer les résultats ?</label>
        <select id="profile" class="form-select" v-model="form.profil_ponderation_id" required>
          <option disabled :value="null">Choisissez un profil de notation...</option>
          <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.nom_profil }}</option>
        </select>

        <!-- Messages et Bouton de soumission -->
        <div v-if="successMsg" class="alert alert-success mt-4">{{ successMsg }}</div>
        <div v-if="errorMsg" class="alert alert-danger mt-4">{{ errorMsg }}</div>

        <div class="d-flex justify-content-end align-items-center mt-4">
          <small v-if="!isFormValid" class="text-danger me-3">Veuillez remplir tous les champs et sélectionner 2 à 4 compétences.</small>
          <button type="submit" class="btn btn-primary btn-lg" :disabled="isSubmitting || !isFormValid">
            <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2"></span>
            {{ isSubmitting ? 'Création...' : 'Lancer l\'Entretien' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import * as api from '@/services/api';

const router = useRouter();
const candidates = ref([]);
const profiles = ref([]);
const errorMsg = ref('');
const successMsg = ref('');
const isLoadingInitialData = ref(true);
const isSubmitting = ref(false);

const form = ref({
  candidate_id: null,
  poste_vise: '',
  profil_ponderation_id: null,
  competences: []
});

const availableCompetencies = ['Communication', 'Résolution de problèmes', 'Leadership', 'Travail d\'équipe', 'Adaptabilité', 'Gestion du stress', 'Connaissances Techniques', 'Initiative & Proactivité'];

const isFormValid = computed(() => {
  const compCount = form.value.competences.length;
  return form.value.candidate_id && form.value.poste_vise && form.value.profil_ponderation_id && compCount >= 2 && compCount <= 4;
});

onMounted(async () => {
  try {
    const [candidatesRes, profilesRes] = await Promise.all([
      api.getCandidates(),
      api.getProfilesForSelection()
    ]);
    candidates.value = candidatesRes.data;
    profiles.value = profilesRes.data;
    if (profiles.value.length > 0) {
      // Pré-sélectionne le premier profil par défaut
      form.value.profil_ponderation_id = profiles.value[0].id;
    }
  } catch (error) {
    errorMsg.value = "Erreur de chargement des données de configuration.";
  } finally {
    isLoadingInitialData.value = false;
  }
});

const handleCreateSession = async () => {
  isSubmitting.value = true;
  successMsg.value = '';
  errorMsg.value = '';
  try {
    await api.createSession(form.value);
    // On ne réinitialise pas le formulaire, on redirige directement
    router.push({ name: 'recruiter-dashboard' });
  } catch (error) {
    errorMsg.value = error.response?.data?.msg || "Erreur lors de la création de la session.";
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
.step-circle {
  display: inline-block;
  width: 1.5rem;
  height: 1.5rem;
  line-height: 1.5rem;
  border-radius: 50%;
  background-color: var(--blue-primary);
  color: white;
  text-align: center;
  font-size: 0.9rem;
  margin-right: 0.5rem;
}
.competencies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
}
.form-check-input {
  display: none;
}
.form-check-label {
  padding: 0.75rem 1rem;
  border: 1px solid #dee2e6;
  border-radius: 50px; /* Forme de pilule */
  cursor: pointer;
  width: 100%;
  text-align: center;
  transition: all 0.2s ease-in-out;
}
.form-check-input:checked + .form-check-label {
  background-color: var(--blue-primary);
  color: white;
  border-color: var(--blue-primary);
  font-weight: 500;
  box-shadow: 0 4px 10px rgba(0, 95, 115, 0.2);
}
.form-check-input:disabled + .form-check-label {
    background-color: #f8f9fa;
    color: #adb5bd;
    cursor: not-allowed;
    border-color: #dee2e6;
}
</style>
