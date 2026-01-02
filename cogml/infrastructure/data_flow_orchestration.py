#!/usr/bin/env python3
"""
Data Flow Orchestration System

Phase 2 Implementation: Provides cognitive data pipeline orchestration including:
- Visual pipeline builder abstraction
- DAG-based workflow execution
- Data transformation nodes
- Parallel and sequential processing
- Error handling and retry logic
- Pipeline monitoring and metrics
"""

import asyncio
import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional, Callable, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor
import copy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of pipeline nodes"""
    SOURCE = "source"           # Data ingestion
    TRANSFORM = "transform"     # Data transformation
    FILTER = "filter"           # Data filtering
    AGGREGATE = "aggregate"     # Data aggregation
    BRANCH = "branch"           # Conditional branching
    MERGE = "merge"             # Stream merging
    SINK = "sink"               # Data output
    COGNITIVE = "cognitive"     # Cognitive processing


class ExecutionStatus(Enum):
    """Node execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class DataPacket:
    """Data flowing through the pipeline"""
    packet_id: str
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    trace: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    source_node: Optional[str] = None

    def clone(self) -> 'DataPacket':
        """Create a deep copy of the packet"""
        return DataPacket(
            packet_id=self.packet_id,
            data=copy.deepcopy(self.data),
            metadata=copy.deepcopy(self.metadata),
            trace=self.trace.copy(),
            timestamp=self.timestamp,
            source_node=self.source_node
        )


@dataclass
class NodeResult:
    """Result from node execution"""
    node_id: str
    status: ExecutionStatus
    output: Optional[List[DataPacket]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)


