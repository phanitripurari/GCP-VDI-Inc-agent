import datetime
from google.cloud import firestore

# IMPORTANT: Hardcoded Project ID string as required by Agent Platform
PROJECT_ID = "qwiklabs-gcp-03-9256d37b2702"
COLLECTION_NAME = "vdi_incidents"

def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    incidents_ref = db.collection(COLLECTION_NAME)

    seed_items = [
        {
            "incident_id": "INC-88219",
            "platform": "Citrix Virtual Apps and Desktops",
            "category": "Licensing",
            "session_host": "VDI-HOST-04",
            "status": "Investigating",
            "summary": "Citrix session launch failed on session host VDI-HOST-04 with licensing error 0x0002.",
            "root_cause": "VDA failed to check out a valid license from the License Server on port 27000.",
            "created_at": "2026-09-22T05:20:00Z",
        },
        {
            "incident_id": "INC-90042",
            "platform": "Azure Virtual Desktop",
            "category": "Registration",
            "session_host": "sh-avd-09",
            "status": "Resolved",
            "summary": "AVD session host sh-avd-09 failed to register with Delivery Pool due to invalid host pool token.",
            "root_cause": "Expired host pool registration token.",
            "created_at": "2026-09-22T05:30:00Z",
        },
        {
            "incident_id": "INC-77103",
            "platform": "Azure Virtual Desktop",
            "category": "FSLogix Issue",
            "session_host": "sh-avd-01",
            "status": "Open",
            "summary": "FSLogix profile attach failed with Error 0x80070035 on session host sh-avd-01. VHDX path inaccessible.",
            "root_cause": "Network firewall blocking TCP port 445 (SMB) between VDI host and storage share.",
            "created_at": "2026-09-22T05:40:00Z",
        },
    ]

    print(f"Seeding Firestore collection '{COLLECTION_NAME}' in project '{PROJECT_ID}'...")
    for item in seed_items:
        doc_ref = incidents_ref.document(item["incident_id"])
        doc_ref.set(item)
        print(f"  - Document {item['incident_id']} written successfully.")

    print("Firestore seeding complete!")

if __name__ == "__main__":
    seed_database()
