<template>
  <div id="app-container">
    <header>
      <nav class="navbar navbar-expand-lg fixed-top navbar-light bg-white shadow-sm">
        <div class="container">
          <router-link class="navbar-brand d-flex align-items-center" to="/">
            <img src="../src/assets/logo1.png" alt="Logo IntelliHire" class="me-2" style="height: 30px;" />
            <span>IntelliHire</span>
          </router-link>


          <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
          </button>


          <div class="collapse navbar-collapse justify-content-end" id="navbarNav">
            <ul class="navbar-nav align-items-lg-center">

              <!-- --- ACTIONS POUR UTILISATEUR NON CONNECTÉ --- -->
              <template v-if="!authStore.isAuthenticated">
                <li class="nav-item">
                  <router-link to="/login" class="nav-link">Connexion</router-link>
                </li>
                <li class="nav-item ms-lg-2">
                  <router-link to="/register" class="btn btn-primary btn-sm">Inscription</router-link>
                </li>
              </template>

              <!-- --- ACTIONS POUR UTILISATEUR CONNECTÉ --- -->
              <template v-else>
                <li class="nav-item dropdown">
                  <a class="nav-link dropdown-toggle" href="#" id="navbarUserDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                    <i class="bi bi-person-circle me-1"></i>
                    {{ authStore.user?.nom }}
                  </a>
                  <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="navbarUserDropdown">
                    <li>
                      <h6 class="dropdown-header">Rôle: {{ authStore.user?.role }}</h6>
                    </li>
                    <li><hr class="dropdown-divider"></li>
                    <!-- Bouton "Mon Espace" dans le dropdown -->
                    <li>
                      <a class="dropdown-item" href="#" @click.prevent="handleDashboard">
                        <i class="bi bi-speedometer2 me-2"></i>Mon Espace
                      </a>
                    </li>
                    <!-- Bouton "Historique" (candidat) dans le dropdown -->
                    <li v-if="authStore.userRole === 'candidat'">
                       <router-link to="/history" class="dropdown-item">
                         <i class="bi bi-clock-history me-2"></i>Mon Historique
                       </router-link>
                    </li>
                    <!-- AJOUT DU LIEN POUR LE RECRUTEUR -->
                    <li v-if="authStore.userRole === 'recruteur'">
                      <router-link to="/recruiter/questions" class="dropdown-item">
                        <i class="bi bi-card-checklist me-2"></i>Gérer mes questions
                      </router-link>
                    </li>
                    <!-- === AJOUT DU MENU ADMIN === -->
                    <div v-if="authStore.userRole === 'admin'">
                        <li><hr class="dropdown-divider"></li>
                        <li><h6 class="dropdown-header">Administration</h6></li>
                        <li>
                           <router-link to="/admin/users" class="dropdown-item">
                             <i class="bi bi-people-fill me-2"></i>Gestion Utilisateurs
                           </router-link>
                        </li>
                        <li>
                           <router-link to="/admin/questions" class="dropdown-item">
                             <i class="bi bi-patch-question-fill me-2"></i>Supervision Questions
                           </router-link>
                        </li>
                        <li>
                           <router-link to="/admin/export" class="dropdown-item">
                             <i class="bi bi-file-earmark-arrow-down-fill me-2"></i>Export Données
                           </router-link>
                        </li>
                        <li><router-link to="/admin/config-ia" class="dropdown-item">
                          <i class="bi bi-sliders me-2"></i>Configuration IA
                        </router-link>
                      </li>
                      <li>
                        <router-link to="/admin/status" class="dropdown-item">
                            <i class="bi bi-heart-pulse-fill me-2"></i>Statut du Système
                        </router-link>
                      </li>
                    </div>
                    <li><hr class="dropdown-divider"></li>
                    <li>
                      <router-link to="/profile" class="dropdown-item">
                        <i class="bi bi-person-fill-gear me-2"></i>Mon Profil
                      </router-link>
                    </li>

                    <!-- Bouton "Déconnexion" dans le dropdown -->
                    <li>
                      <a class="dropdown-item text-danger" href="#" @click.prevent="handleLogout">
                        <i class="bi bi-box-arrow-right me-2"></i>Déconnexion
                      </a>
                    </li>
                  </ul>
                </li>
              </template>

            </ul>
          </div>
        </div>
      </nav>
    </header>

    <div style="padding-top: 70px;">
      <main class="container my-4">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <footer class="mt-auto py-3" style="background-color: var(--surface-color); border-top: 1px solid var(--border-color);">
      <div class="container text-center">
        <span class="text-muted">© {{ currentYear }} IntelliHire – Recrutement intelligent</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

const handleLogout = () => {
  authStore.logout();
  router.push('/');
};

const handleDashboard = () => {
  const navbar = document.getElementById('navbarNav');
  if (navbar && navbar.classList.contains('show')) {
    navbar.classList.remove('show');
  }

  const role = authStore.userRole;

  switch (role) {
    case 'admin':
      router.push({ name: 'admin-dashboard' });
      break;
    case 'recruteur':
      router.push({ name: 'recruiter-dashboard' });
      break;
    case 'candidat':
      router.push({ name: 'candidate-dashboard' });
      break;
    default:
      router.push('/');
  }
};

const currentYear = new Date().getFullYear()
</script>

<style>
#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

main {
  flex: 1;
}

.navbar .navbar-brand {
    color: var(--blue-primary) !important;
    font-weight: 700;
}

.navbar .nav-link {
    color: var(--text-body);
}
.navbar .nav-link:hover {
    color: var(--blue-primary);
}

.dropdown-menu {
  border-radius: 0.5rem;
  border-color: var(--border-color);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.dropdown-item {
  display: flex;
  align-items: center;
}
.dropdown-item i {
  width: 24px;
}

/* Transitions de page */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
