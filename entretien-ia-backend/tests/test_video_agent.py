import pytest
from unittest.mock import MagicMock
from agents.VideoAgent import VideoAgent

@pytest.fixture
def video_agent():
    return VideoAgent()

def test_interpret_gaze_direction(video_agent):
    """
    Valide la couche de traduction "métier". (Ce test était déjà correct).
    """
    assert video_agent._interpret_gaze_direction("gauche") == "Auto-observation"
    assert video_agent._interpret_gaze_direction("centre") == "Contact Visuel"
    assert video_agent._interpret_gaze_direction("droite") == "Lecture"
    assert video_agent._interpret_gaze_direction("hors_champ") == "Distraction"

def create_mock_landmarks(face_center_x):
    """
    Fonction d'aide pour créer de fausses données MediaPipe.
    """
    mock_landmark_list = []
    central_points_indices = [1, 4, 5, 8, 9, 10, 151, 152, 199, 234]
    
    for i in range(max(central_points_indices) + 1):
        landmark = MagicMock()
        if i in central_points_indices:
            landmark.x = face_center_x
        else:
            landmark.x = 0.5
        mock_landmark_list.append(landmark)
        
    mock_face = MagicMock()
    mock_face.landmark = mock_landmark_list
    return mock_face

def test_classify_gaze_by_face_center_looks_left(video_agent):
    """
    Valide que si le visage est tourné vers la GAUCHE DE L'IMAGE,
    la direction est bien 'gauche'.
    """
    # --- CORRECTION DE LA VALEUR SIMULÉE ---
    # Un visage à gauche de l'image a une coordonnée X FAIBLE (ex: 0.40)
    mock_face_landmarks = create_mock_landmarks(0.40)
    direction = video_agent._classify_gaze_direction_by_face_center(mock_face_landmarks)
    assert direction == "gauche"
    # --- FIN DE LA CORRECTION ---

def test_classify_gaze_by_face_center_looks_center(video_agent):
    """
    Valide que si le visage est au centre, le regard est classé 'centre'.
    (Ce test était déjà correct).
    """
    mock_face_landmarks = create_mock_landmarks(0.50)
    direction = video_agent._classify_gaze_direction_by_face_center(mock_face_landmarks)
    assert direction == "centre"

def test_classify_gaze_by_face_center_looks_right(video_agent):
    """
    Valide que si le visage est tourné vers la DROITE DE L'IMAGE,
    la direction est bien 'droite'.
    """
    # --- CORRECTION DE LA VALEUR SIMULÉE ---
    # Un visage à droite de l'image a une coordonnée X ÉLEVÉE (ex: 0.60)
    mock_face_landmarks = create_mock_landmarks(0.60)
    direction = video_agent._classify_gaze_direction_by_face_center(mock_face_landmarks)
    assert direction == "droite"
    # --- FIN DE LA CORRECTION ---

def test_classify_gaze_handles_errors_gracefully(video_agent):
    """
    Valide que la fonction ne plante pas si les landmarks sont invalides.
    (Ce test était déjà correct).
    """
    mock_invalid_landmarks = MagicMock()
    mock_invalid_landmarks.landmark = []
    direction = video_agent._classify_gaze_direction_by_face_center(mock_invalid_landmarks)
    assert direction == "hors_champ"