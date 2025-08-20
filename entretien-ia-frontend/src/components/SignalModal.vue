<template>
  <div class="modal fade" :id="modalId" tabindex="-1" aria-hidden="true" ref="modalElement">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Gérer le Signalement</h5>
          <button type="button" class="btn-close" @click="closeModal" aria-label="Close"></button>
        </div>
        <div class="modal-body" v-if="question">
          <p><strong>Question :</strong> "{{ question.intitule }}"</p>
          <div class="form-check form-switch mb-3">
            <input class="form-check-input" type="checkbox" role="switch" id="signalementSwitch" v-model="isSignaled">
            <label class="form-check-label" for="signalementSwitch">
              <strong>{{ isSignaled ? 'Question Signalée' : 'Question Conforme' }}</strong>
            </label>
          </div>
          <div v-if="isSignaled">
            <label for="commentaireAdmin" class="form-label">Raison du signalement (optionnel)</label>
            <textarea id="commentaireAdmin" class="form-control" v-model="commentaire" rows="3"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="closeModal">Annuler</button>
          <button type="button" class="btn btn-primary" @click="submitSignalement">Enregistrer</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { Modal } from 'bootstrap';

const props = defineProps({ question: Object, modalId: { type: String, default: 'signalModal' } });
const emit = defineEmits(['signalSaved']);
const modalElement = ref(null);
let modalInstance = null;

const isSignaled = ref(false);
const commentaire = ref('');

watch(() => props.question, (newQuestion) => {
  if (newQuestion) {
    isSignaled.value = newQuestion.signalement_admin || false;
    commentaire.value = newQuestion.commentaire_admin || '';
  }
});

onMounted(() => { modalInstance = new Modal(modalElement.value); });
const closeModal = () => modalInstance.hide();

const submitSignalement = () => {
  emit('signalSaved', {
    questionId: props.question.id,
    signalement: isSignaled.value,
    commentaire: commentaire.value
  });
  closeModal();
};
</script>
