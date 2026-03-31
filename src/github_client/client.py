"""Async GitHub API client for PR review operations."""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_PR_URL_PATTERN = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)"
)
_API_BASE = "https://api.github.com"


class GitHubClient:
    """Client for interacting with the GitHub API."""

    def __init__(self, token: str | None = None) -> None:
        """Initialize the GitHub client.

        Args:
            token: GitHub personal access token. Falls back to GITHUB_TOKEN env var.
        """
        self._token = token or os.environ["GITHUB_TOKEN"]
        self._headers = {
            "Authorization": f"token {self._token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    @staticmethod
    def _parse_pr_url(pr_url: str) -> tuple[str, str, int]:
        """Extract owner, repo, and PR number from a GitHub PR URL.

        Args:
            pr_url: Full GitHub pull request URL.

        Returns:
            Tuple of (owner, repo, pr_number).

        Raises:
            ValueError: If the URL does not match the expected pattern.
        """
        match = _PR_URL_PATTERN.match(pr_url)
        if not match:
            raise ValueError(f"Invalid GitHub PR URL: {pr_url}")
        return match["owner"], match["repo"], int(match["number"])

    async def get_pr_diff(self, pr_url: str) -> str:
        """Fetch the unified diff for a pull request.

        Args:
            pr_url: Full GitHub pull request URL.

        Returns:
            The raw unified diff as a string.
        """
        owner, repo, pr_number = self._parse_pr_url(pr_url)
        url = f"{_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {**self._headers, "Accept": "application/vnd.github.v3.diff"}

        async with httpx.AsyncClient() as client:
            logger.info("Fetching diff for %s/%s#%d", owner, repo, pr_number)
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text

    async def get_pr_files(self, pr_url: str) -> list[dict[str, Any]]:
        """Fetch the list of changed files in a pull request.

        Args:
            pr_url: Full GitHub pull request URL.

        Returns:
            List of file metadata dicts from the GitHub API.
        """
        owner, repo, pr_number = self._parse_pr_url(pr_url)
        url = f"{_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files"

        async with httpx.AsyncClient() as client:
            logger.info("Fetching files for %s/%s#%d", owner, repo, pr_number)
            response = await client.get(url, headers=self._headers)
            response.raise_for_status()
            return response.json()

    async def post_review_comment(
        self, pr_url: str, body: str, commit_sha: str
    ) -> None:
        """Post a top-level review comment on a pull request.

        Args:
            pr_url: Full GitHub pull request URL.
            body: Markdown body of the review comment.
            commit_sha: The commit SHA to attach the review to.
        """
        owner, repo, pr_number = self._parse_pr_url(pr_url)
        url = f"{_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        payload = {
            "commit_id": commit_sha,
            "body": body,
            "event": "COMMENT",
        }

        async with httpx.AsyncClient() as client:
            logger.info("Posting review comment on %s/%s#%d", owner, repo, pr_number)
            response = await client.post(
                url, headers=self._headers, json=payload
            )
            response.raise_for_status()

    async def post_inline_comment(
        self,
        pr_url: str,
        body: str,
        commit_sha: str,
        path: str,
        line: int,
    ) -> None:
        """Post an inline review comment on a specific file and line.

        Args:
            pr_url: Full GitHub pull request URL.
            body: Markdown body of the inline comment.
            commit_sha: The commit SHA to attach the comment to.
            path: File path relative to the repo root.
            line: Line number in the diff to comment on.
        """
        owner, repo, pr_number = self._parse_pr_url(pr_url)
        url = f"{_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        payload = {
            "commit_id": commit_sha,
            "body": body,
            "path": path,
            "line": line,
            "side": "RIGHT",
        }

        async with httpx.AsyncClient() as client:
            logger.info(
                "Posting inline comment on %s/%s#%d at %s:%d",
                owner, repo, pr_number, path, line,
            )
            response = await client.post(
                url, headers=self._headers, json=payload
            )
            response.raise_for_status()
