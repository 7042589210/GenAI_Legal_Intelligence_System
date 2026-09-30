import os
import sys
import pytest

# Add project root and backend folder to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

@pytest.fixture
def sample_contract_text():
    return """
    --- Page 1 (Native) ---
    Clause 1. Definitions and Interpretation
    This agreement is entered into between Tata Consultancy Services and CMSS.

    Section 2. Limitation of Liability
    Neither party shall be liable for indirect damages, capped at total contract value.

    Clause 3. Termination
    Either party may terminate this agreement upon 30 days written notice.
    """
