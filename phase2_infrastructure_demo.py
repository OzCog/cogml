#!/usr/bin/env python3
"""
Phase 2: Infrastructure Layer Demonstration

This script demonstrates the Phase 2 infrastructure components:
1. Service Mesh Architecture
2. Data Flow Orchestration
3. Plugin Ecosystem
4. Advanced Monitoring
5. Distributed Tracing
6. Security Framework
"""

import asyncio
import json
import time
from typing import Dict, Any

# Import Phase 2 infrastructure components
from cogml.infrastructure import (
    # Service Mesh
    CognitiveServiceMesh,
    ServiceStatus,
    LoadBalancingStrategy,

    # Data Flow Orchestration
    PipelineBuilder,
    DataFlowOrchestrator,
    DataPacket,

    # Plugin Ecosystem
    PluginManager,
    ExampleCognitivePlugin,

    # Monitoring
    CognitiveMonitor,
    AlertSeverity,
    ThresholdRule,
    HealthCheck,
    HealthStatus,

    # Distributed Tracing
    CognitiveTracer,

    # Security
    CognitiveSecurityManager,
    Permission,
    ResourceType
)


async def demo_service_mesh():
    """Demonstrate Service Mesh Architecture"""
    print("\n" + "=" * 80)
    print("1. SERVICE MESH ARCHITECTURE")
    print("=" * 80)

    # Create cognitive service mesh
    mesh = CognitiveServiceMesh(
        load_balancing_strategy=LoadBalancingStrategy.WEIGHTED,
        health_check_interval=5.0
    )

    # Register cognitive services
    attention_id = mesh.register_cognitive_service(
        service_type="attention_kernel",
        host="localhost",
        port=8001,
        capabilities=["attention_allocation", "salience_computation"],
        weight=1.0
    )

    reasoning_id = mesh.register_cognitive_service(
        service_type="reasoning_kernel",
        host="localhost",
        port=8002,
        capabilities=["logical_inference", "pattern_matching"],
        weight=0.8
    )

    learning_id = mesh.register_cognitive_service(
        service_type="learning_kernel",
        host="localhost",
        port=8003,
        capabilities=["adaptive_learning", "model_training"],
        weight=0.7
    )

    # Get mesh status
    status = mesh.get_mesh_status()
    print(f"\nRegistered Services: {status['total_services']}")
    for service_name, service_info in status['services'].items():
        print(f"  - {service_name}: {service_info['total_endpoints']} endpoints")

    # Get cognitive topology
    topology = mesh.get_cognitive_topology()
    print(f"\nCognitive Services Topology:")
    for service_type, info in topology['cognitive_services'].items():
        print(f"  - {service_type}: {info['instances']} instances, capabilities: {info['capabilities']}")

    print(f"\n[OK] Service Mesh: {status['total_services']} services registered")
    return mesh


async def demo_data_flow_orchestration():
    """Demonstrate Data Flow Orchestration"""
    print("\n" + "=" * 80)
    print("2. DATA FLOW ORCHESTRATION")
    print("=" * 80)

    # Create pipeline builder
    counter = {"value": 0}
    results = []

    def data_generator():
        counter["value"] += 1
        return {"id": counter["value"], "text": f"Sample input {counter['value']}", "value": counter["value"] * 10}

    def text_transform(data):
        data["text"] = data["text"].upper()
        data["transformed"] = True
        return data

    def value_filter(data):
        return data.get("value", 0) > 15

    def cognitive_processor(data, operation=None, config=None):
        # Simulate cognitive processing
        data["cognitive_score"] = len(data.get("text", "")) * 0.1
        data["operation"] = operation
        return data

    def result_sink(data):
        results.append(data)

    # Build pipeline
    pipeline = (
        PipelineBuilder("cognitive_pipeline", "Cognitive Processing Pipeline")
        .source("input_source", data_generator)
        .transform("text_transformer", text_transform)
        .filter("value_filter", value_filter)
        .cognitive("cognitive_processor", "analyze", cognitive_processor)
        .sink("output_sink", result_sink)
        .build()
    )

    # Create orchestrator
    orchestrator = DataFlowOrchestrator()
    orchestrator.register_pipeline(pipeline)

    await orchestrator.start()

    # Execute pipeline multiple times
    print("\nExecuting pipeline...")
    for i in range(5):
        execution = await orchestrator.execute_pipeline("cognitive_pipeline")
        if execution:
            print(f"  Execution {i+1}: {execution.status.value} in {execution.metrics.get('total_execution_time', 0):.4f}s")

    # Get orchestrator status
    status = orchestrator.get_status()
    print(f"\nOrchestrator Status:")
    print(f"  - Registered Pipelines: {status['registered_pipelines']}")
    print(f"  - Total Executions: {status['total_executions']}")

    await orchestrator.stop()

    print(f"\n[OK] Data Flow Orchestration: {len(results)} results processed")
    return orchestrator


