#!/usr/bin/env python3
"""
Plugin Ecosystem for Hot-Pluggable Cognitive Modules

Phase 2 Implementation: Provides a flexible plugin architecture including:
- Dynamic plugin discovery and loading
- Hot-pluggable cognitive modules
- Plugin lifecycle management
- Dependency resolution between plugins
- Sandboxed execution environment
- Plugin marketplace interface
"""

import asyncio
import importlib
import importlib.util
import inspect
import json
import time
import hashlib
import logging
import os
import sys
from typing import Dict, List, Any, Optional, Callable, Type, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    """Plugin lifecycle status"""
    DISCOVERED = "discovered"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    UNLOADED = "unloaded"
    ERROR = "error"


class PluginType(Enum):
    """Types of cognitive plugins"""
    KERNEL = "kernel"               # Core cognitive kernel
    PROCESSOR = "processor"         # Data processor
    TRANSFORMER = "transformer"     # Data transformer
    ANALYZER = "analyzer"           # Analysis module
    CONNECTOR = "connector"         # External system connector
    EXTENSION = "extension"         # Feature extension
    INTEGRATION = "integration"     # Third-party integration


@dataclass
class PluginMetadata:
    """Plugin metadata and configuration"""
    plugin_id: str
    name: str
    version: str
    description: str
    plugin_type: PluginType
    author: str = ""
    license: str = ""
    homepage: str = ""
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    min_system_version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Create metadata from dictionary"""
        return cls(
            plugin_id=data.get("plugin_id", ""),
            name=data.get("name", ""),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            plugin_type=PluginType(data.get("plugin_type", "extension")),
            author=data.get("author", ""),
            license=data.get("license", ""),
            homepage=data.get("homepage", ""),
            dependencies=data.get("dependencies", []),
            capabilities=data.get("capabilities", []),
            config_schema=data.get("config_schema", {}),
            min_system_version=data.get("min_system_version", "1.0.0"),
            tags=data.get("tags", [])
        )


class CognitivePlugin(ABC):
    """
    Abstract base class for cognitive plugins.

    All plugins must inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._status = PluginStatus.DISCOVERED
        self._metrics: Dict[str, Any] = {}
        self._start_time: Optional[float] = None

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        pass

    @abstractmethod
    async def activate(self) -> bool:
        """Activate the plugin for use"""
        pass

    @abstractmethod
    async def deactivate(self) -> bool:
        """Deactivate the plugin"""
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown and cleanup the plugin"""
        pass

    @abstractmethod
    async def process(self, data: Any, **kwargs) -> Any:
        """Process data through the plugin"""
        pass

    def get_status(self) -> PluginStatus:
        """Get current plugin status"""
        return self._status

    def get_metrics(self) -> Dict[str, Any]:
        """Get plugin metrics"""
        return self._metrics

    def update_metric(self, key: str, value: Any):
        """Update a plugin metric"""
        self._metrics[key] = value

    def get_capabilities(self) -> List[str]:
        """Get plugin capabilities"""
        return self.metadata.capabilities

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration against schema"""
        # Basic validation - can be extended
        schema = self.metadata.config_schema
        for key, spec in schema.items():
            if spec.get("required", False) and key not in config:
                return False
        return True


@dataclass
class PluginInstance:
    """Container for a loaded plugin instance"""
    metadata: PluginMetadata
    instance: CognitivePlugin
    status: PluginStatus = PluginStatus.LOADED
    load_time: float = 0.0
    module_path: Optional[str] = None
    error: Optional[str] = None
    last_activity: float = 0.0


