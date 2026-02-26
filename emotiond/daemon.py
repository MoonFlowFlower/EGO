"""
Daemon process management and lifecycle
"""
import asyncio
import signal
import logging
import sys
from typing import Dict, Any, Optional
from emotiond.core import homeostasis_loop, consolidation_loop
from emotiond.db import init_db, close_db
from emotiond.config import setup_logging


class DaemonManager:
    """Manages the emotiond daemon lifecycle"""
    
    def __init__(self):
        self.loops: Dict[str, asyncio.Task] = {}
        self.running = False
        self.logger = logging.getLogger("emotiond.daemon")
    
    async def start(self) -> None:
        """Start the daemon and all background loops"""
        if self.running:
            self.logger.warning("Daemon is already running")
            return
        
        self.logger.info("Starting emotiond daemon")
        
        # Initialize database
        await init_db()
        
        # Start background loops
        self.loops["homeostasis"] = asyncio.create_task(homeostasis_loop())
        self.loops["consolidation"] = asyncio.create_task(consolidation_loop())
        
        self.running = True
        self.logger.info("Daemon started successfully")
    
    async def stop(self) -> None:
        """Gracefully stop the daemon and all background loops"""
        if not self.running:
            self.logger.warning("Daemon is not running")
            return
        
        self.logger.info("Stopping emotiond daemon")
        self.running = False
        
        # Cancel all background loops
        for name, task in self.loops.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    self.logger.debug(f"Loop {name} cancelled")
        
        # Close database connections
        await close_db()
        
        self.logger.info("Daemon stopped gracefully")
    
    def is_running(self) -> bool:
        """Check if daemon is running"""
        return self.running
    
    def get_loop_status(self) -> Dict[str, str]:
        """Get status of all background loops"""
        status = {}
        for name, task in self.loops.items():
            if task.done():
                try:
                    if task.exception():
                        status[name] = f"failed: {task.exception()}"
                    else:
                        status[name] = "completed"
                except asyncio.CancelledError:
                    status[name] = "cancelled"
            else:
                status[name] = "running"
        return status


# Global daemon manager instance
daemon_manager = DaemonManager()


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    
    def signal_handler(signum, frame):
        """Handle shutdown signals"""
        logger = logging.getLogger("emotiond.daemon")
        logger.info(f"Received signal {signum}, initiating shutdown")
        
        # Schedule daemon shutdown
        asyncio.create_task(daemon_manager.stop())
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


async def run_daemon():
    """Main daemon entry point"""
    setup_logging()
    setup_signal_handlers()
    
    logger = logging.getLogger("emotiond.daemon")
    
    try:
        await daemon_manager.start()
        
        # Keep the daemon running until stopped
        while daemon_manager.is_running():
            await asyncio.sleep(1)
            
            # Check if any loops have failed
            loop_status = daemon_manager.get_loop_status()
            for name, status in loop_status.items():
                if "failed" in status:
                    logger.error(f"Loop {name} failed: {status}")
                    await daemon_manager.stop()
                    break
        
    except Exception as e:
        logger.error(f"Daemon error: {e}")
        await daemon_manager.stop()
        sys.exit(1)
    
    logger.info("Daemon process completed")