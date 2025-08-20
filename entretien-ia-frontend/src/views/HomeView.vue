<template>
  <div class="homepage">
    <!-- ======================================= -->
    <!-- SECTION 1 : HÉROS (ACCROCHE PRINCIPALE) -->
    <!-- ======================================= -->
    <section class="hero-section">
      <div class="container col-xxl-8 px-4 py-5">
        <div class="row align-items-center g-5 py-5">
          <div class="col-lg-6 text-center text-lg-start">
            <h1 class="display-4 fw-bold lh-1 mb-4 animate__animated animate__fadeInLeft">L'Intelligence Artificielle au service de vos recrutements</h1>
            <p class="lead text-muted mb-4 animate__animated animate__fadeInLeft animate__delay-1s">
              Allez au-delà du CV. Notre plateforme analyse la communication verbale, vocale et émotionnelle pour vous aider à identifier les meilleurs talents, sans biais.
            </p>
            <div class="d-grid gap-3 d-sm-flex justify-content-center justify-content-lg-start animate__animated animate__fadeInUp animate__delay-2s">
              <router-link to="/register" class="btn btn-primary btn-lg shadow-sm px-4 me-sm-3">Commencer une évaluation</router-link>
              <router-link to="/login" class="btn btn-outline-secondary btn-lg px-4">J'ai déjà un compte</router-link>
            </div>
          </div>
          <div class="col-10 col-sm-8 col-lg-6">
            <img src="../assets/jb1.png" class="d-block mx-lg-auto img-fluid animate__animated animate__zoomIn" alt="Illustration Analyse IA" loading="lazy">
          </div>
        </div>
      </div>
    </section>

    <!-- ======================================= -->
    <!-- SECTION 2 : COMMENT ÇA MARCHE ?       -->
    <!-- ======================================= -->
    <section class="how-it-works-section py-5">
      <div class="container px-4 py-5 text-center">
        <h2 class="display-5 fw-bold mb-3">Un processus simple et puissant</h2>
        <p class="lead text-muted col-lg-8 mx-auto mb-5">En trois étapes, transformez vos entretiens en données objectives.</p>
        <div class="row g-4">
          <div class="col-md-4"><div class="step-card"><div class="step-icon"><i class="bi bi-camera-reels-fill"></i></div><h3>1. Enregistrez</h3><p>Le candidat passe son entretien vidéo en répondant à une série de questions prédéfinies.</p></div></div>
          <div class="col-md-4"><div class="step-card"><div class="step-icon"><i class="bi bi-robot"></i></div><h3>2. Analysez</h3><p>Notre IA multimodale traite la vidéo pour évaluer la pertinence, la clarté et l'engagement.</p></div></div>
          <div class="col-md-4"><div class="step-card"><div class="step-icon"><i class="bi bi-file-earmark-text-fill"></i></div><h3>3. Décidez</h3><p>Recevez un rapport complet et objectif pour prendre des décisions de recrutement éclairées.</p></div></div>
        </div>
      </div>
    </section>

    <!-- ======================================= -->
    <!-- SECTION 3: ANALYSE À 360° (maintenant en 4ème, avec un nouveau design) -->
    <!-- ======================================= -->
    <section class="features-section py-5 bg-white">
      <div class="container px-4 py-5">
        <div class="row align-items-center">
          <div class="col-lg-6">
            <h2 class="fw-bold display-5 mb-3">Une Analyse Multimodale Complète</h2>
            <p class="lead text-muted mb-4">
              Notre IA ne se contente pas d'écouter les mots. Elle analyse la manière dont ils sont dits,
              le contexte dans lequel ils sont utilisés et l'émotion qui les accompagne pour une vision
              d'ensemble unique.
            </p>
            <div class="row g-4">
              <!-- Feature 1 -->
              <div class="col-md-6"><div class="feature-item"><i class="bi bi-chat-left-quote-fill"></i><div><h5>Analyse Sémantique</h5><p class="small text-muted mb-0">Évalue la pertinence des réponses.</p></div></div></div>
              <!-- Feature 2 -->
              <div class="col-md-6"><div class="feature-item"><i class="bi bi-spellcheck"></i><div><h5>Analyse de la Clarté</h5><p class="small text-muted mb-0">Mesure la qualité de la grammaire.</p></div></div></div>
              <!-- Feature 3 -->
              <div class="col-md-6"><div class="feature-item"><i class="bi bi-mic-fill"></i><div><h5>Analyse Vocale</h5><p class="small text-muted mb-0">Détecte le débit, les pauses et le ton.</p></div></div></div>
              <!-- Feature 4 -->
              <div class="col-md-6"><div class="feature-item"><i class="bi bi-emoji-smile-fill"></i><div><h5>Analyse Émotionnelle</h5><p class="small text-muted mb-0">Identifie l'ambiance émotionnelle.</p></div></div></div>
            </div>
          </div>
          <div class="col-lg-6 d-none d-lg-block">
            <!-- On peut utiliser la même image ou une autre plus "technique" -->
            <img src="../assets/jb2.png" class="img-fluid rounded-3" alt="Illustration technique">
          </div>
        </div>
      </div>
    </section>

    <!-- ======================================= -->
    <!-- SECTION 4 : AVANTAGES (votre section)   -->
    <!-- ======================================= -->
    <section class="benefits-section py-5">
        <div class="container px-4 py-5">
            <h2 class="text-center fw-bold display-5 mb-5">Conçu pour tous les acteurs du recrutement</h2>
            <div class="row g-4 py-5 row-cols-1 row-cols-lg-3">
                <div class="col"><div class="benefit-card h-100 p-4"><div class="benefit-icon"><i class="bi bi-person-check-fill"></i></div><h3 class="fs-4 mt-3">Pour les Candidats</h3><p class="text-muted">Mettez en valeur vos compétences au-delà du CV. Recevez une analyse constructive pour mieux comprendre vos points forts.</p></div></div>
                <div class="col"><div class="benefit-card h-100 p-4"><div class="benefit-icon"><i class="bi bi-briefcase-fill"></i></div><h3 class="fs-4 mt-3">Pour les Recruteurs</h3><p class="text-muted">Prenez des décisions éclairées grâce à des données objectives. Réduisez les biais et identifiez les meilleurs talents.</p></div></div>
                <div class="col"><div class="benefit-card h-100 p-4"><div class="benefit-icon"><i class="bi bi-building-fill-check"></i></div><h3 class="fs-4 mt-3">Pour l'Entreprise</h3><p class="text-muted">Standardisez et optimisez votre processus de recrutement. Améliorez la qualité de vos embauches et votre marque employeur.</p></div></div>
            </div>
        </div>
    </section>

    <!-- ======================================= -->
    <!-- SECTION 5 : APPEL À L'ACTION FINAL (CTA) -->
    <!-- ======================================= -->
    <section class="cta-section bg-white text-center py-5">
      <div class="container py-5">
        <h2 class="display-5 fw-bold">Prêt à transformer vos entretiens ?</h2>
        <p class="lead text-muted col-lg-8 mx-auto mt-3">Créez un compte gratuitement et découvrez la puissance de l'analyse IA dès aujourd'hui.</p>
        <router-link to="/register" class="btn btn-primary btn-lg mt-4">Je me lance</router-link>
      </div>
    </section>

  </div>
