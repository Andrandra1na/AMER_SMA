<template>
  <div class="container-fluid login-page">
    <div class="row g-0 vh-100">
      <!-- ====================================================== -->
      <!-- Colonne de Gauche : Visuel de Marque                 -->
      <!-- ====================================================== -->
      <div class="col-lg-7 d-none d-lg-flex flex-column justify-content-center align-items-center text-white p-5 hero-side">
        <!-- L'utilisation de 'd-flex' et des utilitaires de centrage garantit un alignement parfait -->
        <i class="bi bi-robot display-1 mb-4"></i>
        <h1 class="display-4 fw-bold text-center">Bienvenue sur IntelliHire</h1>
        <p class="lead text-center col-lg-8">
          La plateforme qui vous aide à révéler votre plein potentiel. Connectez-vous pour commencer.
        </p>
      </div>

      <!-- ====================================================== -->
      <!-- Colonne de Droite : Formulaire de Connexion          -->
      <!-- ====================================================== -->
      <div class="col-lg-5 d-flex flex-column justify-content-center align-items-center bg-light">
        <div class="form-container p-4 p-md-5">
          <div class="text-center mb-5">
            <h2 class="fw-bold">Connexion à votre Espace</h2>
            <p class="text-muted">Content de vous revoir !</p>
          </div>

          <form @submit.prevent="handleLogin" class="w-100">
            <!-- Champ Email avec icône -->
            <div class="form-floating mb-3">
              <input type="email" class="form-control" id="floatingEmail" placeholder="vous@exemple.com" v-model="email" required autocomplete="email">
              <label for="floatingEmail"><i class="bi bi-envelope-fill me-2"></i>Adresse e-mail</label>
            </div>

            <!-- Champ Mot de Passe avec icône et bouton afficher/cacher -->
            <div class="input-group mb-4">
              <div class="form-floating">
                  <input :type="passwordFieldType" class="form-control" id="floatingPassword" placeholder="••••••••" v-model="password" required autocomplete="current-password">
                  <label for="floatingPassword"><i class="bi bi-lock-fill me-2"></i>Mot de passe</label>
              </div>
              <button class="btn btn-outline-secondary" type="button" @click="togglePasswordVisibility" style="border-radius: 0 0.375rem 0.375rem 0;">
                <i :class="passwordFieldType === 'password' ? 'bi bi-eye-fill' : 'bi bi-eye-slash-fill'"></i>
              </button>
            </div>

            <div v-if="errorMsg" class="alert alert-danger d-flex align-items-center"><i class="bi bi-exclamation-triangle-fill me-2"></i>{{ errorMsg }}</div>

            <div class="d-grid mt-4">
              <button type="submit" class="btn btn-primary btn-lg" :disabled="isLoading">
                <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
                Se connecter
              </button>
            </div>
          </form>

          <div class="d-flex justify-content-between align-items-center mt-4">
            <router-link to="/register" class="small">Créer un compte</router-link>
            <router-link to="/forgot-password" class="small">Mot de passe oublié ?</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';

const email = ref('');
const password = ref('');
const errorMsg = ref('');
const isLoading = ref(false);
const authStore = useAuthStore();
const router = useRouter();

// Logique pour afficher/cacher le mot de passe
const isPasswordVisible = ref(false);
const passwordFieldType = computed(() => isPasswordVisible.value ? 'text' : 'password');
const togglePasswordVisibility = () => {
  isPasswordVisible.value = !isPasswordVisible.value;
};

const handleLogin = async () => {
  isLoading.value = true;
  errorMsg.value = '';
  const result = await authStore.login({
    email: email.value,
    password: password.value,
  });
  if (result.success) {
    router.push({ name: 'post-login-redirect' });
  } else {
    errorMsg.value = result.message;
  }
  isLoading.value = false;
};
</script>

<style scoped>
.login-page {
  overflow-x: hidden;
}
.hero-side {
  background: linear-gradient(135deg, var(--blue-primary) 0%, var(--blue-light) 100%);
  /* Ajout d'une animation d'entrée douce */
  animation: slideInFromLeft 0.8s ease-out;
}
@keyframes slideInFromLeft {
  from { transform: translateX(-50px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.form-container {
  width: 100%;
  max-width: 400px; /* Un peu plus compact */
  animation: fadeIn 1s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Amélioration pour les 'floating labels' avec Bootstrap */
.form-floating > .form-control {
  padding-left: 1rem;
}
.form-floating > label {
  padding-left: 1rem;
}
</style>
