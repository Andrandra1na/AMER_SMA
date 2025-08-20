<template>
  <div class="container-fluid reset-password-page">
    <div class="row g-0 vh-100">
      <!-- Colonne de Gauche : Visuel -->
      <div class="col-lg-7 d-none d-lg-flex flex-column justify-content-center align-items-center text-white p-5 hero-side">
        <i class="bi bi-shield-lock-fill display-1 mb-4"></i>
        <h1 class="display-4 fw-bold text-center">Sécurisez votre Compte</h1>
        <p class="lead text-center col-lg-8">
          Choisissez un nouveau mot de passe fort pour protéger vos informations.
        </p>
      </div>

      <!-- Colonne de Droite : Formulaire -->
      <div class="col-lg-5 d-flex flex-column justify-content-center align-items-center bg-light">
        <div class="form-container p-4 p-md-5">
          <div class="text-center mb-4">
            <h2 class="fw-bold">Réinitialiser le Mot de Passe</h2>
          </div>

          <!-- Message de succès -->
          <div v-if="isSuccess" class="alert alert-success text-center">
              <h4 class="alert-heading"><i class="bi bi-check-circle-fill"></i> C'est fait !</h4>
              <p>{{ message }}</p>
              <router-link to="/login" class="btn btn-primary mt-2">Se connecter</router-link>
          </div>

          <!-- Formulaire de réinitialisation -->
          <form v-else @submit.prevent="handleResetPassword" class="w-100">
            <p class="text-muted text-center mb-4">Veuillez entrer votre nouveau mot de passe.</p>
            <div class="input-group mb-3">
               <div class="form-floating">
                  <input type="password" class="form-control" id="floatingNewPassword" placeholder="••••••••" v-model="newPassword" required minlength="8">
                  <label for="floatingNewPassword"><i class="bi bi-lock-fill me-2"></i>Nouveau mot de passe</label>
              </div>
            </div>
            <div class="progress mb-3" style="height: 5px;">
              <div class="progress-bar" :class="passwordStrength.class" :style="{ width: passwordStrength.width }"></div>
            </div>
            <div class="input-group mb-4">
              <div class="form-floating">
                  <input type="password" class="form-control" :class="{ 'is-invalid': passwordMismatch }" id="floatingConfirmPassword" placeholder="••••••••" v-model="confirmPassword" required>
                  <label for="floatingConfirmPassword"><i class="bi bi-check-circle-fill me-2"></i>Confirmer le mot de passe</label>
              </div>
            </div>

            <div v-if="message && !isSuccess" class="alert alert-danger">{{ message }}</div>

            <div class="d-grid mt-4">
              <button type="submit" class="btn btn-primary btn-lg" :disabled="isLoading || passwordMismatch">
                <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
                Réinitialiser mon mot de passe
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import * as api from '@/services/api';

const props = defineProps({ token: { type: String, required: true } });

const newPassword = ref('');
const confirmPassword = ref('');
const isLoading = ref(false);
const message = ref('');
const isSuccess = ref(false);

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

const handleResetPassword = async () => {
  if (passwordMismatch.value) {
    message.value = "Les mots de passe ne correspondent pas.";
    isSuccess.value = false;
    return;
  }
  isLoading.value = true;
  message.value = '';
  isSuccess.value = false;
  try {
    const response = await api.resetPassword(props.token, newPassword.value);
    message.value = response.data.msg;
    isSuccess.value = true;
  } catch (error) {
    message.value = error.response?.data?.msg || "Une erreur est survenue.";
    isSuccess.value = false;
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* On réutilise les styles des autres pages d'authentification */
.hero-side {
  background: linear-gradient(135deg, var(--blue-primary) 0%, var(--blue-light) 100%);
  animation: slideInFromLeft 0.8s ease-out;
}
@keyframes slideInFromLeft {
  from { transform: translateX(-50px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
.form-container {
  width: 100%;
  max-width: 400px;
  animation: fadeIn 1s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.form-floating > label {
  padding-left: 1rem;
}
</style>