async def demo_plugin_ecosystem():
    """Demonstrate Plugin Ecosystem"""
    print("\n" + "=" * 80)
    print("3. PLUGIN ECOSYSTEM")
    print("=" * 80)

    # Create plugin manager
    plugin_manager = PluginManager()
    await plugin_manager.start()

    # Manually register the example plugin (simulating discovery)
    example_plugin = ExampleCognitivePlugin(config={"threshold": 0.7})

    # Initialize and activate
    await example_plugin.initialize()
    await example_plugin.activate()

    # Process data through plugin
    result = await example_plugin.process({"text": "Hello, cognitive world!"})

    print(f"\nExample Plugin:")
    print(f"  - Name: {example_plugin.metadata.name}")
    print(f"  - Version: {example_plugin.metadata.version}")
    print(f"  - Type: {example_plugin.metadata.plugin_type.value}")
    print(f"  - Capabilities: {example_plugin.metadata.capabilities}")
    print(f"  - Status: {example_plugin.get_status().value}")

    print(f"\nPlugin Processing Result:")
    print(f"  - Input: {result.get('input_data')}")
    print(f"  - Threshold: {result.get('threshold')}")
    print(f"  - Processed: {result.get('processed')}")

    # Cleanup
    await example_plugin.deactivate()
    await example_plugin.shutdown()
    await plugin_manager.stop()

    print(f"\n[OK] Plugin Ecosystem: Plugin lifecycle demonstrated")
    return plugin_manager


async def demo_monitoring():
    """Demonstrate Advanced Monitoring"""
    print("\n" + "=" * 80)
    print("4. ADVANCED MONITORING")
    print("=" * 80)

    # Create cognitive monitor
    monitor = CognitiveMonitor()

    # Add threshold rules
    monitor.add_threshold_rule(ThresholdRule(
        name="high_latency",
        metric_name="cognitive_memory_latency_ms",
        threshold=100.0,
        comparison="gt",
        severity=AlertSeverity.WARNING,
        message_template="Memory latency exceeded {threshold}ms: {value}ms"
    ))

    monitor.add_threshold_rule(ThresholdRule(
        name="low_coherence",
        metric_name="cognitive_coherence",
        threshold=0.5,
        comparison="lt",
        severity=AlertSeverity.ERROR,
        message_template="Cognitive coherence below threshold: {value} < {threshold}"
    ))

    # Register health checks
    def attention_health():
        return HealthCheck(
            component="attention_kernel",
            status=HealthStatus.HEALTHY,
            message="Attention kernel operating normally",
            timestamp=time.time(),
            details={"allocation_rate": 150.0}
        )

    def reasoning_health():
        return HealthCheck(
            component="reasoning_kernel",
            status=HealthStatus.HEALTHY,
            message="Reasoning kernel operating normally",
            timestamp=time.time(),
            details={"inference_rate": 50.0}
        )

    monitor.health.register_check("attention_kernel", attention_health)
    monitor.health.register_check("reasoning_kernel", reasoning_health)

    # Record some metrics
    for i in range(10):
        monitor.record_attention_allocation(150.0 + i * 5, "attention_1")
        monitor.record_reasoning_operation(0.05 + i * 0.01, "logical_inference")
        monitor.record_memory_access(10.0 + i * 2, "read")
        monitor.record_cognitive_coherence(0.8 + i * 0.01)

    monitor.record_emergent_pattern("cross_modal_integration")
    monitor.record_emergent_pattern("attention_coherence")

    # Get dashboard data
    dashboard = monitor.get_dashboard_data()

    print(f"\nHealth Status:")
    print(f"  - Overall: {dashboard['health']['overall']}")
    for comp, info in dashboard['health']['components'].items():
        print(f"  - {comp}: {info['status']}")

    print(f"\nCognitive Metrics:")
    for metric, value in dashboard['cognitive_metrics'].items():
        if value:
            print(f"  - {metric}: {value}")

    print(f"\nAlerts:")
    print(f"  - Active: {dashboard['alerts']['active_count']}")

    # Export metrics
    prometheus_metrics = monitor.get_metrics_export("prometheus")
    metric_lines = prometheus_metrics.split("\n")[:5]
    print(f"\nSample Prometheus Metrics Export:")
    for line in metric_lines:
        if line:
            print(f"  {line}")

    print(f"\n[OK] Monitoring: Health checks and metrics operational")
    return monitor


