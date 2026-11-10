import os
import tempfile

os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/invoiceflow_test.db".replace("\\", "/")