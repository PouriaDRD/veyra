"""Veyra executable entrypoint."""

from veyra.bootstrap import ApplicationLifecycle


def main() -> None:
    """Bootstrap Veyra and perform a clean shutdown."""

    with ApplicationLifecycle() as context:
        context.logger.info(
            "application_ready",
        )


if __name__ == "__main__":
    main()
