import sys
from yasinfeed.engine import YasinFeedEngine, handle_signals

def main():
    """
    Main entry point for YasinFeed application.
    Instantiates the engine, initializes modules, registers signal handlers,
    and runs the application.
    """
    engine = YasinFeedEngine()

    # Register OS signal handlers for clean shut-downs (SIGINT/SIGTERM)
    handle_signals(engine)

    # Initialize the core engine and all registered modules
    success = engine.initialize()
    if not success:
        print("CRITICAL: Failed to initialize YasinFeed Engine. Exiting.", file=sys.stderr)
        sys.exit(1)

    try:
        # Start the engine and block on main thread wait-loop
        engine.start()
    except Exception as e:
        engine.logger.critical("Engine encountered an unexpected runtime error: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
