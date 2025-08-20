import pytest
from agents.AudioAgent import AudioAgent

# On peut utiliser pytest.mark.parametrize pour tester plusieurs scénarios
# avec une seule fonction de test. C'est une pratique avancée et très propre.
@pytest.mark.parametrize("speech_duration, total_duration, pause_count, avg_pause, expected_score", [
    # Scénario 1 : Candidat parfait (parle 90% du temps, 2 courtes pauses)
    (54, 60, 2, 0.6, pytest.approx(84.0)), # Score base 90 - (2*1.5) - (0.6*5) = 90 - 3 - 3 = 84
    
    # Scénario 2 : Candidat hésitant (parle 60% du temps, 10 pauses longues)
    (36, 60, 10, 2.0, pytest.approx(35.0)), # Score base 60 - (10*1.5) - (2.0*5) = 60 - 15 - 10 = 35
    
    # Scénario 3 : Candidat très rapide mais haché (parle 95% du temps, mais 20 pauses)
    (57, 60, 20, 0.5, pytest.approx(67.5)), # Score base 95 - (20*1.5=30, mais plafonné à 25) - (0.5*5) = 95 - 25 - 2.5 = 67.5
    
    # Scénario 4 : Cas limite, beaucoup de silence
    (10, 60, 2, 5.0, pytest.approx(0.0)) # Score base 16.6 - (2*1.5) - (5.0*5=25, plafonné à 25) -> négatif, donc 0
])
def test_calculate_fluency_score(speech_duration, total_duration, pause_count, avg_pause, expected_score):
    """
    TEST UNITAIRE : Valide la formule de calcul du score de fluidité
    pour différents profils de candidats.
    """
    # 1. Arrange
    agent = AudioAgent()
    
    # 2. Act
    score = agent._calculate_fluency_score(speech_duration, total_duration, pause_count, avg_pause)
    
    # 3. Assert
    assert score == expected_score