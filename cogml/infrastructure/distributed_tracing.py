#!/usr/bin/env python3
"""
Distributed Tracing for Cross-Component Debugging

Phase 2 Implementation: Provides distributed tracing capabilities including:
- OpenTelemetry-compatible trace context propagation
- Span creation and management
- Cross-component trace correlation
- Performance bottleneck identification
- Trace visualization support
- Error tracking and debugging
"""

import asyncio
import json
import time
import hashlib
import logging
import threading
import random
from typing import Dict, List, Any, Optional, Callable, Set, Generator
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from contextlib import contextmanager
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpanKind(Enum):
    """Types of spans"""
    INTERNAL = "internal"       # Internal operation
    SERVER = "server"           # Server-side request handling
    CLIENT = "client"           # Client-side request
    PRODUCER = "producer"       # Message producer
    CONSUMER = "consumer"       # Message consumer


class SpanStatus(Enum):
    """Span completion status"""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class SpanContext:
    """Trace and span context for propagation"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    trace_flags: int = 1  # 1 = sampled
    trace_state: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "trace_flags": self.trace_flags,
            "trace_state": self.trace_state
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpanContext':
        return cls(
            trace_id=data.get("trace_id", ""),
            span_id=data.get("span_id", ""),
            parent_span_id=data.get("parent_span_id"),
            trace_flags=data.get("trace_flags", 1),
            trace_state=data.get("trace_state", {})
        )

    def to_header(self) -> str:
        """Convert to W3C Trace Context header format"""
        sampled = "01" if self.trace_flags & 1 else "00"
        return f"00-{self.trace_id}-{self.span_id}-{sampled}"

    @classmethod
    def from_header(cls, header: str) -> Optional['SpanContext']:
        """Parse W3C Trace Context header"""
        try:
            parts = header.split("-")
            if len(parts) != 4:
                return None
            return cls(
                trace_id=parts[1],
                span_id=parts[2],
                trace_flags=int(parts[3], 16)
            )
        except Exception:
            return None


@dataclass
class SpanEvent:
    """Event within a span"""
    name: str
    timestamp: float
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanLink:
    """Link to another span"""
    context: SpanContext
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """Represents a single span in a trace"""
    name: str
    context: SpanContext
    kind: SpanKind = SpanKind.INTERNAL
    start_time: float = 0.0
    end_time: Optional[float] = None
    status: SpanStatus = SpanStatus.UNSET
    status_message: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    links: List[SpanLink] = field(default_factory=list)
    resource: Dict[str, str] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        """Get span duration in milliseconds"""
        if self.end_time is None:
            return (time.time() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000

    @property
    def is_recording(self) -> bool:
        """Check if span is still recording"""
        return self.end_time is None

    def set_attribute(self, key: str, value: Any):
        """Set a span attribute"""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to the span"""
        self.events.append(SpanEvent(
            name=name,
            timestamp=time.time(),
            attributes=attributes or {}
        ))

    def add_link(self, context: SpanContext, attributes: Optional[Dict[str, Any]] = None):
        """Add a link to another span"""
        self.links.append(SpanLink(
            context=context,
            attributes=attributes or {}
        ))

    def set_status(self, status: SpanStatus, message: str = ""):
        """Set span status"""
        self.status = status
        self.status_message = message

    def record_exception(self, exception: Exception):
        """Record an exception in the span"""
        self.add_event("exception", {
            "exception.type": type(exception).__name__,
            "exception.message": str(exception),
            "exception.stacktrace": traceback.format_exc()
        })
        self.set_status(SpanStatus.ERROR, str(exception))

    def end(self):
        """End the span"""
        if self.end_time is None:
            self.end_time = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize span to dictionary"""
        return {
            "name": self.name,
            "context": self.context.to_dict(),
            "kind": self.kind.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "status_message": self.status_message,
            "attributes": self.attributes,
            "events": [
                {"name": e.name, "timestamp": e.timestamp, "attributes": e.attributes}
                for e in self.events
            ],
            "links": [
                {"context": l.context.to_dict(), "attributes": l.attributes}
                for l in self.links
            ],
            "resource": self.resource
        }


class Tracer:
    """Creates and manages spans"""

    def __init__(
        self,
        service_name: str,
        service_version: str = "1.0.0",
        sample_rate: float = 1.0
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.sample_rate = sample_rate

        self._current_span: threading.local = threading.local()
        self._span_processors: List[Callable[[Span], None]] = []

    def _generate_id(self, length: int = 16) -> str:
        """Generate a random hex ID"""
        return hashlib.md5(
            f"{time.time()}:{random.random()}".encode()
        ).hexdigest()[:length]

    def _should_sample(self) -> bool:
        """Determine if trace should be sampled"""
        return random.random() < self.sample_rate

    def add_span_processor(self, processor: Callable[[Span], None]):
        """Add a span processor"""
        self._span_processors.append(processor)

    def get_current_span(self) -> Optional[Span]:
        """Get the current active span"""
        return getattr(self._current_span, 'span', None)

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Optional[SpanContext] = None,
        attributes: Optional[Dict[str, Any]] = None,
        links: Optional[List[SpanLink]] = None
    ) -> Span:
        """Start a new span"""
        # Get parent context
        if parent is None:
            current = self.get_current_span()
            if current:
                parent = current.context

        # Determine sampling
        if parent:
            trace_id = parent.trace_id
            parent_span_id = parent.span_id
            trace_flags = parent.trace_flags
        else:
            trace_id = self._generate_id(32)
            parent_span_id = None
            trace_flags = 1 if self._should_sample() else 0

        context = SpanContext(
            trace_id=trace_id,
            span_id=self._generate_id(16),
            parent_span_id=parent_span_id,
            trace_flags=trace_flags
        )

        span = Span(
            name=name,
            context=context,
            kind=kind,
            start_time=time.time(),
            attributes=attributes or {},
            links=links or [],
            resource={
                "service.name": self.service_name,
                "service.version": self.service_version
            }
        )

        return span

    @contextmanager
    def start_as_current_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Generator[Span, None, None]:
        """Context manager for starting a span as the current span"""
        span = self.start_span(name, kind=kind, attributes=attributes)
        previous = getattr(self._current_span, 'span', None)
        self._current_span.span = span

        try:
            yield span
            if span.status == SpanStatus.UNSET:
                span.set_status(SpanStatus.OK)
        except Exception as e:
            span.record_exception(e)
            raise
        finally:
            span.end()
            self._current_span.span = previous

            # Process span
            for processor in self._span_processors:
                try:
                    processor(span)
                except Exception as e:
                    logger.error(f"Span processor error: {e}")


@dataclass
class Trace:
    """Complete trace containing multiple spans"""
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    root_span: Optional[Span] = None

    @property
    def duration_ms(self) -> float:
        """Get total trace duration"""
        if not self.spans:
            return 0.0
        start = min(s.start_time for s in self.spans)
        end = max(s.end_time or time.time() for s in self.spans)
        return (end - start) * 1000

    @property
    def span_count(self) -> int:
        """Get number of spans in trace"""
        return len(self.spans)

    @property
    def error_count(self) -> int:
        """Get number of error spans"""
        return sum(1 for s in self.spans if s.status == SpanStatus.ERROR)

    def get_span_tree(self) -> Dict[str, Any]:
        """Get hierarchical representation of spans"""
        span_map = {s.context.span_id: s for s in self.spans}
        children: Dict[str, List[Span]] = defaultdict(list)

        root = None
        for span in self.spans:
            if span.context.parent_span_id:
                children[span.context.parent_span_id].append(span)
            else:
                root = span

        def build_tree(span: Span) -> Dict[str, Any]:
            return {
                "name": span.name,
                "span_id": span.context.span_id,
                "duration_ms": span.duration_ms,
                "status": span.status.value,
                "attributes": span.attributes,
                "children": [build_tree(c) for c in children.get(span.context.span_id, [])]
            }

        if root:
            return build_tree(root)
        return {}


class TraceStore:
    """Stores and retrieves traces"""

    def __init__(self, max_traces: int = 1000):
        self.max_traces = max_traces
        self._traces: Dict[str, Trace] = {}
        self._span_index: Dict[str, List[str]] = defaultdict(list)  # service -> trace_ids
        self._lock = threading.RLock()

    def add_span(self, span: Span):
        """Add a span to the store"""
        with self._lock:
            trace_id = span.context.trace_id

            if trace_id not in self._traces:
                if len(self._traces) >= self.max_traces:
                    # Remove oldest trace
                    oldest = min(self._traces.values(), key=lambda t: t.spans[0].start_time if t.spans else 0)
                    del self._traces[oldest.trace_id]

                self._traces[trace_id] = Trace(trace_id=trace_id)

            trace = self._traces[trace_id]
            trace.spans.append(span)

            if span.context.parent_span_id is None:
                trace.root_span = span

            # Index by service
            service = span.resource.get("service.name", "unknown")
            if trace_id not in self._span_index[service]:
                self._span_index[service].append(trace_id)

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a complete trace"""
        return self._traces.get(trace_id)

    def get_traces_by_service(
        self,
        service_name: str,
        limit: int = 100
    ) -> List[Trace]:
        """Get traces involving a service"""
        trace_ids = self._span_index.get(service_name, [])[-limit:]
        return [self._traces[tid] for tid in trace_ids if tid in self._traces]

    def search_traces(
        self,
        service: Optional[str] = None,
        operation: Optional[str] = None,
        min_duration_ms: Optional[float] = None,
        has_error: Optional[bool] = None,
        limit: int = 100
    ) -> List[Trace]:
        """Search for traces matching criteria"""
        results = []

        for trace in self._traces.values():
            if len(results) >= limit:
                break

            # Apply filters
            if service:
                if not any(s.resource.get("service.name") == service for s in trace.spans):
                    continue

            if operation:
                if not any(operation in s.name for s in trace.spans):
                    continue

            if min_duration_ms and trace.duration_ms < min_duration_ms:
                continue

            if has_error is not None:
                trace_has_error = trace.error_count > 0
                if has_error != trace_has_error:
                    continue

            results.append(trace)

        return results

    def get_service_dependencies(self) -> Dict[str, Set[str]]:
        """Analyze service dependencies from traces"""
        dependencies: Dict[str, Set[str]] = defaultdict(set)

        for trace in self._traces.values():
            span_services = {}
            for span in trace.spans:
                service = span.resource.get("service.name", "unknown")
                span_services[span.context.span_id] = service

            for span in trace.spans:
                if span.context.parent_span_id:
                    parent_service = span_services.get(span.context.parent_span_id)
                    child_service = span_services.get(span.context.span_id)
                    if parent_service and child_service and parent_service != child_service:
                        dependencies[parent_service].add(child_service)

        return dict(dependencies)


