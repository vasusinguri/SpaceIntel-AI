import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from bs4 import BeautifulSoup
import html as html_module

# Load environment variables from .env file
load_dotenv()

def clean_html(text):
    """
    Clean HTML from text using BeautifulSoup.
    Defensive measure to ensure no HTML enters the database from AI responses.
    """
    if not text:
        return ""
    soup = BeautifulSoup(str(text), 'html.parser')
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text(separator=' ', strip=True)
    text = html_module.unescape(text)
    text = ' '.join(text.split())
    return text.strip()

# Define the structured output format using Pydantic
class SpaceIntelAnalysis(BaseModel):
    category: str = Field(
        ...,
        description="The category of the article. Must be exactly one of: 'Astronomy', 'Space Exploration', 'Space Technology', 'Space Business', or 'Research & Discoveries'."
    )
    summary: str = Field(
        ...,
        description="A simple, clear explanation of the article in plain language. 2-3 sentences."
    )
    why_it_matters: str = Field(
        ...,
        description="Explain why this news is significant or what impact it has. 1-2 sentences."
    )
    importance_score: int = Field(
        ...,
        description="Rate the importance of this news from 1 (lowest) to 10 (highest)."
    )
    impact_type: str = Field(
        ...,
        description="Must be exactly one of: 'Short-Term' or 'Long-Term'."
    )
    who_cares: List[str] = Field(
        ...,
        description="A list of target groups who care or benefit from this news. Choose from: 'Investors', 'Researchers', 'Students', 'Space Startups', 'Government Agencies', 'Satellite Companies', etc."
    )

def analyze_article(title, source, content_hint="", api_key=None):
    """
    Sends article metadata to the Gemini API and retrieves a structured intelligence analysis.
    Supports both the new 'google-genai' SDK and the legacy 'google-generativeai' SDK.
    """
    # Retrieve API key
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
        
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("Gemini API Key is not set. Please update your .env file or GEMINI_API_KEY environment variable.")

    prompt = f"""
    You are an expert Space Intelligence Analyst. Analyze the following space-related news article and categorize and extract intelligence from it.

    Article Details:
    - Title: {title}
    - Source: {source}
    - Details: {content_hint}

    Constraints:
    - category: Must be exactly one of: 'Astronomy', 'Space Exploration', 'Space Technology', 'Space Business', 'Research & Discoveries'.
    - summary: Plain language, easy to read, 2-3 sentences.
    - why_it_matters: Why is this news significant? 1-2 sentences.
    - importance_score: Integer from 1 to 10.
    - impact_type: Exactly 'Short-Term' or 'Long-Term'.
    - who_cares: List of groups that benefit from this news (e.g. Investors, Researchers, Students, Space Startups, Government Agencies, Satellite Companies).

    Analyze the article and output the JSON adhering to the schema.
    """

    # Try using the new google-genai SDK
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SpaceIntelAnalysis,
                temperature=0.1
            )
        )
        
        # Parse the JSON response
        data = json.loads(response.text)
        
        # Clean HTML from all text fields as a defensive measure
        if "summary" in data:
            data["summary"] = clean_html(data["summary"])
        if "why_it_matters" in data:
            data["why_it_matters"] = clean_html(data["why_it_matters"])
        if "category" in data:
            data["category"] = clean_html(data["category"])
        
        return data
        
    except ImportError:
        # Fallback to the legacy google-generativeai SDK
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Request JSON output
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            data = json.loads(response.text)
            
            # Clean HTML from all text fields as a defensive measure
            if "summary" in data:
                data["summary"] = clean_html(data["summary"])
            if "why_it_matters" in data:
                data["why_it_matters"] = clean_html(data["why_it_matters"])
            if "category" in data:
                data["category"] = clean_html(data["category"])
            
            # Validate output keys
            if "category" not in data or "summary" not in data:
                raise ValueError("Incomplete response from Gemini API.")
                
            # Basic sanitization of category
            valid_categories = ["Astronomy", "Space Exploration", "Space Technology", "Space Business", "Research & Discoveries"]
            cat = data.get("category", "")
            if cat not in valid_categories:
                # Find best match or default
                matched = False
                for vc in valid_categories:
                    if vc.lower() in cat.lower():
                        data["category"] = vc
                        matched = True
                        break
                if not matched:
                    data["category"] = "Research & Discoveries"
                    
            # Basic sanitization of impact type
            impact = data.get("impact_type", "")
            if impact not in ["Short-Term", "Long-Term"]:
                data["impact_type"] = "Short-Term" if "short" in impact.lower() else "Long-Term"
                
            # Basic validation of importance score
            try:
                data["importance_score"] = int(data.get("importance_score", 5))
            except Exception:
                data["importance_score"] = 5
                
            return data
            
        except Exception as e:
            raise RuntimeError(f"Error during Gemini analysis using fallback SDK: {e}")
            
    except Exception as e:
        raise RuntimeError(f"Error during Gemini analysis: {e}")

if __name__ == "__main__":
    # Test stub
    print("Testing Gemini Analyzer...")
    try:
        sample_title = "NASA's Voyager 1 Sends Data from Interstellar Space After Engineering Fix"
        sample_source = "NASA News"
        result = analyze_article(sample_title, sample_source, "Engineers successfully resolved an issue with telemetry communication on the 46-year-old spacecraft.")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("Test failed (this is expected if API key is not configured):", e)
