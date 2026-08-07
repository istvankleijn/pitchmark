import geopandas as gpd
import numpy as np
import shapely
from scipy.integrate import solve_ivp

# Physics constants
MOI_SOLID_SPHERE = 0.4

# Unit conversions
ONE_FOOT = 0.3048  # m
ONE_YARD = 3 * ONE_FOOT  # m
FEET_PER_YARD = 3
INCHES_PER_YARD = 36

# All physics below is in yards and seconds.
GRAVITY = 9.8 / ONE_YARD  # yd/s^2

# Golf rules
BALL_RADIUS = 0.84 / INCHES_PER_YARD  # yd
HOLE_RADIUS = 2.125 / INCHES_PER_YARD  # yd


def softness(stimp_reading, *, ball_moi=MOI_SOLID_SPHERE, gravity=GRAVITY):
    """
    Convert a Stimpmeter reading (in feet) to a surface softness.

    By design, a golf ball leaves a Stimpmeter at a speed of 6.0 ft/s. The distance it
    then travels, in feet, is the surface's Stimpmeter reading.
    The softness of a deformable surface with respect to a ball is equivalent to the
    fraction of the ball that lies beneath the level surface.
    """
    init_ball_speed = 6.0 / FEET_PER_YARD  # yd/s
    stimp_reading = stimp_reading / FEET_PER_YARD  # ft -> yd
    return (init_ball_speed**2) * (1.0 + ball_moi) / (2 * gravity * stimp_reading)


class Surface:
    def __init__(self, stimp, *, gdf=None, ball_moi=MOI_SOLID_SPHERE, gravity=GRAVITY):
        self.stimp = stimp
        self.softness = softness(stimp, ball_moi=ball_moi, gravity=gravity)
        if gdf is None:
            self.gdf = gpd.GeoDataFrame()
        else:
            self.gdf = gdf
        self.strtree = None if self.gdf.empty else shapely.STRtree(self.gdf.geometry)
        self.ball_moi = ball_moi
        self.gravity = gravity

    def _lookup(self, x, y, columns):
        if self.strtree is None:
            return None
        candidates = self.strtree.query(shapely.Point(x, y), predicate="within")
        if len(candidates) == 0:
            return None
        return self.gdf.iloc[candidates[0]][columns].to_numpy()

    def normal(self, x, y):
        values = self._lookup(x, y, ["normal_x", "normal_y", "normal_z"])
        return np.array([0.0, 0.0, 1.0]) if values is None else values

    def z(self, x, y):
        return self._lookup(x, y, ["z"])

    def simple_roll_du(self, u):
        x, y, vx, vy = u
        dx = vx
        dy = vy

        g = self.gravity
        I_b = self.ball_moi
        rho_g = self.softness

        nx, ny, nz = self.normal(x, y)
        v = np.sqrt(vx * vx + vy * vy)
        cos_theta = vx / v
        sin_theta = vy / v

        # Resolve gravity/slope into components forward and perpendicular to the
        # ball's current direction of travel. The rolling-friction contact point is
        # offset ahead of the ball by the local slope rather than sitting directly
        # opposite velocity, which is why this can't be a simple v-antiparallel drag
        # term - adapted from Penner (Can J Phys 2002) for a slope that varies
        # spatially rather than Penner's fixed slope direction.
        prefactor = -g * I_b / (1.0 + I_b)
        dv_forward = prefactor * (rho_g / I_b + nx * cos_theta - ny * sin_theta)
        dv_perpendicular = prefactor * (nx * sin_theta + ny * cos_theta)

        dvx = dv_forward * cos_theta - dv_perpendicular * sin_theta
        dvy = dv_forward * sin_theta + dv_perpendicular * cos_theta
        return [dx, dy, dvx, dvy]

    def roll_ball(
        self,
        x0,
        y0,
        vx0,
        vy0,
        *,
        tmax=10.0,
        method="LSODA",
        events=None,
        dense=False,
        **kwargs,
    ):
        if events is None:
            events = [MinBallSpeed(1e-6)]

        def f(t, u):
            return self.simple_roll_du(u)

        tspan = (0.0, tmax)
        u0 = np.array([x0, y0, vx0, vy0])
        sol = solve_ivp(
            f,
            tspan,
            u0,
            method=method,
            events=events,
            dense_output=dense,
            **kwargs,
        )
        end_point = sol.y.T[-1]
        if dense:
            return (end_point, sol)
        else:
            return end_point


class MinBallSpeed:
    def __init__(self, min_speed, *, terminal=True, direction=0):
        self.terminal = terminal
        self.direction = direction
        self.min_speed = min_speed

    def __call__(self, t, u):
        x, y, vx, vy = u
        v2 = vx * vx + vy * vy
        return v2 - self.min_speed * self.min_speed


class Green(Surface):
    def __init__(
        self,
        stimp,
        *,
        hole_location=None,
        hole_radius=HOLE_RADIUS,
        holing_vmax=1.63,
        **kwargs,
    ):
        super().__init__(stimp, **kwargs)
        self.hole_location = (0.0, 0.0) if hole_location is None else hole_location
        self.hole_radius = hole_radius
        self.hole_radius_squared = hole_radius * hole_radius
        self.holing_vmax = holing_vmax

    def impact_function(self, u):
        x, y, vx, vy = u
        x0, y0 = self.hole_location
        squared_distance_to_hole = (x - x0) * (x - x0) + (y - y0) * (y - y0)
        impact = squared_distance_to_hole / self.hole_radius_squared
        v = np.sqrt(vx * vx + vy * vy)
        return v - self.holing_vmax * (1.0 - impact)
