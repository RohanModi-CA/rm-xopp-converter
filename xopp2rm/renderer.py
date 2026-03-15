import subprocess
import tempfile
import os

def generate_ghost_pdf(xml_string: str) -> str:
    """Calls Xournal++ to render the ghost PDF. Returns path to PDF."""
    # 1. Create a temp .xopp file
    with tempfile.NamedTemporaryFile(suffix=".xopp", delete=False, mode="w") as f:
        f.write(xml_string)
        temp_xopp = f.name

    # 2. Define output path
    temp_pdf = temp_xopp.replace(".xopp", ".pdf")

    # 3. Call Xournal++
    subprocess.run([
        "xournalpp", 
        temp_xopp, 
        "--create-pdf", 
        temp_pdf
    ], check=True, capture_output=True)

    os.remove(temp_xopp) # Clean up the XML
    return temp_pdf
