"""Process supervision and rolling-hour crash restart accounting."""
from collections import deque
import multiprocessing
import time


class RestartWindow:
    def __init__(self):
        self.restarts = deque()

    def allow(self, now):
        while self.restarts and self.restarts[0] <= now - 3600:
            self.restarts.popleft()
        if len(self.restarts) >= 3:
            return False
        self.restarts.append(now)
        return True


def runtime_worker(connection, options):
    from .runtime import Runtime
    runtime = None
    try:
        runtime = Runtime(**options)
        connection.send({'event':'ready'})
        while True:
            if connection.poll(.5):
                command = connection.recv()
                if command == 'close':
                    runtime.close('owner_closed')
                    return
                if command == 'stop': runtime.engine.stop()
                elif command == 'reconnect': runtime.reconnect_body()
                elif command == 'replay': runtime.replay_latest_mc()
            if runtime._closed.is_set(): return
            if not runtime.watcher.is_alive():
                raise RuntimeError('runtime_watchdog_exited')
            connection.send({'event':'status','text':runtime.status()})
    except (EOFError,BrokenPipeError):
        pass
    except Exception as error:
        try: connection.send({'event':'error','text':getattr(error,'code',type(error).__name__)})
        except (OSError,EOFError): pass
        raise SystemExit(1) from None
    finally:
        if runtime: runtime.close('worker_exiting')
        connection.close()


class Supervisor:
    def __init__(self, options, *, target=runtime_worker, clock=time.monotonic):
        self.options, self.target, self.clock = options, target, clock
        self.window = RestartWindow()
        self.process = self.connection = None
        self.stopped = False
        self.status = '正在启动内核……'
        self.last_error = ''

    def start(self):
        context = multiprocessing.get_context('spawn')
        parent, child = context.Pipe()
        self.connection = parent
        self.process = context.Process(target=self.target,args=(child,self.options))
        self.process.start()
        child.close()

    def send(self, command):
        if command == 'close': self.stopped = True
        try:
            if self.connection: self.connection.send(command)
        except (OSError,EOFError): pass

    def tick(self):
        if self.connection:
            try:
                while self.connection.poll():
                    event = self.connection.recv()
                    if event['event'] == 'status':
                        self.status = event['text']
                        if self.last_error: self.status += '；最近恢复前错误：'+self.last_error
                    elif event['event'] == 'error': self.last_error = event['text']
            except (OSError,EOFError): pass
        if self.process and not self.process.is_alive() and not self.stopped:
            self.process.join()
            self.last_error = self.last_error or f'内核进程退出（{self.process.exitcode}）'
            self.connection.close()
            if self.window.allow(self.clock()):
                self.status = '内核正在自动恢复；旧动作不会重放。最近错误：' + self.last_error
                self.start()
            else:
                self.stopped = True
                self.status = '已停止：一小时内自动重启已达 3 次。最近错误：' + self.last_error
        return self.status

    def close(self):
        self.send('close')
        if self.process:
            self.process.join(8)
            if self.process.is_alive():
                self.process.terminate()
                self.process.join(3)
        if self.connection: self.connection.close()