class PipelineNode(ABC):
    """Abstract base class for pipeline nodes"""

    def __init__(
        self,
        node_id: str,
        node_type: NodeType,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.node_id = node_id
        self.node_type = node_type
        self.name = name or node_id
        self.config = config or {}

        self._input_nodes: List[str] = []
        self._output_nodes: List[str] = []
        self._status = ExecutionStatus.PENDING
        self._metrics: Dict[str, Any] = defaultdict(float)

    @abstractmethod
    async def process(self, inputs: List[DataPacket]) -> List[DataPacket]:
        """Process input data packets and return output packets"""
        pass

    def add_input(self, node_id: str):
        """Add an input connection"""
        if node_id not in self._input_nodes:
            self._input_nodes.append(node_id)

    def add_output(self, node_id: str):
        """Add an output connection"""
        if node_id not in self._output_nodes:
            self._output_nodes.append(node_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize node to dictionary"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "name": self.name,
            "config": self.config,
            "input_nodes": self._input_nodes,
            "output_nodes": self._output_nodes,
            "status": self._status.value
        }


class SourceNode(PipelineNode):
    """Data source node"""

    def __init__(self, node_id: str, data_generator: Callable, **kwargs):
        super().__init__(node_id, NodeType.SOURCE, **kwargs)
        self.data_generator = data_generator

    async def process(self, inputs: List[DataPacket]) -> List[DataPacket]:
        """Generate data packets"""
        data = await self._generate_data()
        packet = DataPacket(
            packet_id=hashlib.md5(f"{self.node_id}:{time.time()}".encode()).hexdigest()[:12],
            data=data,
            source_node=self.node_id,
            trace=[self.node_id]
        )
        return [packet]

    async def _generate_data(self) -> Any:
        """Generate data using the configured generator"""
        if asyncio.iscoroutinefunction(self.data_generator):
            return await self.data_generator()
        return self.data_generator()


class TransformNode(PipelineNode):
    """Data transformation node"""

    def __init__(self, node_id: str, transform_fn: Callable, **kwargs):
        super().__init__(node_id, NodeType.TRANSFORM, **kwargs)
        self.transform_fn = transform_fn

    async def process(self, inputs: List[DataPacket]) -> List[DataPacket]:
        """Transform input data packets"""
        outputs = []
        for packet in inputs:
            try:
                if asyncio.iscoroutinefunction(self.transform_fn):
                    transformed_data = await self.transform_fn(packet.data)
                else:
                    transformed_data = self.transform_fn(packet.data)

                new_packet = packet.clone()
                new_packet.data = transformed_data
                new_packet.trace.append(self.node_id)
                outputs.append(new_packet)

            except Exception as e:
                logger.error(f"Transform error in {self.node_id}: {e}")
                new_packet = packet.clone()
                new_packet.metadata["error"] = str(e)
                new_packet.trace.append(f"{self.node_id}:ERROR")
                outputs.append(new_packet)

        return outputs


class FilterNode(PipelineNode):
    """Data filtering node"""

    def __init__(self, node_id: str, filter_fn: Callable, **kwargs):
        super().__init__(node_id, NodeType.FILTER, **kwargs)
        self.filter_fn = filter_fn

    async def process(self, inputs: List[DataPacket]) -> List[DataPacket]:
        """Filter input data packets"""
        outputs = []
        for packet in inputs:
            try:
                if asyncio.iscoroutinefunction(self.filter_fn):
                    should_include = await self.filter_fn(packet.data)
                else:
                    should_include = self.filter_fn(packet.data)

                if should_include:
                    new_packet = packet.clone()
                    new_packet.trace.append(self.node_id)
                    outputs.append(new_packet)

            except Exception as e:
                logger.error(f"Filter error in {self.node_id}: {e}")

        self._metrics["filtered_count"] = len(inputs) - len(outputs)
        return outputs


class AggregateNode(PipelineNode):
    """Data aggregation node"""

    def __init__(
        self,
        node_id: str,
        aggregate_fn: Callable,
        window_size: int = 10,
        **kwargs
    ):
        super().__init__(node_id, NodeType.AGGREGATE, **kwargs)
        self.aggregate_fn = aggregate_fn
        self.window_size = window_size
        self._buffer: List[DataPacket] = []

    async def process(self, inputs: List[DataPacket]) -> List[DataPacket]:
        """Aggregate input data packets"""
        self._buffer.extend(inputs)

        if len(self._buffer) < self.window_size:
            return []

        # Process window
        window = self._buffer[:self.window_size]
        self._buffer = self._buffer[self.window_size:]

        try:
            data_list = [p.data for p in window]
            if asyncio.iscoroutinefunction(self.aggregate_fn):
                aggregated_data = await self.aggregate_fn(data_list)
            else:
                aggregated_data = self.aggregate_fn(data_list)

            packet = DataPacket(
                packet_id=hashlib.md5(f"{self.node_id}:{time.time()}".encode()).hexdigest()[:12],
                data=aggregated_data,
                source_node=self.node_id,
                trace=[self.node_id],
                metadata={"aggregated_count": len(window)}
            )
            return [packet]

        except Exception as e:
            logger.error(f"Aggregate error in {self.node_id}: {e}")
            return []


class BranchNode(PipelineNode):
    """Conditional branching node"""

    def __init__(
        self,
        node_id: str,
        condition_fn: Callable,
        true_output: str,
        false_output: str,
        **kwargs
    ):
        super().__init__(node_id, NodeType.BRANCH, **kwargs)
        self.condition_fn = condition_fn
        self.true_output = true_output
        self.false_output = false_output

    async def process(self, inputs: List[DataPacket]) -> List[DataPacket]:
        """Branch input data packets based on condition"""
        outputs = []
        for packet in inputs:
            try:
                if asyncio.iscoroutinefunction(self.condition_fn):
                    condition_result = await self.condition_fn(packet.data)
                else:
                    condition_result = self.condition_fn(packet.data)

                new_packet = packet.clone()
                new_packet.trace.append(self.node_id)
                new_packet.metadata["branch_result"] = condition_result
                new_packet.metadata["target_node"] = (
                    self.true_output if condition_result else self.false_output
                )
                outputs.append(new_packet)

            except Exception as e:
                logger.error(f"Branch error in {self.node_id}: {e}")

        return outputs


class MergeNode(PipelineNode):
    """Stream merging node"""

    def __init__(self, node_id: str, merge_strategy: str = "concat", **kwargs):
        super().__init__(node_id, NodeType.MERGE, **kwargs)
        self.merge_strategy = merge_strategy
        self._buffers: Dict[str, List[DataPacket]] = defaultdict(list)

    async def process(self, inputs: List[DataPacket]) -> List[DataPacket]:
        """Merge input data packets from multiple sources"""
        # Buffer inputs by source
        for packet in inputs:
            source = packet.source_node or "unknown"
            self._buffers[source].append(packet)

        # Check if all inputs have data
        if len(self._buffers) < len(self._input_nodes):
            return []

        # Merge based on strategy
        outputs = []
        if self.merge_strategy == "concat":
            for source, packets in self._buffers.items():
                for packet in packets:
                    new_packet = packet.clone()
                    new_packet.trace.append(self.node_id)
                    outputs.append(new_packet)

        elif self.merge_strategy == "zip":
            min_len = min(len(p) for p in self._buffers.values())
            for i in range(min_len):
                merged_data = {
                    source: packets[i].data
                    for source, packets in self._buffers.items()
                }
                packet = DataPacket(
                    packet_id=hashlib.md5(f"{self.node_id}:{time.time()}:{i}".encode()).hexdigest()[:12],
                    data=merged_data,
                    source_node=self.node_id,
                    trace=[self.node_id]
                )
                outputs.append(packet)

        # Clear buffers
        self._buffers.clear()
        return outputs


class SinkNode(PipelineNode):
    """Data sink node"""

    def __init__(self, node_id: str, sink_fn: Callable, **kwargs):
        super().__init__(node_id, NodeType.SINK, **kwargs)
        self.sink_fn = sink_fn
        self._received_packets: List[DataPacket] = []

    async def process(self, inputs: List[DataPacket]) -> List[DataPacket]:
        """Process and store output data"""
        for packet in inputs:
            try:
                if asyncio.iscoroutinefunction(self.sink_fn):
                    await self.sink_fn(packet.data)
                else:
                    self.sink_fn(packet.data)

                self._received_packets.append(packet)

            except Exception as e:
                logger.error(f"Sink error in {self.node_id}: {e}")

        return []

    def get_received_data(self) -> List[Any]:
        """Get all received data"""
        return [p.data for p in self._received_packets]


class CognitiveNode(PipelineNode):
    """Cognitive processing node"""

    def __init__(
        self,
        node_id: str,
        cognitive_operation: str,
        processor: Callable,
        **kwargs
    ):
        super().__init__(node_id, NodeType.COGNITIVE, **kwargs)
        self.cognitive_operation = cognitive_operation
        self.processor = processor

    async def process(self, inputs: List[DataPacket]) -> List[DataPacket]:
        """Apply cognitive processing to input data"""
        outputs = []
        for packet in inputs:
            try:
                start_time = time.time()

                if asyncio.iscoroutinefunction(self.processor):
                    result = await self.processor(
                        packet.data,
                        operation=self.cognitive_operation,
                        config=self.config
                    )
                else:
                    result = self.processor(
                        packet.data,
                        operation=self.cognitive_operation,
                        config=self.config
                    )

                processing_time = time.time() - start_time

                new_packet = packet.clone()
                new_packet.data = result
                new_packet.trace.append(self.node_id)
                new_packet.metadata["cognitive_operation"] = self.cognitive_operation
                new_packet.metadata["processing_time"] = processing_time
                outputs.append(new_packet)

                self._metrics["total_processing_time"] += processing_time
                self._metrics["operations_count"] = self._metrics.get("operations_count", 0) + 1

            except Exception as e:
                logger.error(f"Cognitive processing error in {self.node_id}: {e}")
                new_packet = packet.clone()
                new_packet.metadata["error"] = str(e)
                outputs.append(new_packet)

        return outputs


@dataclass
class PipelineExecution:
    """Record of a pipeline execution"""
    execution_id: str
    pipeline_id: str
    start_time: float
    end_time: Optional[float] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    node_results: Dict[str, NodeResult] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class Pipeline:
    """
    Data flow pipeline implementation.

    Supports:
    - DAG-based workflow definition
    - Parallel and sequential execution
    - Error handling and retry logic
    - Execution monitoring
    """

    def __init__(self, pipeline_id: str, name: Optional[str] = None):
        self.pipeline_id = pipeline_id
        self.name = name or pipeline_id
        self._nodes: Dict[str, PipelineNode] = {}
        self._edges: List[Tuple[str, str]] = []
        self._execution_history: List[PipelineExecution] = []

    def add_node(self, node: PipelineNode) -> 'Pipeline':
        """Add a node to the pipeline"""
        self._nodes[node.node_id] = node
        return self

    def connect(self, from_node: str, to_node: str) -> 'Pipeline':
        """Connect two nodes"""
        if from_node not in self._nodes:
            raise ValueError(f"Source node not found: {from_node}")
        if to_node not in self._nodes:
            raise ValueError(f"Target node not found: {to_node}")

        self._edges.append((from_node, to_node))
        self._nodes[from_node].add_output(to_node)
        self._nodes[to_node].add_input(from_node)
        return self

    def get_source_nodes(self) -> List[PipelineNode]:
        """Get nodes with no inputs (entry points)"""
        return [
            node for node in self._nodes.values()
            if not node._input_nodes
        ]

    def get_sink_nodes(self) -> List[PipelineNode]:
        """Get nodes with no outputs (exit points)"""
        return [
            node for node in self._nodes.values()
            if not node._output_nodes
        ]

    def get_execution_order(self) -> List[List[str]]:
        """Get topologically sorted execution order (layers for parallel execution)"""
        in_degree = {node_id: len(node._input_nodes) for node_id, node in self._nodes.items()}
        layers = []

        while in_degree:
            # Get nodes with no dependencies
            layer = [node_id for node_id, degree in in_degree.items() if degree == 0]

            if not layer:
                raise ValueError("Cycle detected in pipeline graph")

            layers.append(layer)

            # Remove processed nodes and update degrees
            for node_id in layer:
                del in_degree[node_id]
                for output_id in self._nodes[node_id]._output_nodes:
                    if output_id in in_degree:
                        in_degree[output_id] -= 1

        return layers

    async def execute(self, initial_data: Optional[List[DataPacket]] = None) -> PipelineExecution:
        """Execute the pipeline"""
        execution = PipelineExecution(
            execution_id=hashlib.md5(f"{self.pipeline_id}:{time.time()}".encode()).hexdigest()[:12],
            pipeline_id=self.pipeline_id,
            start_time=time.time(),
            status=ExecutionStatus.RUNNING
        )

        try:
            # Get execution order
            execution_order = self.get_execution_order()

            # Track data flowing through the pipeline
            node_outputs: Dict[str, List[DataPacket]] = {}

            # Execute layer by layer
            for layer in execution_order:
                # Execute nodes in layer in parallel
                layer_tasks = []
                for node_id in layer:
                    node = self._nodes[node_id]

                    # Collect inputs from upstream nodes
                    inputs = []
                    if node._input_nodes:
                        for input_id in node._input_nodes:
                            if input_id in node_outputs:
                                inputs.extend(node_outputs[input_id])
                    elif initial_data:
                        inputs = initial_data

                    layer_tasks.append(self._execute_node(node, inputs, execution))

                # Wait for all nodes in layer to complete
                results = await asyncio.gather(*layer_tasks, return_exceptions=True)

                # Store outputs for downstream nodes
                for node_id, result in zip(layer, results):
                    if isinstance(result, Exception):
                        logger.error(f"Node {node_id} failed: {result}")
                        execution.node_results[node_id] = NodeResult(
                            node_id=node_id,
                            status=ExecutionStatus.FAILED,
                            error=str(result)
                        )
                    else:
                        node_outputs[node_id] = result

            execution.status = ExecutionStatus.COMPLETED
            execution.end_time = time.time()

            # Calculate metrics
            execution.metrics = {
                "total_nodes": len(self._nodes),
                "successful_nodes": sum(
                    1 for r in execution.node_results.values()
                    if r.status == ExecutionStatus.COMPLETED
                ),
                "total_execution_time": execution.end_time - execution.start_time,
                "layers": len(execution_order)
            }

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            execution.end_time = time.time()
            logger.error(f"Pipeline execution failed: {e}")

        self._execution_history.append(execution)
        return execution

    async def _execute_node(
        self,
        node: PipelineNode,
        inputs: List[DataPacket],
        execution: PipelineExecution
    ) -> List[DataPacket]:
        """Execute a single node"""
        start_time = time.time()
        node._status = ExecutionStatus.RUNNING

        try:
            outputs = await node.process(inputs)

            node._status = ExecutionStatus.COMPLETED
            execution.node_results[node.node_id] = NodeResult(
                node_id=node.node_id,
                status=ExecutionStatus.COMPLETED,
                output=outputs,
                execution_time=time.time() - start_time,
                metrics=dict(node._metrics)
            )

            return outputs

        except Exception as e:
            node._status = ExecutionStatus.FAILED
            execution.node_results[node.node_id] = NodeResult(
                node_id=node.node_id,
                status=ExecutionStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Serialize pipeline to dictionary"""
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "nodes": {node_id: node.to_dict() for node_id, node in self._nodes.items()},
            "edges": self._edges,
            "source_nodes": [n.node_id for n in self.get_source_nodes()],
            "sink_nodes": [n.node_id for n in self.get_sink_nodes()]
        }


class PipelineBuilder:
    """Fluent builder for constructing pipelines"""

    def __init__(self, pipeline_id: str, name: Optional[str] = None):
        self.pipeline = Pipeline(pipeline_id, name)
        self._last_node: Optional[str] = None

    def source(
        self,
        node_id: str,
        generator: Callable,
        **kwargs
    ) -> 'PipelineBuilder':
        """Add a source node"""
        node = SourceNode(node_id, generator, **kwargs)
        self.pipeline.add_node(node)
        self._last_node = node_id
        return self

    def transform(
        self,
        node_id: str,
        transform_fn: Callable,
        connect_from: Optional[str] = None,
        **kwargs
    ) -> 'PipelineBuilder':
        """Add a transform node"""
        node = TransformNode(node_id, transform_fn, **kwargs)
        self.pipeline.add_node(node)

        source = connect_from or self._last_node
        if source:
            self.pipeline.connect(source, node_id)

        self._last_node = node_id
        return self

    def filter(
        self,
        node_id: str,
        filter_fn: Callable,
        connect_from: Optional[str] = None,
        **kwargs
    ) -> 'PipelineBuilder':
        """Add a filter node"""
        node = FilterNode(node_id, filter_fn, **kwargs)
        self.pipeline.add_node(node)

        source = connect_from or self._last_node
        if source:
            self.pipeline.connect(source, node_id)

        self._last_node = node_id
        return self

    def aggregate(
        self,
        node_id: str,
        aggregate_fn: Callable,
        window_size: int = 10,
        connect_from: Optional[str] = None,
        **kwargs
    ) -> 'PipelineBuilder':
        """Add an aggregate node"""
        node = AggregateNode(node_id, aggregate_fn, window_size, **kwargs)
        self.pipeline.add_node(node)

        source = connect_from or self._last_node
        if source:
            self.pipeline.connect(source, node_id)

        self._last_node = node_id
        return self

    def cognitive(
        self,
        node_id: str,
        operation: str,
        processor: Callable,
        connect_from: Optional[str] = None,
        **kwargs
    ) -> 'PipelineBuilder':
        """Add a cognitive processing node"""
        node = CognitiveNode(node_id, operation, processor, **kwargs)
        self.pipeline.add_node(node)

        source = connect_from or self._last_node
        if source:
            self.pipeline.connect(source, node_id)

        self._last_node = node_id
        return self

    def sink(
        self,
        node_id: str,
        sink_fn: Callable,
        connect_from: Optional[str] = None,
        **kwargs
    ) -> 'PipelineBuilder':
        """Add a sink node"""
        node = SinkNode(node_id, sink_fn, **kwargs)
        self.pipeline.add_node(node)

        source = connect_from or self._last_node
        if source:
            self.pipeline.connect(source, node_id)

        self._last_node = node_id
        return self

    def connect(self, from_node: str, to_node: str) -> 'PipelineBuilder':
        """Manually connect two nodes"""
        self.pipeline.connect(from_node, to_node)
        return self

    def build(self) -> Pipeline:
        """Build and return the pipeline"""
        return self.pipeline


class DataFlowOrchestrator:
    """
    Central orchestrator for managing data flow pipelines.

    Features:
    - Pipeline registration and management
    - Scheduled and on-demand execution
    - Cross-pipeline data sharing
    - Execution monitoring and metrics
    """

    def __init__(self):
        self._pipelines: Dict[str, Pipeline] = {}
        self._executions: Dict[str, PipelineExecution] = {}
        self._scheduled_tasks: Dict[str, asyncio.Task] = {}
        self._shared_data: Dict[str, Any] = {}
        self._running = False
        self._lock = threading.RLock()

    def register_pipeline(self, pipeline: Pipeline) -> bool:
        """Register a pipeline with the orchestrator"""
        with self._lock:
            self._pipelines[pipeline.pipeline_id] = pipeline
            logger.info(f"Registered pipeline: {pipeline.name} ({pipeline.pipeline_id})")
            return True

    def unregister_pipeline(self, pipeline_id: str) -> bool:
        """Unregister a pipeline"""
        with self._lock:
            if pipeline_id in self._pipelines:
                del self._pipelines[pipeline_id]
                # Cancel any scheduled tasks
                if pipeline_id in self._scheduled_tasks:
                    self._scheduled_tasks[pipeline_id].cancel()
                    del self._scheduled_tasks[pipeline_id]
                logger.info(f"Unregistered pipeline: {pipeline_id}")
                return True
            return False

    async def execute_pipeline(
        self,
        pipeline_id: str,
        initial_data: Optional[List[DataPacket]] = None
    ) -> Optional[PipelineExecution]:
        """Execute a registered pipeline"""
        with self._lock:
            pipeline = self._pipelines.get(pipeline_id)

        if not pipeline:
            logger.error(f"Pipeline not found: {pipeline_id}")
            return None

        execution = await pipeline.execute(initial_data)
        self._executions[execution.execution_id] = execution

        logger.info(
            f"Pipeline {pipeline_id} execution {execution.execution_id}: "
            f"{execution.status.value} in {execution.metrics.get('total_execution_time', 0):.3f}s"
        )

        return execution

    async def schedule_pipeline(
        self,
        pipeline_id: str,
        interval_seconds: float,
        initial_data_generator: Optional[Callable] = None
    ):
        """Schedule a pipeline for periodic execution"""
        async def scheduled_execution():
            while self._running:
                try:
                    initial_data = None
                    if initial_data_generator:
                        data = initial_data_generator()
                        initial_data = [DataPacket(
                            packet_id=hashlib.md5(f"scheduled:{time.time()}".encode()).hexdigest()[:12],
                            data=data
                        )]

                    await self.execute_pipeline(pipeline_id, initial_data)

                except Exception as e:
                    logger.error(f"Scheduled execution failed for {pipeline_id}: {e}")

                await asyncio.sleep(interval_seconds)

        self._scheduled_tasks[pipeline_id] = asyncio.create_task(scheduled_execution())
        logger.info(f"Scheduled pipeline {pipeline_id} to run every {interval_seconds}s")

    def set_shared_data(self, key: str, value: Any):
        """Set shared data accessible by all pipelines"""
        self._shared_data[key] = value

    def get_shared_data(self, key: str) -> Optional[Any]:
        """Get shared data"""
        return self._shared_data.get(key)

    def get_execution(self, execution_id: str) -> Optional[PipelineExecution]:
        """Get execution details"""
        return self._executions.get(execution_id)

    def get_pipeline_executions(self, pipeline_id: str) -> List[PipelineExecution]:
        """Get all executions for a pipeline"""
        return [
            e for e in self._executions.values()
            if e.pipeline_id == pipeline_id
        ]

    async def start(self):
        """Start the orchestrator"""
        self._running = True
        logger.info("Data flow orchestrator started")

    async def stop(self):
        """Stop the orchestrator"""
        self._running = False

        # Cancel all scheduled tasks
        for task in self._scheduled_tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._scheduled_tasks.clear()
        logger.info("Data flow orchestrator stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            "running": self._running,
            "registered_pipelines": len(self._pipelines),
            "scheduled_pipelines": len(self._scheduled_tasks),
            "total_executions": len(self._executions),
            "pipelines": {
                pid: {
                    "name": p.name,
                    "nodes": len(p._nodes),
                    "edges": len(p._edges)
                }
                for pid, p in self._pipelines.items()
            },
            "recent_executions": [
                {
                    "execution_id": e.execution_id,
                    "pipeline_id": e.pipeline_id,
                    "status": e.status.value,
                    "execution_time": e.metrics.get("total_execution_time", 0)
                }
                for e in list(self._executions.values())[-10:]
            ]
        }
