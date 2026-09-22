import datetime
from google.cloud import firestore

# HARDCODED GCP project ID string required for Agent Platform deployment
PROJECT_ID = "qwiklabs-gcp-03-9256d37b2702"
COLLECTION_NAME = "vdi_incidents"

def get_firestore_client() -> firestore.Client:
    """Returns a Firestore client initialized with hardcoded project ID."""
    return firestore.Client(project=PROJECT_ID)

def list_vdi_incidents(status: str = None, platform: str = None) -> list[dict]:
    """Lists VDI incidents stored in the Firestore database.

    Args:
        status: Optional status to filter by (e.g. 'Open', 'Investigating', 'Resolved').
        platform: Optional VDI platform filter (e.g. 'Azure Virtual Desktop', 'Citrix Virtual Apps and Desktops').

    Returns:
        List of incident records from Firestore.
    """
    db = get_firestore_client()
    query = db.collection(COLLECTION_NAME)

    if status:
        query = query.where("status", "==", status)
    if platform:
        query = query.where("platform", "==", platform)

    docs = query.stream()
    incidents = []
    for doc in docs:
        data = doc.to_dict()
        data["doc_id"] = doc.id
        incidents.append(data)
    return incidents

def get_vdi_incident(incident_id: str) -> dict:
    """Retrieves a specific VDI incident record from Firestore by incident_id.

    Args:
        incident_id: The unique incident identifier (e.g. 'INC-88219', 'INC-90042').

    Returns:
        The incident dictionary or error message if not found.
    """
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(incident_id)
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        data["doc_id"] = doc.id
        return data
    return {"error": f"Incident '{incident_id}' not found in Firestore."}

def save_vdi_incident(
    incident_id: str,
    platform: str,
    category: str,
    session_host: str,
    status: str,
    summary: str,
    root_cause: str,
) -> str:
    """Saves or updates a VDI incident record in Firestore.

    Args:
        incident_id: Incident ID (e.g. 'INC-10294').
        platform: VDI platform (e.g. 'Citrix', 'Azure Virtual Desktop', 'Omnissa Horizon').
        category: Incident category (e.g. 'Licensing', 'Registration', 'FSLogix Issue').
        session_host: Target session host identifier.
        status: Current status ('Open', 'Investigating', 'Resolved').
        summary: Brief summary of the incident.
        root_cause: Probable or confirmed root cause description.

    Returns:
        Confirmation message.
    """
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(incident_id)

    record = {
        "incident_id": incident_id,
        "platform": platform,
        "category": category,
        "session_host": session_host,
        "status": status,
        "summary": summary,
        "root_cause": root_cause,
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    doc_ref.set(record, merge=True)
    return f"Incident '{incident_id}' successfully saved to Firestore."
