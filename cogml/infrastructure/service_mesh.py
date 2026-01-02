#!/usr/bin/env python3
"""
Service Mesh Architecture for Cognitive Component Communication

Phase 2 Implementation: Provides microservice communication patterns including:
- Service discovery and registration
- Load balancing across cognitive kernels
- Circuit breaker patterns for fault tolerance
- Health checking and automatic failover
- Request routing and traffic management
"""

import asyncio
import json
import time
import hashlib
import random
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class ServiceEndpoint:
    """Represents a service endpoint in the mesh"""
    service_id: str
    service_name: str
    host: str
    port: int
    protocol: str = "http"
    weight: float = 1.0
    status: ServiceStatus = ServiceStatus.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_health_check: float = 0.0
    response_times: List[float] = field(default_factory=list)
    error_count: int = 0
    success_count: int = 0

    @property
    def address(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

    @property
    def average_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return sum(self.response_times[-100:]) / len(self.response_times[-100:])

    @property
    def error_rate(self) -> float:
        total = self.error_count + self.success_count
        if total == 0:
            return 0.0
        return self.error_count / total


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance"""
    service_id: str
    state: CircuitState = CircuitState.CLOSED
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout: float = 30.0  # Time before attempting recovery
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0

    def record_success(self):
        """Record successful request"""
        self.success_count += 1
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                logger.info(f"Circuit closed for service {self.service_id}")

    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.success_count = 0
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit opened for service {self.service_id}")

    def allow_request(self) -> bool:
        """Check if request should be allowed"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit half-open for service {self.service_id}")
                return True
            return False

        # HALF_OPEN - allow limited requests
        return True


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    RESPONSE_TIME = "response_time"


