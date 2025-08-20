<template>
  <div class="container-fluid config-ia-page">
    <h1 class="display-5 fw-bold mb-2">Configuration des Pondérations IA</h1>
    <p class="lead text-muted mb-5">Créez et gérez des profils d'évaluation pour adapter l'analyse aux différents types de postes.</p>

    <!-- Gestion des états de chargement et d'erreur -->
    <div v-if="isLoading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>
    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-else class="row g-5">
      <!-- Colonne de gauche : Formulaire d'édition/création -->
      <div class="col-lg-5">
        <div class="card shadow-sm sticky-top" style="top: 100px;">
          <div class="card-body p-4">
            <h4 class="card-title fw-bold d-flex align-items-center">
              <i class="bi bi-pencil-square me-2"></i>
              {{ isEditing ? 'Modifier le Profil' : 'Nouveau Profil de Pondération' }}
            </h4>
            <hr>
            <form @submit.prevent="handleSave">
              <div class="mb-3">
                <label for="profileName" class="form-label">Nom du Profil <span class="text-danger">*</span></label>
                <input id="profileName" v-model="currentProfile.nom_profil" class="form-control" placeholder="Ex: Profil Technique Senior" required>
              </div>
              <div class="mb-4">
                <label for="profileDesc" class="form-label">Description</label>
                <textarea id="profileDesc" v-model="currentProfile.description" class="form-control" rows="2" placeholder="Ex: Priorise la pertinence et la clarté."></textarea>
              </div>

              <!-- On utilise notre composant de sliders et on écoute son événement 'update' -->
              <WeightSliders :weights="currentProfile.poids" @update="updateWeights" />

              <!-- Affichage du total des poids avec une couleur dynamique -->
              <div class="d-flex justify-content-end mt-3 fw-bold" :class="totalWeight === 100 ? 'text-success' : 'text-danger'">
                Total : {{ totalWeight }} / 100 %
              </div>

              <!-- Boutons d'action -->
              <div class="d-flex gap-2 mt-3">
                <button type="submit" class="btn btn-primary" :disabled="totalWeight !== 100 || isSaving">
                  <span v-if="isSaving" class="spinner-border spinner-border-sm me-2"></span>
                  <i v-else class="bi bi-check-lg me-1"></i>
                  {{ isEditing ? 'Sauvegarder' : 'Créer' }}
                </button>
                <button v-if="isEditing" type="button" class="btn btn-outline-secondary" @click="resetForm">Annuler</button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <!-- Colonne de droite : Liste des profils existants -->
      <div class="col-lg-7">
        <h3 class="fw-bold mb-3">Profils Existants ({{ profiles.length }})</h3>
        <div v-if="profiles.length === 0" class="text-center p-5 bg-light rounded">
            <h4>Aucun profil personnalisé créé.</h4>
            <p class="text-muted">Utilisez le formulaire à gauche pour créer votre premier modèle d'évaluation.</p>
        </div>
        <div v-else class="row row-cols-1 row-cols-md-2 g-4">
          <div v-for="p in profiles" :key="p.id" class="col">
            <div class="card profile-card h-100" :class="{ 'active': currentProfile.id === p.id }">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h5 class="card-title fw-bold">{{ p.nom_profil }}</h5>
                    <p class="card-text text-muted small">{{ p.description }}</p>
                  </div>
                  <div class="btn-group">
                    <button @click="editProfile(p)" class="btn btn-sm btn-outline-secondary" title="Modifier"><i class="bi bi-pencil"></i></button>
                    <button @click="deleteProfile(p)" class="btn btn-sm btn-outline-danger" title="Supprimer"><i class="bi bi-trash"></i></button>
                  </div>
                </div>
                <!-- Mini-graphique de répartition -->
                <div style="height: 150px;" class="mt-3">
                    <Doughnut :data="getChartDataForProfile(p.poids)" :options="chartOptions" />
                </div>
              </div>
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
import WeightSliders from '@/components/WeightSliders.vue';
import { Doughnut } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, ArcElement } from 'chart.js';

ChartJS.register(Title, Tooltip, Legend, ArcElement);

