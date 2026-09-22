from google.adk.tools import ToolContext


def lookup_vdi_error_code(error_code: str) -> dict:
    """Looks up official vendor documentation and diagnostic details for a VDI error code.

    Args:
        error_code: The hex or decimal VDI error code (e.g., '0x80070035', '0x0002', '1030', '0x80070005').

    Returns:
        A dictionary containing error code details, vendor explanation, affected platform, and common remediation.
    """
    code_clean = error_code.strip().lower()

    # Pre-populated authoritative VDI error code knowledge base
    knowledge_base = {
        "0x80070035": {
            "error_code": "0x80070035",
            "hex_name": "ERROR_BAD_NETPATH",
            "description": "The network path was not found.",
            "platform": "FSLogix / Azure Virtual Desktop / Windows 365",
            "primary_cause": "Session host cannot reach the SMB profile storage share. VHDX file path is inaccessible.",
            "required_ports": ["TCP 445 (SMB)"],
            "recommended_action": "Check Network Security Groups (NSGs), firewall port 445, and SMB storage share availability.",
        },
        "0x0002": {
            "error_code": "0x0002",
            "hex_name": "CTX_VDA_NOT_LICENSED",
            "description": "Citrix VDA Licensing Check-out Failure.",
            "platform": "Citrix Virtual Apps and Desktops (CVAD) / Citrix DaaS",
            "primary_cause": "The VDA failed to check out a valid license from the Citrix License Server or the licensing grace period expired.",
            "required_ports": ["TCP 27000 (Licensing)", "TCP 8082 (Console)"],
            "recommended_action": "Verify Citrix Licensing Service status on the License Server and check port 27000 connectivity from VDA.",
        },
        "0x80070005": {
            "error_code": "0x80070005",
            "hex_name": "ERROR_ACCESS_DENIED",
            "description": "Access is denied.",
            "platform": "FSLogix / Citrix UPM / Active Directory",
            "primary_cause": "Insufficient NTFS or SMB Share permissions on the user profile directory.",
            "required_ports": ["TCP 445 (SMB)", "TCP 88 (Kerberos)"],
            "recommended_action": "Review Storage NTFS Full Control permissions for the FSLogix ODFC/Profile share for affected user SIDs.",
        },
        "1030": {
            "error_code": "1030",
            "hex_name": "CTX_SERVER_NOT_ACCEPTING_CONNECTIONS",
            "description": "The Citrix Server is not accepting connections.",
            "platform": "Citrix Virtual Apps and Desktops",
            "primary_cause": "VDA Citrix Desktop Service is stopped or host is in Maintenance Mode.",
            "required_ports": ["TCP 1494 (ICA)", "TCP 2598 (CGP)"],
            "recommended_action": "Verify Citrix Desktop Service status on VDA host and confirm host is not in Maintenance Mode in Delivery Controller.",
        },
    }

    # Match exact code or sanitized code without leading zeroes
    for key, data in knowledge_base.items():
        if key in code_clean or code_clean in key:
            return data

    return {
        "error_code": error_code,
        "hex_name": "UNKNOWN_VDI_ERROR",
        "description": "Custom or vendor-specific error code.",
        "platform": "General VDI / Windows Event Log",
        "primary_cause": "Uncached error code. Check Windows Event Viewer under Applications and Services Logs -> Microsoft/Citrix.",
        "required_ports": ["TCP 445", "TCP 3389"],
        "recommended_action": "Review host System/Application logs for surrounding Event IDs.",
    }


def lookup_network_ip_info(ip_or_domain: str) -> dict:
    """Fetches real-time ISP, ASN, organization, and geolocation network details for an IP or domain.

    Args:
        ip_or_domain: The IP address (e.g. '8.8.8.8') or domain name (e.g. 'citrix.com') to query.

    Returns:
        A dictionary containing network provider, ISP, country, city, AS number, and IP info.
    """
    import json
    import os
    import urllib.request

    api_key = os.environ.get("IP_API_KEY")
    query = ip_or_domain.strip()

    if api_key:
        url = f"https://pro.ip-api.com/json/{query}?key={api_key}"
    else:
        url = f"http://ip-api.com/json/{query}"

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "VDIIncidentAgent/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except Exception as err:
        return {
            "error": f"Failed to query network IP info for '{ip_or_domain}': {err}"
        }


