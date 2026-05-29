#!/usr/bin/env python3
"""
Standalone embedding service for Mythos.
Runs locally (outside Docker) to avoid PyTorch + uvicorn async conflicts.
Provides GPU-accelerated embeddings via HTTP API.
"""
import os
import sys
import time
import logging
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import torch
import numpy as np
import threading
from typing import List

LOG_LEVEL = os.getenv("EMBED_LOG_LEVEL", "INFO").upper()
class ColorFormatter(logging.Formatter):
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    PURPLE = "\033[35m"
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        ts = self.formatTime(record, "%H:%M:%S")
        level = record.levelname
        msg = record.getMessage()

        # Pattern-based coloring for specific lines
        if "GPU detected" in msg:
            msg = f"{self.CYAN}{msg}{self.RESET}"
        elif msg.startswith("VRAM:"):
            msg = f"{self.PURPLE}{msg}{self.RESET}"
        elif "Initializing model load" in msg or "Starting Mythos Embedding Service" in msg:
            msg = f"{self.GREEN}{msg}{self.RESET}"
        else:
            # Color labels for Model/Device/Endpoint with colored values
            label_val = re.match(r"\s*Model:\s*(.*)", msg)
            if label_val:
                msg = f"{self.CYAN}   Model:{self.RESET} {self.PURPLE}{label_val.group(1)}{self.RESET}"
            else:
                label_val = re.match(r"\s*Device:\s*(.*)", msg)
                if label_val:
                    msg = f"{self.CYAN}   Device:{self.RESET} {self.PURPLE}{label_val.group(1)}{self.RESET}"
                else:
                    label_val = re.match(r"\s*Endpoint:\s*(.*)", msg)
                    if label_val:
                        msg = f"{self.CYAN}   Endpoint:{self.RESET} {self.PURPLE}{label_val.group(1)}{self.RESET}"

        # Color the level tag (cyan) and keep timestamp neutral
        level_colored = f"{self.CYAN}{level}{self.RESET}"
        return f"[{ts}] {level_colored} {msg}"

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(ColorFormatter())
logger = logging.getLogger()
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
logger.handlers = [handler]

app = FastAPI(title="Mythos Embedding Service")

# GPU detection
GPU_AVAILABLE = torch.cuda.is_available()
DEVICE = "cuda" if GPU_AVAILABLE else "cpu"
DEVICE_NAME = None
VRAM_GB = None

if GPU_AVAILABLE:
    DEVICE_NAME = torch.cuda.get_device_name(0)
    VRAM_GB = torch.cuda.get_device_properties(0).total_memory / 1024**3
    logging.info("GPU detected: %s", DEVICE_NAME)
    logging.info("VRAM: %.1f GB", VRAM_GB)
else:
    DEVICE_NAME = "cpu"
    logging.info("No GPU detected; using CPU")