</template>

<script setup>

</script>

<style scoped>
@import 'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css';

/* Section Héros */
.hero-section {
  background: linear-gradient(180deg, rgba(255,255,255,1) 0%, var(--bg-color) 100%);
}
.hero-section h1 { color: var(--text-dark); }
.hero-section .btn-primary {
  padding: 1rem 2rem;
  font-size: 1.25rem;
}
.hero-section .btn-outline-secondary {
  padding: 1rem 2rem;
  font-size: 1.25rem;
}
.hero-section img {
  border-radius: 1rem;
}

/* Section "Comment ça marche ?" */
.how-it-works-section { background-color: var(--bg-color); }
.step-card {
  background-color: var(--surface-color);
  padding: 2rem;
  border-radius: 1rem;
  border: 1px solid var(--border-color);
  height: 100%;
}
.step-icon {
  width: 70px;
  height: 70px;
  margin: 0 auto 1.5rem auto;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--blue-primary);
  color: white;
  font-size: 2rem;
}

/* Section "Fonctionnalités" */
.feature-card {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.feature-icon {
  color: var(--blue-light);
  font-size: 2rem;
}

.features-section .lead {
  max-width: 80%; /* Pour un texte moins large et plus lisible */
}
.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  border-radius: 0.75rem;
  transition: background-color 0.3s ease;
}
.feature-item:hover {
  background-color: var(--bg-color);
}
.feature-item i {
  font-size: 1.75rem;
  color: var(--blue-light);
  margin-top: 5px; /* Pour un meilleur alignement vertical */
}
.feature-item h5 {
  font-weight: 600;
  color: var(--text-dark);
  margin-bottom: 0.25rem;
}

/* Section "Avantages" */
.benefits-section { background-color: var(--bg-color); }
.benefit-card {
  background-color: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: 1rem;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  text-align: center;
}
.benefit-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 1rem 3rem rgba(0,0,0,.1) !important;
}
.benefit-icon {
  width: 70px;
  height: 70px;
  margin: 0 auto 1.5rem auto;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--green-validation);
  color: var(--blue-primary);
  font-size: 2rem;
}
.benefit-card h3 { color: var(--text-dark); }

/* Section CTA */
.cta-section .btn-primary {
  padding: 1rem 2.5rem;
  font-size: 1.25rem;
}
</style>
