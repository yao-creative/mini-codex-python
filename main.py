from bootstrap import Bootstrap
from Session import Session


def main(argv=None):
    # Run bootstrap logic
    app_state = Bootstrap().run(argv)
    # further processing can go here
    # Auth can go here.
    # Startup Session



if __name__ == "__main__":
    main()
