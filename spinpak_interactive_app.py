"""
SpinPAK Interactive Application
Two-panel PyQt6 app with:
1. Left panel: Joukowsky airfoil with sliders to adjust parameters
2. Right panel: Revolution shape with Joukowsky airfoil revolution
   - Slider to adjust airfoil Y position
   - Slider to adjust number of revolutions (1-12)
"""

import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QSlider, QLabel, QSplitter,
                              QPushButton, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from shapely.geometry import LineString, Point
from scipy.optimize import minimize, minimize_scalar
import svgwrite
from datetime import datetime


# ============================================================================
# HELPER FUNCTIONS (from simplified_logo.ipynb)
# ============================================================================

def plot_joukowsky(R, x_center, y_center, scale=1.0):
    """Generate Joukowsky airfoil coordinates.

    Args:
        R: Radius of the generating circle
        x_center: X center of the generating circle
        y_center: Y center of the generating circle
        scale: Scale factor for the output airfoil (default 1.0)
    """
    n_points = 400
    theta = np.linspace(0, 2 * np.pi, n_points)
    w = (x_center + R * np.cos(theta)) + 1j * (y_center + R * np.sin(theta))
    a = R
    z = w + (a**2) / w
    return z.real * scale, z.imag * scale


def reflect(points, angle_deg):
    """Reflect points across a line through origin at given angle."""
    theta = np.radians(angle_deg)
    cos_theta = np.cos(-theta)
    sin_theta = np.sin(-theta)
    rotation_matrix = np.array([[cos_theta, -sin_theta], [sin_theta, cos_theta]])
    cos_theta_inv = np.cos(theta)
    sin_theta_inv = np.sin(theta)
    rotation_matrix_inv = np.array([[cos_theta_inv, -sin_theta_inv], [sin_theta_inv, cos_theta_inv]])
    reflected_points = []
    for p in points:
        p_rotated = rotation_matrix @ p
        p_reflected_rotated = np.array([p_rotated[0], -p_rotated[1]])
        p_reflected = rotation_matrix_inv @ p_reflected_rotated
        reflected_points.append(p_reflected)
    return np.array(reflected_points)


def rotate(points, angle_deg, center=(0, 0)):
    """Rotate points around a center."""
    angle_rad = np.radians(angle_deg)
    R = np.array([[np.cos(angle_rad), -np.sin(angle_rad)],
                  [np.sin(angle_rad),  np.cos(angle_rad)]])
    return (points - center) @ R.T + center


