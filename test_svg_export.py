#!/usr/bin/env python3
"""
Quick test script to verify SVG export functionality
Creates a sample logo and exports it to SVG
"""

import sys
import numpy as np
from spinpak_interactive_app import (
    generate_revolution_shape,
    plot_joukowsky,
    rotate
)
import svgwrite

def test_export():
    """Test SVG export with default parameters."""
    print("Generating revolution shape...")
    revolution_paths = generate_revolution_shape()

    print("Generating Joukowsky airfoil...")
    R = 0.85
    x_center = -0.1
    y_center = 0.23
    y_offset = 0.0
    n_revolutions = 3

    x, y = plot_joukowsky(R, x_center, y_center)
    y_adjusted = y + y_offset
    airfoil_points = np.column_stack([x, y_adjusted])

    print(f"Creating {n_revolutions}× revolution pattern...")
    all_points = []

    # Add revolution shape points
    for path in revolution_paths:
        all_points.extend(path)

    # Add airfoil points with revolutions
    angle_step = 360.0 / n_revolutions
    for i in range(n_revolutions):
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

    # Create SVG
    filename = "test_spinpak_logo_3rev.svg"
    scale = 300
    svg_width = width * scale
    svg_height = height * scale

    print(f"Creating SVG: {filename}")
    dwg = svgwrite.Drawing(filename, size=(f'{svg_width}px', f'{svg_height}px'),
                           viewBox=f'{min_x - padding} {min_y - padding} {width} {height}')

    # Add background
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
    print("Drawing revolution shape...")
    for path in revolution_paths:
        path_data = points_to_path(path)
        dwg.add(dwg.path(d=path_data,
                       stroke='blue',
                       stroke_width=0.01,
                       fill='none',
                       opacity=0.6))

    # Draw airfoils (red)
    print(f"Drawing {n_revolutions} airfoils...")
    for i in range(n_revolutions):
        angle = i * angle_step
        rotated_airfoil = rotate(airfoil_points, angle, center=(0, 0))
        path_data = points_to_path(rotated_airfoil)
        dwg.add(dwg.path(d=path_data,
                       stroke='red',
                       stroke_width=0.015,
                       fill='none',
                       opacity=0.8))

    # Add metadata
    dwg.add(dwg.text(f'SpinPAK Logo - {n_revolutions}× Revolution',
                    insert=(min_x - padding + 0.05, min_y - padding + 0.15),
                    font_size='0.1',
                    fill='gray'))

    print("Saving SVG...")
    dwg.save()
    print(f"✓ Successfully created: {filename}")
    print(f"  Size: {svg_width:.0f}px × {svg_height:.0f}px")
    print(f"  ViewBox: {min_x - padding:.2f} {min_y - padding:.2f} {width:.2f} {height:.2f}")

if __name__ == "__main__":
    test_export()
