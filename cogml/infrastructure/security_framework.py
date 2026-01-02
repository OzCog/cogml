#!/usr/bin/env python3
"""
Security Framework with Unified Controls

Phase 2 Implementation: Provides comprehensive security controls including:
- Authentication and authorization
- Role-based access control (RBAC)
- API key management
- Request validation and sanitization
- Rate limiting
- Audit logging
- Encryption utilities
"""

import asyncio
import hashlib
import hmac
import json
import time
import secrets
import logging
import threading
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict
from functools import wraps
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Permission(Enum):
    """System permissions"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    KERNEL_ACCESS = "kernel_access"
    PIPELINE_MANAGE = "pipeline_manage"
    PLUGIN_MANAGE = "plugin_manage"
    METRICS_VIEW = "metrics_view"
    TRACE_VIEW = "trace_view"
    CONFIG_MODIFY = "config_modify"


class ResourceType(Enum):
    """Protected resource types"""
    KERNEL = "kernel"
    PIPELINE = "pipeline"
    PLUGIN = "plugin"
    ATOMSPACE = "atomspace"
    CONFIG = "config"
    METRICS = "metrics"
    TRACES = "traces"
    SYSTEM = "system"


@dataclass
class Role:
    """User role with associated permissions"""
    name: str
    description: str
    permissions: Set[Permission] = field(default_factory=set)
    resource_access: Dict[ResourceType, Set[Permission]] = field(default_factory=dict)

    def has_permission(self, permission: Permission) -> bool:
        """Check if role has a permission"""
        return permission in self.permissions or Permission.ADMIN in self.permissions

    def can_access_resource(self, resource_type: ResourceType, permission: Permission) -> bool:
        """Check if role can access a resource with given permission"""
        if Permission.ADMIN in self.permissions:
            return True
        if resource_type in self.resource_access:
            return permission in self.resource_access[resource_type]
        return False


@dataclass
class Identity:
    """User or service identity"""
    identity_id: str
    name: str
    identity_type: str  # "user", "service", "api_key"
    roles: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    last_active: float = 0.0
    active: bool = True


@dataclass
class APIKey:
    """API key for authentication"""
    key_id: str
    key_hash: str  # Hashed key value
    identity_id: str
    name: str
    scopes: Set[str] = field(default_factory=set)
    created_at: float = 0.0
    expires_at: Optional[float] = None
    last_used: float = 0.0
    active: bool = True


@dataclass
class Session:
    """Active session"""
    session_id: str
    identity_id: str
    created_at: float
    expires_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    active: bool = True


@dataclass
class AuditEvent:
    """Security audit event"""
    event_id: str
    timestamp: float
    event_type: str
    identity_id: Optional[str]
    resource_type: Optional[ResourceType]
    resource_id: Optional[str]
    action: str
    result: str  # "success", "failure", "denied"
    details: Dict[str, Any] = field(default_factory=dict)
    source_ip: Optional[str] = None


class AuthenticationProvider(ABC):
    """Abstract base for authentication providers"""

    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> Optional[Identity]:
        """Authenticate and return identity if successful"""
        pass


class APIKeyAuthProvider(AuthenticationProvider):
    """API key authentication provider"""

    def __init__(self, key_store: Dict[str, APIKey]):
        self.key_store = key_store

    def authenticate(self, credentials: Dict[str, Any]) -> Optional[Identity]:
        """Authenticate using API key"""
        api_key = credentials.get("api_key")
        if not api_key:
            return None

        key_hash = self._hash_key(api_key)

        for stored_key in self.key_store.values():
            if hmac.compare_digest(stored_key.key_hash, key_hash):
                if not stored_key.active:
                    return None
                if stored_key.expires_at and time.time() > stored_key.expires_at:
                    return None

                stored_key.last_used = time.time()
                return Identity(
                    identity_id=stored_key.identity_id,
                    name=stored_key.name,
                    identity_type="api_key",
                    metadata={"key_id": stored_key.key_id}
                )

        return None

    def _hash_key(self, key: str) -> str:
        """Hash an API key"""
        return hashlib.sha256(key.encode()).hexdigest()


class RBACManager:
    """Role-based access control manager"""

    # Predefined roles
    DEFAULT_ROLES = {
        "admin": Role(
            name="admin",
            description="Full system access",
            permissions={Permission.ADMIN}
        ),
        "operator": Role(
            name="operator",
            description="Operational access",
            permissions={
                Permission.READ,
                Permission.EXECUTE,
                Permission.KERNEL_ACCESS,
                Permission.PIPELINE_MANAGE,
                Permission.METRICS_VIEW,
                Permission.TRACE_VIEW
            }
        ),
        "developer": Role(
            name="developer",
            description="Development access",
            permissions={
                Permission.READ,
                Permission.WRITE,
                Permission.EXECUTE,
                Permission.PLUGIN_MANAGE
            },
            resource_access={
                ResourceType.PLUGIN: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
                ResourceType.PIPELINE: {Permission.READ, Permission.WRITE},
                ResourceType.KERNEL: {Permission.READ}
            }
        ),
        "viewer": Role(
            name="viewer",
            description="Read-only access",
            permissions={Permission.READ, Permission.METRICS_VIEW, Permission.TRACE_VIEW}
        )
    }

    def __init__(self):
        self._roles: Dict[str, Role] = dict(self.DEFAULT_ROLES)
        self._identity_roles: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.RLock()

    def add_role(self, role: Role):
        """Add a custom role"""
        with self._lock:
            self._roles[role.name] = role

    def remove_role(self, role_name: str) -> bool:
        """Remove a role"""
        with self._lock:
            if role_name in self.DEFAULT_ROLES:
                return False  # Can't remove default roles
            if role_name in self._roles:
                del self._roles[role_name]
                return True
            return False

    def get_role(self, role_name: str) -> Optional[Role]:
        """Get a role by name"""
        return self._roles.get(role_name)

    def assign_role(self, identity_id: str, role_name: str) -> bool:
        """Assign a role to an identity"""
        if role_name not in self._roles:
            return False
        with self._lock:
            self._identity_roles[identity_id].add(role_name)
        return True

    def revoke_role(self, identity_id: str, role_name: str) -> bool:
        """Revoke a role from an identity"""
        with self._lock:
            if identity_id in self._identity_roles:
                self._identity_roles[identity_id].discard(role_name)
                return True
        return False

    def get_identity_roles(self, identity_id: str) -> List[Role]:
        """Get all roles for an identity"""
        role_names = self._identity_roles.get(identity_id, set())
        return [self._roles[name] for name in role_names if name in self._roles]

    def check_permission(
        self,
        identity_id: str,
        permission: Permission,
        resource_type: Optional[ResourceType] = None
    ) -> bool:
        """Check if identity has permission"""
        roles = self.get_identity_roles(identity_id)

        for role in roles:
            if role.has_permission(permission):
                return True
            if resource_type and role.can_access_resource(resource_type, permission):
                return True

        return False


class RateLimiter:
    """Rate limiting implementation"""

    def __init__(
        self,
        requests_per_second: float = 10.0,
        burst_size: int = 20
    ):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self._buckets: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"tokens": burst_size, "last_update": time.time()}
        )
        self._lock = threading.RLock()

    def allow_request(self, key: str) -> bool:
        """Check if request should be allowed"""
        with self._lock:
            bucket = self._buckets[key]
            now = time.time()

            # Refill tokens
            elapsed = now - bucket["last_update"]
            bucket["tokens"] = min(
                self.burst_size,
                bucket["tokens"] + elapsed * self.requests_per_second
            )
            bucket["last_update"] = now

            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return True

            return False

    def get_wait_time(self, key: str) -> float:
        """Get time to wait before next allowed request"""
        with self._lock:
            bucket = self._buckets[key]
            if bucket["tokens"] >= 1:
                return 0.0
            return (1 - bucket["tokens"]) / self.requests_per_second


class AuditLogger:
    """Security audit logging"""

    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self._events: List[AuditEvent] = []
        self._lock = threading.RLock()

    def log_event(
        self,
        event_type: str,
        action: str,
        result: str,
        identity_id: Optional[str] = None,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None
    ):
        """Log a security event"""
        event = AuditEvent(
            event_id=secrets.token_hex(8),
            timestamp=time.time(),
            event_type=event_type,
            identity_id=identity_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            details=details or {},
            source_ip=source_ip
        )

        with self._lock:
            self._events.append(event)
            if len(self._events) > self.max_events:
                self._events = self._events[-self.max_events:]

        # Also log to standard logger
        log_msg = f"AUDIT: {event_type} - {action} - {result}"
        if identity_id:
            log_msg += f" (identity: {identity_id})"
        if resource_type:
            log_msg += f" (resource: {resource_type.value}/{resource_id})"

        if result == "denied" or result == "failure":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

    def get_events(
        self,
        identity_id: Optional[str] = None,
        event_type: Optional[str] = None,
        since: Optional[float] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Query audit events"""
        events = self._events.copy()

        if identity_id:
            events = [e for e in events if e.identity_id == identity_id]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if since:
            events = [e for e in events if e.timestamp >= since]

        return events[-limit:]