def generate_revolution_shape():
    """Generate the revolution shape (SpinPAK logo base)."""
    # Parameters
    r1 = 1.0      # Inner arc radius
    r2 = 1.2      # Outer arc radius
    R = 0.05      # Rounding corner radius
    R_joint = 0.3 # Joint rounding radius

    # Key points
    p1 = np.array([-0.7, np.sqrt(r1**2 - 0.7**2)])
    p2 = np.array([-0.7, np.sqrt(r2**2 - 0.7**2)])
    p3 = np.array([-0.1, np.sqrt(r1**2 - 0.1**2)])
    p4 = np.array([-0.1, 0])

    # Generate base segments
    theta_outer = np.linspace(np.pi / 2, np.arccos(-0.7 / r2), 100)
    arc1_pts = np.array([(r2 * np.cos(t), r2 * np.sin(t)) for t in theta_outer])
    seg2_pts = np.array([p2, p1])
    theta_inner = np.linspace(np.arccos(-0.7 / r1), np.arccos(-0.1 / r1), 100)
    arc3_pts = np.array([(r1 * np.cos(t), r1 * np.sin(t)) for t in theta_inner])
    seg4_pts = np.array([p3, p4])

    # Rounded corner 1 (Inner corner: arc1 -> seg2)
    def objective_inner(center):
        dists = []
        dist_seg = Point(center).distance(LineString(seg2_pts))
        dists.append((dist_seg - R)**2)
        d_arc = np.min(np.linalg.norm(arc1_pts - center, axis=1))
        dists.append((d_arc - R)**2)
        origin_dist = np.linalg.norm(center)
        if origin_dist > r2 - R:
            dists.append(10 * (origin_dist - (r2 - R))**2)
        return sum(dists)

    res_inner = minimize(objective_inner, [-0.7 + R, 1.0], method='Nelder-Mead')
    circle_center_inner = res_inner.x
    closest_arc_pt_inner = arc1_pts[np.argmin(np.linalg.norm(arc1_pts - circle_center_inner, axis=1))]
    closest_seg_pt_inner = np.array(LineString(seg2_pts).interpolate(
        LineString(seg2_pts).project(Point(circle_center_inner))).coords[0])

    vec_start = closest_arc_pt_inner - circle_center_inner
    vec_end = closest_seg_pt_inner - circle_center_inner
    angle_start = np.arctan2(vec_start[1], vec_start[0])
    angle_end = np.arctan2(vec_end[1], vec_end[0])
    if angle_end < angle_start:
        angle_end += 2 * np.pi
    arc_connection_theta = np.linspace(angle_start, angle_end, 100)
    arc_connection_inner = np.array([circle_center_inner + R * np.array([np.cos(a), np.sin(a)])
                                     for a in arc_connection_theta])

    # Rounded corner 2 (Outer corner: seg2 -> arc3)
    def objective_outer(center):
        dists = []
        dist_seg = Point(center).distance(LineString(seg2_pts))
        dists.append((dist_seg - R)**2)
        d_arc = np.min(np.linalg.norm(arc3_pts - center, axis=1))
        dists.append((d_arc - R)**2)
        origin_dist = np.linalg.norm(center)
        if origin_dist < r1 + R:
            dists.append(1000 * (r1 + R - origin_dist)**2)
        return sum(dists)

    res_outer = minimize(objective_outer, [-0.65, 0.8], method='Nelder-Mead')
    circle_center_outer = res_outer.x
    closest_arc3_pt = arc3_pts[np.argmin(np.linalg.norm(arc3_pts - circle_center_outer, axis=1))]
    closest_seg2_pt = np.array(LineString(seg2_pts).interpolate(
        LineString(seg2_pts).project(Point(circle_center_outer))).coords[0])

    vec_start = closest_seg2_pt - circle_center_outer
    vec_end = closest_arc3_pt - circle_center_outer
    angle_start = np.arctan2(vec_start[1], vec_start[0])
    angle_end = np.arctan2(vec_end[1], vec_end[0])
    if angle_end < angle_start:
        angle_start -= 2 * np.pi
    arc_connection_theta = np.linspace(angle_end, angle_start, 100)
    arc_connection_outer = np.array([circle_center_outer + R * np.array([np.cos(a), np.sin(a)])
                                     for a in arc_connection_theta])[::-1]

    # Rounded corner 3 (Lower corner: arc3 -> seg4)
    line_seg4 = LineString(seg4_pts)

    def objective_x(cx):
        return abs(Point([cx, 0.3]).distance(line_seg4.interpolate(
            line_seg4.project(Point([cx, 0.3])))) - R)

    res_x = minimize_scalar(objective_x, bounds=(-0.3, 0.3), method='bounded')
    x0 = res_x.x

    def objective_y(cy):
        center = np.array([x0, cy])
        return abs(np.min(np.linalg.norm(arc3_pts - center, axis=1)) - R)

    res_y = minimize_scalar(objective_y, bounds=(0.3, 1.0), method='bounded')
    circle_center_low = np.array([x0, res_y.x])

    closest_arc_low = arc3_pts[np.argmin(np.linalg.norm(arc3_pts - circle_center_low, axis=1))]
    closest_seg_low = np.array(line_seg4.interpolate(
        line_seg4.project(Point(circle_center_low))).coords[0])

    vec_start = closest_arc_low - circle_center_low
    vec_end = closest_seg_low - circle_center_low
    angle_start = np.arctan2(vec_start[1], vec_start[0])
    angle_end = np.arctan2(vec_end[1], vec_end[0])
    if angle_start < angle_end:
        angle_end -= 2 * np.pi
    arc_connection_theta = np.linspace(angle_start, angle_end, 100)
    arc_connection_low = np.array([circle_center_low + R * np.array([np.cos(a), np.sin(a)])
                                   for a in arc_connection_theta])

    # Assemble full contour
    index_of_closest_arc_pt_inner = np.argmin(np.linalg.norm(arc1_pts - closest_arc_pt_inner, axis=1))
    arc1_start_to_inner_contact = arc1_pts[:index_of_closest_arc_pt_inner + 1]
    seg_inner_to_outer = np.array([closest_seg_pt_inner, closest_seg2_pt])
    index_of_closest_arc3_outer = np.argmin(np.linalg.norm(arc3_pts - closest_arc3_pt, axis=1))
    index_of_closest_arc3_low = np.argmin(np.linalg.norm(arc3_pts - closest_arc_low, axis=1))
    arc3_outer_to_lower_contact = arc3_pts[index_of_closest_arc3_outer : index_of_closest_arc3_low + 1]
    seg4_to_end = np.array([closest_seg_low, seg4_pts[1]])

    full_contour = np.vstack([
        arc1_start_to_inner_contact,
        arc_connection_inner[1:],
        seg_inner_to_outer[1:],
        arc_connection_outer[1:],
        arc3_outer_to_lower_contact[1:],
        arc_connection_low[1:],
    ])

    # Create reflected version
    full_contour_reflected = reflect(full_contour, 150)
    seg4 = seg4_to_end
    seg4_r = reflect(seg4, 150)

    # Rounded joint between seg4 and seg4_r
    A = seg4[0]
    B = seg4[1]  # The corner point
    C = seg4_r[0]

    u = (A - B) / np.linalg.norm(A - B)
    v = (C - B) / np.linalg.norm(C - B)

    theta = np.arccos(np.clip(np.dot(u, v), -1.0, 1.0)) / 2
    bisector = u + v
    bisector /= np.linalg.norm(bisector)

    d = R_joint / np.sin(theta)
    circle_center = B + d * bisector

    normal_to_AB = np.array([-u[1], u[0]])
    normal_to_BC = np.array([v[1], -v[0]])

    contact_AB = circle_center + R_joint * (-normal_to_AB)
    contact_BC = circle_center + R_joint * (-normal_to_BC)

    angle1 = np.arctan2(*(contact_AB - circle_center)[::-1])
    angle2 = np.arctan2(*(contact_BC - circle_center)[::-1])

    if angle1 < angle2:
        angle2 -= 2 * np.pi

    arc_angles = np.linspace(angle2, angle1, 100)
    arc_x = circle_center[0] + R_joint * np.cos(arc_angles)
    arc_y = circle_center[1] + R_joint * np.sin(arc_angles)

    joint1 = np.array([seg4[0], [contact_AB[0], contact_AB[1]]])
    joint2 = np.array([[contact_BC[0], contact_BC[1]], seg4_r[0]])
    arc_joint = np.vstack([arc_x, arc_y]).T
    arc_joint_flipped = arc_joint[::-1]
    finale1 = np.vstack([joint1, arc_joint_flipped, joint2])

    # Prepare base paths for revolution
    base_paths = [full_contour, finale1, full_contour_reflected]
    paths_to_plot = []

    # For each rotation (0°, 120°, 240°), rotate each base path
    for angle in [0, 120, 240]:
        for path in base_paths:
            rotated_path = rotate(path, angle, center=(0, 0))
            paths_to_plot.append(rotated_path)

    return paths_to_plot


