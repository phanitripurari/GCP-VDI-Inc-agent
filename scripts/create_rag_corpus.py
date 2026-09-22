import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-03-9256d37b2702"
LOCATION = "us-central1"  # Serverless RAG corpus requires us-central1
GCS_PATH = "gs://vdi-incident-agent-assets-qwiklabs/rag/pg49513.txt"

PARSING_PROMPT = (
    "Extract the individual useful facts, remedies, and herbal recipes described in this text. "
    "Ignore and omit all boilerplate, publisher notices, and Gutenberg license text. "
    "Output clean, self-contained prose."
)

def create_corpus():
    print(f"Initializing Vertex AI in project '{PROJECT_ID}', location '{LOCATION}'...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    print("Switching region RAG managed DB config to serverless mode...")
    cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
    rag.update_rag_engine_config(
        rag_engine_config=rag.RagEngineConfig(
            name=cfg,
            rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
        )
    )

    print("Creating serverless RAG corpus...")
    corpus = rag.create_corpus(
        display_name="vdi-gutenberg-corpus",
        embedding_model_config=rag.EmbeddingModelConfig(
            publisher_model="publishers/google/models/text-embedding-005"
        ),
    )
    print(f"Corpus Created Successfully: {corpus.name}")

    print(f"Importing and indexing file from GCS ({GCS_PATH})...")
    resp = rag.import_files(
        corpus_name=corpus.name,
        paths=[GCS_PATH],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
        llm_parser=rag.LlmParserConfig(
            model_name="gemini-2.5-flash",
            custom_parsing_prompt=PARSING_PROMPT,
        ),
    )
    print(f"Import completed! Imported files count: {resp.imported_rag_files_count}")

    with open("rag_corpus_id.txt", "w") as f:
        f.write(corpus.name)

    return corpus.name

if __name__ == "__main__":
    create_corpus()
