# GPU Embeddings Implementation Notes

## Changes Made

### 1. Requirements (`requirements.txt`)
- Added `torch==2.5.*` for GPU detection and tensor operations
- Changed `faiss-cpu==1.8.*` → `faiss-gpu==1.7.2` (GPU-accelerated vector search)
- Kept CPU fallback option commented for easy switching

### 2. Dockerfile (`mythos_backend/Dockerfile`)
- Changed base image: `python:3.11-slim` → `nvidia/cuda:12.1.1-runtime-ubuntu22.04`
- Installed Python 3.11 manually on CUDA image
- Fixed symlink creation for `python` and `pip` commands

### 3. Docker Compose (`docker-compose.yml`)
- Added GPU device configuration:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

### 4. Backend Code (`mythos_backend.py`)

**GPU Detection:**
```python
import torch
GPU_AVAILABLE = torch.cuda.is_available()
DEVICE = "cuda" if GPU_AVAILABLE else "cpu"
```

**Model Loading:**
- SentenceTransformer now loads on GPU: `SentenceTransformer(model_name, device=DEVICE)`
- Prints GPU info on startup (name, VRAM)

**FAISS Indexing:**
- Creates CPU index first, then moves to GPU if available
- Uses `faiss.StandardGpuResources()` and `faiss.index_cpu_to_gpu()`
- Falls back to CPU index if GPU transfer fails

## Performance Expectations

### With Your Hardware (24GB VRAM, 64GB RAM):
- **LM Studio (8-20B models)**: ~6-14GB VRAM
- **Embedding Model (all-MiniLM-L6-v2)**: ~200MB VRAM
- **FAISS GPU Index**: ~100MB VRAM per 100k entries
- **Total Expected**: 7-15GB VRAM usage (safe headroom)

### Speed Improvements:
- **Embedding**: 5-10x faster on GPU vs CPU
- **FAISS Search**: 10-100x faster for large indices (>10k entries)
- **Typical embedding**: ~10-30ms on GPU vs ~50-200ms on CPU

## Fallback Strategy

The system gracefully degrades:
1. **GPU available + working**: Uses GPU for embeddings and FAISS
2. **GPU unavailable**: Falls back to CPU for both
3. **GPU embedding works but FAISS fails**: GPU embeddings, CPU FAISS
4. **Torch not available**: Disables embeddings entirely

## Switching Back to CPU-Only

If you need CPU-only (for any reason):

**Option 1: Quick toggle in requirements.txt**
```txt
# faiss-gpu==1.7.2
faiss-cpu==1.8.*
```

**Option 2: Revert Dockerfile to slim base**
```dockerfile
FROM python:3.11-slim
```

**Option 3: Comment out GPU config in docker-compose.yml**
```yaml
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: all
#           capabilities: [gpu]
```

## Monitoring GPU Usage

```powershell
# Watch GPU usage in real-time
nvidia-smi -l 1

# Check from inside container
docker exec mythos_backend nvidia-smi

# Verify GPU in Python
docker exec mythos_backend python -c "import torch; print('GPU:', torch.cuda.is_available())"
```

## Troubleshooting

**Issue: "No CUDA-capable device is detected"**
- Check NVIDIA Container Toolkit installed: `docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi`
- Verify Docker Desktop → Settings → Resources → WSL Integration enabled

**Issue: "FAISS GPU failed"**
- System falls back to CPU FAISS automatically
- Check logs for specific error
- May happen if VRAM exhausted by LM Studio

**Issue: Slow startup (5+ minutes)**
- CUDA base image is large (~1.5GB download first time)
- Model downloads on first run (~80MB for all-MiniLM-L6-v2)
- Subsequent starts faster (~30 seconds)
