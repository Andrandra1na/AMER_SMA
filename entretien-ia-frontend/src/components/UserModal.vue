<template>
  <div class="modal fade" :id="modalId" tabindex="-1" aria-hidden="true" ref="modalElement">
    <div class="modal-dialog">
      <div class="modal-content">
        <form @submit.prevent="submitForm">
          <div class="modal-header"><h5 class="modal-title">{{ isEditing ? 'Modifier l\'Utilisateur' : 'Créer un Utilisateur' }}</h5><button type="button" class="btn-close" @click="closeModal"></button></div>
          <div class="modal-body">
            <div class="mb-3"><label for="nom" class="form-label">Nom Complet</label><input type="text" id="nom" class="form-control" v-model="editableUser.nom" required></div>
            <div class="mb-3"><label for="email" class="form-label">Email</label><input type="email" id="email" class="form-control" v-model="editableUser.email" required></div>
            <div class="mb-3"><label for="role" class="form-label">Rôle</label><select id="role" class="form-select" v-model="editableUser.role" required><option value="candidat">Candidat</option><option value="recruteur">Recruteur</option><option value="admin">Admin</option></select></div>
            <div class="mb-3">
              <label for="password" class="form-label">{{ isEditing ? 'Nouveau Mot de Passe (laisser vide pour ne pas changer)' : 'Mot de Passe Temporaire' }}</label>
              <input type="password" id="password" class="form-control" v-model="editableUser.password" :required="!isEditing">
            </div>
          </div>
          <div class="modal-footer"><button type="button" class="btn btn-secondary" @click="closeModal">Annuler</button><button type="submit" class="btn btn-primary">{{ isEditing ? 'Enregistrer' : 'Créer' }}</button></div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { Modal } from 'bootstrap';

const props = defineProps({ user: Object, modalId: { type: String, default: 'userModal' } });
const emit = defineEmits(['userSaved']);

const modalElement = ref(null);
let modalInstance = null;
const editableUser = ref({});

const isEditing = computed(() => !!editableUser.value.id);

watch(() => props.user, (newUser) => {
  if (newUser) {
    editableUser.value = { ...newUser, password: '' }; // On ne pré-remplit jamais le mot de passe
  } else {
    editableUser.value = { nom: '', email: '', role: 'candidat', password: '' };
  }
}, { immediate: true });

onMounted(() => { modalInstance = new Modal(modalElement.value); });
const closeModal = () => modalInstance.hide();
const submitForm = () => {
  emit('userSaved', editableUser.value);
  closeModal();
};
</script>