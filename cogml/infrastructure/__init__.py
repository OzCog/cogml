"""
OpenCog Central Infrastructure Layer

Phase 2 Implementation: Advanced infrastructure components for the cognitive system.

This package provides:
- Service Mesh Architecture for cognitive component communication
- Data Flow Orchestration for pipeline management
- Plugin Ecosystem for hot-pluggable cognitive modules
- Advanced Monitoring for real-time process visualization
- Distributed Tracing for cross-component debugging
- Security Framework for unified access control

Usage:
    from cogml.infrastructure import (
        CognitiveServiceMesh,
        DataFlowOrchestrator,
        PluginManager,
        CognitiveMonitor,
        CognitiveTracer,
        CognitiveSecurityManager
    )
"""

from .service_mesh import (
    ServiceMesh,
    CognitiveServiceMesh,
    ServiceRegistry,
    ServiceEndpoint,
    ServiceRequest,
    ServiceResponse,
    ServiceStatus,
    CircuitState,
    LoadBalancingStrategy,
    LoadBalancer,
    CircuitBreaker
)

from .data_flow_orchestration import (
    Pipeline,
    PipelineBuilder,
    DataFlowOrchestrator,
    PipelineNode,
    SourceNode,
    TransformNode,
    FilterNode,
    AggregateNode,
    MergeNode,
    SinkNode,
    CognitiveNode,
    DataPacket,
    NodeType,
    ExecutionStatus
)

from .plugin_ecosystem import (
    PluginManager,
    PluginRegistry,
    PluginLoader,
    CognitivePlugin,
    PluginMetadata,
    PluginType,
    PluginStatus,
    PluginSandbox,
    DependencyResolver,
    ExampleCognitivePlugin,
    AttentionKernelPlugin
)

from .monitoring import (
    CognitiveMonitor,
    MetricCollector,
    AlertManager,
    HealthMonitor,
    ThresholdRule,
    AnomalyDetector,
    MetricType,
    AlertSeverity,
    HealthStatus,
    Metric,
    Alert,
    HealthCheck,
    CognitiveMetrics
)

from .distributed_tracing import (
    CognitiveTracer,
    Tracer,
    TraceStore,
    TraceContextPropagator,
    Span,
    SpanContext,
    SpanKind,
    SpanStatus,
    SpanEvent,
    SpanLink,
    Trace
)

from .security_framework import (
    SecurityManager,
    CognitiveSecurityManager,
    RBACManager,
    RateLimiter,
    AuditLogger,
    InputValidator,
    EncryptionUtils,
    Permission,
    ResourceType,
    Role,
    Identity,
    APIKey,
    Session,
    AuditEvent
)

__all__ = [
    # Service Mesh
    "ServiceMesh",
    "CognitiveServiceMesh",
    "ServiceRegistry",
    "ServiceEndpoint",
    "ServiceRequest",
    "ServiceResponse",
    "ServiceStatus",
    "CircuitState",
    "LoadBalancingStrategy",
    "LoadBalancer",
    "CircuitBreaker",

    # Data Flow Orchestration
    "Pipeline",
    "PipelineBuilder",
    "DataFlowOrchestrator",
    "PipelineNode",
    "SourceNode",
    "TransformNode",
    "FilterNode",
    "AggregateNode",
    "MergeNode",
    "SinkNode",
    "CognitiveNode",
    "DataPacket",
    "NodeType",
    "ExecutionStatus",

    # Plugin Ecosystem
    "PluginManager",
    "PluginRegistry",
    "PluginLoader",
    "CognitivePlugin",
    "PluginMetadata",
    "PluginType",
    "PluginStatus",
    "PluginSandbox",
    "DependencyResolver",
    "ExampleCognitivePlugin",
    "AttentionKernelPlugin",

    # Monitoring
    "CognitiveMonitor",
    "MetricCollector",
    "AlertManager",
    "HealthMonitor",
    "ThresholdRule",
    "AnomalyDetector",
    "MetricType",
    "AlertSeverity",
    "HealthStatus",
    "Metric",
    "Alert",
    "HealthCheck",
    "CognitiveMetrics",

    # Distributed Tracing
    "CognitiveTracer",
    "Tracer",
    "TraceStore",
    "TraceContextPropagator",
    "Span",
    "SpanContext",
    "SpanKind",
    "SpanStatus",
    "SpanEvent",
    "SpanLink",
    "Trace",

    # Security Framework
    "SecurityManager",
    "CognitiveSecurityManager",
    "RBACManager",
    "RateLimiter",
    "AuditLogger",
    "InputValidator",
    "EncryptionUtils",
    "Permission",
    "ResourceType",
    "Role",
    "Identity",
    "APIKey",
    "Session",
    "AuditEvent"
]

__version__ = "2.0.0"
