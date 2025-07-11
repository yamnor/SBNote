import asyncio
import subprocess
import os
from datetime import datetime, timedelta
from typing import List, Optional
from logger import logger

class GitHistoryManager:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.retention_days = 30
        self.max_history_count = 100
    
    def _initialize_git_repository(self):
        """Gitリポジトリの初期化"""
        git_path = os.path.join(self.base_path, '.git')
        
        if not os.path.exists(git_path):
            try:
                # Gitリポジトリを初期化
                subprocess.run(['git', 'init'], cwd=self.base_path, check=True)
                
                # Git設定
                subprocess.run(['git', 'config', 'user.name', 'SBNote System'], 
                             cwd=self.base_path, check=True)
                subprocess.run(['git', 'config', 'user.email', 'system@sbnote.local'], 
                             cwd=self.base_path, check=True)
                
                # .gitignoreを作成
                self._create_gitignore()
                
                # 初期コミット
                subprocess.run(['git', 'add', '.'], cwd=self.base_path, check=True)
                subprocess.run(['git', 'commit', '-m', 'Initial commit: SBNote setup'], 
                             cwd=self.base_path, check=True)
                
                logger.info("Git repository initialized successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to initialize Git repository: {e}")
    
    def _create_gitignore(self):
        """Gitignoreファイルの作成"""
        gitignore_content = """# Attachments (not tracked)
files/
# Search index (not tracked)
index/
# Log files
*.log
# Temporary files
*.tmp
# System files
.DS_Store
Thumbs.db
"""
        gitignore_path = os.path.join(self.base_path, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
    
    async def commit_note_change(self, filename: str, data):
        """ノート変更のGitコミット"""
        try:
            # コミットメッセージを生成
            message = self._generate_commit_message(filename, data)
            
            # Git操作を実行
            subprocess.run(['git', 'add', f'notes/{filename}'], 
                         cwd=self.base_path, check=True)
            subprocess.run(['git', 'commit', '-m', message], 
                         cwd=self.base_path, check=True)
            
            logger.debug(f"Git commit successful: {message}")
            
            # 古い履歴のクリーンアップ
            await self._cleanup_old_history()
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git commit failed: {e}")
            # エラーでもノート保存は継続
        except Exception as e:
            logger.error(f"Unexpected error in Git commit: {e}")
    
    def _generate_commit_message(self, filename: str, data) -> str:
        """コミットメッセージの生成"""
        # データからタイトルを取得（簡易版）
        title = "Unknown"
        if hasattr(data, 'new_title') and data.new_title:
            title = data.new_title
        elif hasattr(data, 'title') and data.title:
            title = data.title
        
        if hasattr(data, 'new_content') and data.new_content is not None:
            return f"Auto-save: {title} - 内容を更新"
        elif hasattr(data, 'new_title') and data.new_title is not None:
            return f"Auto-save: {title} - タイトルを変更"
        elif hasattr(data, 'tags') and data.tags is not None:
            return f"Auto-save: {title} - タグを更新"
        else:
            return f"Auto-save: {title} - 変更"
    
    async def get_note_history(self, filename: str) -> List[dict]:
        """ノートの履歴を取得"""
        try:
            # 拡張子がなければ.mdを付与
            if not filename.endswith('.md'):
                filename = filename + '.md'
            result = subprocess.run(
                ['git', 'log', '--oneline', '--format=%H|%s|%ai', f'notes/{filename}'],
                cwd=self.base_path, capture_output=True, text=True, check=True
            )
            
            history = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 2)
                    if len(parts) >= 3:
                        commit_hash, message, date = parts
                        history.append({
                            'commit_hash': commit_hash,
                            'message': message,
                            'date': date
                        })
            
            return history[:self.max_history_count]
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get note history: {e}")
            return []
    
    async def get_note_version(self, filename: str, commit_hash: str) -> Optional[str]:
        """特定バージョンのノート内容を取得"""
        try:
            # 拡張子がなければ.mdを付与
            if not filename.endswith('.md'):
                filename = filename + '.md'
            result = subprocess.run(
                ['git', 'show', f'{commit_hash}:notes/{filename}'],
                cwd=self.base_path, capture_output=True, text=True, check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get note version: {e}")
            return None
    
    async def restore_note_version(self, filename: str, commit_hash: str) -> bool:
        """特定バージョンに復元"""
        try:
            # 拡張子がなければ.mdを付与
            if not filename.endswith('.md'):
                filename = filename + '.md'
            # 現在のバージョンをバックアップ
            backup_path = self._backup_current_version(filename)
            
            # 指定バージョンの内容を取得
            content = await self.get_note_version(filename, commit_hash)
            if not content:
                return False
            
            # ファイルを復元
            filepath = os.path.join(self.base_path, 'notes', filename)
            with open(filepath, 'w') as f:
                f.write(content)
            
            # 復元をGitに記録
            message = f"Restore: {filename} to version {commit_hash[:8]}"
            subprocess.run(['git', 'add', f'notes/{filename}'], 
                         cwd=self.base_path, check=True)
            subprocess.run(['git', 'commit', '-m', message], 
                         cwd=self.base_path, check=True)
            
            logger.info(f"Note restored successfully: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore note version: {e}")
            # バックアップから復元を試行
            if backup_path:
                self._restore_from_backup(filename, backup_path)
            return False
    
    def _backup_current_version(self, filename: str) -> Optional[str]:
        """現在のバージョンをバックアップ"""
        try:
            backup_dir = os.path.join(self.base_path, '.backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{filename}.backup.{timestamp}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            source_path = os.path.join(self.base_path, 'notes', filename)
            if os.path.exists(source_path):
                import shutil
                shutil.copy2(source_path, backup_path)
                return backup_path
        except Exception as e:
            logger.error(f"Failed to backup current version: {e}")
        return None
    
    def _restore_from_backup(self, filename: str, backup_path: str):
        """バックアップから復元"""
        try:
            target_path = os.path.join(self.base_path, 'notes', filename)
            import shutil
            shutil.copy2(backup_path, target_path)
            logger.info(f"Restored from backup: {filename}")
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
    
    async def _cleanup_old_history(self):
        """古い履歴のクリーンアップ"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d')
            
            # 古いコミットを削除
            subprocess.run([
                'git', 'reflog', 'expire', '--expire=' + cutoff_str
            ], cwd=self.base_path, check=True)
            
            # Git GC
            subprocess.run(['git', 'gc', '--auto'], cwd=self.base_path, check=True)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to cleanup old history: {e}") 