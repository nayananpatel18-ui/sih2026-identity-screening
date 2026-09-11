"""
Abstract Data Adapter Interface for Dataset Integration.
Allows the screening pipeline to seamlessly consume different datasets
(Synthetic, MIDV-500, MIDV-2020, DocTamper, IDNet) without pipeline rewrites.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from app.data.models import CanonicalDocumentSample


class BaseDataAdapter(ABC):
    """
    Abstract adapter for wrapping identity dataset formats into canonical document samples.
    """

    @property
    @abstractmethod
    def dataset_name(self) -> str:
        """Unique dataset identifier string."""
        pass

    @abstractmethod
    def list_samples(self) -> List[str]:
        """Return list of available sample IDs in this dataset."""
        pass

    @abstractmethod
    def get_sample(self, sample_id: str) -> Optional[CanonicalDocumentSample]:
        """Fetch and convert a specific sample into a CanonicalDocumentSample."""
        pass

    @abstractmethod
    def get_sample_by_case_type(self, case_type: str) -> Optional[CanonicalDocumentSample]:
        """Convenience method to retrieve demo cases by label: 'genuine', 'tampered', 'uncertain'."""
        pass


class DatasetRegistry:
    """Registry to register and query active data adapters."""
    _adapters: Dict[str, BaseDataAdapter] = {}

    @classmethod
    def register(cls, adapter: BaseDataAdapter):
        cls._adapters[adapter.dataset_name] = adapter

    @classmethod
    def get(cls, dataset_name: str) -> Optional[BaseDataAdapter]:
        return cls._adapters.get(dataset_name)

    @classmethod
    def list_datasets(cls) -> List[str]:
        return list(cls._adapters.keys())