class InputValidator:
    """Input validation and sanitization"""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize a string input"""
        # Truncate to max length
        value = value[:max_length]
        # Remove null bytes
        value = value.replace("\x00", "")
        return value

    @staticmethod
    def validate_identifier(value: str) -> bool:
        """Validate an identifier (alphanumeric + underscore)"""
        if not value:
            return False
        return all(c.isalnum() or c == "_" or c == "-" for c in value)

    @staticmethod
    def validate_json(value: str) -> bool:
        """Validate JSON string"""
        try:
            json.loads(value)
            return True
        except json.JSONDecodeError:
            return False

    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitize a file path to prevent path traversal"""
        # Remove path traversal attempts
        while ".." in path:
            path = path.replace("..", "")
        while "//" in path:
            path = path.replace("//", "/")
        return path.strip("/")


class EncryptionUtils:
    """Encryption utilities"""

    @staticmethod
    def generate_key(length: int = 32) -> bytes:
        """Generate a random encryption key"""
        return secrets.token_bytes(length)

    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> tuple:
        """Hash a password with salt"""
        if salt is None:
            salt = secrets.token_bytes(16)

        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            iterations=100000
        )

        return base64.b64encode(key).decode(), base64.b64encode(salt).decode()

    @staticmethod
    def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
        """Verify a password against stored hash"""
        salt = base64.b64decode(stored_salt)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            iterations=100000
        )

        return hmac.compare_digest(
            base64.b64encode(key).decode(),
            stored_hash
        )

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)