class TraceContextPropagator:
    """Propagates trace context across service boundaries"""

    TRACE_CONTEXT_HEADER = "traceparent"
    TRACE_STATE_HEADER = "tracestate"

    def inject(self, context: SpanContext, carrier: Dict[str, str]):
        """Inject trace context into carrier (headers)"""
        carrier[self.TRACE_CONTEXT_HEADER] = context.to_header()
        if context.trace_state:
            state_str = ",".join(f"{k}={v}" for k, v in context.trace_state.items())
            carrier[self.TRACE_STATE_HEADER] = state_str

    def extract(self, carrier: Dict[str, str]) -> Optional[SpanContext]:
        """Extract trace context from carrier (headers)"""
        trace_header = carrier.get(self.TRACE_CONTEXT_HEADER)
        if not trace_header:
            return None

        context = SpanContext.from_header(trace_header)
        if not context:
            return None

        # Parse trace state
        trace_state = carrier.get(self.TRACE_STATE_HEADER)
        if trace_state:
            for pair in trace_state.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    context.trace_state[key.strip()] = value.strip()

        return context


class CognitiveTracer:
    """
    Distributed tracing system for cognitive components.

    Features:
    - Cognitive-specific span annotations
    - Cross-kernel trace correlation
    - Performance bottleneck detection
    - Error chain analysis
    """

    COGNITIVE_OPERATIONS = {
        "attention_allocation": "Allocating attention resources",
        "reasoning_inference": "Performing logical inference",
        "pattern_matching": "Matching cognitive patterns",
        "memory_access": "Accessing knowledge store",
        "pipeline_processing": "Processing data pipeline",
        "kernel_communication": "Inter-kernel communication"
    }

    def __init__(self, service_name: str = "cognitive-system"):
        self.tracer = Tracer(service_name)
        self.store = TraceStore()
        self.propagator = TraceContextPropagator()

        # Register span processor
        self.tracer.add_span_processor(self._process_span)

    def _process_span(self, span: Span):
        """Process completed spans"""
        self.store.add_span(span)

        # Log slow spans
        if span.duration_ms > 100:
            logger.warning(
                f"Slow span detected: {span.name} took {span.duration_ms:.2f}ms"
            )

    @contextmanager
    def trace_operation(
        self,
        operation: str,
        kernel_id: Optional[str] = None,
        **attributes
    ) -> Generator[Span, None, None]:
        """Trace a cognitive operation"""
        span_name = f"{operation}"
        if kernel_id:
            span_name = f"{kernel_id}/{operation}"

        span_attributes = {
            "cognitive.operation": operation,
            "cognitive.operation.description": self.COGNITIVE_OPERATIONS.get(operation, ""),
            **attributes
        }

        if kernel_id:
            span_attributes["cognitive.kernel.id"] = kernel_id

        with self.tracer.start_as_current_span(
            span_name,
            kind=SpanKind.INTERNAL,
            attributes=span_attributes
        ) as span:
            yield span

    @contextmanager
    def trace_attention(
        self,
        kernel_id: str,
        atom_id: str,
        sti: float
    ) -> Generator[Span, None, None]:
        """Trace attention allocation"""
        with self.trace_operation(
            "attention_allocation",
            kernel_id=kernel_id,
            atom_id=atom_id,
            sti=sti
        ) as span:
            yield span

    @contextmanager
    def trace_reasoning(
        self,
        rule_name: str,
        inference_type: str
    ) -> Generator[Span, None, None]:
        """Trace reasoning operation"""
        with self.trace_operation(
            "reasoning_inference",
            rule=rule_name,
            inference_type=inference_type
        ) as span:
            yield span

    @contextmanager
    def trace_pipeline(
        self,
        pipeline_id: str,
        node_id: str
    ) -> Generator[Span, None, None]:
        """Trace pipeline processing"""
        with self.trace_operation(
            "pipeline_processing",
            pipeline_id=pipeline_id,
            node_id=node_id
        ) as span:
            yield span

    def create_child_context(self) -> Optional[SpanContext]:
        """Create a child context for cross-service propagation"""
        current = self.tracer.get_current_span()
        if current:
            return SpanContext(
                trace_id=current.context.trace_id,
                span_id=self.tracer._generate_id(16),
                parent_span_id=current.context.span_id,
                trace_flags=current.context.trace_flags
            )
        return None

    def inject_context(self, headers: Dict[str, str]):
        """Inject current trace context into headers"""
        current = self.tracer.get_current_span()
        if current:
            self.propagator.inject(current.context, headers)

    def extract_context(self, headers: Dict[str, str]) -> Optional[SpanContext]:
        """Extract trace context from headers"""
        return self.propagator.extract(headers)

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a specific trace"""
        return self.store.get_trace(trace_id)

    def search_traces(self, **kwargs) -> List[Trace]:
        """Search for traces"""
        return self.store.search_traces(**kwargs)

    def get_slow_operations(self, threshold_ms: float = 100.0) -> List[Dict[str, Any]]:
        """Find slow operations across all traces"""
        slow_ops = []

        for trace in self.store._traces.values():
            for span in trace.spans:
                if span.duration_ms >= threshold_ms:
                    slow_ops.append({
                        "trace_id": span.context.trace_id,
                        "span_id": span.context.span_id,
                        "name": span.name,
                        "duration_ms": span.duration_ms,
                        "service": span.resource.get("service.name"),
                        "attributes": span.attributes
                    })

        return sorted(slow_ops, key=lambda x: x["duration_ms"], reverse=True)

    def get_error_traces(self, limit: int = 100) -> List[Trace]:
        """Get traces containing errors"""
        return self.store.search_traces(has_error=True, limit=limit)

    def get_dependency_graph(self) -> Dict[str, Any]:
        """Get service dependency graph"""
        deps = self.store.get_service_dependencies()
        return {
            "services": list(set(deps.keys()) | set(s for svc in deps.values() for s in svc)),
            "edges": [
                {"from": src, "to": dst}
                for src, dsts in deps.items()
                for dst in dsts
            ]
        }

    def get_trace_statistics(self) -> Dict[str, Any]:
        """Get trace statistics"""
        traces = list(self.store._traces.values())
        if not traces:
            return {"total_traces": 0}

        durations = [t.duration_ms for t in traces]
        error_counts = [t.error_count for t in traces]

        return {
            "total_traces": len(traces),
            "total_spans": sum(t.span_count for t in traces),
            "traces_with_errors": sum(1 for t in traces if t.error_count > 0),
            "duration_stats": {
                "min_ms": min(durations),
                "max_ms": max(durations),
                "avg_ms": sum(durations) / len(durations),
                "p95_ms": sorted(durations)[int(len(durations) * 0.95)] if durations else 0
            },
            "services": list(self.store._span_index.keys())
        }
