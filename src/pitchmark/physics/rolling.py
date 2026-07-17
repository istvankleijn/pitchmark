import geopandas as gpd
import numpy as np
import shapely
from scipy.integrate import solve_ivp

# Physics constants
MOI_SOLID_SPHERE = 0.4
GRAVITY = 9.8  # m/s^2

# Unit conversions
ONE_FOOT = 0.3048  # m
ONE_YARD = 3 * ONE_FOOT

# Golf rules
BALL_RADIUS = 0.02135  # m
HOLE_RADIUS = 0.054  # m


def softness(stimp_reading, *, ball_moi=MOI_SOLID_SPHERE, gravity=GRAVITY):
    """
    Convert Stimpmeter reading to a surface softness.

    By design, a golf ball leaves a Stimpmeter at a speed of 6.0 ft/s. The distance it
    then travels is the surface's reading.
    The softness of a deformable surface with respect to a ball is equivalent to the
    fraction of the ball that lies beneath the level surface.
    """
    init_ball_speed = 6.0 * ONE_FOOT
    return (init_ball_speed**2) * (1.0 + ball_moi) / (2 * gravity * stimp_reading)


class Surface:
    def __init__(self, stimp, *, gdf=None, ball_moi=MOI_SOLID_SPHERE, gravity=GRAVITY):
        self.stimp = stimp
        self.softness = softness(stimp, ball_moi=ball_moi, gravity=gravity)
        if gdf is None:
            self.gdf = gpd.GeoDataFrame()
        else:
            self.gdf = gdf
        self.ball_moi = ball_moi
        self.gravity = gravity

    def normal(self, x, y):
        return self.gdf.loc[
            self.gdf.intersects(shapely.Point(x, y)),
            ["normal_x", "normal_y", "normal_z"],
        ].values

    def z(self, x, y):
        return self.gdf.loc[
            self.gdf.intersects(shapely.Point(x, y)),
            ["z"],
        ].values

    def simple_roll_du(self, u):
        x, y, vx, vy = u
        dx = vx
        dy = vy

        g = self.gravity
        I_b = self.ball_moi
        rho_g = self.softness

        nx, ny, nz = self.normal(x, y)
        grade = np.sqrt(1.0 - nz * nz)
        v = np.sqrt(vx * vx + vy * vy)

        prefactor = g / I_b
        dvx = prefactor * (grade * nx - rho_g * vx / v)
        dvy = prefactor * (grade * ny - rho_g * vy / v)
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
