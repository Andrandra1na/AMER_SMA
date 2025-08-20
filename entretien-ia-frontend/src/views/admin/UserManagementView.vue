<template>
  <div class="container-fluid user-management-page">
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
      <h1 class="display-5 fw-bold">Gestion des Utilisateurs</h1>
      <button class="btn btn-primary" @click="openModalForCreate"><i class="bi bi-person-plus-fill me-2"></i>Ajouter un Utilisateur</button>
    </div>

    <!-- Cartes de statistiques rapides -->
    <div class="row g-4 mb-4">
      <div class="col-md-4"><div class="card kpi-card shadow-sm"><div class="card-body"><i class="bi bi-people-fill"></i><div><p class="h3 fw-bolder mb-0">{{ userStats.total }}</p><div class="text-muted">Total Utilisateurs</div></div></div></div></div>
      <div class="col-md-4"><div class="card kpi-card shadow-sm"><div class="card-body"><i class="bi bi-briefcase-fill text-info"></i><div><p class="h3 fw-bolder mb-0">{{ userStats.recruiters }}</p><div class="text-muted">Recruteurs</div></div></div></div></div>
      <div class="col-md-4"><div class="card kpi-card shadow-sm"><div class="card-body"><i class="bi bi-person-fill text-secondary"></i><div><p class="h3 fw-bolder mb-0">{{ userStats.candidates }}</p><div class="text-muted">Candidats</div></div></div></div></div>
    </div>

    <div class="card shadow-sm">
      <div class="card-header bg-light d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Liste des Comptes</h5>
        <div class="col-12 col-md-4">
            <input type="text" class="form-control form-control-sm" v-model="searchValue" placeholder="Rechercher par nom ou email...">
        </div>
      </div>
      <div class="card-body">
        <EasyDataTable
          :headers="headers"
          :items="users"
          :search-field="['nom', 'email']"
          :search-value="searchValue"
          :loading="isLoading"
          :rows-per-page="10"
          theme-color="#005f73"
          table-class-name="custom-table"
          rows-per-page-message="Lignes par page"
          rows-of-page-separator-message="sur"
          empty-message="Aucun utilisateur ne correspond à votre recherche"
          buttons-pagination
          show-index
        >
          <!-- Templates pour customiser les colonnes -->
          <template #item-role="{ role }">
            <span class="badge" :class="roleBadge(role)">{{ role }}</span>
          </template>
          <template #item-actions="user">
            <div class="d-inline-flex gap-2">
              <button class="btn btn-sm btn-outline-secondary" @click="openModalForEdit(user)" title="Modifier"><i class="bi bi-pencil-fill"></i></button>
              <button class="btn btn-sm btn-outline-danger" @click="handleDelete(user)" :disabled="isCurrentUser(user.id)" title="Supprimer"><i class="bi bi-trash-fill"></i></button>
            </div>
          </template>
        </EasyDataTable>
      </div>
    </div>

    <UserModal :user="selectedUser" @userSaved="handleSave" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import * as api from '@/services/api';
import UserModal from '@/components/UserModal.vue';
import { Modal } from 'bootstrap';
// Import de la DataTable
import EasyDataTable from 'vue3-easy-data-table';
import 'vue3-easy-data-table/dist/style.css';


const authStore = useAuthStore();
const users = ref([]);
const isLoading = ref(true);
const selectedUser = ref(null);
const searchValue = ref('');

// Configuration des colonnes pour la DataTable
const headers = [
  { text: "Nom", value: "nom", sortable: true },
  { text: "Email", value: "email", sortable: true },
  { text: "Rôle", value: "role", sortable: true },
  { text: "Inscrit le", value: "date_inscription", sortable: true },
  { text: "Actions", value: "actions", align: 'end' },
];

const fetchUsers = async () => {
  isLoading.value = true;
  try {
    const response = await api.getAllUsers();
    users.value = response.data;
  } finally { isLoading.value = false; }
};

onMounted(fetchUsers);

// Propriété calculée pour les statistiques des cartes KPI
const userStats = computed(() => {
    const total = users.value.length;
    const recruiters = users.value.filter(u => u.role === 'recruteur').length;
    const candidates = users.value.filter(u => u.role === 'candidat').length;
    return { total, recruiters, candidates };
});

const openModalForCreate = () => {
  selectedUser.value = null;
  Modal.getOrCreateInstance(document.getElementById('userModal')).show();
};
const openModalForEdit = (user) => {
  selectedUser.value = user;
  Modal.getOrCreateInstance(document.getElementById('userModal')).show();
};

const handleSave = async (userData) => {
  const dataToSave = { ...userData };
  if (!dataToSave.password) delete dataToSave.password;

  try {
    if (dataToSave.id) {
      await api.updateUser(dataToSave.id, dataToSave);
    } else {
      await api.createUser(dataToSave);
    }
    await fetchUsers();
  } catch(err) {
    console.error("Erreur de sauvegarde:", err);
    alert("Une erreur est survenue.");
  }
};

const handleDelete = async (user) => {
  if (confirm(`Supprimer l'utilisateur ${user.nom} ? Cette action est irréversible.`)) {
    try {
      await api.deleteUser(user.id);
      await fetchUsers();
    } catch(err) {
      console.error("Erreur de suppression:", err);
      alert("Une erreur est survenue.");
    }
  }
};

const isCurrentUser = (userId) => authStore.user?.user_id === userId;
const roleBadge = (role) => {
  if (role === 'admin') return 'bg-danger';
  if (role === 'recruteur') return 'bg-info text-dark';
  return 'bg-secondary';
};
</script>

<style>
/* Style global pour la DataTable */
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
</style>
