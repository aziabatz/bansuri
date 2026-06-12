from datetime import datetime
import json
import threading
import os
import base64
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

try:
    import psutil
except ImportError:
    psutil = None


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class DashboardHandler(BaseHTTPRequestHandler):
    def check_auth(self):
        """Verifies Basic Auth credentials"""
        if not self.server.username or not self.server.password:
            return True

        auth_header = self.headers.get("Authorization")
        if not auth_header:
            self.send_auth_request()
            return False

        try:
            method, encoded = auth_header.split()
            if method.lower() != "basic":
                raise ValueError
            decoded = base64.b64decode(encoded).decode("utf-8")
            user, pwd = decoded.split(":", 1)

            if user == self.server.username and pwd == self.server.password:
                return True
        except Exception:
            pass

        self.send_auth_request()
        return False

    def send_auth_request(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Bansuri Dashboard"')
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Unauthorized")

    def do_GET(self):
        if not self.check_auth():
            return

        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            try:
                with open(os.path.join(os.path.dirname(__file__), "index.html"), "rb") as f:
                    self.wfile.write(f.read())
            except Exception as e:
                self.wfile.write(f"Error loading template: {e}".encode("utf-8"))
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            data = self.server.get_status_data()
            self.wfile.write(json.dumps(data, default=str).encode("utf-8"))
        elif self.path.startswith("/api/logs"):
            query = parse_qs(urlparse(self.path).query)
            task_name = query.get("task", [None])[0]
            log_type = query.get("type", ["stdout"])[0]
            try:
                offset = int(query.get("offset", ["0"])[0])
                limit = int(query.get("limit", ["51200"])[0])  # Default 50KB
            except ValueError:
                offset = 0
                limit = 51200

            if not task_name:
                self.send_error(400, "Missing task name")
                return

            content = self.server.get_task_logs(task_name, log_type, offset, limit)
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self):
        if not self.check_auth():
            return

        if self.path == "/api/control":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)

                task_name = data.get("task")
                action = data.get("action")

                success = self.server.handle_control(task_name, action)

                self.send_response(200 if success else 400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": success}).encode("utf-8"))
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass  # TODO: add debug logs


class Dashboard:
    def __init__(self, orchestrator, port=80, username=None, password=None):
        self.orchestrator = orchestrator
        self.port = port
        self.username = username
        self.password = password
        self.server = None
        self.thread = None
        self._master_proc = None

    def get_status_data(self):
        tasks = []
        global_cpu = 0.0
        global_mem = 0

        # Master process (that is bansuri)
        try:
            if psutil:
                if not self._master_proc:
                    self._master_proc = psutil.Process(os.getpid())
                global_cpu += self._master_proc.cpu_percent(interval=None)
                global_mem += self._master_proc.memory_info().rss
        except Exception:
            pass

        # Retrieve task runners resources
        try:
            runners = list(self.orchestrator.runners.values())
        except RuntimeError:
            runners = []

        for runner in runners:
            stats = runner.get_resource_usage()
            global_cpu += stats["cpu"]
            global_mem += stats["memory"]

            tasks.append(
                {
                    "name": runner.config.name,
                    "status": runner.status,
                    "last_run": runner.last_run,
                    "next_run": runner.next_run,
                    "attempts": runner.attempts,
                    "failed_attempts": runner.failed_attempts,
                    "command": runner.config.command,
                    "resources": stats,
                }
            )

        return {"tasks": tasks, "global": {"cpu": global_cpu, "memory": global_mem}}

    def get_task_logs(self, task_name, log_type="stdout", offset=0, limit=51200):
        """Tracks tasks logs"""
        runner = self.orchestrator.runners.get(task_name)
        if not runner:
            return "Task not found"

        config = runner.config
        file_path = None
        cwd = config.working_directory

        if log_type == "stdout":
            file_path = config.stdout
        elif log_type == "stderr":
            file_path = config.stderr

        if not file_path:
            return f"No {log_type} log file configured."

        if cwd and not os.path.isabs(file_path):
            file_path = os.path.join(cwd, file_path)

        if not os.path.exists(file_path):
            return f"Log file not found: {file_path}"

        try:
            file_size = os.path.getsize(file_path)

            end_pos = file_size - offset
            if end_pos <= 0:
                return ""

            start_pos = max(0, end_pos - limit)
            read_len = end_pos - start_pos

            with open(file_path, "rb") as f:
                f.seek(start_pos)
                content = f.read(read_len).decode("utf-8", errors="replace")
            return content
        except Exception as e:
            return f"Error reading log: {e}"

    def handle_control(self, task_name, action):
        """A handler for task controls from Dashboard"""
        runner = self.orchestrator.runners.get(task_name)
        if not runner:
            return False

        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [DASHBOARD] Action '{action}' requested for '{task_name}'"
        )

        if action == "start":
            runner.start()
        elif action == "stop":
            runner.stop()
        elif action == "restart":
            # Run in a separate thread to avoid blocking the HTTP response
            def _restart():
                runner.stop()
                runner.start()

            threading.Thread(target=_restart, daemon=True).start()
        return True

    def start(self):
        self.server = ThreadingHTTPServer(("0.0.0.0", self.port), DashboardHandler)
        self.server.username = self.username
        self.server.password = self.password
        self.server.get_status_data = self.get_status_data
        self.server.handle_control = self.handle_control
        self.server.get_task_logs = self.get_task_logs
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [DASHBOARD] Server started at http://0.0.0.0:80"
        )

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
