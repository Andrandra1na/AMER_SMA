<template>
  <Radar :data="chartData" :options="chartOptions" />
</template>

<script setup>
import { computed } from 'vue';
import { Radar } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, PointElement, RadialLinearScale, LineElement, Filler } from 'chart.js';

ChartJS.register(Title, Tooltip, Legend, PointElement, RadialLinearScale, LineElement, Filler);

const props = defineProps({
  scores: {
    type: Object,
    required: true,
    default: () => ({})
  }
});


const normalizeRelevance = (score) => (score || 0) * 100;
const normalizeGrammar = (score) => (score || 0) * 100;

const normalizeSpeechRate = (rate) => {
  if (!rate) return 0;
  const ideal = 150, range = 30; // Idéal entre 120 et 180 mots/min
  const diff = Math.abs(rate - ideal);
  return Math.max(0, 100 - (diff / range) * 100);
};

const normalizePauseCount = (count) => {
  if (count === null || count === undefined) return 0;
  // Moins il y a de pauses, meilleur est le score (jusqu'à une certaine limite)
  if (count <= 4) return 100;
  if (count > 12) return 0;
  return 100 - ((count - 4) * 12.5);
};

const chartData = computed(() => ({
  labels: [
    ['Pertinence', 'des Réponses'],
    ['Clarté', '(Grammaire)'],
    ['Dynamisme', '(Débit vocal)'],
    ['Fluidité', '(Gestion des Pauses)'],
  ],
  datasets: [{
    label: 'Performance du Candidat',
    backgroundColor: 'rgba(0, 95, 115, 0.2)',
    borderColor: 'rgba(0, 95, 115, 1)',
    pointBackgroundColor: 'rgba(0, 95, 115, 1)',
    pointBorderColor: '#fff',
    pointHoverBackgroundColor: '#fff',
    pointHoverBorderColor: 'rgba(0, 95, 115, 1)',
    borderWidth: 2,
    data: [
      normalizeRelevance(props.scores.relevance_avg),
      normalizeGrammar(props.scores.grammar_avg),
      normalizeSpeechRate(props.scores.speech_rate),
      normalizePauseCount(props.scores.pause_count),
    ],
  }],
}));

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    r: {
      angleLines: { color: 'rgba(0, 0, 0, 0.1)' },
      grid: { color: 'rgba(0, 0, 0, 0.1)' },
      pointLabels: {
        font: { size: 13, family: 'Poppins', weight: '500' },
        color: '#495057' 
      },
      ticks: {
        backdropColor: '#ffffff',
        color: '#6c757d',
        stepSize: 25,
      },
      suggestedMin: 0,
      suggestedMax: 100,
    },
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (context) => {
            if (context.raw !== null && context.raw !== undefined) {
                return `${context.dataset.label}: ${context.raw.toFixed(0)} / 100`;
            }
            return '';
        }
      }
    }
  },
}));
</script>
