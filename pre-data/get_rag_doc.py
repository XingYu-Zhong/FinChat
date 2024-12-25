import os
import hashlib
import json
import subprocess

def md5(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def get_md_files_content(target_path):
    result = []
    docs_data_path = os.path.join(target_path, 'docs', 'data')
    
    for subdir, _, files in os.walk(docs_data_path):
        subdir_rel = os.path.relpath(subdir, docs_data_path)  # 使用相对路径
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(subdir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    result.append({
                        'subdirectory': subdir_rel,
                        'filename': file,
                        'content': content,
                        'md5': md5(content)
                    })
    return result

def save_to_jsonl(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def load_jsonl(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def get_changed_files(current_files, old_files):
    old_files_dict = {os.path.join(entry['subdirectory'], entry['filename']): entry['md5'] for entry in old_files}
    changed_files = []
    
    for entry in current_files:
        file_path = os.path.join(entry['subdirectory'], entry['filename'])
        if old_files_dict.get(file_path) != entry['md5']:
            changed_files.append(entry)
    return changed_files

def update_or_clone_repo(url, target_path, commit_id=None, history_nums=None):
    if not os.path.exists(target_path):
        # 如果目标路径不存在，克隆仓库
        subprocess.run(['git', 'clone', url, target_path], check=True)
    else:
        try:
            # 获取当前分支
            branch = subprocess.run(
                ['git', '-C', target_path, 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True, text=True, check=True
            ).stdout.strip()
            
            if branch == 'HEAD':
                # 分离 HEAD 状态，尝试切换到默认分支
                # 获取远程默认分支
                default_branch = subprocess.run(
                    ['git', '-C', target_path, 'symbolic-ref', 'refs/remotes/origin/HEAD'],
                    capture_output=True, text=True, check=True
                ).stdout.strip().split('/')[-1]
                
                print(f"切换到默认分支: {default_branch}")
                subprocess.run(['git', '-C', target_path, 'checkout', default_branch], check=True)
                branch = default_branch
            
            print(f"当前分支: {branch}")
            # 拉取最新代码
            subprocess.run(['git', '-C', target_path, 'pull', 'origin', branch], check=True)
            print(f"已拉取最新代码到分支: {branch}")
        except subprocess.CalledProcessError as e:
            print(f"Error during git operations: {e}")
            raise
    
    # 切换到指定 commit 或处理历史版本
    if commit_id:
        subprocess.run(['git', '-C', target_path, 'checkout', commit_id], check=True)
        print(f"已切换到指定提交: {commit_id}")
    elif history_nums is not None:
        # 获取历史版本的 commit hash
        log_command = ['git', '-C', target_path, 'log', '--format=%H', f'--max-count={history_nums + 1}']
        result = subprocess.run(log_command, capture_output=True, text=True, check=True)
        commits = result.stdout.strip().split('\n')
        
        if len(commits) > history_nums:
            target_commit = commits[-1]
            subprocess.run(['git', '-C', target_path, 'checkout', target_commit], check=True)
            print(f"已切换到历史提交: {target_commit}")
        else:
            print(f"Error: Unable to find sufficient history. Found {len(commits)} commits.")
    else:
        # 如果没有指定 history_nums 或 commit_id，则保持在当前分支，确保在最新提交
        # 不需要额外的 checkout 操作
        latest_commit = subprocess.run(
            ['git', '-C', target_path, 'rev-parse', 'HEAD'],
            capture_output=True, text=True, check=True
        ).stdout.strip()
        print(f"保持在最新提交: {latest_commit}")

if __name__ == '__main__':
    url = 'https://github.com/akfamily/akshare'
    target_path = 'data/akshare'
    update_or_clone_repo(url, target_path, None, 50)

    # 文件路径设置
    current_docs_file = 'data/current_docs.jsonl'
    old_docs_file = 'data/old_docs.jsonl'
    update_file = 'data/update_file.jsonl'

    # 备份旧文件
    if os.path.exists(current_docs_file):
        os.rename(current_docs_file, old_docs_file)

    # 获取当前文件信息
    current_data = get_md_files_content(target_path)
    print(f"当前文件数量: {len(current_data)}")  # 调试信息
    save_to_jsonl(current_data, current_docs_file)

    # 加载旧文件信息
    old_data = load_jsonl(old_docs_file)
    print(f"旧文件数量: {len(old_data)}")  # 调试信息

    # 获取有变动的文件
    changed_files = get_changed_files(current_data, old_data)
    print(f"变动文件数量: {len(changed_files)}")  # 调试信息

    # 保存变动文件信息
    save_to_jsonl(changed_files, update_file)