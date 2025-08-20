<template>
  <div class="player-page container py-4">
    <div v-if="isLoading" class="text-center mt-5">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="mt-2 text-muted">Chargement de la vidéo...</p>
    </div>
    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-else-if="session" class="player-container">
      <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap">
        <div>
          <h1 class="h3 fw-bold">Relecture de l'Entretien #{{ session.id }}</h1>
          <p class="text-muted mb-0">Poste : {{ session.poste_vise }}</p>
        </div>
        <button @click="goBack" class="btn btn-outline-secondary mt-2 mt-md-0">
          <i class="bi bi-arrow-left me-2"></i>Retour
        </button>
      </div>
      <div class="video-wrapper shadow rounded overflow-hidden mt-4">
        <video v-if="videoUrl" ref="videoPlayer" :src="videoUrl" controls controlsList="nodownload" class="w-100"></video>
        <div v-else class="alert alert-warning m-0">Le chemin de la vidéo est introuvable.</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import * as api from '@/services/api';

const props = defineProps({
  id: { type: [String, Number], required: true },
});

const router = useRouter();
const authStore = useAuthStore();
const session = ref(null);
const isLoading = ref(true);
const error = ref('');

const videoUrl = computed(() => {
  const path_from_db = session.value?.video_path;
  if (path_from_db && authStore.token) {
    const clean_path = path_from_db.replace(/\\/g, '/');
    return `http://localhost:5000/media/${clean_path}?jwt=${authStore.token}`;
  }
  return '';
});

onMounted(async () => {
  try {
    const response = await api.getSessionDetails(props.id);
    session.value = response.data;
  } catch (err) {
    error.value = "Impossible de charger les détails de la session.";
  } finally {
    isLoading.value = false;
  }
});

const goBack = () => router.go(-1);
</script>

<style scoped>
.video-wrapper { max-width: 900px; margin: auto; background-color: #000; }
</style>
