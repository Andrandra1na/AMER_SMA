import cv2
import mediapipe as mp
import numpy as np
from tqdm import tqdm

class VideoAgent:
    """
    Agent d'analyse visuelle utilisant MediaPipe.
    Implémente une détection du regard robuste, basée sur la position
    globale du visage, optimisée pour des conditions vidéo variables.
    """
    def __init__(self, frames_per_second_to_analyze=2):
        """
        Initialise l'agent en chargeant le modèle FaceMesh de MediaPipe.
        """
        print("Initialisation du VideoAgent avec MediaPipe (mode robuste)...")
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.4 # Seuil de suivi tolérant
        )
        self.fps_analyze = frames_per_second_to_analyze
        print("VideoAgent prêt.")

    def _classify_gaze_direction_by_face_center(self, face_landmarks) -> str:
        """
        [MÉTHODE ROBUSTE]
        Classe la direction du regard en se basant sur le centre de gravité du visage.
        """
        try:
            central_points_indices = [1, 4, 5, 8, 9, 10, 151, 152, 199, 234]
            face_center_x = np.mean([face_landmarks.landmark[i].x for i in central_points_indices])
            
            if face_center_x < 0.45: return "gauche"
            if face_center_x > 0.55: return "droite"
            return "centre"
        except (ValueError, IndexError, AttributeError):
            return "hors_champ"

    def _interpret_gaze_direction(self, direction: str) -> str:
        """
        Traduit la direction géométrique en comportement, en tenant compte de l'UI.
        """
        mapping = {
            "gauche": "Auto-observation",
            "centre": "Contact Visuel",
            "droite": "Lecture",
            "hors_champ": "Distraction"
        }
        return mapping.get(direction, "Inconnu")

    def analyze_gaze(self, video_path: str, events_timeline: list):
        """
        Analyse le regard en lisant la vidéo de manière séquentielle et robuste.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"ERREUR (VideoAgent): Impossible d'ouvrir la vidéo {video_path}")
            return None

        video_fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = max(1, int(video_fps / self.fps_analyze))
        
        gaze_events = []
        current_frame_idx = 0

        # Boucle de lecture avec barre de progression
        with tqdm(total=total_frames, desc="Analyse Vidéo (Regard)", unit="frame") as pbar:
            while cap.isOpened():
                success, image = cap.read()
                if not success:
                    break

                if current_frame_idx % frame_interval == 0:
                    timestamp = current_frame_idx / video_fps
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    image_rgb.flags.writeable = False
                    results = self.face_mesh.process(image_rgb)
                    
                    direction = "hors_champ"
                    if results.multi_face_landmarks:
                        direction = self._classify_gaze_direction_by_face_center(results.multi_face_landmarks[0])

                    gaze_events.append({"timestamp": timestamp, "behavior": self._interpret_gaze_direction(direction)})
                
                current_frame_idx += 1
                pbar.update(1)
        
        cap.release()
        
        if not gaze_events:
            print("AVERTISSEMENT (VideoAgent): Aucun événement de regard n'a pu être extrait.")
            return None

        # --- DÉBUT DE LA MODIFICATION DANS L'AGRÉGATION ---

        # Agrégation globale des comportements (inchangé)
        global_behaviors = [event['behavior'] for event in gaze_events]
        total_frames_analyzed = len(global_behaviors)
        gaze_global_distribution = {b: round((global_behaviors.count(b) / total_frames_analyzed) * 100, 2) for b in set(global_behaviors)}
        
        # Agrégation contextuelle par question (corrigée)
        gaze_by_question = {}
        
        # On détermine la fin réelle de l'analyse du regard à partir des données extraites
        last_gaze_timestamp = gaze_events[-1]['timestamp'] if gaze_events else 0

        for i, event in enumerate(events_timeline):
            question_id = str(event['questionId'])
            start_time = event['timestamp']
            
            # Si c'est la dernière question, son temps de fin est la fin de l'analyse,
            # et non la durée potentiellement imprécise de la vidéo.
            end_time = events_timeline[i + 1]['timestamp'] if i + 1 < len(events_timeline) else last_gaze_timestamp + 0.1 # On ajoute une petite marge

            question_behaviors = [e['behavior'] for e in gaze_events if start_time <= e['timestamp'] < end_time]
            
            if question_behaviors:
                total_q_frames = len(question_behaviors)
                gaze_by_question[question_id] = {b: round((question_behaviors.count(b) / total_q_frames) * 100, 2) for b in set(question_behaviors)}
            else:
                 gaze_by_question[question_id] = {"Distraction": 100.0}

        # --- FIN DE LA MODIFICATION ---

        return { "gaze_global_distribution": gaze_global_distribution, "gaze_by_question": gaze_by_question }