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
        """Initialize Git repository"""
        git_path = os.path.join(self.base_path, '.git')
        
        if not os.path.exists(git_path):
            try:
                # Initialize Git repository
                subprocess.run(['git', 'init'], cwd=self.base_path, check=True)
                
                # Git configuration
                subprocess.run(['git', 'config', 'user.name', 'SBNote System'], 
                             cwd=self.base_path, check=True)
                subprocess.run(['git', 'config', 'user.email', 'system@sbnote.local'], 
                             cwd=self.base_path, check=True)
                
                # Create .gitignore
                self._create_gitignore()
                
                # Initial commit
                subprocess.run(['git', 'add', '.'], cwd=self.base_path, check=True)
                subprocess.run(['git', 'commit', '-m', 'Initial commit: SBNote setup'], 
                             cwd=self.base_path, check=True)
                
                logger.info("Git repository initialized successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to initialize Git repository: {e}")
    
    def _create_gitignore(self):
        """Create .gitignore file"""
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
        """Git commit for note changes"""
        try:
            # Generate commit message
            message = self._generate_commit_message(filename, data)
            
            # Execute Git operations
            subprocess.run(['git', 'add', f'notes/{filename}'], 
                         cwd=self.base_path, check=True)
            subprocess.run(['git', 'commit', '-m', message], 
                         cwd=self.base_path, check=True)
            
            logger.debug(f"Git commit successful: {message}")
            
            # Cleanup old history
            await self._cleanup_old_history()
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git commit failed: {e}")
            # Continue note saving even if error occurs
        except Exception as e:
            logger.error(f"Unexpected error in Git commit: {e}")
    
    def _generate_commit_message(self, filename: str, data) -> str:
        """Generate commit message"""
        # Get title from data (simplified)
        title = "Unknown"
        if hasattr(data, 'new_title') and data.new_title:
            title = data.new_title
        elif hasattr(data, 'title') and data.title:
            title = data.title
        
        if hasattr(data, 'new_content') and data.new_content is not None:
            return f"Auto-save: {title} - Update content"
        elif hasattr(data, 'new_title') and data.new_title is not None:
            return f"Auto-save: {title} - Change title"
        elif hasattr(data, 'tags') and data.tags is not None:
            return f"Auto-save: {title} - Update tags"
        else:
            return f"Auto-save: {title} - Changes"
    
    async def get_note_history(self, filename: str) -> List[dict]:
        """Get note history"""
        try:
            # Add .md extension if not present
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
        """Get content of specific version"""
        try:
            # Add .md extension if not present
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
        """Restore to specific version"""
        try:
            # Add .md extension if not present
            if not filename.endswith('.md'):
                filename = filename + '.md'
            # Backup current version
            backup_path = self._backup_current_version(filename)
            
            # Get content of specified version
            content = await self.get_note_version(filename, commit_hash)
            if not content:
                return False
            
            # Restore file
            filepath = os.path.join(self.base_path, 'notes', filename)
            with open(filepath, 'w') as f:
                f.write(content)
            
            # Record restoration in Git
            message = f"Restore: {filename} to version {commit_hash[:8]}"
            subprocess.run(['git', 'add', f'notes/{filename}'], 
                         cwd=self.base_path, check=True)
            subprocess.run(['git', 'commit', '-m', message], 
                         cwd=self.base_path, check=True)
            
            logger.info(f"Note restored successfully: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore note version: {e}")
            # Try to restore from backup
            if backup_path:
                self._restore_from_backup(filename, backup_path)
            return False
    
    def _backup_current_version(self, filename: str) -> Optional[str]:
        """Backup current version"""
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
        """Restore from backup"""
        try:
            target_path = os.path.join(self.base_path, 'notes', filename)
            import shutil
            shutil.copy2(backup_path, target_path)
            logger.info(f"Restored from backup: {filename}")
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
    
    async def _cleanup_old_history(self):
        """Cleanup old history"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d')
            
            # Delete old commits
            subprocess.run([
                'git', 'reflog', 'expire', '--expire=' + cutoff_str
            ], cwd=self.base_path, check=True)
            
            # Git GC
            subprocess.run(['git', 'gc', '--auto'], cwd=self.base_path, check=True)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to cleanup old history: {e}") 