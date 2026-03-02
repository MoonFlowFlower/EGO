#!/usr/bin/env python3
"""
Main entry point for emotiond daemon

US-705: Offline Rollouts are disabled by default.
Use --enable-rollouts to enable for diagnostic/recovery scenarios.
"""
import argparse
import os
import sys


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="OpenEmotion Daemon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  emotiond                          # Start daemon (rollouts disabled)
  emotiond --enable-rollouts        # Start with rollouts enabled
  emotiond --port 8080              # Start on custom port
        """
    )
    parser.add_argument(
        "--enable-rollouts",
        action="store_true",
        default=False,
        help="Enable offline rollouts (disabled by default for safety)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("EMOTIOND_HOST", "127.0.0.1"),
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("EMOTIOND_PORT", "18080")),
        help="Port to bind to (default: 18080)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Log level (default: info)"
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Set environment variables based on CLI args
    if args.enable_rollouts:
        os.environ["EMOTIOND_ENABLE_ROLLOUTS"] = "1"
    
    # Import after setting env vars so config picks them up
    import uvicorn
    from emotiond.config import HOST, PORT
    
    # Use CLI args if provided, else fall back to config defaults
    host = args.host if args.host != "127.0.0.1" else HOST
    port = args.port if args.port != 18080 else PORT
    
    uvicorn.run(
        "emotiond.api:app",
        host=host,
        port=port,
        log_level=args.log_level
    )


if __name__ == "__main__":
    main()
