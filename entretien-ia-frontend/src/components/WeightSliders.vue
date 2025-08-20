<template>
  <div>
    <!-- On boucle sur les clés de l'objet 'weights' pour créer un slider pour chaque critère -->
    <div v-for="(label, key) in weightLabels" :key="key" class="mb-3">

      <label :for="key" class="form-label d-flex justify-content-between">
        <span>{{ label }}</span>
        <strong>{{ weights[key]?.toFixed(0) }} %</strong>
      </label>

      <input
        type="range"
        class="form-range"
        :id="key"
        min="0"
        max="100"
        step="1"
        :value="weights[key]"
        @input="emitUpdate(key, $event.target.value)"
      >
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  weights: {
    type: Object,
    required: true
  }
});

// Le composant va émettre un événement 'update' vers son parent
const emit = defineEmits(['update']);

const weightLabels = ref({
  relevance: 'Pertinence Sémantique',
  clarity: 'Clarté (Grammaire)',
  fluency: 'Fluidité (Voix)',
  engagement: 'Engagement (Émotion)'
});


/**
 * Fonction appelée à chaque fois qu'un slider est bougé.
 * Elle n'effectue aucun calcul, elle prévient simplement le parent.
 * @param {string} key - La clé du poids qui a changé (ex: 'relevance').
 * @param {string} value - La nouvelle valeur du slider (sous forme de chaîne).
 */
const emitUpdate = (key, value) => {
  // On émet un objet contenant la clé modifiée et sa nouvelle valeur numérique.
  // Le composant parent (ConfigIAView) se chargera de la logique de rééquilibrage.
  emit('update', { key, value: Number(value) });
};
</script>

