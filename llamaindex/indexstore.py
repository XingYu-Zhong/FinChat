import os


from llama_index.core import VectorStoreIndex, Document,StorageContext,load_index_from_storage,Settings
from llamaindex.instructionembedding import InstructionEmbedding
from predata.get_rag_doc import RagDocProcessor

import re

def extract_description(text):
    # 查找 "描述: " 或 "描述：" 后面的内容，直到遇到空行或其他标记行
    pattern = r'描述[:|：]\s*(.*?)(?:\n\n|\n限量|\n输入参数|\n输出参数|\n接口示例)'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

class IndexStore:
    def __init__(self, embedding_model_name="embedding-2", index_dir='.llama_index', 
                 update_rag_doc=False, api_key=None, base_url=None):
        """初始化索引存储
        Args:
            embedding_model_name (str): 嵌入模型名称
            index_dir (str): 索引存储目录
            update_rag_doc (bool): 是否更新 RAG 文档
            api_key (str, optional): API密钥
            base_url (str, optional): 基础URL
        """
        # 初始化嵌入模型
        Settings.embed_model = InstructionEmbedding(
            model_name=embedding_model_name,
            api_key=api_key,
            base_url=base_url
        )
        
        self.index_dir = index_dir
        self.processor = RagDocProcessor(history_nums=None)
        self.titles = self.processor.get_all_titles()
        
        # 初始化文档变更列表
        self.add_doc = []
        self.del_doc_ids = []

        self._initialize_index(update_rag_doc)
        self._persist_index()

    def _process_changes(self, data_list, min_content_length=50):
        """处理文档变更
        Args:
            data_list (list): 变更数据列表
            min_content_length (int): 最小内容长度
        """
        for item in data_list:
            for change in item['change_list']:
                if change['type'] == 'a' and len(change['content']) >= min_content_length:
                    description = extract_description(change['content']) or change['content']
                    # 如果description长度超过100，就只要前100个字符
                    if len(description) > 100:
                        description = description[:100]
                    # 确保text字段不包含'content:'前缀
                    if description.startswith('content:'):
                        description = description[8:].strip()
                    doc = Document(
                        text=description,  # 用于embedding的主要文本内容
                        id_=change['split_md5'],
                        metadata={'full_text': change['content']}  # 完整内容存储在metadata中
                    )
                    self.add_doc.append(doc)
                elif change['type'] == 'd':
                    self.del_doc_ids.append(change['split_md5'])

    def _initialize_index(self, update_rag_doc):
        """初始化或更新索引"""
        if os.path.exists(self.index_dir):
            self._load_existing_index(update_rag_doc)
        else:
            self._create_new_index()

    def _load_existing_index(self, update_rag_doc):
        """加载现有索引"""
        storage_context = StorageContext.from_defaults(persist_dir=self.index_dir)
        self.index = load_index_from_storage(storage_context)
        
        if update_rag_doc:
            data_list = self.processor.update_run()
            self._process_changes(data_list)
            
            # 批量处理文档变更
            if self.del_doc_ids:
                self.index.delete_nodes(self.del_doc_ids)
            if self.add_doc:
                self.index.insert_nodes(self.add_doc)

    def _create_new_index(self):
        """创建新索引"""
        data_list = self.processor.update_run(is_new=True)
        self._process_changes(data_list)
        self.index = VectorStoreIndex(self.add_doc)
        self.add_doc = []  # 清空添加列表

    def _persist_index(self):
        """持久化索引"""
        self.index.storage_context.persist(persist_dir=self.index_dir)

    def search(self, query: str, top_k: int = 5) -> list:
        """搜索相关文档
        Args:
            query (str): 查询文本
            top_k (int): 返回结果数量
        Returns:
            list: 相关文档列表
        """
        response = self.index.as_retriever(similarity_top_k=top_k).retrieve(query)
        return [item.node.metadata.get('full_text', '') for item in response]
    
    def get_titles(self) -> list:
        """获取所有标题
        Returns:
            list: 标题列表
        """
        return self.titles