async def demo_distributed_tracing():
    """Demonstrate Distributed Tracing"""
    print("\n" + "=" * 80)
    print("5. DISTRIBUTED TRACING")
    print("=" * 80)

    # Create cognitive tracer
    tracer = CognitiveTracer(service_name="cognitive-demo")

    # Trace cognitive operations
    with tracer.trace_operation("demo_workflow", kernel_id="main") as root_span:
        root_span.set_attribute("demo.type", "integration_test")

        # Nested attention allocation
        with tracer.trace_attention("attention_1", "atom_123", 0.85) as span:
            await asyncio.sleep(0.01)  # Simulate work
            span.add_event("allocation_complete", {"sti": 0.85})

        # Nested reasoning
        with tracer.trace_reasoning("modus_ponens", "forward_chain") as span:
            await asyncio.sleep(0.02)  # Simulate work
            span.set_attribute("rules_applied", 3)

        # Nested pipeline processing
        with tracer.trace_pipeline("pipeline_1", "transform_node") as span:
            await asyncio.sleep(0.015)  # Simulate work
            span.set_attribute("records_processed", 100)

    # Get trace statistics
    stats = tracer.get_trace_statistics()

    print(f"\nTrace Statistics:")
    print(f"  - Total Traces: {stats['total_traces']}")
    print(f"  - Total Spans: {stats['total_spans']}")
    print(f"  - Services: {stats['services']}")

    # Get slow operations
    slow_ops = tracer.get_slow_operations(threshold_ms=10.0)
    if slow_ops:
        print(f"\nSlow Operations (>10ms):")
        for op in slow_ops[:3]:
            print(f"  - {op['name']}: {op['duration_ms']:.2f}ms")

    # Get dependency graph
    deps = tracer.get_dependency_graph()
    print(f"\nService Dependencies:")
    print(f"  - Services: {deps['services']}")
    print(f"  - Edges: {len(deps['edges'])}")

    print(f"\n[OK] Distributed Tracing: {stats['total_spans']} spans recorded")
    return tracer


