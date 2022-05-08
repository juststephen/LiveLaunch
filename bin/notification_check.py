from datetime import datetime, timedelta, timezone

class NotificationCheck:
    """
    Contains what notification types to send
    depending on the old status, new status
    and old start and new start datetimes.

    Notes
    -----
    Call the object like so
    `NotificationCheck()(old_status, new_status)`,
    to get the following results:

    None : send no notifications.
    0 : Status notifications only.
    1 : T-0 change notifications only.
    2 : Both notification types.
    """
    def __init__(self) -> None:
        # 4 week cutoff for T-0 change notifications
        self.timedelta_4w = timedelta(weeks=4)
        # Dictionary containing statuses
        self.notification_status = {
            1: {1: 1, 2: 2, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 2},
            2: {1: 2, 2: None, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 2},
            3: {i: None for i in range(9)},
            4: {i: None for i in range(9)},
            5: {1: 2, 2: 2, 3: 0, 4: 0, 5: None, 6: 0, 7: 0, 8: 2},
            6: {1: None, 2: None, 3: 0, 4: 0, 5: None, 6: None, 7: 0, 8: None},
            7: {i: None for i in range(9)},
            8: {1: 2, 2: 2, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 1}
        }

    def __call__(
        self,
        old_status: int,
        new_status: int,
        old_start: datetime,
        new_start: datetime = None
    ) -> int or None:
        """
        Receive the notification type.

        Parameters
        ----------
        old_status : int
            Old status ID.
        new_status : int
            New status ID.
        old_start : datetime
            Old start datetime object.
        new_start : datetime, default: None
            New start datetime object.

        Returns
        -------
        notification_type : int
            None : send no notifications.
            0 : Status notifications only.
            1 : T-0 change notifications only.
            2 : Both notification types.
        """
        # Start datetime checks
        if new_start:
            # Current UTC time
            now = datetime.now(timezone.utc)
            # Only handle events within 4 weeks
            start_check = now < old_start < now + self.timedelta_4w
        else:
            start_check = False

        # Launches
        if all((old_status, new_status)):
            status = self.notification_status[old_status][new_status]
            if status:
                # None or T-0 change only
                if status == 1:
                    return status if start_check else None
                # Both or status only
                else:
                    return status if start_check else 0
            # None or status only
            else:
                return status

        # Events
        return 1 if start_check else None