class SecurityManager:
    """
    Central security manager for the cognitive system.

    Features:
    - Authentication and authorization
    - Role-based access control
    - API key management
    - Rate limiting
    - Audit logging
    - Input validation
    """

    def __init__(self):
        self.rbac = RBACManager()
        self.rate_limiter = RateLimiter()
        self.audit = AuditLogger()
        self.validator = InputValidator()
        self.encryption = EncryptionUtils()

        self._identities: Dict[str, Identity] = {}
        self._api_keys: Dict[str, APIKey] = {}
        self._sessions: Dict[str, Session] = {}
        self._auth_providers: List[AuthenticationProvider] = []
        self._lock = threading.RLock()

        # Add default API key auth provider
        self._auth_providers.append(APIKeyAuthProvider(self._api_keys))

    def create_identity(
        self,
        name: str,
        identity_type: str = "user",
        roles: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Identity:
        """Create a new identity"""
        identity = Identity(
            identity_id=secrets.token_hex(16),
            name=name,
            identity_type=identity_type,
            roles=roles or [],
            metadata=metadata or {},
            created_at=time.time()
        )

        with self._lock:
            self._identities[identity.identity_id] = identity

        # Assign roles
        for role in identity.roles:
            self.rbac.assign_role(identity.identity_id, role)

        self.audit.log_event(
            "identity_created",
            action=f"Created identity: {name}",
            result="success",
            identity_id=identity.identity_id
        )

        return identity

    def generate_api_key(
        self,
        identity_id: str,
        name: str,
        scopes: Optional[Set[str]] = None,
        expires_in_days: Optional[int] = None
    ) -> tuple:
        """Generate a new API key for an identity"""
        if identity_id not in self._identities:
            raise ValueError("Identity not found")

        # Generate key
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = APIKey(
            key_id=secrets.token_hex(8),
            key_hash=key_hash,
            identity_id=identity_id,
            name=name,
            scopes=scopes or set(),
            created_at=time.time(),
            expires_at=time.time() + (expires_in_days * 86400) if expires_in_days else None
        )

        with self._lock:
            self._api_keys[api_key.key_id] = api_key

        self.audit.log_event(
            "api_key_created",
            action=f"Created API key: {name}",
            result="success",
            identity_id=identity_id
        )

        # Return key_id and the raw key (only time it's available)
        return api_key.key_id, raw_key

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        with self._lock:
            if key_id in self._api_keys:
                self._api_keys[key_id].active = False

                self.audit.log_event(
                    "api_key_revoked",
                    action=f"Revoked API key: {key_id}",
                    result="success"
                )
                return True
        return False

    def authenticate(self, credentials: Dict[str, Any]) -> Optional[Identity]:
        """Authenticate using available providers"""
        for provider in self._auth_providers:
            identity = provider.authenticate(credentials)
            if identity:
                self.audit.log_event(
                    "authentication",
                    action="User authenticated",
                    result="success",
                    identity_id=identity.identity_id
                )
                return identity

        self.audit.log_event(
            "authentication",
            action="Authentication failed",
            result="failure",
            details={"reason": "Invalid credentials"}
        )
        return None

    def authorize(
        self,
        identity_id: str,
        permission: Permission,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[str] = None
    ) -> bool:
        """Check if identity is authorized for an action"""
        if identity_id not in self._identities:
            self.audit.log_event(
                "authorization",
                action=f"Check permission: {permission.value}",
                result="denied",
                identity_id=identity_id,
                resource_type=resource_type,
                resource_id=resource_id,
                details={"reason": "Identity not found"}
            )
            return False

        allowed = self.rbac.check_permission(identity_id, permission, resource_type)

        self.audit.log_event(
            "authorization",
            action=f"Check permission: {permission.value}",
            result="success" if allowed else "denied",
            identity_id=identity_id,
            resource_type=resource_type,
            resource_id=resource_id
        )

        return allowed

    def check_rate_limit(self, key: str) -> bool:
        """Check if request is within rate limits"""
        allowed = self.rate_limiter.allow_request(key)

        if not allowed:
            self.audit.log_event(
                "rate_limit",
                action="Rate limit check",
                result="denied",
                details={"key": key}
            )

        return allowed

    def create_session(
        self,
        identity_id: str,
        expires_in: float = 3600
    ) -> Session:
        """Create a new session"""
        session = Session(
            session_id=secrets.token_urlsafe(32),
            identity_id=identity_id,
            created_at=time.time(),
            expires_at=time.time() + expires_in
        )

        with self._lock:
            self._sessions[session.session_id] = session

        return session

    def validate_session(self, session_id: str) -> Optional[Identity]:
        """Validate a session and return identity"""
        session = self._sessions.get(session_id)

        if not session or not session.active:
            return None

        if time.time() > session.expires_at:
            session.active = False
            return None

        return self._identities.get(session.identity_id)

    def invalidate_session(self, session_id: str):
        """Invalidate a session"""
        if session_id in self._sessions:
            self._sessions[session_id].active = False

    def require_auth(self, permission: Permission, resource_type: Optional[ResourceType] = None):
        """Decorator to require authentication and authorization"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get identity from context (would be set by middleware)
                identity_id = kwargs.get("_identity_id")

                if not identity_id:
                    raise PermissionError("Authentication required")

                if not self.authorize(identity_id, permission, resource_type):
                    raise PermissionError(f"Permission denied: {permission.value}")

                return await func(*args, **kwargs)

            return wrapper
        return decorator

    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status"""
        return {
            "identities": len(self._identities),
            "active_api_keys": sum(1 for k in self._api_keys.values() if k.active),
            "active_sessions": sum(
                1 for s in self._sessions.values()
                if s.active and time.time() < s.expires_at
            ),
            "roles": list(self.rbac._roles.keys()),
            "recent_events": [
                {
                    "event_id": e.event_id,
                    "type": e.event_type,
                    "action": e.action,
                    "result": e.result,
                    "timestamp": e.timestamp
                }
                for e in self.audit.get_events(limit=10)
            ],
            "rate_limit_config": {
                "requests_per_second": self.rate_limiter.requests_per_second,
                "burst_size": self.rate_limiter.burst_size
            }
        }


# Cognitive-specific security extensions
class CognitiveSecurityManager(SecurityManager):
    """
    Extended security manager for cognitive system protection.

    Additional features:
    - Kernel access control
    - Pipeline execution authorization
    - Plugin sandboxing permissions
    - Cognitive data protection
    """

    COGNITIVE_PERMISSIONS = {
        "kernel:attention": Permission.KERNEL_ACCESS,
        "kernel:reasoning": Permission.KERNEL_ACCESS,
        "kernel:learning": Permission.KERNEL_ACCESS,
        "pipeline:create": Permission.PIPELINE_MANAGE,
        "pipeline:execute": Permission.EXECUTE,
        "plugin:install": Permission.PLUGIN_MANAGE,
        "plugin:execute": Permission.EXECUTE,
        "atomspace:read": Permission.READ,
        "atomspace:write": Permission.WRITE
    }

    def __init__(self):
        super().__init__()

        # Add cognitive-specific roles
        self.rbac.add_role(Role(
            name="cognitive_operator",
            description="Cognitive system operator",
            permissions={
                Permission.KERNEL_ACCESS,
                Permission.PIPELINE_MANAGE,
                Permission.EXECUTE,
                Permission.METRICS_VIEW
            }
        ))

        self.rbac.add_role(Role(
            name="cognitive_researcher",
            description="Cognitive research access",
            permissions={Permission.READ, Permission.EXECUTE},
            resource_access={
                ResourceType.KERNEL: {Permission.READ, Permission.EXECUTE},
                ResourceType.ATOMSPACE: {Permission.READ}
            }
        ))

    def authorize_kernel_access(
        self,
        identity_id: str,
        kernel_type: str,
        operation: str
    ) -> bool:
        """Authorize kernel access"""
        perm_key = f"kernel:{kernel_type}"
        permission = self.COGNITIVE_PERMISSIONS.get(perm_key, Permission.KERNEL_ACCESS)

        return self.authorize(
            identity_id,
            permission,
            ResourceType.KERNEL,
            resource_id=kernel_type
        )

    def authorize_pipeline_operation(
        self,
        identity_id: str,
        pipeline_id: str,
        operation: str
    ) -> bool:
        """Authorize pipeline operation"""
        if operation == "create":
            permission = Permission.PIPELINE_MANAGE
        elif operation == "execute":
            permission = Permission.EXECUTE
        else:
            permission = Permission.READ

        return self.authorize(
            identity_id,
            permission,
            ResourceType.PIPELINE,
            resource_id=pipeline_id
        )

    def authorize_plugin_operation(
        self,
        identity_id: str,
        plugin_id: str,
        operation: str
    ) -> bool:
        """Authorize plugin operation"""
        if operation in ["install", "uninstall", "update"]:
            permission = Permission.PLUGIN_MANAGE
        elif operation == "execute":
            permission = Permission.EXECUTE
        else:
            permission = Permission.READ

        return self.authorize(
            identity_id,
            permission,
            ResourceType.PLUGIN,
            resource_id=plugin_id
        )

    def create_service_identity(
        self,
        service_name: str,
        permissions: Optional[Set[Permission]] = None
    ) -> tuple:
        """Create a service identity with API key"""
        identity = self.create_identity(
            name=service_name,
            identity_type="service",
            roles=["operator"]
        )

        # Assign specific permissions if provided
        if permissions:
            custom_role = Role(
                name=f"service_{service_name}",
                description=f"Custom role for {service_name}",
                permissions=permissions
            )
            self.rbac.add_role(custom_role)
            self.rbac.assign_role(identity.identity_id, custom_role.name)

        # Generate API key
        key_id, raw_key = self.generate_api_key(
            identity.identity_id,
            f"{service_name}_key",
            scopes={"service"}
        )

        return identity, key_id, raw_key
