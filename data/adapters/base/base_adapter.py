"""
Base adapter class for all IGVF Catalog data adapters.

This module provides a base class that consolidates common functionality
across all data adapters, including:
- Schema loading and validation
- Writer management
- Common configuration
- Standard error handling
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

from jsonschema import Draft202012Validator, ValidationError

from adapters.writer import Writer
from schemas.registry import get_schema


class BaseAdapter(ABC):
    """
    Abstract base class for all data adapters.

    All adapters should inherit from this class and implement the required
    abstract methods. This ensures consistency across adapters and reduces
    code duplication.

    Attributes:
        filepath (str): Path to the input data file
        label (str): Label identifying the data type being processed
        writer (Writer): Writer instance for output
        validate (bool): Whether to validate documents against schema
        source (str): Data source name
        version (str): Data source version
        source_url (str): URL to the data source
        logger (logging.Logger): Logger instance for this adapter

    Example:
        >>> class MyAdapter(BaseAdapter):
        ...     ALLOWED_LABELS = ['my_data']
        ...
        ...     def __init__(self, filepath, label, writer, validate=False):
        ...         super().__init__(filepath, label, writer, validate)
        ...         self.source = 'MyDataSource'
        ...         self.version = 'v1.0'
        ...         self.source_url = 'https://example.com/data'
        ...
        ...     def _get_schema_collection(self):
        ...         return 'nodes', 'my_collection'
        ...
        ...     def process_file(self):
        ...         self.writer.open()
        ...         # Process data...
        ...         self.writer.close()
    """

    # Subclasses should override these class attributes
    ALLOWED_LABELS: List[str] = []

    def __init__(
        self,
        filepath: str,
        label: str,
        writer: Optional[Writer] = None,
        validate: bool = False,
        **kwargs
    ):
        """
        Initialize the base adapter.

        Args:
            filepath: Path to the input data file
            label: Label identifying the data type
            writer: Writer instance for output (optional)
            validate: Whether to validate documents against schema
            **kwargs: Additional adapter-specific arguments

        Raises:
            ValueError: If label is not in ALLOWED_LABELS
        """
        # Validate label
        if self.ALLOWED_LABELS and label not in self.ALLOWED_LABELS:
            raise ValueError(
                f'Invalid label: {label}. '
                f'Allowed values: {", ".join(self.ALLOWED_LABELS)}'
            )

        # Core attributes
        self.filepath = filepath
        self.label = label
        self.writer = writer
        self.validate = validate

        # Initialize logger
        self.logger = self._setup_logger()

        # Initialize validation if requested
        if self.validate:
            self._setup_validation()

        # Log initialization
        self.logger.info(
            f'Initialized {self.__class__.__name__} '
            f'(label={label}, validate={validate})'
        )

    def _setup_logger(self) -> logging.Logger:
        """
        Set up logger for this adapter.

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _setup_validation(self) -> None:
        """
        Set up schema validation.

        Loads the appropriate schema and creates a validator instance.
        Subclasses can override _get_schema_collection() to specify
        which schema to load.
        """
        try:
            schema_type, collection = self._get_schema_collection()
            self.schema = get_schema(
                schema_type,
                collection,
                self.__class__.__name__
            )
            self.validator = Draft202012Validator(self.schema)
            self.logger.debug(
                f'Loaded schema: {schema_type}/{collection}/{self.__class__.__name__}'
            )
        except Exception as e:
            self.logger.error(f'Failed to load schema: {e}')
            raise

    def _get_schema_collection(self) -> tuple:
        """
        Get the schema collection path.

        Returns:
            Tuple of (schema_type, collection_name)
            Example: ('nodes', 'genes') or ('edges', 'genes_proteins')

        Note:
            Subclasses should override this method to specify which
            schema to use for validation. Default implementation uses
            _get_schema_type() and _get_collection_name() if defined.
        """
        # Try to use the helper methods if subclass defines them
        schema_type = self._get_schema_type() if hasattr(
            self, '_get_schema_type') else 'nodes'
        collection_name = self._get_collection_name() if hasattr(
            self, '_get_collection_name') else None

        if collection_name is None:
            raise NotImplementedError(
                f'{self.__class__.__name__} must implement either '
                f'_get_schema_collection() or _get_collection_name()'
            )

        return schema_type, collection_name

    def validate_doc(self, doc: Dict[str, Any]) -> None:
        """
        Validate a document against the loaded schema.

        Args:
            doc: Document to validate

        Raises:
            ValueError: If document fails validation

        Note:
            This method is only called if validate=True was passed
            to the constructor.
        """
        if not self.validate:
            return

        try:
            self.validator.validate(doc)
        except ValidationError as e:
            error_msg = f'Document validation failed: {e.message}'
            self.logger.error(f'{error_msg}\nDocument: {doc}')
            raise ValueError(error_msg)

    @abstractmethod
    def process_file(self) -> None:
        """
        Process the input file.

        This is the main method that processes the input data file
        and writes output using the writer.

        Subclasses must implement this method with their specific
        data processing logic.

        Typical pattern:
            1. Open writer: self.writer.open()
            2. Read and process input file
            3. For each output document:
               - Create document dict
               - Validate if needed: self.validate_doc(doc)
               - Write: self.writer.write(json.dumps(doc))
            4. Close writer: self.writer.close()
        """
        pass

    def get_config_path(self, relative_path: str) -> Path:
        """
        Get absolute path to a configuration/support file.

        Args:
            relative_path: Relative path from data/ directory

        Returns:
            Absolute Path object

        Example:
            >>> path = adapter.get_config_path(
            ...     'data_loading_support_files/mapping.pkl'
            ... )
        """
        base_dir = Path(__file__).parent.parent.parent
        return base_dir / relative_path


# Helper methods for convenience - subclasses can use these patterns
# but they're all handled by the base _get_schema_collection() method
