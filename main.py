from bootstrap import bootstrap
from core import Core

def main(argv=None):
    # Run bootstrap logic
    app_state = Bootstrap().run(argv)
    # further processing can go here
    
    Core(app_state).run()


if __name__ == "__main__":
    main()