class LoadBalancer:
    """Load balancer for distributing requests across service instances"""

    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.WEIGHTED):
        self.strategy = strategy
        self._round_robin_index: Dict[str, int] = defaultdict(int)
        self._active_connections: Dict[str, int] = defaultdict(int)

    def select_endpoint(self, endpoints: List[ServiceEndpoint]) -> Optional[ServiceEndpoint]:
        """Select an endpoint based on the load balancing strategy"""
        healthy_endpoints = [e for e in endpoints if e.status == ServiceStatus.HEALTHY]

        if not healthy_endpoints:
            # Fallback to degraded endpoints
            healthy_endpoints = [e for e in endpoints if e.status != ServiceStatus.UNHEALTHY]

        if not healthy_endpoints:
            return None

        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin(healthy_endpoints)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED:
            return self._weighted(healthy_endpoints)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections(healthy_endpoints)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(healthy_endpoints)
        elif self.strategy == LoadBalancingStrategy.RESPONSE_TIME:
            return self._response_time(healthy_endpoints)

        return healthy_endpoints[0]

    def _round_robin(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Round robin selection"""
        service_name = endpoints[0].service_name
        index = self._round_robin_index[service_name]
        endpoint = endpoints[index % len(endpoints)]
        self._round_robin_index[service_name] = (index + 1) % len(endpoints)
        return endpoint

    def _weighted(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Weighted random selection"""
        total_weight = sum(e.weight for e in endpoints)
        r = random.uniform(0, total_weight)
        cumulative = 0
        for endpoint in endpoints:
            cumulative += endpoint.weight
            if r <= cumulative:
                return endpoint
        return endpoints[-1]

    def _least_connections(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Select endpoint with least active connections"""
        return min(endpoints, key=lambda e: self._active_connections[e.service_id])

    def _response_time(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Select endpoint with best response time"""
        return min(endpoints, key=lambda e: e.average_response_time or float('inf'))


class ServiceRegistry:
    """Central registry for service discovery"""

    def __init__(self):
        self._services: Dict[str, Dict[str, ServiceEndpoint]] = defaultdict(dict)
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()

    def register(self, endpoint: ServiceEndpoint) -> bool:
        """Register a service endpoint"""
        with self._lock:
            self._services[endpoint.service_name][endpoint.service_id] = endpoint

            if endpoint.service_id not in self._circuit_breakers:
                self._circuit_breakers[endpoint.service_id] = CircuitBreaker(
                    service_id=endpoint.service_id
                )

            logger.info(f"Registered service: {endpoint.service_name} ({endpoint.service_id})")
            self._notify_subscribers(endpoint.service_name, "register", endpoint)
            return True

    def deregister(self, service_id: str) -> bool:
        """Deregister a service endpoint"""
        with self._lock:
            for service_name, endpoints in self._services.items():
                if service_id in endpoints:
                    endpoint = endpoints.pop(service_id)
                    logger.info(f"Deregistered service: {service_name} ({service_id})")
                    self._notify_subscribers(service_name, "deregister", endpoint)
                    return True
            return False

    def get_endpoints(self, service_name: str) -> List[ServiceEndpoint]:
        """Get all endpoints for a service"""
        with self._lock:
            return list(self._services.get(service_name, {}).values())

    def get_endpoint(self, service_id: str) -> Optional[ServiceEndpoint]:
        """Get specific endpoint by ID"""
        with self._lock:
            for endpoints in self._services.values():
                if service_id in endpoints:
                    return endpoints[service_id]
            return None

    def get_circuit_breaker(self, service_id: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker for a service"""
        return self._circuit_breakers.get(service_id)

    def update_health(self, service_id: str, status: ServiceStatus):
        """Update health status of a service"""
        with self._lock:
            for endpoints in self._services.values():
                if service_id in endpoints:
                    endpoints[service_id].status = status
                    endpoints[service_id].last_health_check = time.time()
                    return

    def subscribe(self, service_name: str, callback: Callable):
        """Subscribe to service changes"""
        self._subscribers[service_name].append(callback)

    def _notify_subscribers(self, service_name: str, event: str, endpoint: ServiceEndpoint):
        """Notify subscribers of service changes"""
        for callback in self._subscribers.get(service_name, []):
            try:
                callback(event, endpoint)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")

    def list_services(self) -> Dict[str, List[str]]:
        """List all registered services"""
        with self._lock:
            return {
                name: list(endpoints.keys())
                for name, endpoints in self._services.items()
            }


@dataclass
class ServiceRequest:
    """Request to be routed through the mesh"""
    request_id: str
    service_name: str
    method: str
    path: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None
    timeout: float = 30.0
    retries: int = 3
    trace_id: Optional[str] = None
    span_id: Optional[str] = None


@dataclass
class ServiceResponse:
    """Response from a service in the mesh"""
    request_id: str
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None
    response_time: float = 0.0
    endpoint_id: str = ""
    error: Optional[str] = None


class ServiceMesh:
    """
    Main service mesh implementation for cognitive component communication.

    Features:
    - Service discovery and registration
    - Load balancing with multiple strategies
    - Circuit breaker pattern for fault tolerance
    - Health checking
    - Request routing and tracing
    """

    def __init__(
        self,
        load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.WEIGHTED,
        health_check_interval: float = 10.0,
        enable_tracing: bool = True
    ):
        self.registry = ServiceRegistry()
        self.load_balancer = LoadBalancer(strategy=load_balancing_strategy)
        self.health_check_interval = health_check_interval
        self.enable_tracing = enable_tracing

        self._health_check_handlers: Dict[str, Callable] = {}
        self._request_handlers: Dict[str, Callable] = {}
        self._middleware: List[Callable] = []

        self._running = False
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._health_check_task: Optional[asyncio.Task] = None

    def register_service(
        self,
        service_name: str,
        host: str,
        port: int,
        protocol: str = "http",
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a new service with the mesh"""
        service_id = hashlib.md5(
            f"{service_name}:{host}:{port}:{time.time()}".encode()
        ).hexdigest()[:12]

        endpoint = ServiceEndpoint(
            service_id=service_id,
            service_name=service_name,
            host=host,
            port=port,
            protocol=protocol,
            weight=weight,
            status=ServiceStatus.UNKNOWN,
            metadata=metadata or {}
        )

        self.registry.register(endpoint)
        return service_id

    def deregister_service(self, service_id: str) -> bool:
        """Deregister a service from the mesh"""
        return self.registry.deregister(service_id)

    def add_health_check(self, service_name: str, handler: Callable):
        """Add a health check handler for a service"""
        self._health_check_handlers[service_name] = handler

    def add_request_handler(self, service_name: str, handler: Callable):
        """Add a request handler for a service"""
        self._request_handlers[service_name] = handler

    def add_middleware(self, middleware: Callable):
        """Add middleware for request/response processing"""
        self._middleware.append(middleware)

    async def route_request(self, request: ServiceRequest) -> ServiceResponse:
        """Route a request through the mesh"""
        start_time = time.time()

        # Generate trace IDs if tracing enabled
        if self.enable_tracing and not request.trace_id:
            request.trace_id = hashlib.md5(
                f"{request.request_id}:{time.time()}".encode()
            ).hexdigest()[:16]
            request.span_id = hashlib.md5(
                f"{request.trace_id}:{request.service_name}".encode()
            ).hexdigest()[:8]

        # Apply middleware
        for middleware in self._middleware:
            request = await middleware(request)

        # Get available endpoints
        endpoints = self.registry.get_endpoints(request.service_name)
        if not endpoints:
            return ServiceResponse(
                request_id=request.request_id,
                status_code=503,
                error=f"No endpoints available for service: {request.service_name}"
            )

        # Try to route with retries
        last_error = None
        for attempt in range(request.retries):
            # Select endpoint
            endpoint = self.load_balancer.select_endpoint(endpoints)
            if not endpoint:
                continue

            # Check circuit breaker
            circuit = self.registry.get_circuit_breaker(endpoint.service_id)
            if circuit and not circuit.allow_request():
                logger.warning(f"Circuit open for {endpoint.service_id}, skipping")
                continue

            try:
                # Execute request
                response = await self._execute_request(endpoint, request)

                # Record success
                if circuit:
                    circuit.record_success()

                endpoint.success_count += 1
                response_time = time.time() - start_time
                endpoint.response_times.append(response_time)
                response.response_time = response_time
                response.endpoint_id = endpoint.service_id

                return response

            except Exception as e:
                last_error = str(e)
                logger.error(f"Request failed to {endpoint.service_id}: {e}")

                # Record failure
                if circuit:
                    circuit.record_failure()
                endpoint.error_count += 1

                # Remove from candidates for this request
                endpoints = [e for e in endpoints if e.service_id != endpoint.service_id]

        return ServiceResponse(
            request_id=request.request_id,
            status_code=503,
            response_time=time.time() - start_time,
            error=f"All endpoints failed: {last_error}"
        )

    async def _execute_request(
        self,
        endpoint: ServiceEndpoint,
        request: ServiceRequest
    ) -> ServiceResponse:
        """Execute a request to an endpoint"""
        handler = self._request_handlers.get(request.service_name)

        if handler:
            # Use registered handler
            result = await handler(endpoint, request)
            return ServiceResponse(
                request_id=request.request_id,
                status_code=200,
                body=result
            )

        # Default: simulate local request
        await asyncio.sleep(0.001)  # Minimal processing time
        return ServiceResponse(
            request_id=request.request_id,
            status_code=200,
            body={"processed": True, "endpoint": endpoint.address}
        )

    async def perform_health_checks(self):
        """Perform health checks on all registered services"""
        for service_name, endpoints in self.registry._services.items():
            handler = self._health_check_handlers.get(service_name)

            for service_id, endpoint in endpoints.items():
                try:
                    if handler:
                        is_healthy = await handler(endpoint)
                        status = ServiceStatus.HEALTHY if is_healthy else ServiceStatus.UNHEALTHY
                    else:
                        # Default: mark as healthy
                        status = ServiceStatus.HEALTHY

                    self.registry.update_health(service_id, status)

                except Exception as e:
                    logger.error(f"Health check failed for {service_id}: {e}")
                    self.registry.update_health(service_id, ServiceStatus.UNHEALTHY)

    async def _health_check_loop(self):
        """Background health check loop"""
        while self._running:
            await self.perform_health_checks()
            await asyncio.sleep(self.health_check_interval)

    async def start(self):
        """Start the service mesh"""
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Service mesh started")

    async def stop(self):
        """Stop the service mesh"""
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        self._executor.shutdown(wait=False)
        logger.info("Service mesh stopped")

    def get_mesh_status(self) -> Dict[str, Any]:
        """Get current mesh status"""
        services = {}
        for service_name, endpoints in self.registry._services.items():
            services[service_name] = {
                "endpoints": [
                    {
                        "id": e.service_id,
                        "address": e.address,
                        "status": e.status.value,
                        "weight": e.weight,
                        "avg_response_time": e.average_response_time,
                        "error_rate": e.error_rate,
                        "circuit_state": self.registry.get_circuit_breaker(e.service_id).state.value
                        if self.registry.get_circuit_breaker(e.service_id) else "unknown"
                    }
                    for e in endpoints.values()
                ],
                "total_endpoints": len(endpoints),
                "healthy_endpoints": sum(
                    1 for e in endpoints.values() if e.status == ServiceStatus.HEALTHY
                )
            }

        return {
            "timestamp": time.time(),
            "running": self._running,
            "load_balancing_strategy": self.load_balancer.strategy.value,
            "services": services,
            "total_services": len(services)
        }


# Cognitive-specific service mesh extensions
class CognitiveServiceMesh(ServiceMesh):
    """
    Extended service mesh with cognitive-specific features.

    Provides specialized routing for cognitive components:
    - Attention kernel routing
    - Reasoning service discovery
    - Learning kernel load balancing
    """

    COGNITIVE_SERVICES = {
        "attention_kernel": "Manages attention allocation and salience",
        "reasoning_kernel": "Handles PLN and inference operations",
        "learning_kernel": "Manages adaptive learning processes",
        "memory_service": "AtomSpace and knowledge storage",
        "sensory_service": "Sensory input processing",
        "motor_service": "Motor output generation"
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cognitive_priorities: Dict[str, float] = {}

    def set_cognitive_priority(self, service_name: str, priority: float):
        """Set priority for cognitive service routing"""
        self._cognitive_priorities[service_name] = priority

    def register_cognitive_service(
        self,
        service_type: str,
        host: str,
        port: int,
        capabilities: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """Register a cognitive service with type-specific metadata"""
        if service_type not in self.COGNITIVE_SERVICES:
            logger.warning(f"Unknown cognitive service type: {service_type}")

        metadata = kwargs.pop("metadata", {})
        metadata["service_type"] = service_type
        metadata["capabilities"] = capabilities or []
        metadata["description"] = self.COGNITIVE_SERVICES.get(service_type, "Unknown")

        return self.register_service(
            service_name=service_type,
            host=host,
            port=port,
            metadata=metadata,
            **kwargs
        )

    async def route_cognitive_request(
        self,
        service_type: str,
        operation: str,
        data: Any,
        priority: Optional[float] = None
    ) -> ServiceResponse:
        """Route a cognitive operation request"""
        request = ServiceRequest(
            request_id=hashlib.md5(f"{service_type}:{operation}:{time.time()}".encode()).hexdigest()[:12],
            service_name=service_type,
            method="POST",
            path=f"/cognitive/{operation}",
            body={
                "operation": operation,
                "data": data,
                "priority": priority or self._cognitive_priorities.get(service_type, 0.5)
            }
        )

        return await self.route_request(request)

    def get_cognitive_topology(self) -> Dict[str, Any]:
        """Get cognitive service topology"""
        topology = {
            "cognitive_services": {},
            "connections": [],
            "health_summary": {
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0
            }
        }

        for service_type in self.COGNITIVE_SERVICES:
            endpoints = self.registry.get_endpoints(service_type)
            if endpoints:
                topology["cognitive_services"][service_type] = {
                    "instances": len(endpoints),
                    "capabilities": list(set(
                        cap
                        for e in endpoints
                        for cap in e.metadata.get("capabilities", [])
                    )),
                    "priority": self._cognitive_priorities.get(service_type, 0.5)
                }

                for e in endpoints:
                    if e.status == ServiceStatus.HEALTHY:
                        topology["health_summary"]["healthy"] += 1
                    elif e.status == ServiceStatus.DEGRADED:
                        topology["health_summary"]["degraded"] += 1
                    else:
                        topology["health_summary"]["unhealthy"] += 1

        return topology
