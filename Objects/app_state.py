from Objects.database import DatabaseManager


class AppState:
    # --------------------| Class Level Variables |-------------------- #
    _instance: "AppState | None" = None     # Forward reference
    _initialised: bool = False

    # --------------------|    Singleton Logic    |-------------------- #
    def __new__(cls, db=None, opening_id=None):
        """
        Called before __init__ to check if an instance already exists.
        Creates a new instance if none exists or returns the existing one.
        """

        if not AppState._instance:                      # No singleton instance yet
            AppState._instance = super().__new__(cls)   # Initialises new AppState instance and avoids infinite loop

        return AppState._instance                       # Always return the object stored in _instance

    def __init__(self, db: DatabaseManager | None = None, opening_id: int | None = None):
        """
        Stores the running state as a singleton object to be shared between screens.
        Calling AppState() only creates a new instance if none exist,
        otherwise returning the existing one.
        :param db: The database manager
        :param opening_id: The selected opening id
        """

        # __init__ gets called everytime AppState() is called, even if __new__ returns an existing instance
        if not AppState._initialised:                           # The singleton hasn't been initialised yet
            if db: self.db: DatabaseManager = db                # Don't change self.db if db is None
            self.selected_opening_id: int | None = opening_id   # Always set selected_opening_id to opening_id

            AppState._initialised = True