// --- Fonctions d'aide et états ---
const createDefaultProfile = () => ({
  id: null,
  nom_profil: '',
  description: '',
  poids: { relevance: 25, clarity: 25, fluency: 25, engagement: 25 }
});

const profiles = ref([]);
const isLoading = ref(true);
const currentProfile = ref(createDefaultProfile());
const isSaving = ref(false);
const error = ref('');

const isEditing = computed(() => !!currentProfile.value.id);
const totalWeight = computed(() => {
    if (!currentProfile.value.poids) return 0;
    return Math.round(Object.values(currentProfile.value.poids).reduce((sum, val) => sum + val, 0));
});

// --- Logique de Rééquilibrage Automatique des Poids ---
const updateWeights = ({ key, value }) => {
  const newWeights = { ...currentProfile.value.poids };
  const oldValue = newWeights[key];
  const diff = value - oldValue;

  newWeights[key] = value;

  const otherKeys = Object.keys(newWeights).filter(k => k !== key);

  if (otherKeys.length > 0) {
    const sumOfOthers = otherKeys.reduce((sum, k) => sum + newWeights[k], 0);
    const remainder = 100 - value;

    if (sumOfOthers > 0) {
      // Distribue la différence proportionnellement
      for (const k of otherKeys) {
        const proportion = newWeights[k] / sumOfOthers;
        newWeights[k] = remainder * proportion;
      }
    } else {
      // Si tous les autres sont à 0, distribue équitablement
      for (const k of otherKeys) {
        newWeights[k] = remainder / otherKeys.length;
      }
    }

    // Arrondit et ajuste le dernier pour que la somme fasse exactement 100
    let totalRounded = 0;
    for (let i = 0; i < otherKeys.length; i++) {
      const k = otherKeys[i];
      if (i < otherKeys.length - 1) {
        newWeights[k] = Math.round(newWeights[k]);
        totalRounded += newWeights[k];
      } else {
        newWeights[k] = 100 - value - totalRounded;
      }
    }
  }
  currentProfile.value.poids = newWeights;
};

// --- Logique de gestion des données (CRUD) ---
const fetchProfiles = async () => {
  isLoading.value = true;
  try {
    const response = await api.getProfiles();
    profiles.value = response.data;
  } catch(e) {
    error.value = "Impossible de charger les profils de pondération.";
    console.error("Erreur chargement profils:", e);
  } finally { isLoading.value = false; }
};
onMounted(fetchProfiles);

const resetForm = () => { currentProfile.value = createDefaultProfile(); };
const editProfile = (profile) => { currentProfile.value = JSON.parse(JSON.stringify(profile)); };

const handleSave = async () => {
    isSaving.value = true;
    try {
        if (isEditing.value) {
            await api.updateProfile(currentProfile.value.id, currentProfile.value);
        } else {
            await api.createProfile(currentProfile.value);
        }
        resetForm();
        await fetchProfiles();
    } catch(e) {
        console.error("Erreur de sauvegarde:", e);
        alert("Une erreur est survenue.");
    } finally {
        isSaving.value = false;
    }
};

const deleteProfile = async (profile) => {
    if (confirm(`Supprimer le profil "${profile.nom_profil}" ?`)) {
        try {
            await api.deleteProfile(profile.id);
            if (currentProfile.value.id === profile.id) resetForm();
            await fetchProfiles();
        } catch(e) { console.error("Erreur de suppression:", e); }
    }
};

const getChartDataForProfile = (poids) => {
    if (!poids) return { labels: [], datasets: [] };
    const labels = ['Pertinence', 'Clarté', 'Fluidité', 'Engagement'];
    const data = [poids.relevance, poids.clarity, poids.fluency, poids.engagement];
    return {
        labels,
        datasets: [{ data, backgroundColor: ['#005f73', '#0a9396', '#94d2bd', '#e9ecef'] }]
    };
};
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'right' } }
};
</script>

<style scoped>
.sticky-top { top: 100px; }
.profile-card { transition: all 0.2s ease-in-out; border: 1px solid var(--border-color); }
.profile-card.active { border-color: var(--blue-primary); box-shadow: 0 0 0 4px rgba(0, 95, 115, 0.15); }
.profile-card:hover { transform: translateY(-5px); }
</style>
