
import sys
import json
import os
from bs4 import BeautifulSoup

def validate_webpage(file_path):
    results = {
        "status": "success",
        "message": "Validation passed",
        "checks": []
    }
    
    if not os.path.exists(file_path):
        results["status"] = "error"
        results["message"] = f"File not found: {file_path}"
        print(json.dumps(results))
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')
            
        # Check 1: Title
        title = soup.title
        if title and title.string:
            results["checks"].append({"name": "Title", "status": "pass", "detail": title.string})
        else:
            results["checks"].append({"name": "Title", "status": "fail", "detail": "Missing <title>"})
            results["status"] = "error"
            
        # Check 2: Meta Description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            results["checks"].append({"name": "Meta Description", "status": "pass", "detail": "Found"})
        else:
            results["checks"].append({"name": "Meta Description", "status": "warning", "detail": "Missing description (SEO impact)"})
            # Warnings don't fail the build in this strictness level
            
        # Check 3: H1
        h1 = soup.find('h1')
        if h1:
            results["checks"].append({"name": "H1 Tag", "status": "pass", "detail": h1.get_text()[:30]})
        else:
            results["checks"].append({"name": "H1 Tag", "status": "fail", "detail": "Missing <h1>"})
            results["status"] = "error"
            
        # Check 4: Images
        images = soup.find_all('img')
        missing_alt = 0
        for img in images:
            if not img.get('alt'):
                missing_alt += 1
        
        if missing_alt > 0:
            results["checks"].append({"name": "Image Alt Text", "status": "warning", "detail": f"{missing_alt} images missing alt text"})
        else:
             results["checks"].append({"name": "Image Alt Text", "status": "pass", "detail": "All images have alt text"})

        if results["status"] == "error":
            results["message"] = "Validation failed: " + ", ".join([c["name"] for c in results["checks"] if c["status"] == "fail"])

    except Exception as e:
        results["status"] = "error"
        results["message"] = str(e)

    print(json.dumps(results, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Usage: python validate_webpage.py <html_file>"}))
        sys.exit(1)
    
    validate_webpage(sys.argv[1])
