from extensions import celery
from services import analysis_service

@celery.task(name='tasks.run_analysis_task')
def run_analysis_task(session_id: int):
    print(f"TÂCHE CELERY REÇUE : Démarrage de l'analyse pour la session {session_id}")
    try:
        analysis_service.run_analysis(session_id)
        print(f"TÂCHE CELERY TERMINÉE : Analyse de la session {session_id} réussie.")
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        print(f"TÂCHE CELERY ÉCHOUÉE : Erreur lors de l'analyse de la session {session_id}: {e}")
        return {"status": "failure", "session_id": session_id, "error": str(e)}