<template>
  <div class="modal fade" :id="modalId" tabindex="-1" aria-hidden="true" ref="modalElement">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <form @submit.prevent="submitForm">
          <div class="modal-header">
            <h5 class="modal-title">{{ isEditing ? 'Modifier la Question' : 'Nouvelle Question' }}</h5>
            <button type="button" class="btn-close" @click="closeModal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Intitulé<span class="text-danger">*</span></label>
              <textarea class="form-control" v-model="editableQuestion.intitule" rows="3" required></textarea>
            </div>
            <div class="row g-3">
              <div class="col-md-6"><label class="form-label">Catégorie<span class="text-danger">*</span></label><input type="text" class="form-control" v-model="editableQuestion.category" required></div>
              <div class="col-md-6"><label class="form-label">Phase de l'entretien</label><input type="text" class="form-control" v-model="editableQuestion.phase"></div>
              <div class="col-md-6"><label class="form-label">Poste Ciblé (optionnel)</label><input type="text" class="form-control" v-model="editableQuestion.role_target"></div>
              <div class="col-md-6"><label class="form-label">Niveau d'Expérience</label><input type="text" class="form-control" v-model="editableQuestion.experience_level"></div>
              <div class="col-md-6"><label class="form-label">Difficulté</label><select class="form-select" v-model="editableQuestion.difficulty"><option>Facile</option><option>Moyenne</option><option>Difficile</option></select></div>
              <div class="col-md-6"><label class="form-label">Type (STAR, etc.)</label><input type="text" class="form-control" v-model="editableQuestion.source_type"></div>
            </div>
            <div class="mb-3 mt-3">
              <label class="form-label">Réponse Idéale (pour l'IA)</label>
              <textarea class="form-control" v-model="editableQuestion.ideal_answer" rows="3"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Mots-clés (séparés par des virgules)</label>
              <input type="text" class="form-control" :value="keywordsString" @input="updateKeywords">
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">Annuler</button>
            <button type="submit" class="btn btn-primary">{{ isEditing ? 'Enregistrer' : 'Créer' }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { Modal } from 'bootstrap';

const props = defineProps({
  question: Object,
  modalId: { type: String, default: 'questionModal' }
});
const emit = defineEmits(['questionSaved']);

const modalElement = ref(null);
let modalInstance = null;

const createEmptyQuestion = () => ({
  id: null, intitule: '', category: '', phase: '', role_target: '',
  experience_level: '', difficulty: 'Moyenne', source_type: '',
  ideal_answer: '', keywords: []
});

const editableQuestion = ref(createEmptyQuestion());
const isEditing = computed(() => !!editableQuestion.value.id);

// Gère l'affichage des mots-clés dans l'input
const keywordsString = computed(() => (editableQuestion.value.keywords || []).join(', '));
const updateKeywords = (event) => {
  editableQuestion.value.keywords = event.target.value.split(',').map(k => k.trim()).filter(k => k);
};

watch(() => props.question, (newQuestion) => {
  editableQuestion.value = newQuestion ? { ...createEmptyQuestion(), ...newQuestion } : createEmptyQuestion();
}, { immediate: true, deep: true });

onMounted(() => { modalInstance = new Modal(modalElement.value); });
const closeModal = () => modalInstance.hide();
const submitForm = () => {
  emit('questionSaved', editableQuestion.value);
  closeModal();
};
</script>
