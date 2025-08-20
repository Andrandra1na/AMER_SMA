<template>
  <div class="container-fluid forgot-password-page">
    <div class="row g-0 vh-100">
      <!-- Colonne de Gauche : Visuel -->
      <div class="col-lg-7 d-none d-lg-flex flex-column justify-content-center align-items-center text-white p-5 hero-side">
        <i class="bi bi-key-fill display-1 mb-4"></i>
        <h1 class="display-4 fw-bold text-center">Un oubli, ça arrive !</h1>
        <p class="lead text-center col-lg-8">
          Pas de panique. Nous allons vous aider à retrouver l'accès à votre compte en toute sécurité.
        </p>
      </div>

      <!-- Colonne de Droite : Formulaire -->
      <div class="col-lg-5 d-flex flex-column justify-content-center align-items-center bg-light">
        <div class="form-container p-4 p-md-5">
          <div class="text-center mb-4">
            <h2 class="fw-bold">Mot de Passe Oublié</h2>
          </div>

          <!-- Message de succès -->
          <div v-if="message" class="alert alert-success text-center">
            <h4 class="alert-heading"><i class="bi bi-envelope-check-fill"></i> Vérifiez vos e-mails !</h4>
            <p>{{ message }}</p>
            <p class="mb-0">Un lien pour réinitialiser votre mot de passe a été envoyé à <strong>{{ email }}</strong>.</p>
          </div>

          <!-- Formulaire de demande -->
          <form v-else @submit.prevent="handleForgotPassword" class="w-100">
            <p class="text-muted text-center mb-4">Entrez votre adresse e-mail pour recevoir les instructions.</p>
            <div class="form-floating mb-3">
              <input type="email" class="form-control" id="floatingEmail" placeholder="vous@exemple.com" v-model="email" required>
              <label for="floatingEmail"><i class="bi bi-envelope-fill me-2"></i>Adresse e-mail</label>
            </div>
            <div class="d-grid mt-4">
              <button type="submit" class="btn btn-primary btn-lg" :disabled="isLoading">
                <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
                {{ isLoading ? 'Envoi en cours...' : 'Envoyer le lien' }}
              </button>
            </div>
          </form>

          <p class="text-center mt-4 text-muted small">
            <router-link to="/login"><i class="bi bi-arrow-left me-1"></i>Retour à la page de connexion</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import * as api from '@/services/api';

const email = ref('');
const isLoading = ref(false);
const message = ref('');

const handleForgotPassword = async () => {
  isLoading.value = true;
  try {
    const response = await api.forgotPassword(email.value);
    message.value = response.data.msg;
  } catch (error) {
    // On affiche un message générique même en cas d'erreur pour la sécurité
    message.value = "Si un compte est associé à cet email, un lien de réinitialisation a été envoyé.";
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* On réutilise les styles des pages de connexion/inscription */
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
