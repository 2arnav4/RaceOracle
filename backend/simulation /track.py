"""
Track module: Defines the circular racing track geometry and lap tracking.
"""

import math


class Track:
    """
    Represents a circular racing track centered at origin (0, 0).
    
    The track is a perfect circle with a given radius. Progress is measured
    as distance along the centerline, starting at (radius, 0) and going
    counterclockwise.
    """

    def __init__(self, radius=100.0):
        """
        Initialize the track.

        Args:
            radius: Radius of the circular track in meters (default: 100.0)
        """
        self.radius = radius
        self._lap_distance = 2 * math.pi * radius

    def get_lap_distance(self):
        """Return the total distance of one lap around the track."""
        return self._lap_distance

    def get_centerline_point(self, progress):
        """
        Get the (x, y) coordinates on the centerline at a given progress.

        The progress wraps around the track: progress % lap_distance gives
        the position within the current lap.

        Args:
            progress: Distance traveled along centerline (meters)

        Returns:
            Tuple of (x, y) coordinates on the centerline
        """
        # Normalize progress to [0, lap_distance)
        normalized = progress % self._lap_distance

        # Convert progress to angle: 0 progress = angle 0 (point (radius, 0))
        # Progress increases counterclockwise
        angle = normalized / self.radius

        # Compute Cartesian coordinates on circle
        x = self.radius * math.cos(angle)
        y = self.radius * math.sin(angle)

        return (x, y)

    def progress_from_position(self, x, y):
        """
        Convert Cartesian coordinates (x, y) to track progress.

        Returns the shortest distance along the centerline to reach (x, y)
        from the starting point (radius, 0). If the position is not exactly
        on the centerline, uses the projection onto the circle.

        Args:
            x: X-coordinate
            y: Y-coordinate

        Returns:
            Progress along the centerline (distance from start), within [0, lap_distance)
        """
        # Calculate angle from origin
        angle = math.atan2(y, x)

        # Ensure angle is in [0, 2π)
        if angle < 0:
            angle += 2 * math.pi

        # Convert angle to progress
        progress = angle * self.radius

        # Clamp to [0, lap_distance)
        progress = progress % self._lap_distance

        return progress

    def is_lap_complete(self, current_progress, previous_progress):
        """
        Detect if a vehicle has completed a lap.

        A lap is complete if the vehicle's progress has wrapped around the
        track (i.e., crossed the progress=0 line). This happens when:
        - previous_progress >= some threshold near lap_distance
        - current_progress is now small (close to 0)

        Args:
            current_progress: Current progress along centerline (meters)
            previous_progress: Progress from the previous timestep

        Returns:
            True if a lap was just completed, False otherwise
        """
        # Detect wrap-around: if previous > 0.9 * lap_distance and current < 0.1 * lap_distance
        threshold_high = 0.9 * self._lap_distance
        threshold_low = 0.1 * self._lap_distance

        return previous_progress >= threshold_high and current_progress < threshold_low

    def get_distance_to_centerline(self, x, y):
        """
        Calculate the perpendicular distance from point (x, y) to the track centerline.

        Args:
            x: X-coordinate
            y: Y-coordinate

        Returns:
            Distance to centerline (0 if on centerline, positive if outside)
        """
        distance_from_origin = math.sqrt(x**2 + y**2)
        return abs(distance_from_origin - self.radius)

    def get_track_bounds(self):
        """
        Return the bounds of the track for collision/boundary detection.

        Returns:
            Dict with 'inner_radius' and 'outer_radius' defining the track boundaries
        """
        # Define a track width of 80 meters (40 meters on each side of centerline)
        track_width = 80.0
        inner_radius = self.radius - track_width / 2
        outer_radius = self.radius + track_width / 2

        return {
            "inner_radius": inner_radius,
            "outer_radius": outer_radius,
            "centerline_radius": self.radius,
        }

    def __repr__(self):
        return f"Track(radius={self.radius}, lap_distance={self._lap_distance:.2f})"
