from core import Core


def main(argv=None):
    # Run bootstrap logic
    app_state = Bootstrap().run(argv)
    # further processing can go here

    Core().run(app_state)


if __name__ == "__main__":
    main()
