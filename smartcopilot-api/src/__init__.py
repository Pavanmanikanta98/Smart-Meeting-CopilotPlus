

'''
# MCP Integration via Singleton Manager
import time
import json
import threading
from queue import Queue, Empty
from mcpserver import start_mcp_server, send_mcp_request

class MCPManager:
    """Singleton MCP Manager for notebook integration"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.server_process = None
            self.initialized = False
            self.response_queue = Queue()
            self.request_id = 0
            self.debug = True
            self._initialized = True
    
    def start_server(self):
        """Start MCP server as a subprocess"""
        if self.server_process and self.server_process.poll() is None:
            print("✅ MCP server already running")
            return True
        
        print("🚀 Starting MCP server...")
        self.server_process = start_mcp_server()
        
        if self.server_process is None:
            print("❌ Failed to start MCP server")
            return False
        
        # Wait a moment for server to initialize
        time.sleep(2)
        
        if self.is_server_running():
            print("✅ MCP server started successfully")
            # Perform initialization handshake
            return self._initialize_connection()
        else:
            print("❌ MCP server failed to start")
            return False
    
    def _initialize_connection(self):
        """Perform MCP initialization handshake"""
        if self.initialized:
            return True
        
        print("🤝 Initializing MCP connection...")
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "notebook-mcp-client",
                    "version": "1.0"
                }
            },
            "id": self._get_request_id()
        }
        
        init_response = self._send_request(init_request)
        
        if "error" in init_response:
            print(f"❌ Initialize failed: {init_response['error']}")
            return False
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        self._send_notification(initialized_notification)
        self.initialized = True
        print("✅ MCP connection initialized")
        return True
    
    def is_server_running(self):
        """Check if MCP server is running"""
        return self.server_process and self.server_process.poll() is None
    
    def _get_request_id(self):
        """Get next request ID"""
        self.request_id += 1
        return self.request_id
    
    def _send_request(self, request):
        """Send request and wait for response"""
        if not self.is_server_running():
            return {"error": "MCP server not running"}
        
        if self.debug:
            print(f"[MCP REQUEST] {json.dumps(request, indent=2)}")
        
        try:
            response = send_mcp_request(self.server_process, request)
            
            if self.debug:
                print(f"[MCP RESPONSE] {json.dumps(response, indent=2)}")
            
            return response
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def _send_notification(self, notification):
        """Send notification (no response expected)"""
        if not self.is_server_running():
            return False
        
        if self.debug:
            print(f"[MCP NOTIFICATION] {json.dumps(notification, indent=2)}")
        
        try:
            # For notifications, we don't expect a response
            self.server_process.stdin.write(json.dumps(notification) + "\n")
            self.server_process.stdin.flush()
            return True
        except Exception as e:
            if self.debug:
                print(f"[NOTIFICATION ERROR] {e}")
            return False
    
    def list_tools(self):
        """List available MCP tools"""
        if not self.initialized:
            if not self.start_server():
                return {"error": "Failed to initialize MCP server"}
        
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",  # Correct MCP method name
            "params": {},
            "id": self._get_request_id()
        }
        
        return self._send_request(request)
    
    def mcp_request(self, tool_name: str, args: dict = None) -> dict:
        """Make request to MCP server via stdio"""
        if not self.initialized:
            if not self.start_server():
                return {"error": "Failed to initialize MCP server"}
        
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",  # Correct MCP method name
            "params": {
                "name": tool_name,
                "arguments": args or {}
            },
            "id": self._get_request_id()
        }
        
        return self._send_request(request)
    
    def call_tool(self, tool_name: str, arguments: dict = None) -> dict:
        """Alias for mcp_request for consistency"""
        return self.mcp_request(tool_name, arguments)
    
    def get_server_status(self):
        """Get comprehensive server status"""
        status = {
            "running": self.is_server_running(),
            "initialized": self.initialized,
            "process_id": self.server_process.pid if self.server_process else None
        }
        
        if status["running"] and status["initialized"]:
            # Try to get tools to verify connectivity
            tools_response = self.list_tools()
            if "result" in tools_response:
                status["tools_count"] = len(tools_response["result"].get("tools", []))
                status["status"] = "healthy"
            else:
                status["status"] = "connection_issues"
                status["error"] = tools_response.get("error", "Unknown error")
        elif status["running"]:
            status["status"] = "not_initialized"
        else:
            status["status"] = "not_running"
        
        return status
    
    def restart_server(self):
        """Restart the MCP server"""
        print("🔄 Restarting MCP server...")
        self.stop_server()
        time.sleep(1)
        return self.start_server()
    
    def stop_server(self):
        """Stop the MCP server"""
        if self.server_process and self.server_process.poll() is None:
            print("🛑 Stopping MCP server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
                print("✅ MCP server stopped")
            except:
                self.server_process.kill()
                print("⚡ MCP server force killed")
        
        self.server_process = None
        self.initialized = False
    
    def test_connection(self):
        """Test MCP connection with basic tool listing"""
        print("🧪 Testing MCP connection...")
        
        status = self.get_server_status()
        print(f"Server Status: {status}")
        
        if status["status"] == "healthy":
            tools_response = self.list_tools()
            if "result" in tools_response:
                tools = tools_response["result"].get("tools", [])
                print(f"✅ Connection successful! Found {len(tools)} tools:")
                for tool in tools[:3]:  # Show first 3 tools
                    print(f"  - {tool['name']}: {tool.get('description', 'No description')}")
                if len(tools) > 3:
                    print(f"  ... and {len(tools) - 3} more tools")
                return True
            else:
                print(f"❌ Failed to list tools: {tools_response}")
                return False
        else:
            print(f"❌ Server not healthy: {status['status']}")
            return False

# Initialize MCP manager (singleton)
print("🔧 Initializing MCP Manager...")
mcp_manager = MCPManager()

# Auto-start server
if mcp_manager.start_server():
    print("🎉 MCP Manager ready for use!")
    
    # Quick connection test
    mcp_manager.test_connection()
else:
    print("⚠️  MCP Manager initialized but server failed to start")
    print("   Use mcp_manager.start_server() to retry")

print("\n📋 Available methods:")
print("  - mcp_manager.list_tools()")
print("  - mcp_manager.call_tool(tool_name, arguments)")
print("  - mcp_manager.get_server_status()")
print("  - mcp_manager.test_connection()")
print("  - mcp_manager.restart_server()")
print("  - mcp_manager.stop_server()")
'''