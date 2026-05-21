"""
BOB (Build, Open PR, Branch) Automation
Handles automated code fixes, branch creation, PR management, and deployment.
"""

import logging
import os
import subprocess
from typing import Dict, Any, Optional, List
from pathlib import Path
import git
from github import Github, GithubException

from src.config_manager import ConfigManager
from src.utils import retry_with_backoff, sanitize_string, format_timestamp

logger = logging.getLogger(__name__)


class BOBAutomation:
    """Automates the process of applying fixes and creating pull requests."""
    
    def __init__(self, config: ConfigManager):
        """
        Initialize BOB automation.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.bob_config = config.get_bob_config()
        
        self.repository_url = self.bob_config.get('repository_url', '')
        self.repository_token = self.bob_config.get('repository_token', '')
        self.base_branch = self.bob_config.get('base_branch', 'main')
        self.branch_prefix = self.bob_config.get('branch_prefix', 'autofix')
        self.require_approval = self.bob_config.get('require_approval', True)
        self.auto_merge = self.bob_config.get('auto_merge_on_approval', True)
        
        # Initialize GitHub client
        self.github_client = Github(self.repository_token)
        
        # Extract repository info from URL
        self.repo_owner, self.repo_name = self._parse_repository_url()
        
        # Local repository path
        self.local_repo_path = Path('temp_repo')
        
        logger.info(f"BOB automation initialized for {self.repo_owner}/{self.repo_name}")
    
    def _parse_repository_url(self) -> tuple:
        """
        Parse repository URL to extract owner and name.
        
        Returns:
            Tuple of (owner, repo_name)
        """
        # Handle different URL formats
        url = self.repository_url.replace('.git', '')
        
        if 'github.com' in url:
            parts = url.split('github.com/')[-1].split('/')
            return parts[0], parts[1]
        else:
            raise ValueError(f"Unsupported repository URL format: {self.repository_url}")
    
    @retry_with_backoff(max_retries=3)
    def clone_repository(self) -> git.Repo:
        """
        Clone the repository locally.
        
        Returns:
            Git repository object
        """
        logger.info(f"Cloning repository to {self.local_repo_path}")
        
        # Remove existing directory if present
        if self.local_repo_path.exists():
            import shutil
            shutil.rmtree(self.local_repo_path)
        
        # Clone with authentication
        auth_url = self.repository_url.replace(
            'https://',
            f'https://{self.repository_token}@'
        )
        
        repo = git.Repo.clone_from(auth_url, self.local_repo_path)
        logger.info("Repository cloned successfully")
        
        return repo
    
    def create_branch(self, branch_name: str, repo: git.Repo) -> str:
        """
        Create a new branch for the fix.
        
        Args:
            branch_name: Name of the branch
            repo: Git repository object
            
        Returns:
            Full branch name
        """
        # Ensure we're on the base branch
        repo.git.checkout(self.base_branch)
        repo.git.pull('origin', self.base_branch)
        
        # Create and checkout new branch
        full_branch_name = f"{self.branch_prefix}/{branch_name}"
        repo.git.checkout('-b', full_branch_name)
        
        logger.info(f"Created branch: {full_branch_name}")
        return full_branch_name
    
    def apply_code_patch(self, code_fix: Dict[str, Any], repo: git.Repo) -> bool:
        """
        Apply code fix to the repository.
        
        Args:
            code_fix: Code fix information from ICA
            repo: Git repository object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(self.local_repo_path) / code_fix['file_path']
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Apply changes
            if 'diff' in code_fix and code_fix['diff']:
                # Apply diff patch
                logger.info(f"Applying diff patch to {code_fix['file_path']}")
                
                # Write diff to temporary file
                diff_file = Path(self.local_repo_path) / 'temp.patch'
                with open(diff_file, 'w') as f:
                    f.write(code_fix['diff'])
                
                # Apply patch
                repo.git.apply(str(diff_file))
                diff_file.unlink()
                
            elif 'changes' in code_fix:
                # Apply line-by-line changes
                logger.info(f"Applying changes to {code_fix['file_path']}")
                
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        content = f.read()
                else:
                    content = ""
                
                # Apply each change
                for change in code_fix['changes']:
                    old_text = change.get('old', '')
                    new_text = change.get('new', '')
                    content = content.replace(old_text, new_text)
                
                # Write updated content
                with open(file_path, 'w') as f:
                    f.write(content)
            
            logger.info(f"Code patch applied successfully to {code_fix['file_path']}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying code patch: {str(e)}")
            return False
    
    def apply_iac_patch(self, iac_fix: Dict[str, Any], repo: git.Repo) -> bool:
        """
        Apply Infrastructure as Code fix to the repository.
        
        Args:
            iac_fix: IaC fix information from ICA
            repo: Git repository object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(self.local_repo_path) / iac_fix['file_path']
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read current content
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
            else:
                content = ""
            
            # Apply changes
            for change in iac_fix.get('changes', []):
                old_text = change.get('old', '')
                new_text = change.get('new', '')
                content = content.replace(old_text, new_text)
            
            # Write updated content
            with open(file_path, 'w') as f:
                f.write(content)
            
            logger.info(f"IaC patch applied successfully to {iac_fix['file_path']}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying IaC patch: {str(e)}")
            return False
    
    def apply_config_patch(self, config_fix: Dict[str, Any], repo: git.Repo) -> bool:
        """
        Apply configuration fix to the repository.
        
        Args:
            config_fix: Configuration fix information from ICA
            repo: Git repository object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import json
            import yaml
            
            config_file = Path(self.local_repo_path) / config_fix['config_file']
            
            # Determine file type
            if config_file.suffix in ['.json']:
                # JSON configuration
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                else:
                    config_data = {}
                
                # Apply settings
                config_data.update(config_fix.get('settings', {}))
                
                # Write updated config
                with open(config_file, 'w') as f:
                    json.dump(config_data, f, indent=2)
                    
            elif config_file.suffix in ['.yaml', '.yml']:
                # YAML configuration
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config_data = yaml.safe_load(f)
                else:
                    config_data = {}
                
                # Apply settings
                config_data.update(config_fix.get('settings', {}))
                
                # Write updated config
                with open(config_file, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            
            logger.info(f"Configuration patch applied successfully to {config_fix['config_file']}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying configuration patch: {str(e)}")
            return False
    
    def run_build(self, repo: git.Repo) -> bool:
        """
        Run build command to verify changes.
        
        Args:
            repo: Git repository object
            
        Returns:
            True if build successful, False otherwise
        """
        build_command = self.bob_config.get('build_command', '')
        
        if not build_command:
            logger.info("No build command configured, skipping build")
            return True
        
        try:
            logger.info(f"Running build command: {build_command}")
            
            result = subprocess.run(
                build_command,
                shell=True,
                cwd=self.local_repo_path,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                logger.info("Build completed successfully")
                return True
            else:
                logger.error(f"Build failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error running build: {str(e)}")
            return False
    
    def run_tests(self, repo: git.Repo) -> bool:
        """
        Run tests to verify changes.
        
        Args:
            repo: Git repository object
            
        Returns:
            True if tests pass, False otherwise
        """
        test_command = self.bob_config.get('test_command', '')
        
        if not test_command:
            logger.info("No test command configured, skipping tests")
            return True
        
        try:
            logger.info(f"Running test command: {test_command}")
            
            result = subprocess.run(
                test_command,
                shell=True,
                cwd=self.local_repo_path,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                logger.info("Tests passed successfully")
                return True
            else:
                logger.error(f"Tests failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error running tests: {str(e)}")
            return False
    
    def commit_changes(self, repo: git.Repo, commit_message: str) -> bool:
        """
        Commit changes to the repository.
        
        Args:
            repo: Git repository object
            commit_message: Commit message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Stage all changes
            repo.git.add(A=True)
            
            # Check if there are changes to commit
            if not repo.is_dirty():
                logger.warning("No changes to commit")
                return False
            
            # Commit changes
            repo.index.commit(commit_message)
            logger.info(f"Changes committed: {commit_message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error committing changes: {str(e)}")
            return False
    
    def push_branch(self, repo: git.Repo, branch_name: str) -> bool:
        """
        Push branch to remote repository.
        
        Args:
            repo: Git repository object
            branch_name: Branch name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            origin = repo.remote('origin')
            origin.push(branch_name)
            
            logger.info(f"Branch pushed to remote: {branch_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error pushing branch: {str(e)}")
            return False
    
    def create_pull_request(
        self,
        branch_name: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Create a pull request on GitHub.
        
        Args:
            branch_name: Source branch name
            title: PR title
            body: PR description
            labels: Optional list of labels
            
        Returns:
            PR URL if successful, None otherwise
        """
        try:
            repo = self.github_client.get_repo(f"{self.repo_owner}/{self.repo_name}")
            
            # Create pull request
            pr = repo.create_pull(
                title=title,
                body=body,
                head=branch_name,
                base=self.base_branch
            )
            
            # Add labels if provided
            if labels:
                pr.add_to_labels(*labels)
            
            logger.info(f"Pull request created: {pr.html_url}")
            return pr.html_url
            
        except GithubException as e:
            logger.error(f"Error creating pull request: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating pull request: {str(e)}")
            return None
    
    def apply_patches(
        self,
        analysis_package: Dict[str, Any],
        operation_id: str
    ) -> Dict[str, Any]:
        """
        Complete workflow: apply patches, build, test, and create PR.
        
        Args:
            analysis_package: Analysis package from ICA
            operation_id: Operation ID for tracking
            
        Returns:
            Result dictionary with status and details
        """
        logger.info(f"Starting BOB automation workflow for operation {operation_id}")
        
        try:
            # Clone repository
            repo = self.clone_repository()
            
            # Create branch
            branch_name = sanitize_string(f"{operation_id}-{format_timestamp()}", max_length=50)
            full_branch_name = self.create_branch(branch_name, repo)
            
            # Apply fixes
            fixes_applied = []
            
            code_fix = analysis_package.get('fixes', {}).get('code_fix')
            if code_fix:
                if self.apply_code_patch(code_fix, repo):
                    fixes_applied.append('code')
            
            iac_fix = analysis_package.get('fixes', {}).get('iac_fix')
            if iac_fix:
                if self.apply_iac_patch(iac_fix, repo):
                    fixes_applied.append('infrastructure')
            
            config_fix = analysis_package.get('fixes', {}).get('config_fix')
            if config_fix:
                if self.apply_config_patch(config_fix, repo):
                    fixes_applied.append('configuration')
            
            if not fixes_applied:
                logger.warning("No fixes were applied")
                return {
                    'status': 'no_changes',
                    'message': 'No fixes were applied',
                    'timestamp': format_timestamp()
                }
            
            # Run build
            if not self.run_build(repo):
                logger.error("Build failed, aborting")
                return {
                    'status': 'build_failed',
                    'message': 'Build failed after applying fixes',
                    'timestamp': format_timestamp()
                }
            
            # Run tests
            if not self.run_tests(repo):
                logger.error("Tests failed, aborting")
                return {
                    'status': 'tests_failed',
                    'message': 'Tests failed after applying fixes',
                    'timestamp': format_timestamp()
                }
            
            # Commit changes
            root_cause = analysis_package.get('root_cause', {})
            commit_message = f"Auto-fix: {root_cause.get('summary', 'Fix applied')}\n\nOperation ID: {operation_id}"
            
            if not self.commit_changes(repo, commit_message):
                logger.error("Failed to commit changes")
                return {
                    'status': 'commit_failed',
                    'message': 'Failed to commit changes',
                    'timestamp': format_timestamp()
                }
            
            # Push branch
            if not self.push_branch(repo, full_branch_name):
                logger.error("Failed to push branch")
                return {
                    'status': 'push_failed',
                    'message': 'Failed to push branch to remote',
                    'timestamp': format_timestamp()
                }
            
            # Create pull request
            pr_title = f"[Auto-Fix] {root_cause.get('summary', 'Automated fix')}"
            pr_body = self._generate_pr_body(analysis_package, operation_id, fixes_applied)
            pr_url = self.create_pull_request(
                full_branch_name,
                pr_title,
                pr_body,
                labels=['automated-fix', 'needs-review']
            )
            
            if not pr_url:
                logger.error("Failed to create pull request")
                return {
                    'status': 'pr_failed',
                    'message': 'Failed to create pull request',
                    'timestamp': format_timestamp()
                }
            
            logger.info(f"BOB automation workflow completed successfully")
            
            return {
                'status': 'success',
                'message': 'Fixes applied and pull request created',
                'branch_name': full_branch_name,
                'pr_url': pr_url,
                'fixes_applied': fixes_applied,
                'requires_approval': self.require_approval,
                'timestamp': format_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error in BOB automation workflow: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': format_timestamp()
            }
    
    def _generate_pr_body(
        self,
        analysis_package: Dict[str, Any],
        operation_id: str,
        fixes_applied: List[str]
    ) -> str:
        """
        Generate pull request body with detailed information.
        
        Args:
            analysis_package: Analysis package from ICA
            operation_id: Operation ID
            fixes_applied: List of fix types applied
            
        Returns:
            PR body text
        """
        root_cause = analysis_package.get('root_cause', {})
        risk_assessment = analysis_package.get('risk_assessment', {})
        
        body = f"""## Automated Fix

**Operation ID:** `{operation_id}`
**Timestamp:** {format_timestamp()}

### Root Cause
{root_cause.get('summary', 'Unknown')}

**Category:** {root_cause.get('category', 'unknown')}
**Confidence:** {root_cause.get('confidence', 0):.1%}

### Fixes Applied
{', '.join(fixes_applied).title()}

### Risk Assessment
- **Overall Risk:** {risk_assessment.get('overall_risk', 'medium')}
- **Impact Scope:** {risk_assessment.get('impact_scope', 'unknown')}
- **Testing Required:** {'Yes' if risk_assessment.get('testing_required', True) else 'No'}
- **Approval Required:** {'Yes' if self.require_approval else 'No'}

### Details
{root_cause.get('details', 'No additional details available')}

### Next Steps
"""
        
        for step in analysis_package.get('next_steps', []):
            body += f"- {step}\n"
        
        body += "\n---\n*This pull request was automatically generated by BOB (Build, Open PR, Branch) automation.*"
        
        return body

# Made with Bob
