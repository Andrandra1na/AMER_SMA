<template>
  <div class="container-fluid profile-page" style="max-width: 900px;">
    <!-- Alerte pour le changement de mot de passe obligatoire -->
    <div v-if="authStore.mustChangePassword" class="alert alert-warning mb-4 shadow-sm">
      <h4 class="alert-heading"><i class="bi bi-shield-lock-fill me-2"></i>Action de Sécurité Requise</h4>
      <p>Bienvenue ! Votre compte a été créé avec un mot de passe temporaire. Pour sécuriser votre accès, veuillez définir un nouveau mot de passe personnel ci-dessous.</p>
    </div>

    <h1 class="display-5 fw-bold mb-4">Mon Profil</h1>

    <div v-if="authStore.user">
      <div class="row g-4">
        <!-- Colonne de Gauche : Informations Personnelles -->
        <div class="col-lg-6">
          <div class="card shadow-sm h-100">
            <div class="card-header bg-light">
              <h5 class="mb-0"><i class="bi bi-person-vcard-fill me-2"></i>Informations Personnelles</h5>
            </div>
            <div class="card-body p-4">
              <form @submit.prevent="handleUpdateProfile">
                <div class="form-floating mb-3">
                  <input type="email" class="form-control" id="profileEmail" :value="authStore.user.email" disabled>
                  <label for="profileEmail">Adresse e-mail</label>
                </div>
                <div class="form-floating mb-3">
                  <input type="text" class="form-control text-capitalize" id="profileRole" :value="authStore.user.role" disabled>
                  <label for="profileRole">Rôle</label>
                </div>
                <div class="form-floating mb-3">
                  <input type="text" class="form-control" id="profileName" v-model="nom" required>
                  <label for="profileName">Nom Complet</label>
                </div>
                <button v-if="!authStore.mustChangePassword" type="submit" class="btn btn-primary" :disabled="isLoading">
                  <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
                  Mettre à jour le nom
                </button>
              </form>
            </div>
          </div>
        </div>

        <!-- Colonne de Droite : Changement de Mot de Passe -->
        <div class="col-lg-6">
          <div class="card shadow-sm h-100">
            <div class="card-header bg-light">
              <h5 class="mb-0"><i class="bi bi-key-fill me-2"></i>Changer mon Mot de Passe</h5>
            </div>
            <div class="card-body p-4">
              <form @submit.prevent="handleUpdatePassword">
                <div class="form-floating mb-3">
                  <input type="password" class="form-control" id="newPassword" v-model="newPassword" required minlength="8">
                  <label for="newPassword">Nouveau Mot de Passe</label>
                </div>
                <div class="progress mb-3" style="height: 5px;">
                  <div class="progress-bar" :class="passwordStrength.class" :style="{ width: passwordStrength.width }"></div>
                </div>
                <div class="form-floating mb-3">
                  <input type="password" class="form-control" :class="{ 'is-invalid': passwordMismatch }" id="confirmPassword" v-model="confirmPassword" required>
                  <label for="confirmPassword">Confirmer le Nouveau Mot de Passe</label>
                </div>
                <button type="submit" class="btn btn-primary" :disabled="isLoading || passwordMismatch">
                  <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
                  Changer mon Mot de Passe
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Zone d'affichage des messages de statut -->
    <div v-if="successMessage" class="alert alert-success mt-4 d-flex justify-content-between align-items-center">
      <span><i class="bi bi-check-circle-fill me-2"></i>{{ successMessage }}</span>
      <button v-if="passwordChanged" @click="goToDashboard" class="btn btn-sm btn-success">
        Continuer vers mon espace <i class="bi bi-arrow-right"></i>
      </button>
    </div>
    <div v-if="errorMessage" class="alert alert-danger mt-4">
      <i class="bi bi-exclamation-triangle-fill me-2"></i>{{ errorMessage }}
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import * as api from '@/services/api';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();
const nom = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const isLoading = ref(false);
const successMessage = ref('');
const errorMessage = ref('');
const passwordChanged = ref(false);

onMounted(() => {
  if (authStore.user) {
    nom.value = authStore.user.nom;
  }
});

const passwordMismatch = computed(() => newPassword.value && confirmPassword.value && newPassword.value !== confirmPassword.value);
const passwordStrength = computed(() => {
  const p = newPassword.value;
  let score = 0;
  if (p.length >= 8) score += 25;
  if (/[a-z]/.test(p) && /[A-Z]/.test(p)) score += 25;
  if (/\d/.test(p)) score += 25;
  if (/[^A-Za-z0-9]/.test(p)) score += 25;
  if (score < 50) return { width: score + '%', class: 'bg-danger' };
  if (score < 75) return { width: score + '%', class: 'bg-warning' };
  return { width: score + '%', class: 'bg-success' };
});

const clearMessages = () => {
    successMessage.value = '';
    errorMessage.value = '';
    passwordChanged.value = false;
};

const handleUpdateProfile = async () => {
  clearMessages();
  isLoading.value = true;
  try {
    const response = await api.updateMyProfile({ nom: nom.value });
    const updatedUserInfo = { ...authStore.user, nom: response.data.user_info.nom };
    authStore.setUserData({ access_token: authStore.token, user_info: updatedUserInfo });
    successMessage.value = "Vos informations ont été mises à jour avec succès.";
  } catch (err) {
    errorMessage.value = err.response?.data?.msg || "Erreur lors de la mise à jour.";
  } finally {
    isLoading.value = false;
  }
};

const handleUpdatePassword = async () => {
  clearMessages();
  if (passwordMismatch.value) {
    errorMessage.value = "Les mots de passe ne correspondent pas.";
    return;
  }
  if (newPassword.value.length < 8) {
      errorMessage.value = "Le mot de passe doit contenir au moins 8 caractères.";
      return;
  }

  isLoading.value = true;
  try {
    const response = await api.updateMyProfile({ new_password: newPassword.value });
    const updatedUserInfo = response.data.user_info;
    authStore.setUserData({ access_token: authStore.token, user_info: updatedUserInfo });

    successMessage.value = "Votre mot de passe a été changé avec succès.";
    passwordChanged.value = true;
    newPassword.value = '';
    confirmPassword.value = '';
  } catch (err) {
    errorMessage.value = err.response?.data?.msg || "Erreur lors du changement de mot de passe.";
  } finally {
    isLoading.value = false;
  }
};

const goToDashboard = () => {
    router.push({ name: 'post-login-redirect' });
};
</script>

<style scoped>
.form-floating > label {
  padding-left: 1rem;
}
</style>
