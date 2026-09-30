from backend.prompts.legal_prompts import get_legal_assistant_prompt, get_risk_analysis_prompt

def test_legal_assistant_prompt():
    prompt = get_legal_assistant_prompt()
    formatted = prompt.format(context="Sample legal text", input="What is the liability?")
    assert "Tata Group Legal & Compliance Team" in formatted
    assert "Sample legal text" in formatted
    assert "What is the liability?" in formatted

def test_risk_analysis_prompt():
    prompt = get_risk_analysis_prompt()
    formatted = prompt.format(context="Sample contract text", input="Analyze risk")
    assert "Chief Legal Officer & Legal Risk Analyst" in formatted
    assert "Sample contract text" in formatted
    assert "Analyze risk" in formatted
