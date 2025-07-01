import os
import subprocess
import time
import json
import threading
from dotenv import load_dotenv
from queue import Queue, Empty

class MCPClient:
    def __init__(self):
        self.process = None
        self.response_queue = Queue()
        self.request_id = 0
        self.running = False
        self.stderr_lines = []
        self.debug = True
        self.initialized = False

    def start_server(self):
        """Start the MCP server process with proper environment setup"""
        load_dotenv()
        token = os.getenv("SLACK_BOT_TOKEN")
        team_id = os.getenv("SLACK_TEAM_ID")
        # print("7"*86)
        # print(os.getenv("SLACK_CHANNEL_IDS", ""))
        
        if not token or not team_id:
            print("❌ Missing Slack credentials in .env file")
            print("   Required: SLACK_BOT_TOKEN and SLACK_TEAM_ID")
            return False
            
        env = os.environ.copy()
        env.update({
            "SLACK_BOT_TOKEN": token,
            "SLACK_TEAM_ID": team_id,
            "SLACK_CHANNEL_IDS": os.getenv("SLACK_CHANNEL_IDS", "")
        })
        
        

        try:
            self.process = subprocess.Popen(
                ["npx", "-y", "@modelcontextprotocol/server-slack", "--transport", "stdio"],
                env=env, 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, 
                text=True, 
                bufsize=1
            )
            
            self.running = True
            threading.Thread(target=self._read_stdout, daemon=True).start()
            threading.Thread(target=self._read_stderr, daemon=True).start()
            
            print("⏳ Waiting for MCP server to start...")
            
            # Wait for server startup confirmation
            for i in range(40):
                if any("Slack MCP Server running on stdio" in line for line in self.stderr_lines):
                    print("✅ MCP Server started successfully")
                    return True
                time.sleep(0.5)
                
            print("❌ MCP server failed to start - timeout")
            self._print_stderr_debug()
            return False
            
        except Exception as e:
            print(f"❌ Failed to start MCP server: {e}")
            return False

    def _print_stderr_debug(self):
        """Print recent stderr for debugging"""
        if self.stderr_lines:
            print("\n🔍 Recent server logs:")
            for line in self.stderr_lines[-10:]:  # Last 10 lines
                print(f"   {line}")

    def _read_stdout(self):
        """Read and process stdout from MCP server"""
        while self.running and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if not line:
                    continue
                    
                line = line.strip()
                if self.debug:
                    print(f"[MCP STDOUT] {line}")
                    
                if line:  # Only process non-empty lines
                    try:
                        msg = json.loads(line)
                        self.response_queue.put(msg)
                    except json.JSONDecodeError as e:
                        if self.debug:
                            print(f"[JSON ERROR] Failed to parse: {line} - {e}")
                            
            except Exception as e:
                if self.debug:
                    print(f"[STDOUT ERROR] {e}")
                break

    def _read_stderr(self):
        """Read and process stderr from MCP server"""
        while self.running and self.process.poll() is None:
            try:
                line = self.process.stderr.readline()
                if not line:
                    continue
                    
                line = line.strip()
                if line:  # Only store non-empty lines
                    self.stderr_lines.append(line)
                    if self.debug:
                        print(f"[MCP STDERR] {line}")
                        
            except Exception as e:
                if self.debug:
                    print(f"[STDERR ERROR] {e}")
                break

    def send_request(self, method, params=None, timeout=10):
        """Send a JSON-RPC request to the MCP server"""
        if not self.running or self.process.poll() is not None:
            return {"error": "Server not running"}
            
        self.request_id += 1
        req = {
            "jsonrpc": "2.0", 
            "method": method, 
            "params": params or {}, 
            "id": self.request_id
        }
        
        if self.debug:
            print(f"[MCP REQUEST] {json.dumps(req, indent=2)}")
            
        try:
            self.process.stdin.write(json.dumps(req) + "\n")
            self.process.stdin.flush()
            return self._get_response(self.request_id, timeout)
        except Exception as e:
            return {"error": f"Failed to send request: {e}"}

    def send_notification(self, method, params=None):
        """Send a JSON-RPC notification (no response expected)"""
        if not self.running or self.process.poll() is not None:
            return False
            
        notification = {
            "jsonrpc": "2.0", 
            "method": method
        }
        
        if params:
            notification["params"] = params
            
        if self.debug:
            print(f"[MCP NOTIFICATION] {json.dumps(notification, indent=2)}")
            
        try:
            self.process.stdin.write(json.dumps(notification) + "\n")
            self.process.stdin.flush()
            return True
        except Exception as e:
            if self.debug:
                print(f"[NOTIFICATION ERROR] {e}")
            return False

    def _get_response(self, request_id, timeout):
        """Wait for and return the response to a specific request"""
        start = time.time()
        responses_seen = []
        
        while time.time() - start < timeout:
            try:
                resp = self.response_queue.get(timeout=0.1)
                responses_seen.append(resp.get("id", "no-id"))
                
                if resp.get("id") == request_id:
                    if self.debug:
                        print(f"[MCP RESPONSE] {json.dumps(resp, indent=2)}")
                    return resp
                    
            except Empty:
                continue
                
        if self.debug:
            print(f"[TIMEOUT] Request {request_id} timed out. Seen responses for: {responses_seen}")
        return {"error": "Response timeout", "request_id": request_id}

    def initialize(self):
        """Perform the MCP initialization handshake"""
        init_params = {
            "protocolVersion": "2024-11-05", 
            "capabilities": {}, 
            "clientInfo": {
                "name": "mcp-python-client", 
                "version": "1.0"
            }
        }
        
        print("\n🤝 Sending initialize...")
        init_resp = self.send_request("initialize", init_params, timeout=15)
        
        if "error" in init_resp:
            print(f"❌ Initialize failed: {init_resp['error']}")
            return False
            
        if "result" not in init_resp:
            print(f"❌ Invalid initialize response: {init_resp}")
            return False
            
        print("✅ Initialize successful")
        
        # Send initialized notification
        print("📤 Sending initialized notification...")
        if not self.send_notification("notifications/initialized"):
            print("⚠️  Failed to send initialized notification")
            return False
            
        self.initialized = True
        time.sleep(1)  # Give server time to process
        return True

    def list_tools(self):
        """List available tools using correct MCP method name"""
        if not self.initialized:
            return {"error": "Client not initialized"}
        return self.send_request("tools/list", {}, timeout=15)

    def call_tool(self, tool_name, arguments=None):
        """Call a tool using correct MCP method name"""
        if not self.initialized:
            return {"error": "Client not initialized"}
        return self.send_request("tools/call", {
            "name": tool_name, 
            "arguments": arguments or {}
        }, timeout=30)

    def get_server_info(self):
        """Get server information if available"""
        # This might not be available in all MCP servers
        return self.send_request("server/info", {}, timeout=10)

    def stop(self):
        """Stop the MCP server and cleanup"""
        print("\n🛑 Shutting down MCP client...")
        self.running = False
        
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
                print("✅ Server terminated gracefully")
            except subprocess.TimeoutExpired:
                print("⏰ Server didn't stop gracefully, forcing kill...")
                self.process.kill()
                self.process.wait()
                print("✅ Server killed")

