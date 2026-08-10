import argparse
import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv
from states.agent_state import AgentState
from states.app_state import AppState
from states.conversation_state import ConversationState
from states.core_state import CoreState
from states.worker_state import WorkerState

from states.command_queue import CommandQueueState
from states.config import Config
from states.event_bus import EventBusState


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


class Bootstrap_interface(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def run(self, argv: list[str]) -> AppState: ...


class Bootstrap(Bootstrap_interface):
    def __init__(self):
        pass

    @staticmethod
    def run(argv: list[str]) -> AppState:
        args, unknown, config = parse_and_load_env(argv)

        core_state = CoreState(
            command_queue_state=CommandQueueState(),
            event_bus_state=EventBusState(),
            conversation_state=ConversationState(),
            agent_state=AgentState(config.agent),
            worker_state=WorkerState(config.workers),
        )

        return AppState(config, core_state)
