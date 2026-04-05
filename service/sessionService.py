from model import dataModel
from dtos import sessionDto


def start_session(data: sessionDto.SessionStartRequest, db):
    """Start a new measurement session."""
    existing_session = db.query(dataModel.Session).filter(
        dataModel.Session.session_id == data.session_id
    ).first()

    if existing_session:
        # Update caregiver/medical info if provided on reconnect
        updated = False
        if data.caregiver_phone and not existing_session.caregiver_phone:
            existing_session.caregiver_phone = data.caregiver_phone
            existing_session.caregiver_name = data.caregiver_name
            updated = True
        if data.medical_professional_phone and not existing_session.medical_professional_phone:
            existing_session.medical_professional_phone = data.medical_professional_phone
            existing_session.medical_professional_name = data.medical_professional_name
            updated = True
        if updated:
            db.commit()

        return sessionDto.SessionStartResponse(
            status="session_started",
            session_id=data.session_id
        )

    # Create new session
    new_session = dataModel.Session(
        session_id=data.session_id,
        user_phone=data.user_phone,
        caregiver_phone=data.caregiver_phone,
        caregiver_name=data.caregiver_name,
        medical_professional_phone=data.medical_professional_phone,
        medical_professional_name=data.medical_professional_name,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return sessionDto.SessionStartResponse(
        status="session_started",
        session_id=new_session.session_id
    )


def fetch_session(session_id, db):
    existing_session = db.query(dataModel.Session).filter(
        dataModel.Session.session_id == session_id
    ).first()
    return existing_session