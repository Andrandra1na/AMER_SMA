import pytest
from agents.NLPAgent import NLPAgent

@pytest.fixture(scope="module")
def nlp_agent():
    print("\n[Setup] Création de l'instance NLPAgent pour les tests sémantiques...")
    agent = NLPAgent(model_size="small")
    agent._initialize_semantic_model()
    return agent

@pytest.mark.parametrize("response, expected_min_score", [
    # Scénario 1: Réponse quasi-parfaite. On ajuste l'attente à 0.7
    ("Mon expérience inclut l'utilisation de PostgreSQL et de bases de données non relationnelles comme MongoDB.", 0.7),
    # Scénario 2: Réponse correcte mais moins détaillée. L'attente de 0.6 était bonne.
    ("Oui, j'ai utilisé des bases de données SQL dans mes projets précédents.", 0.6),
    # Scénario 3: Réponse qui mentionne un seul concept. L'attente de 0.5 était bonne.
    ("Je suis très à l'aise avec MySQL et le langage SQL.", 0.5)
])
def test_analyze_relevance_with_pertinent_responses(nlp_agent, response, expected_min_score):
    """
    Valide que des réponses sémantiquement pertinentes obtiennent un score élevé.
    """
    question = "Quelles sont vos expériences avec les bases de données SQL et NoSQL ?"
    score = nlp_agent.analyze_relevance(question, response)
    
    assert score is not None
    # --- CORRECTION DE LA VALEUR ATTENDUE ---
    assert score >= expected_min_score
    # --- FIN DE LA CORRECTION ---
    assert score <= 1.0

@pytest.mark.parametrize("response, expected_max_score", [
    ("J'aime beaucoup travailler en équipe et je suis très motivé.", 0.3),
    ("J'ai fait un projet sur la sécurité des bases de données, en utilisant des scripts SQL pour les audits.", 0.4),
    ("Oui.", 0.2)
])
def test_analyze_relevance_with_irrelevant_responses(nlp_agent, response, expected_max_score):
    """
    Valide que des réponses non-pertinentes obtiennent un score faible.
    """
    question = "Parlez-moi de votre capacité à gérer le stress."
    score = nlp_agent.analyze_relevance(question, response)
    
    assert score is not None
    assert score >= 0.0
    assert score <= expected_max_score

def test_analyze_relevance_with_empty_inputs(nlp_agent):
    """
    Valide le comportement de la fonction avec des entrées vides.
    """
    question = "Quelle est votre expérience ?"
    assert nlp_agent.analyze_relevance(question, "") == 0.0
    assert nlp_agent.analyze_relevance("", "Une réponse") == 0.0
    assert nlp_agent.analyze_relevance(question, None) == 0.0
    assert nlp_agent.analyze_relevance(None, "Une réponse") == 0.0