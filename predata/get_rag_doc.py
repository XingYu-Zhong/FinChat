import os
import hashlib
import json
import subprocess
import logging
from typing import List, Dict, Any

from llama_index.core import Document
from llama_index.core.node_parser import MarkdownNodeParser


class RagDocProcessor:
    def __init__(self,
                 repo_url: str = 'https://github.com/akfamily/akshare',
                 target_path: str = 'data/akshare',
                 current_docs_file: str = 'data/file/current_docs.jsonl',
                 old_docs_file: str = 'data/file/old_docs.jsonl',
                 update_file: str = 'data/file/update_file.jsonl',
                 current_split: str = 'data/split/current_split.jsonl',
                 old_split: str = 'data/split/old_split.jsonl',
                 output_file: str = 'data/split/change_list.jsonl',
                 history_nums: int = None):
        """
        初始化 RagDocProcessor 类。

        :param repo_url: Git 仓库的 URL，默认值为 'https://github.com/akfamily/akshare'。
        :param target_path: 克隆仓库的目标路径，默认值为 'data/akshare'。
        :param current_docs_file: 当前文档信息的 JSONL 文件路径，默认值为 'data/file/current_docs.jsonl'。
        :param old_docs_file: 旧文档信息的 JSONL 文件路径，默认值为 'data/file/old_docs.jsonl'。
        :param update_file: 更新文件信息的 JSONL 文件路径，默认值为 'data/file/update_file.jsonl'。
        :param current_split: 当前拆分文件的 JSONL 文件路径，默认值为 'data/split/current_split.jsonl'。
        :param old_split: 旧的拆分文件的 JSONL 文件路径，默认值为 'data/split/old_split.jsonl'。
        :param output_file: 变化列表的输出文件路径，默认值为 'data/split/change_list.jsonl'。
        :param history_nums: 获取历史版本的提交数，默认值为 50。
        """
        self.repo_url = repo_url
        self.target_path = target_path
        self.current_docs_file = current_docs_file
        self.old_docs_file = old_docs_file
        self.update_file = update_file
        self.current_split = current_split
        self.old_split = old_split
        self.output_file = output_file
        self.history_nums = history_nums

        # 配置日志
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[
                                logging.FileHandler("rag_doc_processor.log"),
                                logging.StreamHandler()
                            ])
        self.logger = logging.getLogger(__name__)


    @staticmethod
    def md5(content: str) -> str:
        """计算给定内容的 MD5 哈希值。"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def get_md_files_content(self) -> List[Dict[str, Any]]:
        """
        获取目标路径下所有 Markdown 文件的内容和 MD5 哈希值。

        :return: 包含文件信息的列表。
        """
        self.logger.info(f"开始获取 Markdown 文件内容，目标路径: {self.target_path}")
        result = []
        docs_data_path = os.path.join(self.target_path, 'docs', 'data')

        for subdir, _, files in os.walk(docs_data_path):
            subdir_rel = os.path.relpath(subdir, docs_data_path)  # 使用相对路径
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(subdir, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        file_md5 = self.md5(content)
                        result.append({
                            'subdirectory': subdir_rel,
                            'filename': file,
                            'content': content,
                            'file_md5': file_md5
                        })
                    except Exception as e:
                        self.logger.error(f"读取文件 {file_path} 失败: {e}")

        self.logger.info(f"共获取到 {len(result)} 个 Markdown 文件")
        return result

    @staticmethod
    def save_to_jsonl(data: List[Dict[str, Any]], output_file: str):
        """
        将数据保存到 JSONL 文件中。

        :param data: 要保存的数据列表。
        :param output_file: 输出文件路径。
        """
        dir_path = os.path.dirname(output_file)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for entry in data:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            logging.info(f"数据已成功保存到 {output_file}")
        except Exception as e:
            logging.error(f"保存数据到 {output_file} 失败: {e}")

    @staticmethod
    def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
        """
        从 JSONL 文件中加载数据。

        :param file_path: JSONL 文件路径。
        :return: 数据列表。
        """
        if not os.path.exists(file_path):
            logging.warning(f"文件 {file_path} 不存在，返回空列表")
            return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = [json.loads(line) for line in f]
            logging.info(f"已从 {file_path} 加载 {len(data)} 条记录")
            return data
        except Exception as e:
            logging.error(f"加载文件 {file_path} 失败: {e}")
            return []

    def get_changed_files(self, current_files: List[Dict[str, Any]], old_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        获取有变动的文件。

        :param current_files: 当前文件信息列表。
        :param old_files: 旧文件信息列表。
        :return: 变动文件列表。
        """
        self.logger.info("开始比较当前文件和旧文件以获取变动文件")
        old_files_dict = {os.path.join(entry['subdirectory'], entry['filename']): entry['file_md5'] for entry in old_files}
        changed_files = []

        for entry in current_files:
            file_path = os.path.join(entry['subdirectory'], entry['filename'])
            if old_files_dict.get(file_path) != entry['file_md5']:
                changed_files.append(entry)

        self.logger.info(f"共发现 {len(changed_files)} 个变动文件")
        return changed_files

    def update_or_clone_repo(self):
        """
        更新或克隆 Git 仓库。
        """
        self.logger.info(f"开始更新或克隆仓库: {self.repo_url} 到路径: {self.target_path}")
        try:
            if not os.path.exists(self.target_path):
                self.logger.info(f"目标路径 {self.target_path} 不存在，开始克隆仓库")
                subprocess.run(['git', 'clone', self.repo_url, self.target_path], check=True)
                self.logger.info("仓库克隆完成")
            else:
                self.logger.info(f"目标路径 {self.target_path} 已存在，开始拉取最新代码")
                branch = subprocess.run(
                    ['git', '-C', self.target_path, 'rev-parse', '--abbrev-ref', 'HEAD'],
                    capture_output=True, text=True, check=True
                ).stdout.strip()

                if branch == 'HEAD':
                    default_branch = subprocess.run(
                        ['git', '-C', self.target_path, 'symbolic-ref', 'refs/remotes/origin/HEAD'],
                        capture_output=True, text=True, check=True
                    ).stdout.strip().split('/')[-1]
                    self.logger.info(f"当前处于分离 HEAD 状态，切换到默认分支: {default_branch}")
                    subprocess.run(['git', '-C', self.target_path, 'checkout', default_branch], check=True)
                    branch = default_branch

                self.logger.info(f"当前分支: {branch}，开始拉取最新代码")
                subprocess.run(['git', '-C', self.target_path, 'pull', 'origin', branch], check=True)
                self.logger.info(f"已拉取最新代码到分支: {branch}")

            # 切换到指定 commit 或处理历史版本
            if self.history_nums is not None:
                self.logger.info(f"切换到最近 {self.history_nums} 个提交中的最早一个")
                log_command = ['git', '-C', self.target_path, 'log', '--format=%H', f'--max-count={self.history_nums + 1}']
                result = subprocess.run(log_command, capture_output=True, text=True, check=True)
                commits = result.stdout.strip().split('\n')

                if len(commits) > self.history_nums:
                    target_commit = commits[-1]
                    subprocess.run(['git', '-C', self.target_path, 'checkout', target_commit], check=True)
                    self.logger.info(f"已切换到历史提交: {target_commit}")
                else:
                    self.logger.warning(f"无法找到足够的历史提交。找到 {len(commits)} 个提交")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git 操作失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"更新或克隆仓库时发生错误: {e}")
            raise

    def split_markdown(self, content: str) -> Dict[str, str]:
        """
        拆分 Markdown 内容，并生成每个节点的 MD5 哈希值。

        :param content: Markdown 文件内容。
        :return: 拆分后的内容字典，键为 split_md5，值为内容。
        """
        md_doc = Document(text=content)
        parser = MarkdownNodeParser()

        md_nodes = parser.get_nodes_from_documents([md_doc])
        result_dict = {}

        for node in md_nodes:
            if '接口' not in node.text:
                continue
            split_md5 = self.md5(node.text)
            result_dict[split_md5] = node.text

        return result_dict

    def process_update_file(self):
        """
        处理更新文件，拆分内容并保存到 current_split.jsonl。
        """
        self.logger.info("开始处理更新文件")
        update_data = self.load_jsonl(self.update_file)

        split_data = []
        for entry in update_data:
            split_dict = self.split_markdown(entry['content'])
            for split_md5, content in split_dict.items():
                new_entry = {
                    'filename': entry['filename'],
                    'split_md5': split_md5,
                    'content': content
                }
                split_data.append(new_entry)

        if os.path.exists(self.current_split):
            os.rename(self.current_split, self.old_split)
            self.logger.info(f"已将 {self.current_split} 重命名为 {self.old_split}")

        self.save_to_jsonl(split_data, self.current_split)
        self.logger.info(f"已保存拆分后的数据到 {self.current_split}")

    def compare_and_generate_changes(self, current_data: List[Dict[str, Any]], old_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        比较当前数据和旧数据，生成变化列表。

        :param current_data: 当前拆分后的数据列表。
        :param old_data: 旧拆分后的数据列表。
        :return: 变化列表。
        """
        self.logger.info("开始比较当前数据和旧数据以生成变化列表")
        old_dict = {entry['split_md5']: entry for entry in old_data}
        current_dict = {entry['split_md5']: entry for entry in current_data}

        changes_dict = {}

        # 处理添加和修改
        for split_md5, current_entry in current_dict.items():
            filename = current_entry['filename']
            if split_md5 not in old_dict:
                change = {
                    'type': 'a',
                    'split_md5': split_md5,
                    'content': current_entry['content']
                }
                changes_dict.setdefault(filename, {'change_list': []})['change_list'].append(change)
            else:
                old_entry = old_dict[split_md5]
                if old_entry['content'] != current_entry['content']:
                    change_del = {
                        'type': 'd',
                        'split_md5': old_entry['split_md5'],
                        'content': old_entry['content']
                    }
                    change_add = {
                        'type': 'a',
                        'split_md5': current_entry['split_md5'],
                        'content': current_entry['content']
                    }
                    changes_dict.setdefault(filename, {'change_list': []})['change_list'].extend([change_del, change_add])

        # 处理删除
        current_md5s = set(current_dict.keys())
        for split_md5, old_entry in old_dict.items():
            if split_md5 not in current_md5s:
                filename = old_entry['filename']
                change = {
                    'type': 'd',
                    'split_md5': old_entry['split_md5'],
                    'content': old_entry['content']
                }
                changes_dict.setdefault(filename, {'change_list': []})['change_list'].append(change)

        # 转换为列表格式
        changes = [{'filename': filename, 'change_list': changes['change_list']} for filename, changes in changes_dict.items()]
        self.logger.info(f"生成了 {len(changes)} 个变化条目")
        return changes

    def delete_files(self):
        """
        删除target_path目录下的file和split目录及其所有内容
        """
        file_dir = os.path.join('data', 'file')
        split_dir = os.path.join('data', 'split')
        try:
            # 删除file目录
            if os.path.exists(file_dir):
                for file in os.listdir(file_dir):
                    file_path = os.path.join(file_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(file_dir)
                self.logger.info(f"已删除目录: {file_dir}")
                
            # 删除split目录
            if os.path.exists(split_dir):
                for file in os.listdir(split_dir):
                    file_path = os.path.join(split_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(split_dir)
                self.logger.info(f"已删除目录: {split_dir}")
                
        except Exception as e:
            self.logger.error(f"删除目录时发生错误: {e}")

    def update_run(self,is_new=False):
        """
        运行整个流程。
        """
        try:
            # 更新或克隆仓库
            self.update_or_clone_repo()
            # 如果是新创建的索引，需要把target_path下file和split目录下的文件都删除，如果存在的话
            if is_new:
                self.delete_files() # 删除file和split目录下的文件
            # 备份旧文件
            if os.path.exists(self.current_docs_file):
                os.rename(self.current_docs_file, self.old_docs_file)
                self.logger.info(f"已将 {self.current_docs_file} 重命名为 {self.old_docs_file}")

            # 获取当前文件信息
            current_files = self.get_md_files_content()
            self.save_to_jsonl(current_files, self.current_docs_file)

            # 加载旧文件信息
            old_files = self.load_jsonl(self.old_docs_file)

            # 获取有变动的文件
            changed_files = self.get_changed_files(current_files, old_files)
            self.save_to_jsonl(changed_files, self.update_file)

            # 处理更新文件
            if not os.path.exists(self.update_file):
                self.logger.error(f"错误: {self.update_file} 文件不存在。")
                return
            self.process_update_file()

            # 加载 current 和 old 数据
            current_split_data = self.load_jsonl(self.current_split)
            old_split_data = self.load_jsonl(self.old_split)
            if not current_split_data:
                current_split_data = old_split_data

            # 比较并生成变化
            changes = self.compare_and_generate_changes(current_split_data, old_split_data)

            # 保存变化到文件
            self.save_to_jsonl(changes, self.output_file)
            self.logger.info(f"已保存变化列表到 {self.output_file}")
            return changes

        except Exception as e:
            self.logger.error(f"运行过程中发生未捕获的异常: {e}")
            return []

    def get_all_titles(self) -> str:
        """
        获取所有 Markdown 文档的标题数据，并过滤掉无用和重复的标题。
        
        :return: 包含过滤后文档标题的字符串，格式为：
                 文件名: 标题1, 标题2, ...
        """
        self.logger.info("开始获取所有 Markdown 文档的标题")
        titles_data = []
        docs_data_path = os.path.join(self.target_path, 'docs', 'data')
        
        # 用于去重的集合
        seen_titles = set()
        
        # 需要过滤的关键词
        filter_keywords = [
            'AKShare', 'github', 'http', 'www', 
            '接口名称', '接口描述', '请求参数', '返回参数',
            '示例代码', '返回示例'
        ]
        
        for subdir, _, files in os.walk(docs_data_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(subdir, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # 使用正则表达式匹配所有标题（#开头的行）
                        import re
                        titles = re.findall(r'^#+ (.+)$', content, re.MULTILINE)
                        
                        # 过滤和清理标题
                        filtered_titles = []
                        for title in titles:
                            # 跳过包含过滤关键词的标题
                            if any(keyword in title for keyword in filter_keywords):
                                continue
                            
                            # 清理标题中的特殊字符和多余空格
                            title = title.strip()
                            
                            # 去重
                            if title not in seen_titles:
                                seen_titles.add(title)
                                filtered_titles.append(title)
                        
                        if filtered_titles:
                            relative_path = os.path.relpath(file_path, docs_data_path)
                            titles_str = f"{relative_path}: {', '.join(filtered_titles)}"
                            titles_data.append(titles_str)
                            
                    except Exception as e:
                        self.logger.error(f"读取文件 {file_path} 失败: {e}")
        
        result = "\n".join(titles_data)
        self.logger.info(f"已获取 {len(titles_data)} 个文件的标题数据")
        return result