# ============================================================================
# MATPLOTLIB CANVAS WIDGETS
# ============================================================================

class JoukowskyCanvas(FigureCanvas):
    """Canvas for displaying the Joukowsky airfoil with interactive controls."""

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 6))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

        # Default parameters
        self.R = 0.85
        self.x_center = -0.1
        self.y_center = 0.23
        self.scale = 1.0

        self.plot_airfoil()

    def plot_airfoil(self):
        """Plot the Joukowsky airfoil with current parameters."""
        self.ax.clear()
        x, y = plot_joukowsky(self.R, self.x_center, self.y_center, self.scale)
        self.ax.plot(x, y, 'b-', linewidth=2)
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_title('Joukowsky Airfoil', fontsize=14, fontweight='bold')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.draw()

    def update_parameters(self, R=None, x_center=None, y_center=None, scale=None):
        """Update airfoil parameters and replot."""
        if R is not None:
            self.R = R
        if x_center is not None:
            self.x_center = x_center
        if y_center is not None:
            self.y_center = y_center
        if scale is not None:
            self.scale = scale
        self.plot_airfoil()


class RevolutionCanvas(FigureCanvas):
    """Canvas for displaying the revolution shape with Joukowsky airfoil."""

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 6))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

        # Generate revolution shape (this is static)
        self.revolution_paths = generate_revolution_shape()

        # Joukowsky parameters
        self.R = 0.85
        self.x_center = -0.1
        self.y_center = 0.23
        self.scale = 1.0  # Scale factor for airfoil
        self.y_offset = 0.0  # Vertical offset for airfoil
        self.n_revolutions = 1  # Number of revolutions for airfoil

        self.plot_combined()

    def plot_combined(self):
        """Plot revolution shape with Joukowsky airfoil(s)."""
        self.ax.clear()

        # Plot revolution shape
        for path in self.revolution_paths:
            self.ax.plot(path[:, 0], path[:, 1], 'b-', linewidth=1.5, alpha=0.6)

        # Generate base Joukowsky airfoil with Y offset and scale
        x, y = plot_joukowsky(self.R, self.x_center, self.y_center, self.scale)
        y_adjusted = y + self.y_offset

        # Create airfoil points array
        airfoil_points = np.column_stack([x, y_adjusted])

        # Plot airfoil with revolutions
        if self.n_revolutions == 1:
            # Single airfoil - no rotation
            self.ax.plot(airfoil_points[:, 0], airfoil_points[:, 1], 'r-',
                        linewidth=2, label='Joukowsky Airfoil')
        else:
            # Multiple revolutions - rotate around origin
            angle_step = 360.0 / self.n_revolutions
            for i in range(self.n_revolutions):
                angle = i * angle_step
                rotated_airfoil = rotate(airfoil_points, angle, center=(0, 0))
                self.ax.plot(rotated_airfoil[:, 0], rotated_airfoil[:, 1], 'r-',
                           linewidth=2, alpha=0.8,
                           label=f'Airfoil {i+1}' if self.n_revolutions <= 6 else None)

        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        title = f'Revolution Shape with Joukowsky Airfoil'
        if self.n_revolutions > 1:
            title += f' ({self.n_revolutions}× Revolution)'
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        if self.n_revolutions <= 6:  # Only show legend if not too many airfoils
            self.ax.legend()
        self.draw()

    def update_y_offset(self, y_offset):
        """Update Y offset and replot."""
        self.y_offset = y_offset
        self.plot_combined()

    def update_n_revolutions(self, n_revolutions):
        """Update number of revolutions and replot."""
        self.n_revolutions = n_revolutions
        self.plot_combined()

    def update_joukowsky_parameters(self, R=None, x_center=None, y_center=None, scale=None):
        """Update Joukowsky parameters from left panel."""
        if R is not None:
            self.R = R
        if x_center is not None:
            self.x_center = x_center
        if y_center is not None:
            self.y_center = y_center
        if scale is not None:
            self.scale = scale
        self.plot_combined()

    def export_to_svg(self, filename):
        """Export the current revolution pattern with airfoils to SVG."""
        # Calculate bounds for all shapes
        all_points = []

        # Add revolution shape points
        for path in self.revolution_paths:
            all_points.extend(path)

        # Add airfoil points
        x, y = plot_joukowsky(self.R, self.x_center, self.y_center, self.scale)
        y_adjusted = y + self.y_offset
        airfoil_points = np.column_stack([x, y_adjusted])

        if self.n_revolutions == 1:
            all_points.extend(airfoil_points)
        else:
            angle_step = 360.0 / self.n_revolutions
            for i in range(self.n_revolutions):
                angle = i * angle_step
                rotated_airfoil = rotate(airfoil_points, angle, center=(0, 0))
                all_points.extend(rotated_airfoil)

        all_points = np.array(all_points)

        # Calculate bounds with padding
        min_x, min_y = all_points.min(axis=0)
        max_x, max_y = all_points.max(axis=0)
        padding = 0.2
        width = max_x - min_x + 2 * padding
        height = max_y - min_y + 2 * padding

        # Create SVG with proper scaling
        scale = 300  # pixels per unit
        svg_width = width * scale
        svg_height = height * scale

        dwg = svgwrite.Drawing(filename, size=(f'{svg_width}px', f'{svg_height}px'),
                               viewBox=f'{min_x - padding} {min_y - padding} {width} {height}')

        # Add background (optional)
        dwg.add(dwg.rect(insert=(min_x - padding, min_y - padding),
                        size=(width, height),
                        fill='white'))

        # Function to convert points to SVG path
        def points_to_path(points):
            if len(points) == 0:
                return ""
            path_data = f"M {points[0][0]},{points[0][1]}"
            for p in points[1:]:
                path_data += f" L {p[0]},{p[1]}"
            return path_data

        # Draw revolution shape (blue)
        for path in self.revolution_paths:
            path_data = points_to_path(path)
            dwg.add(dwg.path(d=path_data,
                           stroke='blue',
                           stroke_width=0.01,
                           fill='none',
                           opacity=0.6))

        # Draw airfoil(s) (red)
        if self.n_revolutions == 1:
            path_data = points_to_path(airfoil_points)
            dwg.add(dwg.path(d=path_data,
                           stroke='red',
                           stroke_width=0.015,
                           fill='none'))
        else:
            angle_step = 360.0 / self.n_revolutions
            for i in range(self.n_revolutions):
                angle = i * angle_step
                rotated_airfoil = rotate(airfoil_points, angle, center=(0, 0))
                path_data = points_to_path(rotated_airfoil)
                dwg.add(dwg.path(d=path_data,
                               stroke='red',
                               stroke_width=0.015,
                               fill='none',
                               opacity=0.8))

        # Add metadata
        dwg.add(dwg.text(f'SpinPAK Logo - {self.n_revolutions}× Revolution',
                        insert=(min_x - padding + 0.05, min_y - padding + 0.15),
                        font_size='0.1',
                        fill='gray'))

        dwg.save()
        return True


