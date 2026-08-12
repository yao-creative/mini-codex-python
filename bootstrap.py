import argparse
import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv
from states.agent import TurnLoopState
from states.conversation import ConversationState

from states.app import AppState
from states.command_queue import CommandQueueState
from states.config import Config
from states.event_bus import EventBusState
from states.session import SessionState
from states.worker import WorkerState


def parse_and_load_env(
    argv: list[str] | None = None,
) -> tuple[argparse.Namespace, list[str], Config]:
    parser = argparse.ArgumentParser(
        description="Bootstrap your app with configuration"
    )
    parser.add_argument(
        "--env-file", type=str, default=".env", help="Path to the .env file"
    )
    args, unknown = parser.parse_known_args(argv)
    env_file = args.env_file if os.path.exists(args.env_file) else ".env"
    if os.path.exists(env_file):
        load_dotenv(dotenv_path=env_file)
    else:
        print(
            f"Warning: .env file '{env_file}' not found. Proceeding without loading environment variables."
        )
    # Load pydantic config AFTER dotenv so env vars are populated
    config = Config(_env_file=env_file if os.path.exists(env_file) else None)
    return args, unknown, config


class BootstrapInterface(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def run(self, argv: list[str]) -> AppState: ...


class Bootstrap(BootstrapInterface):
    def __init__(self):
        pass

    @staticmethod
    def run(argv: list[str]) -> AppState:
        args, unknown, config = parse_and_load_env(argv)

        Session_state = SessionState(
            command_queue_state=CommandQueueState(),
            event_bus_state=EventBusState(),
            turn_loop_state=TurnLoopState(config.agent),
            worker_state=WorkerState(config.workers),
        )

        return AppState(config, Session_state)
