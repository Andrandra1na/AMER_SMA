from database.models import db
from database.models import Users

def register_user(nom, email, password, role='candidat',must_change_password=False):
    existing_user = db.session.execute(db.select(Users).filter_by(email=email)).scalar_one_or_none()
    if existing_user:
        return None  
        
    if role not in ['candidat', 'recruteur', 'admin']:
        role = 'candidat'

    new_user = Users(nom=nom, email=email, role=role, doit_changer_mdp=must_change_password)
    
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    
    return new_user

def authenticate_user(email, password):
    user = db.session.execute(db.select(Users).filter_by(email=email)).scalar_one_or_none()
    
    if user and user.check_password(password):
        return user
        
    return None