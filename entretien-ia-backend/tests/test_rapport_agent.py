from agents.RapportAgent import RapportAgent

def test_calculate_global_score_perfect(db_session, sample_session):
    """
    TEST UNITAIRE : Vérifie que le RapportAgent calcule correctement un score parfait.
    
    'db_session' et 'sample_session' sont les fixtures fournies par conftest.py.
    """
    # 1. Arrange (Arranger)
    # On crée une instance de l'agent
    rapport_agent = RapportAgent()
    
    # On crée des données d'analyse "parfaites" simulées
    perfect_analysis_results = {
        'answers_analysis': [
            {'score_pertinence': 1.0, 'score_grammaire': 1.0},
            {'score_pertinence': 1.0, 'score_grammaire': 1.0}
        ],
        'vocal_analysis': { 'fluency_score': 100.0 },
        'emotion_analysis': { 'scores': {'calme': 0.5, 'heureux': 0.5} } # Engagement maximal
    }
    
    # 2. Act (Agir)
    # On appelle la fonction à tester
    final_score = rapport_agent.calculate_global_score(sample_session.id, perfect_analysis_results)
    
    # 3. Assert (Affirmer)
    # On affirme que le résultat est bien 100.0
    # Le profil de test a une pondération de 50+30+10+10 = 100
    # Donc (100 * 0.5) + (100 * 0.3) + (100 * 0.1) + (100 * 0.1) = 100
    assert final_score == 100.0

def test_calculate_global_score_mixed(db_session, sample_session):
    """
    TEST UNITAIRE : Vérifie un calcul avec des scores moyens.
    """
    # 1. Arrange
    rapport_agent = RapportAgent()
    mixed_analysis_results = {
        'answers_analysis': [
            {'score_pertinence': 0.7, 'score_grammaire': 0.8},
        ],
        'vocal_analysis': { 'fluency_score': 60.0 },
        'emotion_analysis': { 'scores': {'calme': 0.5, 'peur': 0.5} } # Engagement à 50%
    }
    
    # 2. Act
    final_score = rapport_agent.calculate_global_score(sample_session.id, mixed_analysis_results)
    
    # 3. Assert
    # Le calcul attendu est : (70 * 0.5) + (80 * 0.3) + (60 * 0.1) + (50 * 0.1) = 35 + 24 + 6 + 5 = 70.0
    # On utilise pytest.approx pour gérer les imprécisions des nombres à virgule flottante.
    import pytest
    assert final_score == pytest.approx(70.0)