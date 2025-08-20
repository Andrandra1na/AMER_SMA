<template>
  <div class="container-fluid register-page">
    <div class="row g-0 vh-100">
      <!-- Colonne de Gauche : Visuel et Message d'Accueil -->
      <div class="col-lg-7 d-none d-lg-flex flex-column justify-content-center align-items-center text-white p-5 hero-side">
        <i class="bi bi-rocket-takeoff-fill display-1 mb-4"></i>
        <h1 class="display-4 fw-bold text-center">Rejoignez l'Aventure</h1>
        <p class="lead text-center col-lg-8">
          Créez votre compte en quelques instants et préparez-vous à montrer le meilleur de vous-même.
        </p>
      </div>

      <!-- Colonne de Droite : Formulaire d'Inscription -->
      <div class="col-lg-5 d-flex flex-column justify-content-center align-items-center bg-light">
        <div class="form-container p-4 p-md-5">
          <div class="text-center mb-4">
            <h2 class="fw-bold">Créer un Compte</h2>
            <p class="text-muted">C'est simple et rapide.</p>
          </div>

          <!-- Affichage du message de succès APRÈS l'inscription -->
          <div v-if="successMsg" class="alert alert-success text-center">
            <h4 class="alert-heading"><i class="bi bi-check-circle-fill"></i> Inscription Réussie !</h4>
            <p>{{ successMsg }}</p>
            <router-link to="/login" class="btn btn-primary">Se connecter</router-link>
          </div>

          <form v-else @submit.prevent="handleRegister" class="w-100">
            <!-- Champ Nom Complet -->
            <div class="form-floating mb-3">
              <input type="text" class="form-control" id="floatingName" placeholder="Jean Dupont" v-model="name" required>
              <label for="floatingName"><i class="bi bi-person-fill me-2"></i>Nom complet</label>
            </div>
            <!-- Champ Email -->
            <div class="form-floating mb-3">
              <input type="email" class="form-control" id="floatingEmail" placeholder="vous@exemple.com" v-model="email" required>
              <label for="floatingEmail"><i class="bi bi-envelope-fill me-2"></i>Adresse e-mail</label>
            </div>
            <!-- Champ Mot de Passe -->
            <div class="form-floating mb-3">
              <input type="password" class="form-control" id="floatingPassword" placeholder="••••••••" v-model="password" required>
              <label for="floatingPassword"><i class="bi bi-lock-fill me-2"></i>Mot de passe</label>
            </div>
            <!-- Indicateur de force du mot de passe -->
            <div class="progress mb-3" style="height: 5px;">
              <div class="progress-bar" :class="passwordStrength.class" :style="{ width: passwordStrength.width }"></div>
            </div>
            <!-- Champ Confirmer Mot de Passe -->
            <div class="form-floating mb-4">
              <input type="password" class="form-control" :class="{ 'is-invalid': passwordMismatch }" id="floatingConfirmPassword" placeholder="••••••••" v-model="confirmPassword" required>
              <label for="floatingConfirmPassword"><i class="bi bi-check-circle-fill me-2"></i>Confirmer le mot de passe</label>
            </div>

            <div v-if="errorMsg" class="alert alert-danger d-flex align-items-center"><i class="bi bi-exclamation-triangle-fill me-2"></i>{{ errorMsg }}</div>

            <div class="d-grid mt-4">
              <button type="submit" class="btn btn-primary btn-lg" :disabled="isLoading || passwordMismatch">
                <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
                Créer mon compte
              </button>
            </div>
          </form>

          <p v-if="!successMsg" class="text-center mt-4 text-muted small">
            Déjà un compte ? <router-link to="/login">Connectez-vous</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed} from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';

const name = ref('');
const email = ref('');
const password = ref('');
const confirmPassword = ref('');
const errorMsg = ref('');
const successMsg = ref('');
const isLoading = ref(false);
const authStore = useAuthStore();


// Vérifie si les mots de passe correspondent
const passwordMismatch = computed(() => {
  return password.value && confirmPassword.value && password.value !== confirmPassword.value;
});

// Calcule la force du mot de passe pour la barre de progression
const passwordStrength = computed(() => {
  const p = password.value;
  let score = 0;
  if (p.length >= 8) score += 25;
  if (/[a-z]/.test(p) && /[A-Z]/.test(p)) score += 25; // Minuscules et majuscules
  if (/\d/.test(p)) score += 25; // Chiffres
  if (/[^A-Za-z0-9]/.test(p)) score += 25; // Caractères spéciaux

  if (score < 50) return { width: score + '%', class: 'bg-danger' };
  if (score < 75) return { width: score + '%', class: 'bg-warning' };
  return { width: score + '%', class: 'bg-success' };
});

const handleRegister = async () => {
  if (passwordMismatch.value) {
    errorMsg.value = "Les mots de passe ne correspondent pas.";
    return;
  }
  isLoading.value = true;
  errorMsg.value = '';
  successMsg.value = '';

  const result = await authStore.register({
    nom: name.value,
    email: email.value,
    password: password.value,
  });

  if (result.success) {
    successMsg.value = "Votre compte a été créé avec succès !";
    // Plus besoin de redirection automatique, on affiche un message clair
  } else {
    errorMsg.value = result.message;
  }

  isLoading.value = false;
};
</script>

<style scoped>
/* On réutilise les styles de la page de connexion pour la cohérence */
.register-page {
  overflow-x: hidden;
}
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

.form-floating > .form-control {
  padding-left: 1rem;
}
.form-floating > label {
  padding-left: 1rem;
}

/* Style pour le champ invalide (mots de passe qui ne correspondent pas) */
.form-control.is-invalid {
  border-color: var(--bs-danger);
}
</style>