RAG_CORPUS_NAME = "projects/933666491940/locations/us-central1/ragCorpora/7285091366760087552"


def consult_herbal_corpus(query: str) -> str:
    """Searches Culpeper's Complete Herbal corpus (pg49513) and returns matching passages.

    Args:
        query: What to look up (a plant, herb, remedy, or ailment).

    Returns:
        The matched passages from the corpus, or a note if none found.
    """
    import vertexai
    from vertexai.preview import rag

    try:
        vertexai.init(project="qwiklabs-gcp-03-9256d37b2702", location="us-central1")
        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS_NAME)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
        )
        contexts = getattr(resp.contexts, "contexts", [])
        passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
        return "\n\n---\n\n".join(passages) or "No relevant passage found in corpus."
    except Exception as e:
        return f"Retrieval failed: {e}"


GCS_BUCKET_NAME = "vdi-incident-agent-assets-qwiklabs"
GCP_PROJECT_ID = "qwiklabs-gcp-03-9256d37b2702"


def generate_vdi_architecture_image(prompt: str, tool_context: ToolContext) -> dict:
    """Generates an architectural diagram or diagnostic visual for a VDI component, topology, or incident.

    Args:
        prompt: Detailed description of the VDI diagram to generate (e.g. 'Citrix Delivery Controller and Session Host network flow', 'FSLogix profile storage architecture').
        tool_context: ADK ToolContext injected automatically.

    Returns:
        A dictionary containing the generated image filename, public Cloud Storage HTTPS URL, and description.
    """
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage
    from google.adk.tools import ToolContext

    try:
        # 1. Generate image using gemini-3.1-flash-lite-image in global region
        client = genai.Client(vertexai=True, project=GCP_PROJECT_ID, location="global")
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )

        image_bytes = None
        mime_type = "image/png"
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/png"
                break

        if not image_bytes:
            return {"error": "Failed to generate image: No inline image data returned by model."}

        ext = "jpg" if "jpeg" in mime_type else "png"
        image_id = str(uuid.uuid4())[:8]
        filename = f"vdi_diagram_{image_id}.{ext}"

        # 2. Save artifact using tool_context.save_artifact for Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 3. Upload image bytes directly to public GCS bucket (no local file)
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)
        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "filename": filename,
            "public_url": public_url,
            "description": f"Generated VDI visual diagram for prompt: '{prompt}'",
        }
    except Exception as e:
        return {"error": f"Image generation failed: {str(e)}"}


def generate_vdi_incident_video(prompt: str, tool_context: ToolContext) -> dict:
    """Generates a short VDI diagnostic or operational video animation using gemini-omni-flash-preview.

    Args:
        prompt: Detailed description of the VDI video animation to generate (e.g. 'Short video of a server rack diagnostic indicator blinking green').
        tool_context: ADK ToolContext injected automatically.

    Returns:
        A dictionary containing the generated video filename, public Cloud Storage HTTPS URL, and description.
    """
    import base64
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage

    try:
        # 1. Generate video using gemini-omni-flash-preview in global region via interactions API
        client = genai.Client(vertexai=True, project=GCP_PROJECT_ID, location="global")
        res = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
            generation_config={"response_modalities": ["VIDEO"]}
        )

        if not res.output_video or not res.output_video.data:
            return {"error": "Failed to generate video: No video output returned."}

        mime_type = res.output_video.mime_type or "video/mp4"
        raw_data = res.output_video.data
        video_bytes = base64.b64decode(raw_data) if isinstance(raw_data, str) else raw_data

        video_id = str(uuid.uuid4())[:8]
        filename = f"vdi_video_{video_id}.mp4"

        # 2. Save artifact to Playground panel via tool_context
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 3. Upload video bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)
        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "filename": filename,
            "public_url": public_url,
            "description": f"Generated VDI animation video for prompt: '{prompt}'",
        }
    except Exception as e:
        return {"error": f"Video generation failed: {str(e)}"}




