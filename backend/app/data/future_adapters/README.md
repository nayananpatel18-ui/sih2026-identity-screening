# Data Adapter Extension Framework

This directory is reserved for future public dataset adapters.

## Extension Architecture

When integrating new datasets (MIDV-500, MIDV-2020, DocTamper, IDNet), create a new adapter subclass inheriting from `BaseDataAdapter`:

```python
from app.data.base import BaseDataAdapter, DatasetRegistry
from app.data.models import CanonicalDocumentSample

class MIDV500Adapter(BaseDataAdapter):
    @property
    def dataset_name(self) -> str:
        return "midv500"

    def list_samples(self) -> List[str]:
        # Implementation for MIDV-500 directory scanning
        pass

    def get_sample(self, sample_id: str) -> Optional[CanonicalDocumentSample]:
        # Maps MIDV-500 annotation JSON to CanonicalDocumentSample
        pass
```

### Key Principles
1. **Pipeline Decoupling**: The screening pipeline consumes `CanonicalDocumentSample` exclusively. Switching or adding datasets requires ZERO changes to screening algorithms.
2. **Graceful Degradation**: Datasets without face photos or ground-truth annotations leave those fields as `None` or default quality parameters.