def main():
    """Main function to demonstrate MCP client usage"""
    import sys
    
    client = MCPClient()
    
    try:
        # 1. Start the server
        if not client.start_server():
            print("❌ Failed to start server")
            sys.exit(1)

        # 2. Initialize the connection
        if not client.initialize():
            print("❌ Failed to initialize connection")
            sys.exit(1)

        # 3. Discover available tools
        print("\n🔍 Fetching available tools...")
        tools_resp = client.list_tools()
        
        if "error" in tools_resp:
            print(f"❌ Error fetching tools: {tools_resp['error']}")
        elif "result" in tools_resp and "tools" in tools_resp["result"]:
            tools = tools_resp["result"]["tools"]
            print(f"\n📋 Found {len(tools)} available tools:")
            
            for i, tool in enumerate(tools, 1):
                print(f"{i}. {tool['name']}")
                print(f"   Description: {tool.get('description', 'No description')}")
                if 'inputSchema' in tool:
                    print(f"   Input schema: {tool['inputSchema'].get('type', 'unknown')}")
                print()
            
            # 4. Test first tool if available
            if tools:
                first_tool = tools[0]
                print(f"🧪 Testing tool: {first_tool['name']}")
                
                # Try with empty arguments first
                test_result = client.call_tool(first_tool['name'], {})
                print(f"Result: {json.dumps(test_result, indent=2)}")
                
        else:
            print("❌ No tools found or unexpected response format")
            print(f"Response: {tools_resp}")

        # 5. Keep running until interrupted
        print("\n👀 Monitoring server (Ctrl+C to exit)...")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Received interrupt signal")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        client.stop()
        print("🏁 Client stopped")

if __name__ == "__main__":
    main()