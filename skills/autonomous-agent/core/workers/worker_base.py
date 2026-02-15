import sys
import time
import json
import logging
from pathlib import Path
from abc import ABC, abstractmethod

# Ensure we can import core modules
current_dir = Path(__file__).resolve().parent
core_dir = current_dir.parent
if str(core_dir) not in sys.path:
    sys.path.append(str(core_dir))

try:
    from swarm import SwarmOrchestrator
except ImportError:
    # Fallback for direct execution
    sys.path.append(str(core_dir.parent.parent.parent.parent))
    from core.swarm import SwarmOrchestrator

# Setup Worker Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class BaseWorker(ABC):
    def __init__(self, worker_type: str, worker_id: str = None):
        self.worker_type = worker_type
        self.worker_id = worker_id or f"{worker_type}-{int(time.time())}"
        self.orchestrator = SwarmOrchestrator()
        self.logger = logging.getLogger(f"Worker-{self.worker_id}")
        self.running = True

    def start(self):
        self.logger.info(f"Worker {self.worker_id} started. Polling for '{self.worker_type}' tasks...")
        while self.running:
            try:
                task = self.orchestrator.get_pending_task(self.worker_type)
                if task:
                    self.logger.info(f"Received task: {task['task_id']}")
                    try:
                        result = self.execute(task['payload'])
                        self.orchestrator.complete_task(task['task_id'], result)
                        self.logger.info(f"Task {task['task_id']} completed successfully.")
                    except Exception as e:
                        error_msg = str(e)
                        self.logger.error(f"Task {task['task_id']} failed: {error_msg}")
                        self.orchestrator.fail_task(task['task_id'], error_msg)
                else:
                    # Adaptive sleep: can be improved
                    time.sleep(2)
            except KeyboardInterrupt:
                self.logger.info("Stopping worker...")
                self.running = False
            except Exception as e:
                self.logger.error(f"Worker loop error: {e}")
                time.sleep(5)

    @abstractmethod
    def execute(self, payload: dict) -> dict:
        """Execute the task and return result dictionary"""
        pass
