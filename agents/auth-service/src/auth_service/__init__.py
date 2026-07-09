"""Minimal standalone auth service for enterprise-agent-suite.

Implements the five endpoints the frontend `authClient` calls against
`/api/auth`: login, refresh, logout, me, change-password.

Course MVP scope: in-memory users, JWT access + HttpOnly refresh cookie.
"""

from __future__ import annotations
