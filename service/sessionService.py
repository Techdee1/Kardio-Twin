from model import dataModel
from dtos import sessionDto

def start_session(data: sessionDto.SessionStartRequest, db):
    """Start a new measurement session."""
    existing_session = db.query(dataModel.Session).filter(
        dataModel.Session.session_id == data.session_id
    ).first()
    
    if existing_session:
        return sessionDto.SessionStartResponse(
            status="session_started",
            session_id=data.session_id
        )
    
    # Create new session
    new_session = dataModel.Session(
        session_id=data.session_id,
        user_phone=data.user_phone
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return sessionDto.SessionStartResponse(
        status="session_started",
        session_id=new_session.session_id
    )
    
def fetch_session(session_id,db):
    existing_session = db.query(dataModel.Session).filter(
        dataModel.Session.session_id == session_id
    ).first()
    return existing_session