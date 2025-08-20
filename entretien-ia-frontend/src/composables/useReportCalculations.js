import { computed } from 'vue';
import { useAuthStore } from '@/stores/auth';

/**
 * Hook Composable pour tous les calculs et interprétations du rapport.
 * C'est le "cerveau" de l'affichage des rapports.
 * @param {import('vue').Ref<object|null>} report - Référence réactive au rapport brut de l'API.
 */
export function useReportCalculations(report) {
    const answers = computed(() => report.value?.detailed_answers || []);
    const vocal = computed(() => report.value?.vocal_analysis || {});
    const globalScoresAPI = computed(() => report.value?.global_scores || {});
    const emotion = computed(() => report.value?.emotion_scores || {});
    const gaze = computed(() => report.value?.gaze_analysis || {});

    // --- 2. LA NOTE OFFICIELLE (SOURCE UNIQUE DE VÉRITÉ) ---
    const globalScore = computed(() => {
        // On lit directement la note calculée et pondérée par le backend.
        return Math.round(globalScoresAPI.value.note_globale || 0);
    });

    // --- 3. CALCULS DE MOYENNES (pour affichage) ---
    const averageRelevance = computed(() => {
        const scoredAnswers = answers.value.filter(a => a.score_pertinence !== null && a.score_pertinence !== undefined);
        if (scoredAnswers.length === 0) return 0;
        return scoredAnswers.reduce((sum, a) => sum + a.score_pertinence, 0) / scoredAnswers.length;
    });
    const averageGrammar = computed(() => globalScoresAPI.value.grammar_avg || 0);

    // --- 4. INTERPRÉTATIONS QUALITATIVES (basées sur les scores) ---

    const qualification = computed(() => {
        const score = globalScore.value;
        if (score >= 80) return { title: "Profil Très Prometteur", text: "Le candidat démontre d'excellentes compétences et une forte adéquation.", icon: "bi bi-award-fill", bgClass: "bg-success-subtle text-success-emphasis" };
        if (score >= 60) return { title: "Profil Solide à Considérer", text: "Le candidat possède de bonnes bases. Points à approfondir en entretien.", icon: "bi bi-hand-thumbs-up-fill", bgClass: "bg-info-subtle text-info-emphasis" };
        return { title: "Analyse Manuelle Requise", text: "Des points de vigilance ont été détectés. Une analyse détaillée est recommandée.", icon: "bi bi-search", bgClass: "bg-warning-subtle text-warning-emphasis" };
    });

    const finalVerdictForCandidate = computed(() => {
        const score = globalScore.value; // On se base sur le score de 0 à 100
        if (score >= 80) return { title: "Entretien Exceptionnel !", text: "Excellente prestation ! Vos compétences et votre communication correspondent parfaitement à nos attentes.", icon: "bi bi-award-fill", bgClass: "bg-success-subtle text-success-emphasis" };
        if (score >= 60) return { title: "Profil Prometteur", text: "Votre performance est solide et sera étudiée avec attention par nos recruteurs.", icon: "bi bi-hand-thumbs-up-fill", bgClass: "bg-info-subtle text-info-emphasis" };
        if (score >= 40) return { title: "Performance Intéressante", text: "Merci pour votre temps. Cette session a mis en lumière des points forts et des axes de progression.", icon: "bi bi-lightbulb-fill", bgClass: "bg-warning-subtle text-warning-emphasis" };
        return { title: "Axes d'Amélioration Identifiés", text: "Cette évaluation est une opportunité pour identifier des points à développer pour vos prochains entretiens.", icon: "bi bi-graph-up-arrow", bgClass: "bg-secondary-subtle text-secondary-emphasis" };
    });

    // Profil comportemental
    const communicationProfile = computed(() => {
        if (!report.value) return { title: "Analyse en attente", description: "Les données sont insuffisantes.", icon: "bi bi-question-circle-fill" };
        const relevance = averageRelevance.value;
        const grammar = averageGrammar.value;
        const speechRate = vocal.value.speech_rate || 0;
        const dominantEmotion = emotion.value.dominant_emotion;

        if (relevance >= 0.75 && grammar >= 0.8 && speechRate < 145 && ['calme', 'neutre'].includes(dominantEmotion)) return { title: "Profil : Analytique & Précis", description: "Discours méthodique, structuré et factuel.", icon: "bi bi-compass" };
        if (relevance >= 0.6 && speechRate > 155 && ['heureux', 'surpris'].includes(dominantEmotion)) return { title: "Profil : Dynamique & Persuasif", description: "Communication énergique et engageante.", icon: "bi bi-megaphone-fill" };
        return { title: "Profil : Communicant Équilibré", description: "Le style de communication est équilibré.", icon: "bi bi-people-fill" };
    });

    const bestAnswer = computed(() => {
        if (answers.value.length === 0) return { question_intitule: 'N/A' };
        return answers.value.reduce((best, current) => {
            const bestScore = (best.score_pertinence || 0) + (best.score_grammaire || 0);
            const currentScore = (current.score_pertinence || 0) + (current.score_grammaire || 0);
            return currentScore > bestScore ? current : best;
        });
    });

    const competenceScores = computed(() => {
        if (!report.value) return { relevance: 0, clarity: 0, engagement: 0 };

        // Pertinence : 0.6 = 3/5, 0.8 = 4/5
        const relevanceNote = Math.max(1, Math.ceil((averageRelevance.value || 0) * 5));

        // Clarté & Fluidité : On combine grammaire et fluidité vocale
        const grammarScore100 = (averageGrammar.value || 0) * 100;
        const fluencyScore100 = (vocal.value.fluency_score || 0);
        const clarityNote = Math.max(1, Math.ceil(((grammarScore100 * 0.7) + (fluencyScore100 * 0.3)) / 100 * 5));

        // Engagement : basé sur les émotions positives
        let engagementScore = 0.5; // Base neutre
        if (emotion.value && emotion.value.scores) {
            engagementScore = (emotion.value.scores.heureux || 0) + (emotion.value.scores.calme || 0);
        }
        const engagementNote = Math.max(1, Math.ceil(engagementScore * 5));

        return { relevance: relevanceNote, clarity: clarityNote, engagement: engagementNote };
    });

    // --- NOUVEAU : CONSEIL PERSONNALISÉ BASÉ SUR LE RAG ---
    const ragImprovementTip = computed(() => {
        // On cherche la PREMIÈRE réponse qui a été analysée par RAG et qui a un score faible.
        const weakRagAnswer = answers.value.find(
            a => a.pertinence_explication && a.score_pertinence < 0.7
        );

        if (weakRagAnswer) {
            return {
                title: "Améliorer la Précision",
                text: `Pour la question "${weakRagAnswer.question_intitule}", l'IA a noté des imprécisions. Pensez à bien réviser les informations clés sur l'entreprise (valeurs, produits) avant un entretien.`,
                icon: "bi bi-bullseye"
            };
        }

        return null;
    });

    const improvementTip = computed(() => {
        const ragTip = ragImprovementTip.value;
        if (ragTip) return ragTip;

         // Sinon, on utilise l'ancienne logique basée sur le score le plus faible.
        const scores = competenceScores.value;
        if (!scores || !scores.relevance) return { title: "Continuez !", text: "Continuez à vous entraîner pour parfaire votre communication !", icon: "bi bi-graph-up-arrow"};

        const minScore = Math.min(scores.relevance, scores.clarity, scores.engagement);
        if (minScore === scores.relevance) return { title: "Conseil : Pertinence", text: "Pour être plus percutant, essayez de structurer vos réponses en utilisant des exemples concrets (méthode STAR).", icon: "bi bi-bullseye"};
        if (minScore === scores.clarity) return { title: "Conseil : Fluidité", text: "Pour rendre votre discours plus fluide, n'hésitez pas à marquer de courtes pauses pour bien articuler vos phrases.", icon: "bi bi-mic-fill"};
        if (minScore === scores.engagement) return { title: "Conseil : Engagement", text: "Exprimez vos idées avec plus de variations dans le ton de votre voix pour captiver votre auditoire.", icon: "bi bi-emoji-smile-fill"};

        return { title: "Excellent !", text: "Votre communication est très équilibrée, continuez comme ça !", icon: "bi bi-star-fill"};
    });

    const interpretedSpeechRate = computed(() => {
        const rate = vocal.value.speech_rate;
        if (rate > 170) return { text: 'un débit de parole rapide et dynamique' };
        if (rate >= 130) return { text: 'un débit de parole confiant et posé' };
        return { text: 'un débit de parole lent et réfléchi', isFlag: rate < 110 };
    });

    const redFlags = computed(() => {
        const flags = [];
        if (averageRelevance.value < 0.4) flags.push("La pertinence globale des réponses est très faible.");
        if (averageGrammar.value < 0.6) flags.push("La clarté du discours est significativement faible.");
        if (interpretedSpeechRate.value.isFlag) flags.push("Le débit de parole est extrêmement lent.");
        if ((vocal.value.pause_count || 0) > 10) flags.push("Le discours est très haché (nombreuses pauses).");
        return flags;
    });

    const aiSummary = computed(() => {
        if(!report.value) return "";
        const p_score_percent = (averageRelevance.value * 100).toFixed(0);
        const g_score_percent = (averageGrammar.value * 100).toFixed(0);

        let summary = `Le candidat démontre une pertinence moyenne de ${p_score_percent}% et une clarté de ${g_score_percent}%. `;
        summary += `Son élocution se caractérise par ${interpretedSpeechRate.value.text}. `;
        summary += redFlags.value.length > 0 ? "Des points de vigilance ont été notés. " : "Aucun point de friction majeur n'a été identifié. ";
        summary += "Recommandation : " + qualification.value.title + ".";
        return summary;
    });

    const globalGazeContact = computed(() => {
        // Retourne le pourcentage global de contact visuel
        return gaze.value.global_distribution?.['Contact Visuel'] || 0;
    });

    const gazeByQuestionChartData = computed(() => {
        if (!report.value || !gaze.value.by_question) return null;

        const labels = [];
        const contactData = [];
        const lectureData = [];
        const observationData = [];
        const distractionData = [];

        // On itère sur les réponses détaillées pour avoir l'ordre et le texte des questions
        for (const [index, answer] of (report.value.detailed_answers || []).entries()) {
            const questionId = String(answer.question_id);
            labels.push(`Q${index + 1}`);

            const gazeForQuestion = gaze.value.by_question[questionId] || {};
            contactData.push(gazeForQuestion['Contact Visuel'] || 0);
            lectureData.push(gazeForQuestion['Lecture'] || 0);
            observationData.push(gazeForQuestion['Auto-observation'] || 0);
            distractionData.push(gazeForQuestion['Distraction'] || 0);
        }

        if (labels.length === 0) return null;

        return {
        labels,
        datasets: [
            {
                label: 'Contact Visuel',
                data: contactData,
                backgroundColor: 'rgba(0, 95, 115, 0.8)' // Bleu Primaire (positif)
            },
            {
                label: 'Lecture Question',
                data: lectureData,
                backgroundColor: 'rgba(10, 147, 150, 0.6)' // Cyan (neutre-positif)
            },
            {
                label: 'Auto-observation',
                data: observationData,
                backgroundColor: 'rgba(173, 181, 189, 0.7)' // Gris (neutre)
            },
            {
                label: 'Distraction',
                data: distractionData,
                backgroundColor: 'rgba(255, 193, 7, 0.6)' // Orange/Jaune (avertissement)
            }
        ]
    };
    });


    // --- 5. EXPORT DE TOUTES LES DONNÉES NÉCESSAIRES POUR LES VUES ---
    return {
        globalScore,
        qualification,
        finalVerdictForCandidate,

        competenceScores,
        improvementTip,
        redFlags,
        aiSummary,

        chartScores: computed(() => ({
            relevance_avg: averageRelevance.value,
            grammar_avg: averageGrammar.value,
            speech_rate: vocal.value.speech_rate,
            pause_count: vocal.value.pause_count,
        })),

        formattedScores: computed(() => ({
            relevance: (averageRelevance.value * 100).toFixed(0),
            grammar: (averageGrammar.value * 100).toFixed(0),
        })),

        communicationProfile,
        bestAnswer,

        globalScoreStyle: computed(() => ({ '--score': globalScore.value })),
        globalScoreText: computed(() => {
            const score = globalScore.value;
            if (score >= 80) return "Excellente performance";
            if (score >= 60) return "Bonne performance";
            return "Performance à améliorer";
        }),
        globalScoreColor: computed(() => {
            const score = globalScore.value;
            if (score >= 80) return 'var(--success-color)';
            if (score >= 60) return 'var(--blue-light)';
            return 'var(--danger-color)';
        }),

        videoUrl: computed(() => {
            const authStore = useAuthStore();
            const path_from_db = report.value?.session_info?.video_path;
            if (path_from_db && authStore.token) {
                return `http://localhost:5000/media/${path_from_db}?jwt=${authStore.token}`;
            }
            return '';
        }),
        globalGazeContact,
        gazeByQuestionChartData
    };
}