# Load model
try:
    from sentence_transformers import SentenceTransformer
    MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    # Animated loading bar (always on)
    logging.info("Initializing model load...")
    t0 = time.time()
    show_bar = True
    stop_event: threading.Event | None = None
    if show_bar:
        stop_event = threading.Event()

        def _animate_loading():
            width = 40
            phases = ["░", "▒", "▓", "█"]
            # Fixed ANSI colors for parts (similar to test scripts style)
            COLOR_LABEL = "\033[36m"   # Cyan for label text
            COLOR_BAR   = "\033[35m"   # Purple for the bar fill
            COLOR_PHASE = "\033[31m"   # Red for phase glyphs
            COLOR_OK    = "\033[32m"   # Green for completion ✓
            RESET       = "\033[0m"
            i = 0
            while not stop_event.is_set():
                # Animate fill left→right
                filled = (i % (width + 1))
                bar_fill = "█" * filled
                bar_empty = "-" * (width - filled)
                phase = phases[i % len(phases)]
                # Compose colored line: label (cyan), bar (purple), phase (red)
                line = (
                    f"\r{COLOR_LABEL}Loading {MODEL_NAME} on {DEVICE} "
                    f"[{COLOR_BAR}{bar_fill}{RESET}{bar_empty}] "
                    f"{COLOR_PHASE}{phase}{RESET}"
                )
                sys.stdout.write(line)
                sys.stdout.flush()
                time.sleep(0.05)
                i += 1
            # Finalize full bar
            bar = "█" * width
            # Success line: label (cyan), full bar (green), checkmark (green)
            final_line = (
                f"\r{COLOR_LABEL}Loading {MODEL_NAME} on {DEVICE} "
                f"[{COLOR_OK}{bar}{RESET}] {COLOR_OK}✓{RESET}\n"
            )
            sys.stdout.write(final_line)
            sys.stdout.flush()

        th = threading.Thread(target=_animate_loading, daemon=True)
        th.start()

    MODEL = SentenceTransformer(MODEL_NAME, device=DEVICE)

    if stop_event is not None:
        stop_event.set()

    EMBEDDING_DIM = MODEL.get_sentence_embedding_dimension()
    logging.info("Model loaded: %s (%d dims) in %.2fs", MODEL_NAME, EMBEDDING_DIM, time.time() - t0)
except ImportError as e:
    logging.error("sentence-transformers not installed: %s", e)
    exit(1)

class EmbedRequest(BaseModel):
    texts: List[str]
    normalize: bool = False

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    device: str
    dimension: int

@app.get("/health")
def health():
    """Health check endpoint."""
    t0 = time.time()
    info = {
        "status": "healthy",
        "model": MODEL_NAME,
        "device": DEVICE,
        "dimension": EMBEDDING_DIM,
        "gpu_available": GPU_AVAILABLE,
        "device_name": DEVICE_NAME,
        "vram_gb": round(VRAM_GB, 2) if VRAM_GB is not None else None,
        "log_level": LOG_LEVEL,
    }
    info["elapsed_ms"] = int((time.time() - t0) * 1000)
    logging.debug("/health responded in %d ms", info["elapsed_ms"])
    return info

@app.post("/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest):
    """Generate embeddings for input texts."""
    if not req.texts:
        raise HTTPException(status_code=400, detail="No texts provided")
    
    try:
        batch_size = len(req.texts)
        logging.info("/embed start: texts=%d normalize=%s", batch_size, req.normalize)
        t0 = time.time()
        # Generate embeddings (single-threaded, no progress bar)
        embeddings = MODEL.encode(
            req.texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=req.normalize,
            batch_size=batch_size
        )
        dt = (time.time() - t0)
        logging.info("/embed done in %.2f ms", dt * 1000)
        # Convert to list for JSON serialization
        embeddings_list = embeddings.astype(np.float32).tolist()
        
        resp = EmbedResponse(
            embeddings=embeddings_list,
            model=MODEL_NAME,
            device=DEVICE,
            dimension=EMBEDDING_DIM
        )
        # Augment response with diagnostic fields
        data = resp.dict()
        data.update({
            "time_ms": int(dt * 1000),
            "batch_size": batch_size,
            "normalize": req.normalize,
            "gpu_available": GPU_AVAILABLE,
            "device_name": DEVICE_NAME,
            "vram_gb": round(VRAM_GB, 2) if VRAM_GB is not None else None,
            "log_level": LOG_LEVEL,
        })
        return data
    except Exception as e:
        logging.exception("/embed failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

if __name__ == "__main__":
    PORT = int(os.getenv("EMBEDDING_PORT", "8002"))
    logging.info("\n🚀 Starting Mythos Embedding Service on port %d", PORT)
    logging.info("   Model: %s", MODEL_NAME)
    logging.info("   Device: %s", DEVICE)
    logging.info("   Endpoint: http://localhost:%d/embed", PORT)
    
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level=LOG_LEVEL.lower())
