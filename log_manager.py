import os
import asyncio
from datetime import datetime
from typing import List
from collections import deque
import aiofiles
import time

class LogManager:
    def __init__(self, log_file: str, max_lines: int = 1000):
        self.log_file = log_file
        self.max_lines = max_lines
        self.log_buffer = deque(maxlen=max_lines)
        self.lock = asyncio.Lock()
        self.last_file_size = 0
        self.last_file_inode = 0
        self.last_check_time = 0
        
    async def initialize(self):
        """初始化日志管理器，读取现有日志"""
        if not os.path.exists(self.log_file):
            async with aiofiles.open(self.log_file, 'w', encoding='utf-8') as f:
                await f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 日志系统初始化\n")
        
        await self._read_full_log()
        self._update_file_stats()

    def _update_file_stats(self):
        """更新文件状态"""
        try:
            stat = os.stat(self.log_file)
            self.last_file_size = stat.st_size
            self.last_file_inode = stat.st_ino
            self.last_check_time = time.time()
        except Exception as e:
            print(f"更新文件状态失败: {e}")

    async def _read_full_log(self):
        """读取整个日志文件"""
        try:
            async with aiofiles.open(self.log_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                lines = content.splitlines()
                self.log_buffer.clear()
                self.log_buffer.extend(line + '\n' for line in lines[-self.max_lines:])
        except Exception as e:
            print(f"读取日志文件失败: {e}")

    async def _check_file_changes(self):
        """检查文件是否有更新"""
        try:
            current_stat = os.stat(self.log_file)
            current_size = current_stat.st_size
            current_inode = current_stat.st_ino
            
            # 如果文件被替换（inode改变）或被截断（大小变小）
            if current_inode != self.last_file_inode or current_size < self.last_file_size:
                await self._read_full_log()
                self._update_file_stats()
                return
            
            # 如果文件有新内容
            if current_size > self.last_file_size:
                async with aiofiles.open(self.log_file, 'r', encoding='utf-8') as f:
                    await f.seek(self.last_file_size)
                    new_content = await f.read()
                    if new_content:
                        new_lines = new_content.splitlines()
                        self.log_buffer.extend(line + '\n' for line in new_lines)
                
                self.last_file_size = current_size
                self.last_file_inode = current_inode
                self.last_check_time = time.time()
            
        except Exception as e:
            print(f"检查文件更新失败: {e}")
            # 如果检查失败，尝试重新读取整个文件
            await self._read_full_log()
            self._update_file_stats()

    async def append_log(self, message: str):
        """异步追加日志"""
        async with self.lock:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"[{timestamp}] {message}\n"
            
            try:
                async with aiofiles.open(self.log_file, 'a', encoding='utf-8') as f:
                    await f.write(log_entry)
                self.log_buffer.append(log_entry)
                self._update_file_stats()
            except Exception as e:
                print(f"写入日志失败: {e}")

    async def get_logs(self) -> str:
        """获取最新的日志"""
        async with self.lock:
            # 检查文件是否有更新
            await self._check_file_changes()
            return "".join(self.log_buffer)

    async def clear_logs(self):
        """清除所有日志"""
        async with self.lock:
            try:
                async with aiofiles.open(self.log_file, 'w', encoding='utf-8') as f:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    log_entry = f"[{timestamp}] 日志已清除\n"
                    await f.write(log_entry)
                    self.log_buffer.clear()
                    self.log_buffer.append(log_entry)
                self._update_file_stats()
            except Exception as e:
                print(f"清除日志失败: {e}")

class SyncLogManager:
    def __init__(self, log_file: str, max_lines: int = 1000):
        self.log_file = log_file
        self.max_lines = max_lines
        self.log_buffer = deque(maxlen=max_lines)
        self.last_file_size = 0
        self.last_file_inode = 0
        self.last_check_time = 0
        self.initialize()
        
    def initialize(self):
        """初始化日志管理器，读取现有日志"""
        # 只在文件不存在时创建新文件
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] 日志系统初始化\n")
        
        # 读取现有日志内容
        self._read_full_log()
        self._update_file_stats()

    def _update_file_stats(self):
        """更新文件状态"""
        try:
            stat = os.stat(self.log_file)
            self.last_file_size = stat.st_size
            self.last_file_inode = stat.st_ino
            self.last_check_time = time.time()
        except Exception as e:
            print(f"更新文件状态失败: {e}")

    def _read_full_log(self):
        """读取整个日志文件"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
                self.log_buffer.clear()
                self.log_buffer.extend(line + '\n' for line in lines[-self.max_lines:])
        except Exception as e:
            print(f"读取日志文件失败: {e}")

    def _check_file_changes(self):
        """检查文件是否有更新"""
        try:
            current_stat = os.stat(self.log_file)
            current_size = current_stat.st_size
            current_inode = current_stat.st_ino
            
            # 如果文件被替换（inode改变）或被截断（大小变小）
            if current_inode != self.last_file_inode or current_size < self.last_file_size:
                self._read_full_log()
                self._update_file_stats()
                return
            
            # 如果文件有新内容
            if current_size > self.last_file_size:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    f.seek(self.last_file_size)
                    new_content = f.read()
                    if new_content:
                        new_lines = new_content.splitlines()
                        self.log_buffer.extend(line + '\n' for line in new_lines)
                
                self.last_file_size = current_size
                self.last_file_inode = current_inode
                self.last_check_time = time.time()
            
        except Exception as e:
            print(f"检查文件更新失败: {e}")
            # 如果检查失败，尝试重新读取整个文件
            self._read_full_log()
            self._update_file_stats()

    def append_log(self, message: str):
        """同步追加日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        try:
            # 确保文件句柄正确关闭，并立即写入磁盘
            with open(self.log_file, 'a', encoding='utf-8', buffering=1) as f:
                f.write(log_entry)
                f.flush()
                os.fsync(f.fileno())
            self.log_buffer.append(log_entry)
            self._update_file_stats()
        except Exception as e:
            print(f"写入日志失败: {e}")

    def get_logs(self) -> str:
        """获取最新的日志"""
        # 检查文件是否有更新
        self._check_file_changes()
        return "".join(self.log_buffer)

    def clear_logs(self):
        """清除所有日志"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                log_entry = f"[{timestamp}] 日志已清除\n"
                f.write(log_entry)
                self.log_buffer.clear()
                self.log_buffer.append(log_entry)
            self._update_file_stats()
        except Exception as e:
            print(f"清除日志失败: {e}")

# 创建全局日志管理器实例
async_log_manager = None
sync_log_manager = None

async def init_async_log_manager(log_file: str):
    """初始化全局异步日志管理器"""
    global async_log_manager
    async_log_manager = LogManager(log_file)
    await async_log_manager.initialize()

def init_sync_log_manager(log_file: str):
    """初始化全局同步日志管理器"""
    global sync_log_manager
    sync_log_manager = SyncLogManager(log_file)

async def get_async_log_manager() -> LogManager:
    """获取异步日志管理器实例"""
    if async_log_manager is None:
        raise RuntimeError("异步日志管理器未初始化")
    return async_log_manager

def get_sync_log_manager() -> SyncLogManager:
    """获取同步日志管理器实例"""
    if sync_log_manager is None:
        raise RuntimeError("同步日志管理器未初始化")
    return sync_log_manager 