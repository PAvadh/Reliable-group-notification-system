import os
import queue
import subprocess
import sys
import threading
import time


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TIMEOUT = 10


class ManagedProcess:
    def __init__(self, name, script_name, env):
        self.name = name
        self.process = subprocess.Popen(
            [sys.executable, "-u", script_name],
            cwd=PROJECT_ROOT,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.output = []
        self.queue = queue.Queue()
        self.reader = threading.Thread(target=self._read_output, daemon=True)
        self.reader.start()

    def _read_output(self):
        for line in self.process.stdout:
            line = line.rstrip("\n")
            self.output.append(line)
            self.queue.put(line)

    def send_line(self, line):
        if self.process.stdin is None:
            raise RuntimeError(f"{self.name} stdin is unavailable")
        self.process.stdin.write(f"{line}\n")
        self.process.stdin.flush()

    def wait_for_text(self, expected_text, timeout=DEFAULT_TIMEOUT):
        return self.wait_for_occurrences(expected_text, 1, timeout=timeout)

    def wait_for_occurrences(self, expected_text, count, timeout=DEFAULT_TIMEOUT):
        deadline = time.time() + timeout
        while time.time() < deadline:
            matches = sum(1 for line in self.output if expected_text in line)
            if matches >= count:
                return

            remaining = deadline - time.time()
            if remaining <= 0:
                break

            try:
                line = self.queue.get(timeout=min(0.2, remaining))
            except queue.Empty:
                continue

            matches = sum(1 for existing_line in self.output if expected_text in existing_line)
            if matches >= count:
                return

        joined_output = "\n".join(self.output)
        raise AssertionError(
            f"{self.name} did not emit expected text {count} time(s): {expected_text!r}\nOutput so far:\n{joined_output}"
        )

    def stop(self):
        if self.process.poll() is not None:
            return

        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)


def main():
    env = os.environ.copy()
    env.setdefault("UDP_SHARED_SECRET", "demo-shared-secret")

    server = ManagedProcess("server", "server.py", env)
    client_one = ManagedProcess("client-1", "client.py", env)
    client_two = ManagedProcess("client-2", "client.py", env)

    processes = [server, client_one, client_two]

    try:
        server.wait_for_text("UDP Notification Server Started")
        server.wait_for_occurrences("[JOIN] Client-", 2, timeout=DEFAULT_TIMEOUT)

        alert_message = "Smoke test alert"
        server.send_line(alert_message)

        client_one.wait_for_text(f"[ALERT] {alert_message}")
        client_two.wait_for_text(f"[ALERT] {alert_message}")
        server.wait_for_text("[SUCCESS] All clients acknowledged packet 1")

        client_one.send_line("exit")
        client_two.send_line("exit")
        server.send_line("exit")

        print("Smoke test passed")
    finally:
        for managed_process in processes:
            managed_process.stop()


if __name__ == "__main__":
    main()
