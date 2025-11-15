class BaseController:
    """
    Base interface for all race AI controllers.
    Your custom controllers MUST implement `get_action`.
    """

    def __init__(self, name="BaseController"):
        self.name = name

    def reset(self):
        """Called when the race restarts or a vehicle respawns. Override if needed."""
        pass

    def get_action(self, obs):
        """
        Core control method.
        Must return a tuple:
            (throttle: 0-1, brake: 0-1, steering: -1 to 1)
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_action(obs)"
        )
