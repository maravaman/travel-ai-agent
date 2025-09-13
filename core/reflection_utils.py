"""
Reflection Utilities for Dynamic Agent Management
Provides helper functions for inspecting and manipulating Python modules at runtime
"""

import inspect
import importlib
import importlib.util
import logging
from typing import Dict, Any, List, Optional, Type, Callable, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class ReflectionUtils:
    """Utility class for reflection-based operations"""
    
    @staticmethod
    def load_module_from_file(file_path: str, module_name: str = None) -> Optional[Any]:
        """
        Load Python module from file path using reflection
        
        Args:
            file_path: Path to Python file
            module_name: Optional module name (defaults to file stem)
            
        Returns:
            Loaded module or None
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return None
            
            if not module_name:
                module_name = path.stem
            
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                logger.error(f"Could not create spec for {file_path}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            logger.debug(f"Successfully loaded module {module_name} from {file_path}")
            return module
            
        except Exception as e:
            logger.error(f"Failed to load module from {file_path}: {e}")
            return None
    
    @staticmethod
    def find_classes_in_module(module: Any, base_class: Type = None) -> List[Tuple[str, Type]]:
        """
        Find all classes in module, optionally filtered by base class
        
        Args:
            module: Module to inspect
            base_class: Optional base class to filter by
            
        Returns:
            List of (class_name, class_type) tuples
        """
        classes = []
        
        try:
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Skip private classes
                if name.startswith('_'):
                    continue
                
                # Skip classes not defined in this module
                if obj.__module__ != module.__name__:
                    continue
                
                # Filter by base class if specified
                if base_class and not issubclass(obj, base_class):
                    continue
                
                classes.append((name, obj))
            
            logger.debug(f"Found {len(classes)} classes in module {module.__name__}")
            return classes
            
        except Exception as e:
            logger.error(f"Error finding classes in module: {e}")
            return []
    
    @staticmethod
    def find_functions_in_module(module: Any, pattern: str = None) -> List[Tuple[str, Callable]]:
        """
        Find all functions in module, optionally filtered by name pattern
        
        Args:
            module: Module to inspect
            pattern: Optional pattern to match function names
            
        Returns:
            List of (function_name, function) tuples
        """
        functions = []
        
        try:
            for name, obj in inspect.getmembers(module, inspect.isfunction):
                # Skip private functions
                if name.startswith('_'):
                    continue
                
                # Skip functions not defined in this module
                if obj.__module__ != module.__name__:
                    continue
                
                # Filter by pattern if specified
                if pattern and pattern not in name:
                    continue
                
                functions.append((name, obj))
            
            logger.debug(f"Found {len(functions)} functions in module {module.__name__}")
            return functions
            
        except Exception as e:
            logger.error(f"Error finding functions in module: {e}")
            return []
    
    @staticmethod
    def get_class_info(cls: Type) -> Dict[str, Any]:
        """
        Get detailed information about a class using reflection
        
        Args:
            cls: Class to inspect
            
        Returns:
            Dictionary with class information
        """
        try:
            info = {
                "name": cls.__name__,
                "module": cls.__module__,
                "file": inspect.getfile(cls),
                "doc": inspect.getdoc(cls),
                "methods": [],
                "properties": [],
                "class_variables": [],
                "inheritance": [base.__name__ for base in cls.__mro__[1:]],  # Skip self
                "is_abstract": inspect.isabstract(cls)
            }
            
            # Get methods
            for name, method in inspect.getmembers(cls, inspect.ismethod):
                if not name.startswith('_'):
                    info["methods"].append({
                        "name": name,
                        "doc": inspect.getdoc(method),
                        "signature": str(inspect.signature(method))
                    })
            
            # Get properties
            for name, prop in inspect.getmembers(cls, lambda x: isinstance(x, property)):
                info["properties"].append({
                    "name": name,
                    "doc": inspect.getdoc(prop)
                })
            
            # Get class variables
            for name, value in inspect.getmembers(cls):
                if (not name.startswith('_') and 
                    not inspect.ismethod(value) and 
                    not inspect.isfunction(value) and
                    not isinstance(value, property)):
                    info["class_variables"].append({
                        "name": name,
                        "type": type(value).__name__,
                        "value": str(value)[:100]  # Truncate long values
                    })
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting class info: {e}")
            return {"name": cls.__name__, "error": str(e)}
    
    @staticmethod
    def get_function_signature(func: Callable) -> Dict[str, Any]:
        """
        Get function signature information using reflection
        
        Args:
            func: Function to inspect
            
        Returns:
            Dictionary with function signature information
        """
        try:
            sig = inspect.signature(func)
            
            info = {
                "name": func.__name__,
                "doc": inspect.getdoc(func),
                "signature": str(sig),
                "parameters": [],
                "return_annotation": str(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else None
            }
            
            # Get parameter information
            for param_name, param in sig.parameters.items():
                param_info = {
                    "name": param_name,
                    "kind": str(param.kind),
                    "default": str(param.default) if param.default != inspect.Parameter.empty else None,
                    "annotation": str(param.annotation) if param.annotation != inspect.Parameter.empty else None
                }
                info["parameters"].append(param_info)
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting function signature: {e}")
            return {"name": func.__name__, "error": str(e)}
    
    @staticmethod
    def validate_class_inheritance(cls: Type, required_base: Type) -> bool:
        """
        Validate that class inherits from required base class
        
        Args:
            cls: Class to validate
            required_base: Required base class
            
        Returns:
            True if inheritance is valid, False otherwise
        """
        try:
            return inspect.isclass(cls) and issubclass(cls, required_base)
        except Exception as e:
            logger.error(f"Error validating inheritance: {e}")
            return False
    
    @staticmethod
    def get_module_info(module: Any) -> Dict[str, Any]:
        """
        Get comprehensive information about a module
        
        Args:
            module: Module to inspect
            
        Returns:
            Dictionary with module information
        """
        try:
            info = {
                "name": module.__name__,
                "file": getattr(module, "__file__", "Unknown"),
                "doc": inspect.getdoc(module),
                "classes": [],
                "functions": [],
                "variables": [],
                "imports": []
            }
            
            # Get all members
            for name, obj in inspect.getmembers(module):
                if name.startswith('_'):
                    continue
                
                if inspect.isclass(obj) and obj.__module__ == module.__name__:
                    info["classes"].append(name)
                elif inspect.isfunction(obj) and obj.__module__ == module.__name__:
                    info["functions"].append(name)
                elif not callable(obj) and not inspect.ismodule(obj):
                    info["variables"].append({
                        "name": name,
                        "type": type(obj).__name__,
                        "value": str(obj)[:50]  # Truncate long values
                    })
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting module info: {e}")
            return {"name": getattr(module, "__name__", "Unknown"), "error": str(e)}
    
    @staticmethod
    def execute_function_safely(func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute function safely with error handling and result capture
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Execution result dictionary
        """
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            
            return {
                "success": True,
                "result": result,
                "execution_time": (end_time - start_time).total_seconds(),
                "function_name": func.__name__,
                "timestamp": start_time.isoformat()
            }
            
        except Exception as e:
            end_time = datetime.now()
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": (end_time - start_time).total_seconds(),
                "function_name": func.__name__,
                "timestamp": start_time.isoformat()
            }
    
    @staticmethod
    def discover_agent_files(directory: str, pattern: str = "*agent*.py") -> List[str]:
        """
        Discover agent files in directory using pattern matching
        
        Args:
            directory: Directory to search
            pattern: File pattern to match
            
        Returns:
            List of discovered file paths
        """
        try:
            directory_path = Path(directory)
            if not directory_path.exists():
                logger.warning(f"Directory not found: {directory}")
                return []
            
            discovered_files = []
            for file_path in directory_path.glob(pattern):
                if file_path.is_file() and file_path.suffix == '.py':
                    discovered_files.append(str(file_path))
            
            logger.info(f"Discovered {len(discovered_files)} agent files in {directory}")
            return discovered_files
            
        except Exception as e:
            logger.error(f"Error discovering agent files: {e}")
            return []


# Global reflection utils instance
reflection_utils = ReflectionUtils()

def get_reflection_utils() -> ReflectionUtils:
    """Get global reflection utils instance"""
    return reflection_utils