class PluginLoader:
    """Handles plugin discovery and loading"""

    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        self.plugin_dirs = plugin_dirs or []
        self._discovered_plugins: Dict[str, Path] = {}
        self._module_cache: Dict[str, Any] = {}

    def add_plugin_directory(self, path: str):
        """Add a directory to scan for plugins"""
        if path not in self.plugin_dirs:
            self.plugin_dirs.append(path)

    def discover_plugins(self) -> Dict[str, PluginMetadata]:
        """Discover plugins in configured directories"""
        discovered = {}

        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                continue

            for item in os.listdir(plugin_dir):
                plugin_path = Path(plugin_dir) / item

                # Check for plugin.json manifest
                manifest_path = plugin_path / "plugin.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path) as f:
                            manifest = json.load(f)

                        metadata = PluginMetadata.from_dict(manifest)
                        self._discovered_plugins[metadata.plugin_id] = plugin_path
                        discovered[metadata.plugin_id] = metadata

                        logger.info(f"Discovered plugin: {metadata.name} v{metadata.version}")

                    except Exception as e:
                        logger.error(f"Error loading manifest from {manifest_path}: {e}")

                # Check for single-file plugins
                elif item.endswith("_plugin.py"):
                    try:
                        plugin_id = item.replace("_plugin.py", "")
                        self._discovered_plugins[plugin_id] = plugin_path

                        # Load module to get metadata
                        spec = importlib.util.spec_from_file_location(plugin_id, plugin_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)

                            if hasattr(module, "PLUGIN_METADATA"):
                                metadata = PluginMetadata.from_dict(module.PLUGIN_METADATA)
                                discovered[metadata.plugin_id] = metadata

                    except Exception as e:
                        logger.error(f"Error loading plugin from {plugin_path}: {e}")

        return discovered

    def load_plugin(
        self,
        plugin_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[PluginInstance]:
        """Load a discovered plugin"""
        if plugin_id not in self._discovered_plugins:
            logger.error(f"Plugin not discovered: {plugin_id}")
            return None

        plugin_path = self._discovered_plugins[plugin_id]
        load_start = time.time()

        try:
            # Load plugin module
            if plugin_path.is_dir():
                # Package-style plugin
                init_path = plugin_path / "__init__.py"
                spec = importlib.util.spec_from_file_location(
                    plugin_id,
                    init_path,
                    submodule_search_locations=[str(plugin_path)]
                )
            else:
                # Single-file plugin
                spec = importlib.util.spec_from_file_location(plugin_id, plugin_path)

            if not spec or not spec.loader:
                raise ImportError(f"Cannot create module spec for {plugin_id}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_id] = module
            spec.loader.exec_module(module)
            self._module_cache[plugin_id] = module

            # Find plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, CognitivePlugin) and
                    obj is not CognitivePlugin):
                    plugin_class = obj
                    break

            if not plugin_class:
                raise ImportError(f"No CognitivePlugin subclass found in {plugin_id}")

            # Create instance
            instance = plugin_class(config)
            load_time = time.time() - load_start

            plugin_instance = PluginInstance(
                metadata=instance.metadata,
                instance=instance,
                status=PluginStatus.LOADED,
                load_time=load_time,
                module_path=str(plugin_path),
                last_activity=time.time()
            )

            logger.info(f"Loaded plugin: {plugin_id} in {load_time:.3f}s")
            return plugin_instance

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_id}: {e}")
            return PluginInstance(
                metadata=PluginMetadata(
                    plugin_id=plugin_id,
                    name=plugin_id,
                    version="unknown",
                    description="",
                    plugin_type=PluginType.EXTENSION
                ),
                instance=None,  # type: ignore
                status=PluginStatus.ERROR,
                error=str(e)
            )

    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin module"""
        if plugin_id in sys.modules:
            del sys.modules[plugin_id]

        if plugin_id in self._module_cache:
            del self._module_cache[plugin_id]

        return True


class DependencyResolver:
    """Resolves plugin dependencies"""

    def __init__(self):
        self._dependency_graph: Dict[str, Set[str]] = {}

    def add_plugin(self, plugin_id: str, dependencies: List[str]):
        """Add a plugin with its dependencies"""
        self._dependency_graph[plugin_id] = set(dependencies)

    def resolve_order(self, plugins: List[str]) -> List[str]:
        """Resolve loading order based on dependencies"""
        resolved = []
        unresolved = set(plugins)

        while unresolved:
            # Find plugins with all dependencies satisfied
            ready = []
            for plugin_id in unresolved:
                deps = self._dependency_graph.get(plugin_id, set())
                if deps.issubset(set(resolved)):
                    ready.append(plugin_id)

            if not ready:
                # Circular dependency detected
                raise ValueError(f"Circular dependency detected: {unresolved}")

            resolved.extend(sorted(ready))
            unresolved -= set(ready)

        return resolved

    def check_missing_dependencies(self, plugins: Set[str]) -> Dict[str, List[str]]:
        """Check for missing dependencies"""
        missing = {}
        for plugin_id in plugins:
            deps = self._dependency_graph.get(plugin_id, set())
            missing_deps = deps - plugins
            if missing_deps:
                missing[plugin_id] = list(missing_deps)
        return missing


class PluginSandbox:
    """Sandboxed execution environment for plugins"""

    def __init__(self, timeout: float = 30.0, memory_limit: int = 256 * 1024 * 1024):
        self.timeout = timeout
        self.memory_limit = memory_limit
        self._executor = ThreadPoolExecutor(max_workers=4)

    async def execute(
        self,
        plugin: CognitivePlugin,
        method: str,
        *args,
        **kwargs
    ) -> Any:
        """Execute a plugin method in sandbox"""
        loop = asyncio.get_event_loop()

        async def _execute():
            method_fn = getattr(plugin, method, None)
            if not method_fn:
                raise AttributeError(f"Plugin has no method: {method}")

            if asyncio.iscoroutinefunction(method_fn):
                return await method_fn(*args, **kwargs)
            else:
                return await loop.run_in_executor(
                    self._executor,
                    lambda: method_fn(*args, **kwargs)
                )

        try:
            result = await asyncio.wait_for(_execute(), timeout=self.timeout)
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Plugin execution timed out after {self.timeout}s")

    def shutdown(self):
        """Shutdown the sandbox executor"""
        self._executor.shutdown(wait=False)


class PluginRegistry:
    """Central registry for managing plugins"""

    def __init__(self):
        self._plugins: Dict[str, PluginInstance] = {}
        self._capabilities: Dict[str, List[str]] = {}  # capability -> [plugin_ids]
        self._lock = threading.RLock()

    def register(self, plugin_instance: PluginInstance) -> bool:
        """Register a plugin instance"""
        with self._lock:
            plugin_id = plugin_instance.metadata.plugin_id
            self._plugins[plugin_id] = plugin_instance

            # Index by capabilities
            for cap in plugin_instance.metadata.capabilities:
                if cap not in self._capabilities:
                    self._capabilities[cap] = []
                if plugin_id not in self._capabilities[cap]:
                    self._capabilities[cap].append(plugin_id)

            return True

    def unregister(self, plugin_id: str) -> bool:
        """Unregister a plugin"""
        with self._lock:
            if plugin_id not in self._plugins:
                return False

            plugin = self._plugins.pop(plugin_id)

            # Remove from capability index
            for cap in plugin.metadata.capabilities:
                if cap in self._capabilities:
                    self._capabilities[cap] = [
                        pid for pid in self._capabilities[cap] if pid != plugin_id
                    ]

            return True

    def get_plugin(self, plugin_id: str) -> Optional[PluginInstance]:
        """Get a plugin by ID"""
        return self._plugins.get(plugin_id)

    def get_plugins_by_capability(self, capability: str) -> List[PluginInstance]:
        """Get plugins that provide a capability"""
        plugin_ids = self._capabilities.get(capability, [])
        return [self._plugins[pid] for pid in plugin_ids if pid in self._plugins]

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInstance]:
        """Get plugins by type"""
        return [
            p for p in self._plugins.values()
            if p.metadata.plugin_type == plugin_type
        ]

    def list_plugins(self) -> Dict[str, PluginStatus]:
        """List all registered plugins and their status"""
        return {pid: p.status for pid, p in self._plugins.items()}

    def get_all_capabilities(self) -> Dict[str, int]:
        """Get all capabilities and plugin count"""
        return {cap: len(pids) for cap, pids in self._capabilities.items()}


class PluginManager:
    """
    Central manager for the plugin ecosystem.

    Features:
    - Plugin discovery and loading
    - Lifecycle management
    - Hot-plugging support
    - Dependency resolution
    - Sandboxed execution
    """

    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        self.loader = PluginLoader(plugin_dirs)
        self.registry = PluginRegistry()
        self.resolver = DependencyResolver()
        self.sandbox = PluginSandbox()

        self._running = False
        self._lock = threading.RLock()

    async def start(self):
        """Start the plugin manager"""
        self._running = True
        logger.info("Plugin manager started")

    async def stop(self):
        """Stop the plugin manager and unload all plugins"""
        self._running = False

        # Deactivate and unload all plugins
        for plugin_id in list(self.registry._plugins.keys()):
            await self.unload_plugin(plugin_id)

        self.sandbox.shutdown()
        logger.info("Plugin manager stopped")

    def discover_plugins(self) -> Dict[str, PluginMetadata]:
        """Discover available plugins"""
        return self.loader.discover_plugins()

    async def load_plugin(
        self,
        plugin_id: str,
        config: Optional[Dict[str, Any]] = None,
        auto_activate: bool = True
    ) -> Optional[PluginInstance]:
        """Load a plugin"""
        with self._lock:
            # Check if already loaded
            existing = self.registry.get_plugin(plugin_id)
            if existing and existing.status != PluginStatus.ERROR:
                logger.warning(f"Plugin {plugin_id} already loaded")
                return existing

            # Load plugin
            plugin_instance = self.loader.load_plugin(plugin_id, config)
            if not plugin_instance or plugin_instance.status == PluginStatus.ERROR:
                return plugin_instance

            # Register dependencies
            self.resolver.add_plugin(
                plugin_id,
                plugin_instance.metadata.dependencies
            )

            # Initialize plugin
            try:
                success = await self.sandbox.execute(
                    plugin_instance.instance,
                    "initialize"
                )
                if success:
                    plugin_instance.status = PluginStatus.INITIALIZED
                    plugin_instance.instance._status = PluginStatus.INITIALIZED
                else:
                    plugin_instance.status = PluginStatus.ERROR
                    plugin_instance.error = "Initialization failed"
            except Exception as e:
                plugin_instance.status = PluginStatus.ERROR
                plugin_instance.error = str(e)
                logger.error(f"Failed to initialize plugin {plugin_id}: {e}")

            # Register with registry
            self.registry.register(plugin_instance)

            # Auto-activate if requested
            if auto_activate and plugin_instance.status == PluginStatus.INITIALIZED:
                await self.activate_plugin(plugin_id)

            return plugin_instance

    async def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin"""
        with self._lock:
            plugin = self.registry.get_plugin(plugin_id)
            if not plugin:
                return False

            # Deactivate first
            if plugin.status == PluginStatus.ACTIVE:
                await self.deactivate_plugin(plugin_id)

            # Shutdown plugin
            try:
                await self.sandbox.execute(plugin.instance, "shutdown")
            except Exception as e:
                logger.error(f"Error shutting down plugin {plugin_id}: {e}")

            # Unregister and unload
            self.registry.unregister(plugin_id)
            self.loader.unload_plugin(plugin_id)

            logger.info(f"Unloaded plugin: {plugin_id}")
            return True

    async def activate_plugin(self, plugin_id: str) -> bool:
        """Activate a plugin"""
        plugin = self.registry.get_plugin(plugin_id)
        if not plugin or plugin.status != PluginStatus.INITIALIZED:
            return False

        try:
            success = await self.sandbox.execute(plugin.instance, "activate")
            if success:
                plugin.status = PluginStatus.ACTIVE
                plugin.instance._status = PluginStatus.ACTIVE
                plugin.instance._start_time = time.time()
                logger.info(f"Activated plugin: {plugin_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to activate plugin {plugin_id}: {e}")

        return False

    async def deactivate_plugin(self, plugin_id: str) -> bool:
        """Deactivate a plugin"""
        plugin = self.registry.get_plugin(plugin_id)
        if not plugin or plugin.status != PluginStatus.ACTIVE:
            return False

        try:
            success = await self.sandbox.execute(plugin.instance, "deactivate")
            if success:
                plugin.status = PluginStatus.SUSPENDED
                plugin.instance._status = PluginStatus.SUSPENDED
                logger.info(f"Deactivated plugin: {plugin_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to deactivate plugin {plugin_id}: {e}")

        return False

    async def reload_plugin(
        self,
        plugin_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[PluginInstance]:
        """Hot-reload a plugin"""
        logger.info(f"Hot-reloading plugin: {plugin_id}")

        # Get current config if not provided
        current = self.registry.get_plugin(plugin_id)
        if current and not config:
            config = current.instance.config

        # Unload and reload
        await self.unload_plugin(plugin_id)
        return await self.load_plugin(plugin_id, config)

    async def execute_plugin(
        self,
        plugin_id: str,
        data: Any,
        **kwargs
    ) -> Any:
        """Execute a plugin's process method"""
        plugin = self.registry.get_plugin(plugin_id)
        if not plugin or plugin.status != PluginStatus.ACTIVE:
            raise RuntimeError(f"Plugin {plugin_id} not active")

        start_time = time.time()
        try:
            result = await self.sandbox.execute(
                plugin.instance,
                "process",
                data,
                **kwargs
            )
            plugin.last_activity = time.time()
            plugin.instance.update_metric(
                "last_execution_time",
                time.time() - start_time
            )
            return result

        except Exception as e:
            plugin.instance.update_metric("last_error", str(e))
            raise

    async def execute_capability(
        self,
        capability: str,
        data: Any,
        **kwargs
    ) -> List[Any]:
        """Execute all plugins that provide a capability"""
        plugins = self.registry.get_plugins_by_capability(capability)
        results = []

        for plugin in plugins:
            if plugin.status == PluginStatus.ACTIVE:
                try:
                    result = await self.execute_plugin(
                        plugin.metadata.plugin_id,
                        data,
                        **kwargs
                    )
                    results.append({
                        "plugin_id": plugin.metadata.plugin_id,
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "plugin_id": plugin.metadata.plugin_id,
                        "error": str(e)
                    })

        return results

    def get_status(self) -> Dict[str, Any]:
        """Get plugin manager status"""
        plugins = self.registry.list_plugins()

        return {
            "running": self._running,
            "total_plugins": len(plugins),
            "active_plugins": sum(1 for s in plugins.values() if s == PluginStatus.ACTIVE),
            "plugins": {
                pid: {
                    "status": status.value,
                    "metadata": self.registry.get_plugin(pid).metadata.__dict__
                    if self.registry.get_plugin(pid) else None
                }
                for pid, status in plugins.items()
            },
            "capabilities": self.registry.get_all_capabilities(),
            "plugin_dirs": self.loader.plugin_dirs
        }


# Example plugin implementations
class ExampleCognitivePlugin(CognitivePlugin):
    """Example cognitive plugin implementation"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id="example_cognitive_plugin",
            name="Example Cognitive Plugin",
            version="1.0.0",
            description="An example cognitive plugin demonstrating the plugin architecture",
            plugin_type=PluginType.PROCESSOR,
            author="OpenCog Central",
            capabilities=["text_processing", "pattern_detection"],
            config_schema={
                "threshold": {"type": "float", "default": 0.5},
                "max_tokens": {"type": "int", "default": 1000}
            }
        )

    async def initialize(self) -> bool:
        self._status = PluginStatus.INITIALIZED
        return True

    async def activate(self) -> bool:
        self._status = PluginStatus.ACTIVE
        return True

    async def deactivate(self) -> bool:
        self._status = PluginStatus.SUSPENDED
        return True

    async def shutdown(self) -> bool:
        self._status = PluginStatus.UNLOADED
        return True

    async def process(self, data: Any, **kwargs) -> Any:
        threshold = self.config.get("threshold", 0.5)
        return {
            "processed": True,
            "input_data": data,
            "threshold": threshold,
            "plugin": self.metadata.name
        }


class AttentionKernelPlugin(CognitivePlugin):
    """Attention kernel plugin for ECAN-style attention allocation"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id="attention_kernel",
            name="Attention Kernel",
            version="1.0.0",
            description="ECAN-style attention allocation kernel",
            plugin_type=PluginType.KERNEL,
            capabilities=[
                "attention_allocation",
                "salience_computation",
                "focus_management"
            ]
        )

    async def initialize(self) -> bool:
        self._attention_values: Dict[str, float] = {}
        return True

    async def activate(self) -> bool:
        return True

    async def deactivate(self) -> bool:
        return True

    async def shutdown(self) -> bool:
        self._attention_values.clear()
        return True

    async def process(self, data: Any, **kwargs) -> Any:
        operation = kwargs.get("operation", "allocate")

        if operation == "allocate":
            atom_id = data.get("atom_id")
            sti = data.get("sti", 0.5)
            self._attention_values[atom_id] = sti
            return {"allocated": True, "atom_id": atom_id, "sti": sti}

        elif operation == "get_focus":
            # Return top atoms by attention
            sorted_atoms = sorted(
                self._attention_values.items(),
                key=lambda x: x[1],
                reverse=True
            )
            return sorted_atoms[:10]

        return {"error": f"Unknown operation: {operation}"}
