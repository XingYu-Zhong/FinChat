import os
import concurrent.futures
from typing import Any, List, Optional
from pydantic import Field, PrivateAttr
from llm.api.func_get_openai import OpenaiApi
from llama_index.core.embeddings import BaseEmbedding

DEFAULT_EMBED_BATCH_SIZE = 100

class InstructionEmbedding(BaseEmbedding):
    query_instruction: Optional[str] = Field(
        description="Instruction to prepend to query text.",
        default=None
    )
    text_instruction: Optional[str] = Field(
        description="Instruction to prepend to text.",
        default=None
    )
    model_name: str
    embedding_type: str = None
    device: Optional[str] = None
    model: Any = None

    def __init__(
        self, 
        model_name: str = "embedding-2",
        query_instruction: Optional[str] = None,
        text_instruction: Optional[str] = None,
        embed_batch_size: int = DEFAULT_EMBED_BATCH_SIZE,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        device: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(
            embed_batch_size=embed_batch_size,
            model_name=model_name,
            query_instruction=query_instruction,
            text_instruction=text_instruction,
            **kwargs
        )
        
        self.model_name = model_name
        self.device = device
        
        # if model_name in ["text-embedding-ada-002", "text-embedding-3-large", "text-embedding-3-small", "embedding-2", "embedding-3"]:
        self.embedding_type = "openai"
        if api_key is None:
            api_key = os.getenv("openai_api_key")
        if base_url is None:
            base_url = os.getenv("openai_base_url")
        self.model = OpenaiApi(api_key=api_key, base_url=base_url)

    def _format_query_text(self, query_text: str) -> str:
        """Format query text with instruction if provided."""
        
        if '\n' in query_text:
            query_text = query_text.split('\n')[-1].strip()
        print(f'_format_query_text query_text: {query_text}')
        if self.query_instruction:
            return f"{self.query_instruction} {query_text}"
        return query_text

    def _format_text(self, text: str) -> str:
        """Format text with instruction if provided."""
        
        # 如果文本包含metadata和text的组合，只取最后一行作为text
        if '\n' in text:
            text = text.split('\n')[-1].strip()
        print(f'_format_text text: {text}')
        if self.text_instruction:
            return f"{self.text_instruction} {text}"
        return text

    @classmethod
    def class_name(cls) -> str:
        return "InstructionEmbedding"

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get query embedding."""
        formatted_query = self._format_query_text(query)
        if self.embedding_type == "openai":
            return self.model.embedding_model(text=formatted_query, model=self.model_name)
        raise ValueError(f"Unsupported embedding type: {self.embedding_type}")

    async def _aget_query_embedding(self, query: str) -> List[float]:
        """Get query embedding asynchronously."""
        return self._get_query_embedding(query)

    def _get_text_embedding(self, text: str) -> List[float]:
        """Get text embedding."""
        # 如果文本包含metadata和text的组合，只取最后一行作为text
        if '\n' in text:
            text = text.split('\n')[-1].strip()
            
        formatted_text = self._format_text(text)
        if self.embedding_type == "openai":
            return self.model.embedding_model(text=formatted_text, model=self.model_name)
        raise ValueError(f"Unsupported embedding type: {self.embedding_type}")

    async def _aget_text_embedding(self, text: str) -> List[float]:
        """Get text embedding asynchronously."""
        return self._get_text_embedding(text)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get text embeddings for a batch of texts."""
        # 对每个文本进行预处理，只保留最后一行作为实际文本
        processed_texts = []
        for text in texts:
            if '\n' in text:
                text = text.split('\n')[-1].strip()
            processed_texts.append(text)
            
        formatted_texts = [self._format_text(text) for text in processed_texts]
        
        if self.embedding_type == "openai":
            def get_embedding(text):
                return self.model.embedding_model(text=text, model=self.model_name)

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                embeddings = list(executor.map(get_embedding, formatted_texts))
            
            return embeddings
        raise ValueError(f"Unsupported embedding type: {self.embedding_type}")