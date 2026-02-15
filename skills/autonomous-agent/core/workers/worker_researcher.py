from .worker_base import BaseWorker
import time
import json
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

class ResearchWorker(BaseWorker):
    def __init__(self):
        super().__init__(worker_type="search")

    def execute(self, payload: dict) -> dict:
        query = payload.get("query", "")
        self.logger.info(f"Researching: {query}")
        
        results = []
        if DDGS:
            try:
                with DDGS() as ddgs:
                    # Search for text results (limit to 5)
                    ddgs_gen = ddgs.text(query, max_results=5)
                    if ddgs_gen:
                        for r in ddgs_gen:
                            results.append({
                                "title": r.get('title'),
                                "url": r.get('href'),
                                "snippet": r.get('body')
                            })
            except Exception as e:
                self.logger.error(f"DDGS search failed: {e}")
                results = [{"error": str(e)}]
        else:
            self.logger.warning("duckduckgo_search library not found. Using mock data.")
            time.sleep(1) # Network latency simulation
            results = [
                {"title": f"[Mock] Official {query} Documentation", "url": "https://docs.example.com", "snippet": "Library not installed."},
            ]
        
        return {
            "status": "success",
            "summary": f"Research results for: {query}",
            "data": results
        }

if __name__ == "__main__":
    worker = ResearchWorker()
    worker.start()
