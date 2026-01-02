#!/usr/bin/env python3
"""
Advanced Monitoring System for Cognitive Process Visualization

Phase 2 Implementation: Provides real-time monitoring capabilities including:
- Cognitive process metrics collection
- Real-time performance dashboards
- Alert and anomaly detection
- Resource utilization tracking
- Health status aggregation
- Metric visualization support
"""

import asyncio
import json
import time
import logging
import threading
import statistics
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"           # Monotonically increasing
    GAUGE = "gauge"               # Arbitrary values
    HISTOGRAM = "histogram"       # Distribution of values
    SUMMARY = "summary"           # Statistical summary
    TIMER = "timer"               # Duration measurements


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class Metric:
    """Represents a single metric"""
    name: str
    metric_type: MetricType
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""


@dataclass
class Alert:
    """Represents an alert"""
    alert_id: str
    name: str
    message: str
    severity: AlertSeverity
    timestamp: float
    source: str
    labels: Dict[str, str] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[float] = None


@dataclass
class HealthCheck:
    """Health check result"""
    component: str
    status: HealthStatus
    message: str
    timestamp: float
    details: Dict[str, Any] = field(default_factory=dict)


class MetricCollector:
    """Collects and stores metrics"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._counters: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()

    def record_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a counter increment"""
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value

            metric = Metric(
                name=name,
                metric_type=MetricType.COUNTER,
                value=self._counters[key],
                timestamp=time.time(),
                labels=labels or {}
            )
            self._metrics[key].append(metric)

    def record_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        unit: str = ""
    ):
        """Record a gauge value"""
        with self._lock:
            key = self._make_key(name, labels)

            metric = Metric(
                name=name,
                metric_type=MetricType.GAUGE,
                value=value,
                timestamp=time.time(),
                labels=labels or {},
                unit=unit
            )
            self._metrics[key].append(metric)

    def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a histogram value"""
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)

            # Keep histogram values bounded
            if len(self._histograms[key]) > self.max_history:
                self._histograms[key] = self._histograms[key][-self.max_history:]

            metric = Metric(
                name=name,
                metric_type=MetricType.HISTOGRAM,
                value=value,
                timestamp=time.time(),
                labels=labels or {}
            )
            self._metrics[key].append(metric)

    def record_timer(
        self,
        name: str,
        duration: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a timer duration"""
        self.record_histogram(name, duration, labels)

    def get_metric(self, name: str, labels: Optional[Dict[str, str]] = None) -> List[Metric]:
        """Get metric history"""
        key = self._make_key(name, labels)
        return list(self._metrics.get(key, []))

    def get_counter_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value"""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)

    def get_histogram_stats(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """Get histogram statistics"""
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])

        if not values:
            return {}

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stddev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "p95": self._percentile(values, 95),
            "p99": self._percentile(values, 99)
        }

    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create a unique key for a metric"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def get_all_metrics(self) -> Dict[str, List[Metric]]:
        """Get all collected metrics"""
        return {key: list(metrics) for key, metrics in self._metrics.items()}


class AlertManager:
    """Manages alerts and notifications"""

    def __init__(self):
        self._alerts: Dict[str, Alert] = {}
        self._alert_handlers: List[Callable[[Alert], None]] = []
        self._lock = threading.RLock()

    def add_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler"""
        self._alert_handlers.append(handler)

    def fire_alert(
        self,
        name: str,
        message: str,
        severity: AlertSeverity,
        source: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Alert:
        """Fire an alert"""
        with self._lock:
            alert_id = f"{name}:{source}:{time.time()}"

            alert = Alert(
                alert_id=alert_id,
                name=name,
                message=message,
                severity=severity,
                timestamp=time.time(),
                source=source,
                labels=labels or {}
            )

            self._alerts[alert_id] = alert

            # Notify handlers
            for handler in self._alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler error: {e}")

            logger.warning(f"Alert fired: [{severity.value}] {name} - {message}")
            return alert

    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        with self._lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].resolved = True
                self._alerts[alert_id].resolved_at = time.time()

    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        return [a for a in self._alerts.values() if not a.resolved]

    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts by severity"""
        return [a for a in self._alerts.values() if a.severity == severity]


class HealthMonitor:
    """Monitors component health"""

    def __init__(self):
        self._health_checks: Dict[str, Callable[[], HealthCheck]] = {}
        self._last_results: Dict[str, HealthCheck] = {}
        self._lock = threading.RLock()

    def register_check(self, component: str, check_fn: Callable[[], HealthCheck]):
        """Register a health check"""
        self._health_checks[component] = check_fn

    def unregister_check(self, component: str):
        """Unregister a health check"""
        if component in self._health_checks:
            del self._health_checks[component]

    async def run_checks(self) -> Dict[str, HealthCheck]:
        """Run all health checks"""
        results = {}

        for component, check_fn in self._health_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_fn):
                    result = await check_fn()
                else:
                    result = check_fn()
                results[component] = result

            except Exception as e:
                results[component] = HealthCheck(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    timestamp=time.time()
                )

        with self._lock:
            self._last_results = results

        return results

    def get_overall_health(self) -> Tuple[HealthStatus, Dict[str, HealthCheck]]:
        """Get overall system health"""
        if not self._last_results:
            return HealthStatus.UNKNOWN, {}

        statuses = [r.status for r in self._last_results.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.UNKNOWN

        return overall, self._last_results


class ThresholdRule:
    """Alert threshold rule"""

    def __init__(
        self,
        name: str,
        metric_name: str,
        threshold: float,
        comparison: str,  # "gt", "lt", "gte", "lte", "eq"
        severity: AlertSeverity,
        message_template: str,
        labels: Optional[Dict[str, str]] = None,
        for_duration: float = 0.0  # Alert only if condition persists
    ):
        self.name = name
        self.metric_name = metric_name
        self.threshold = threshold
        self.comparison = comparison
        self.severity = severity
        self.message_template = message_template
        self.labels = labels
        self.for_duration = for_duration
        self._condition_start: Optional[float] = None

    def evaluate(self, value: float) -> bool:
        """Evaluate if threshold is breached"""
        if self.comparison == "gt":
            return value > self.threshold
        elif self.comparison == "lt":
            return value < self.threshold
        elif self.comparison == "gte":
            return value >= self.threshold
        elif self.comparison == "lte":
            return value <= self.threshold
        elif self.comparison == "eq":
            return value == self.threshold
        return False


class AnomalyDetector:
    """Simple anomaly detection using statistical methods"""

    def __init__(self, window_size: int = 100, z_threshold: float = 3.0):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self._baselines: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))

    def record(self, metric_name: str, value: float) -> Optional[float]:
        """Record a value and return z-score if anomalous"""
        baseline = self._baselines[metric_name]
        baseline.append(value)

        if len(baseline) < 10:  # Need minimum data points
            return None

        values = list(baseline)
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 1.0

        if stdev == 0:
            return None

        z_score = abs(value - mean) / stdev

        if z_score > self.z_threshold:
            return z_score

        return None


@dataclass
class CognitiveMetrics:
    """Cognitive-specific metrics"""
    attention_allocation_rate: float = 0.0
    reasoning_operations_per_sec: float = 0.0
    memory_access_latency_ms: float = 0.0
    cognitive_coherence: float = 0.0
    emergent_patterns_detected: int = 0
    active_kernels: int = 0
    pipeline_throughput: float = 0.0


class CognitiveMonitor:
    """
    Advanced monitoring system for cognitive processes.

    Features:
    - Cognitive-specific metrics
    - Real-time performance tracking
    - Anomaly detection
    - Health aggregation
    - Alert management
    """

    def __init__(self):
        self.metrics = MetricCollector()
        self.alerts = AlertManager()
        self.health = HealthMonitor()
        self.anomaly_detector = AnomalyDetector()

        self._threshold_rules: List[ThresholdRule] = []
        self._running = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_interval = 10.0

        # Pre-define cognitive metrics
        self._cognitive_metrics = CognitiveMetrics()

    def add_threshold_rule(self, rule: ThresholdRule):
        """Add a threshold alerting rule"""
        self._threshold_rules.append(rule)

    def remove_threshold_rule(self, rule_name: str):
        """Remove a threshold rule"""
        self._threshold_rules = [r for r in self._threshold_rules if r.name != rule_name]

    def record_attention_allocation(self, allocation_rate: float, kernel_id: str):
        """Record attention allocation metrics"""
        self.metrics.record_gauge(
            "cognitive_attention_allocation_rate",
            allocation_rate,
            labels={"kernel": kernel_id},
            unit="ops/sec"
        )
        self._cognitive_metrics.attention_allocation_rate = allocation_rate

    def record_reasoning_operation(self, duration: float, operation_type: str):
        """Record reasoning operation metrics"""
        self.metrics.record_timer(
            "cognitive_reasoning_duration",
            duration,
            labels={"type": operation_type}
        )
        self.metrics.record_counter(
            "cognitive_reasoning_operations_total",
            labels={"type": operation_type}
        )

    def record_memory_access(self, latency_ms: float, access_type: str):
        """Record memory access metrics"""
        self.metrics.record_histogram(
            "cognitive_memory_latency_ms",
            latency_ms,
            labels={"type": access_type}
        )
        self._cognitive_metrics.memory_access_latency_ms = latency_ms

    def record_cognitive_coherence(self, coherence: float):
        """Record cognitive coherence metric"""
        self.metrics.record_gauge(
            "cognitive_coherence",
            coherence,
            unit="ratio"
        )
        self._cognitive_metrics.cognitive_coherence = coherence

        # Check for anomaly
        z_score = self.anomaly_detector.record("cognitive_coherence", coherence)
        if z_score:
            self.alerts.fire_alert(
                name="cognitive_coherence_anomaly",
                message=f"Cognitive coherence anomaly detected (z-score: {z_score:.2f})",
                severity=AlertSeverity.WARNING,
                source="anomaly_detector"
            )

    def record_emergent_pattern(self, pattern_type: str):
        """Record emergent pattern detection"""
        self.metrics.record_counter(
            "cognitive_emergent_patterns_total",
            labels={"type": pattern_type}
        )
        self._cognitive_metrics.emergent_patterns_detected += 1

    def record_kernel_activity(self, kernel_id: str, active: bool):
        """Record kernel activity"""
        self.metrics.record_gauge(
            "cognitive_kernel_active",
            1.0 if active else 0.0,
            labels={"kernel": kernel_id}
        )

    def record_pipeline_throughput(self, throughput: float, pipeline_id: str):
        """Record pipeline throughput"""
        self.metrics.record_gauge(
            "cognitive_pipeline_throughput",
            throughput,
            labels={"pipeline": pipeline_id},
            unit="packets/sec"
        )
        self._cognitive_metrics.pipeline_throughput = throughput

    async def _check_thresholds(self):
        """Check threshold rules and fire alerts"""
        for rule in self._threshold_rules:
            metrics = self.metrics.get_metric(rule.metric_name, rule.labels)
            if not metrics:
                continue

            latest_value = metrics[-1].value

            if rule.evaluate(latest_value):
                if rule.for_duration > 0:
                    if rule._condition_start is None:
                        rule._condition_start = time.time()
                    elif time.time() - rule._condition_start >= rule.for_duration:
                        message = rule.message_template.format(
                            value=latest_value,
                            threshold=rule.threshold
                        )
                        self.alerts.fire_alert(
                            name=rule.name,
                            message=message,
                            severity=rule.severity,
                            source="threshold_monitor",
                            labels=rule.labels
                        )
                        rule._condition_start = None
                else:
                    message = rule.message_template.format(
                        value=latest_value,
                        threshold=rule.threshold
                    )
                    self.alerts.fire_alert(
                        name=rule.name,
                        message=message,
                        severity=rule.severity,
                        source="threshold_monitor",
                        labels=rule.labels
                    )
            else:
                rule._condition_start = None

    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                # Run health checks
                await self.health.run_checks()

                # Check threshold rules
                await self._check_thresholds()

            except Exception as e:
                logger.error(f"Monitoring error: {e}")

            await asyncio.sleep(self._monitoring_interval)

    async def start(self, interval: float = 10.0):
        """Start the monitoring system"""
        self._running = True
        self._monitoring_interval = interval
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Cognitive monitor started")

    async def stop(self):
        """Stop the monitoring system"""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Cognitive monitor stopped")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard visualization"""
        overall_health, health_checks = self.health.get_overall_health()

        return {
            "timestamp": time.time(),
            "health": {
                "overall": overall_health.value,
                "components": {
                    comp: {
                        "status": check.status.value,
                        "message": check.message,
                        "details": check.details
                    }
                    for comp, check in health_checks.items()
                }
            },
            "cognitive_metrics": {
                "attention_allocation_rate": self._cognitive_metrics.attention_allocation_rate,
                "reasoning_operations_per_sec": self._cognitive_metrics.reasoning_operations_per_sec,
                "memory_access_latency_ms": self._cognitive_metrics.memory_access_latency_ms,
                "cognitive_coherence": self._cognitive_metrics.cognitive_coherence,
                "emergent_patterns_detected": self._cognitive_metrics.emergent_patterns_detected,
                "pipeline_throughput": self._cognitive_metrics.pipeline_throughput
            },
            "alerts": {
                "active_count": len(self.alerts.get_active_alerts()),
                "by_severity": {
                    severity.value: len(self.alerts.get_alerts_by_severity(severity))
                    for severity in AlertSeverity
                },
                "recent": [
                    {
                        "id": a.alert_id,
                        "name": a.name,
                        "message": a.message,
                        "severity": a.severity.value,
                        "timestamp": a.timestamp
                    }
                    for a in self.alerts.get_active_alerts()[-5:]
                ]
            },
            "metrics_summary": {
                "attention": self.metrics.get_histogram_stats("cognitive_attention_allocation_rate"),
                "reasoning": self.metrics.get_histogram_stats("cognitive_reasoning_duration"),
                "memory": self.metrics.get_histogram_stats("cognitive_memory_latency_ms")
            }
        }

    def get_metrics_export(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        all_metrics = self.metrics.get_all_metrics()

        if format == "json":
            export_data = {
                key: [
                    {
                        "name": m.name,
                        "type": m.metric_type.value,
                        "value": m.value,
                        "timestamp": m.timestamp,
                        "labels": m.labels
                    }
                    for m in metrics
                ]
                for key, metrics in all_metrics.items()
            }
            return json.dumps(export_data, indent=2)

        elif format == "prometheus":
            lines = []
            for key, metrics in all_metrics.items():
                if not metrics:
                    continue
                latest = metrics[-1]
                labels_str = ",".join(f'{k}="{v}"' for k, v in latest.labels.items())
                metric_name = latest.name.replace(".", "_").replace("-", "_")
                if labels_str:
                    lines.append(f"{metric_name}{{{labels_str}}} {latest.value}")
                else:
                    lines.append(f"{metric_name} {latest.value}")
            return "\n".join(lines)

        return ""