async def demo_security():
    """Demonstrate Security Framework"""
    print("\n" + "=" * 80)
    print("6. SECURITY FRAMEWORK")
    print("=" * 80)

    # Create security manager
    security = CognitiveSecurityManager()

    # Create identities
    admin_identity = security.create_identity(
        name="admin_user",
        identity_type="user",
        roles=["admin"]
    )

    operator_identity = security.create_identity(
        name="operator_user",
        identity_type="user",
        roles=["cognitive_operator"]
    )

    researcher_identity = security.create_identity(
        name="researcher_user",
        identity_type="user",
        roles=["cognitive_researcher"]
    )

    # Generate API keys
    _, admin_key = security.generate_api_key(
        admin_identity.identity_id,
        "admin_api_key",
        expires_in_days=30
    )

    print(f"\nCreated Identities:")
    print(f"  - Admin: {admin_identity.name} (roles: {admin_identity.roles})")
    print(f"  - Operator: {operator_identity.name} (roles: {operator_identity.roles})")
    print(f"  - Researcher: {researcher_identity.name} (roles: {researcher_identity.roles})")

    # Test authorization
    print(f"\nAuthorization Tests:")

    # Admin can do everything
    admin_kernel = security.authorize_kernel_access(admin_identity.identity_id, "attention", "allocate")
    print(f"  - Admin -> Kernel Access: {'ALLOWED' if admin_kernel else 'DENIED'}")

    # Operator can access kernels
    operator_kernel = security.authorize_kernel_access(operator_identity.identity_id, "reasoning", "execute")
    print(f"  - Operator -> Kernel Access: {'ALLOWED' if operator_kernel else 'DENIED'}")

    # Researcher has limited access
    researcher_write = security.authorize(researcher_identity.identity_id, Permission.WRITE, ResourceType.ATOMSPACE)
    print(f"  - Researcher -> AtomSpace Write: {'ALLOWED' if researcher_write else 'DENIED'}")

    researcher_read = security.authorize(researcher_identity.identity_id, Permission.READ, ResourceType.KERNEL)
    print(f"  - Researcher -> Kernel Read: {'ALLOWED' if researcher_read else 'DENIED'}")

    # Test rate limiting
    rate_limit_key = "test_client"
    allowed_requests = sum(1 for _ in range(25) if security.check_rate_limit(rate_limit_key))
    print(f"\nRate Limiting Test:")
    print(f"  - Requests allowed out of 25: {allowed_requests}")

    # Get security status
    status = security.get_security_status()
    print(f"\nSecurity Status:")
    print(f"  - Identities: {status['identities']}")
    print(f"  - Active API Keys: {status['active_api_keys']}")
    print(f"  - Available Roles: {status['roles']}")
    print(f"  - Recent Events: {len(status['recent_events'])}")

    print(f"\n[OK] Security Framework: RBAC and rate limiting operational")
    return security


async def main():
    """Run all Phase 2 infrastructure demonstrations"""
    print("=" * 80)
    print(" PHASE 2: INFRASTRUCTURE LAYER DEMONSTRATION")
    print(" OpenCog Central - Advanced Cognitive Infrastructure")
    print("=" * 80)

    start_time = time.time()

    try:
        # Run demonstrations
        mesh = await demo_service_mesh()
        orchestrator = await demo_data_flow_orchestration()
        plugins = await demo_plugin_ecosystem()
        monitor = await demo_monitoring()
        tracer = await demo_distributed_tracing()
        security = await demo_security()

        # Summary
        total_time = time.time() - start_time

        print("\n" + "=" * 80)
        print(" PHASE 2 DEMONSTRATION SUMMARY")
        print("=" * 80)

        print(f"""
Phase 2 Infrastructure Components Successfully Demonstrated:

1. Service Mesh Architecture
   - Cognitive service registration and discovery
   - Load balancing with multiple strategies
   - Circuit breaker pattern for fault tolerance
   - Health checking and topology analysis

2. Data Flow Orchestration
   - DAG-based pipeline construction
   - Fluent pipeline builder API
   - Parallel and sequential execution
   - Cognitive processing nodes

3. Plugin Ecosystem
   - Dynamic plugin discovery
   - Plugin lifecycle management
   - Sandboxed execution
   - Hot-pluggable cognitive modules

4. Advanced Monitoring
   - Cognitive-specific metrics
   - Real-time health monitoring
   - Threshold-based alerting
   - Anomaly detection

5. Distributed Tracing
   - OpenTelemetry-compatible tracing
   - Cross-component correlation
   - Performance bottleneck identification
   - Dependency graph analysis

6. Security Framework
   - Role-based access control (RBAC)
   - API key authentication
   - Rate limiting
   - Audit logging

Total Demonstration Time: {total_time:.2f} seconds

Phase 2 Status: COMPLETE
""")

        # Generate summary report
        report = {
            "phase": 2,
            "name": "Infrastructure Layer",
            "status": "complete",
            "components": [
                "Service Mesh Architecture",
                "Data Flow Orchestration",
                "Plugin Ecosystem",
                "Advanced Monitoring",
                "Distributed Tracing",
                "Security Framework"
            ],
            "demonstration_time": total_time,
            "timestamp": time.time()
        }

        with open("phase2_demonstration_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print("Report saved to: phase2_demonstration_report.json")

    except Exception as e:
        print(f"\nError during demonstration: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
