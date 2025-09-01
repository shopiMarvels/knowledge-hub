"""
MCP File Tool

This module implements file operations as an MCP (Model Context Protocol) tool.
It provides file reading, writing, and manipulation capabilities for AI agents.
"""

import asyncio
import logging
import os
import pathlib
from typing import Dict, List, Optional, Union, Any
import aiofiles
import json

logger = logging.getLogger(__name__)

class FileTool:
    """
    MCP File Tool for file operations
    
    This tool provides file system operations that can be used by AI agents
    through the Model Context Protocol interface.
    """
    
    def __init__(self, base_path: str = "/app/data"):
        """
        Initialize the File Tool
        
        Args:
            base_path: Base directory for file operations (security constraint)
        """
        self.base_path = pathlib.Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileTool initialized with base path: {self.base_path}")
    
    def _validate_path(self, file_path: str) -> pathlib.Path:
        """
        Validate and resolve file path within base directory
        
        Args:
            file_path: Relative file path
            
        Returns:
            Resolved absolute path
            
        Raises:
            ValueError: If path is outside base directory
        """
        try:
            # Convert to Path object and resolve
            path = pathlib.Path(file_path)
            if path.is_absolute():
                raise ValueError("Absolute paths are not allowed")
            
            # Resolve within base path
            full_path = (self.base_path / path).resolve()
            
            # Ensure path is within base directory
            if not str(full_path).startswith(str(self.base_path.resolve())):
                raise ValueError("Path outside base directory not allowed")
                
            return full_path
            
        except Exception as e:
            raise ValueError(f"Invalid file path: {e}")
    
    async def read_file(self, file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Read file contents
        
        Args:
            file_path: Relative path to file
            encoding: File encoding (default: utf-8)
            
        Returns:
            Dict containing file contents and metadata
        """
        try:
            validated_path = self._validate_path(file_path)
            
            if not validated_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "content": None
                }
            
            async with aiofiles.open(validated_path, 'r', encoding=encoding) as file:
                content = await file.read()
            
            # Get file stats
            stat = validated_path.stat()
            
            return {
                "success": True,
                "content": content,
                "metadata": {
                    "path": file_path,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "encoding": encoding
                }
            }
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    async def write_file(self, file_path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Write content to file
        
        Args:
            file_path: Relative path to file
            content: Content to write
            encoding: File encoding (default: utf-8)
            
        Returns:
            Dict containing operation result
        """
        try:
            validated_path = self._validate_path(file_path)
            
            # Create parent directories if they don't exist
            validated_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(validated_path, 'w', encoding=encoding) as file:
                await file.write(content)
            
            # Get file stats after writing
            stat = validated_path.stat()
            
            return {
                "success": True,
                "message": f"File written successfully: {file_path}",
                "metadata": {
                    "path": file_path,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "encoding": encoding
                }
            }
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_files(self, directory_path: str = "") -> Dict[str, Any]:
        """
        List files in directory
        
        Args:
            directory_path: Relative directory path (empty for base directory)
            
        Returns:
            Dict containing file list and metadata
        """
        try:
            if directory_path:
                validated_path = self._validate_path(directory_path)
            else:
                validated_path = self.base_path
            
            if not validated_path.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {directory_path}",
                    "files": []
                }
            
            if not validated_path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {directory_path}",
                    "files": []
                }
            
            files = []
            for item in validated_path.iterdir():
                relative_path = item.relative_to(self.base_path)
                stat = item.stat()
                
                files.append({
                    "name": item.name,
                    "path": str(relative_path),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else None,
                    "modified": stat.st_mtime
                })
            
            return {
                "success": True,
                "files": sorted(files, key=lambda x: (x["type"], x["name"])),
                "directory": directory_path or "."
            }
            
        except Exception as e:
            logger.error(f"Error listing directory {directory_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "files": []
            }
    
    async def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete file
        
        Args:
            file_path: Relative path to file
            
        Returns:
            Dict containing operation result
        """
        try:
            validated_path = self._validate_path(file_path)
            
            if not validated_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            if validated_path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is a directory, not a file: {file_path}"
                }
            
            validated_path.unlink()
            
            return {
                "success": True,
                "message": f"File deleted successfully: {file_path}"
            }
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """
        Get MCP tool schema for this tool
        
        Returns:
            MCP tool schema dictionary
        """
        return {
            "name": "file_tool",
            "description": "File operations tool for reading, writing, and managing files",
            "methods": {
                "read_file": {
                    "description": "Read file contents",
                    "parameters": {
                        "file_path": {"type": "string", "description": "Relative path to file"},
                        "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"}
                    }
                },
                "write_file": {
                    "description": "Write content to file",
                    "parameters": {
                        "file_path": {"type": "string", "description": "Relative path to file"},
                        "content": {"type": "string", "description": "Content to write"},
                        "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"}
                    }
                },
                "list_files": {
                    "description": "List files in directory",
                    "parameters": {
                        "directory_path": {"type": "string", "description": "Relative directory path", "default": ""}
                    }
                },
                "delete_file": {
                    "description": "Delete file",
                    "parameters": {
                        "file_path": {"type": "string", "description": "Relative path to file"}
                    }
                }
            }
        }

# Example usage and testing
async def test_file_tool():
    """Test function for the File Tool (for development)"""
    tool = FileTool()
    
    # Test write
    result = await tool.write_file("test.txt", "Hello, World!")
    print("Write result:", result)
    
    # Test read
    result = await tool.read_file("test.txt")
    print("Read result:", result)
    
    # Test list
    result = await tool.list_files()
    print("List result:", result)
    
    # Test delete
    result = await tool.delete_file("test.txt")
    print("Delete result:", result)

if __name__ == "__main__":
    # Run tests if file is executed directly
    asyncio.run(test_file_tool())