# ============================================================================
# MAIN APPLICATION WINDOW
# ============================================================================

class SpinPAKApp(QMainWindow):
    """Main application window with two interactive panels."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('SpinPAK Interactive Application')
        self.setGeometry(100, 100, 1600, 800)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Create splitter for two panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # ===== LEFT PANEL: Joukowsky Airfoil with controls =====
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Canvas
        self.joukowsky_canvas = JoukowskyCanvas()
        left_layout.addWidget(self.joukowsky_canvas)

        # Sliders for Joukowsky parameters
        # R slider
        r_layout = QHBoxLayout()
        r_label = QLabel('Radius (R):')
        self.r_value_label = QLabel('0.85')
        self.r_slider = QSlider(Qt.Orientation.Horizontal)
        self.r_slider.setMinimum(50)  # 0.50
        self.r_slider.setMaximum(120)  # 1.20
        self.r_slider.setValue(85)  # 0.85
        self.r_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.r_slider.setTickInterval(10)
        self.r_slider.valueChanged.connect(self.on_r_changed)
        r_layout.addWidget(r_label)
        r_layout.addWidget(self.r_slider)
        r_layout.addWidget(self.r_value_label)
        left_layout.addLayout(r_layout)

        # X center slider
        x_layout = QHBoxLayout()
        x_label = QLabel('X Center:')
        self.x_value_label = QLabel('-0.10')
        self.x_slider = QSlider(Qt.Orientation.Horizontal)
        self.x_slider.setMinimum(-50)  # -0.50
        self.x_slider.setMaximum(50)   # 0.50
        self.x_slider.setValue(-10)    # -0.10
        self.x_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.x_slider.setTickInterval(10)
        self.x_slider.valueChanged.connect(self.on_x_changed)
        x_layout.addWidget(x_label)
        x_layout.addWidget(self.x_slider)
        x_layout.addWidget(self.x_value_label)
        left_layout.addLayout(x_layout)

        # Y center slider
        y_layout = QHBoxLayout()
        y_label = QLabel('Y Center:')
        self.y_value_label = QLabel('0.23')
        self.y_slider = QSlider(Qt.Orientation.Horizontal)
        self.y_slider.setMinimum(0)    # 0.00
        self.y_slider.setMaximum(50)   # 0.50
        self.y_slider.setValue(23)     # 0.23
        self.y_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.y_slider.setTickInterval(10)
        self.y_slider.valueChanged.connect(self.on_y_changed)
        y_layout.addWidget(y_label)
        y_layout.addWidget(self.y_slider)
        y_layout.addWidget(self.y_value_label)
        left_layout.addLayout(y_layout)

        # Scale slider
        scale_layout = QHBoxLayout()
        scale_label = QLabel('Scale:')
        self.scale_value_label = QLabel('1.00')
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setMinimum(10)   # 0.10
        self.scale_slider.setMaximum(300)  # 3.00
        self.scale_slider.setValue(100)    # 1.00
        self.scale_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.scale_slider.setTickInterval(20)
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        scale_layout.addWidget(scale_label)
        scale_layout.addWidget(self.scale_slider)
        scale_layout.addWidget(self.scale_value_label)
        left_layout.addLayout(scale_layout)

        # ===== RIGHT PANEL: Revolution shape with airfoil =====
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Canvas
        self.revolution_canvas = RevolutionCanvas()
        right_layout.addWidget(self.revolution_canvas)

        # Y offset slider
        offset_layout = QHBoxLayout()
        offset_label = QLabel('Airfoil Y Offset:')
        self.offset_value_label = QLabel('0.00')
        self.offset_slider = QSlider(Qt.Orientation.Horizontal)
        self.offset_slider.setMinimum(-100)  # -1.00
        self.offset_slider.setMaximum(100)   # 1.00
        self.offset_slider.setValue(0)       # 0.00
        self.offset_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.offset_slider.setTickInterval(20)
        self.offset_slider.valueChanged.connect(self.on_offset_changed)
        offset_layout.addWidget(offset_label)
        offset_layout.addWidget(self.offset_slider)
        offset_layout.addWidget(self.offset_value_label)
        right_layout.addLayout(offset_layout)

        # Number of revolutions slider
        rev_layout = QHBoxLayout()
        rev_label = QLabel('Number of Revolutions:')
        self.rev_value_label = QLabel('1')
        self.rev_slider = QSlider(Qt.Orientation.Horizontal)
        self.rev_slider.setMinimum(1)    # 1 revolution
        self.rev_slider.setMaximum(12)   # 12 revolutions
        self.rev_slider.setValue(1)      # 1 revolution (default)
        self.rev_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.rev_slider.setTickInterval(1)
        self.rev_slider.valueChanged.connect(self.on_revolution_changed)
        rev_layout.addWidget(rev_label)
        rev_layout.addWidget(self.rev_slider)
        rev_layout.addWidget(self.rev_value_label)
        right_layout.addLayout(rev_layout)

        # Export button
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        self.export_button = QPushButton('Export to SVG')
        self.export_button.setMinimumWidth(150)
        self.export_button.clicked.connect(self.on_export_clicked)
        export_layout.addWidget(self.export_button)
        export_layout.addStretch()
        right_layout.addLayout(export_layout)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([800, 800])

    def on_r_changed(self, value):
        """Handle R slider change."""
        r_value = value / 100.0
        self.r_value_label.setText(f'{r_value:.2f}')
        self.joukowsky_canvas.update_parameters(R=r_value)
        self.revolution_canvas.update_joukowsky_parameters(R=r_value)

    def on_x_changed(self, value):
        """Handle X center slider change."""
        x_value = value / 100.0
        self.x_value_label.setText(f'{x_value:.2f}')
        self.joukowsky_canvas.update_parameters(x_center=x_value)
        self.revolution_canvas.update_joukowsky_parameters(x_center=x_value)

    def on_y_changed(self, value):
        """Handle Y center slider change."""
        y_value = value / 100.0
        self.y_value_label.setText(f'{y_value:.2f}')
        self.joukowsky_canvas.update_parameters(y_center=y_value)
        self.revolution_canvas.update_joukowsky_parameters(y_center=y_value)

    def on_scale_changed(self, value):
        """Handle scale slider change."""
        scale_value = value / 100.0
        self.scale_value_label.setText(f'{scale_value:.2f}')
        self.joukowsky_canvas.update_parameters(scale=scale_value)
        self.revolution_canvas.update_joukowsky_parameters(scale=scale_value)

    def on_offset_changed(self, value):
        """Handle Y offset slider change."""
        offset_value = value / 100.0
        self.offset_value_label.setText(f'{offset_value:.2f}')
        self.revolution_canvas.update_y_offset(offset_value)

    def on_revolution_changed(self, value):
        """Handle number of revolutions slider change."""
        self.rev_value_label.setText(f'{value}')
        self.revolution_canvas.update_n_revolutions(value)

    def on_export_clicked(self):
        """Handle export button click."""
        # Generate default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        n_rev = self.revolution_canvas.n_revolutions
        default_filename = f"spinpak_logo_{n_rev}rev_{timestamp}.svg"

        # Open file dialog
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logo to SVG",
            default_filename,
            "SVG Files (*.svg);;All Files (*)"
        )

        if filename:
            try:
                # Ensure .svg extension
                if not filename.lower().endswith('.svg'):
                    filename += '.svg'

                # Export to SVG
                success = self.revolution_canvas.export_to_svg(filename)

                if success:
                    QMessageBox.information(
                        self,
                        "Export Successful",
                        f"Logo exported successfully to:\n{filename}"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export logo:\n{str(e)}"
                )


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    app = QApplication(sys.argv)
    window = SpinPAKApp()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
