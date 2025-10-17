# SpinPAK Interactive Application

A PyQt6 application for interactive visualization and manipulation of Joukowsky airfoils and revolution shapes.

## Features

### Left Panel: Joukowsky Airfoil Editor
- **Interactive plot** of the Joukowsky airfoil
- **Four sliders** to adjust airfoil parameters in real-time:
  - **Radius (R)**: Controls the size of the generating circle (range: 0.50 - 1.20)
  - **X Center**: Adjusts the horizontal position of the generating circle (range: -0.50 - 0.50)
  - **Y Center**: Adjusts the vertical position of the generating circle (range: 0.00 - 0.50)
  - **Scale**: Uniformly scales the entire airfoil (range: 0.10 - 3.00)
    - 1.00 = original size
    - < 1.00 = smaller airfoil
    - > 1.00 = larger airfoil

### Right Panel: Revolution Shape with Airfoil
- **3× 120° revolution pattern** (SpinPAK logo base shape) displayed in blue
- **Joukowsky airfoil** overlaid on the revolution shape in red
- **Y Offset slider**: Vertically shifts the airfoil position (range: -1.00 - 1.00)
- **Number of Revolutions slider**: Create multiple rotated copies of the airfoil (range: 1 - 12)
  - 1 revolution: Single airfoil
  - 2 revolutions: Two airfoils at 0° and 180°
  - 3 revolutions: Three airfoils at 0°, 120°, and 240°
  - And so on...
- **Export to SVG button**: Save the current logo design as a scalable vector graphics file
  - Automatic filename with timestamp and revolution count
  - High-quality vector output suitable for production use
- **Synchronized with left panel**: Changes to airfoil parameters in the left panel automatically update the right panel

## Installation

1. Make sure you have the required dependencies:
```bash
pip install -r requirements.txt
```

The main requirements are:
- PyQt6
- matplotlib
- numpy
- scipy
- shapely

## Usage

### Running the Application

From the project directory:
```bash
python spinpak_interactive_app.py
```

Or with virtual environment:
```bash
source venv/bin/activate
python spinpak_interactive_app.py
```

### Controls

1. **Adjust Joukowsky airfoil shape**:
   - Move the sliders in the left panel to change:
     - **R**: Base radius of the generating circle
     - **X Center**: Horizontal offset (affects airfoil thickness/camber)
     - **Y Center**: Vertical offset (affects airfoil curvature)
     - **Scale**: Overall size multiplier
   - The airfoil shape updates in real-time in both panels

2. **Position the airfoil on the revolution shape**:
   - Use the "Airfoil Y Offset" slider in the right panel
   - This moves the entire airfoil vertically without changing its shape

3. **Create airfoil revolutions**:
   - Use the "Number of Revolutions" slider in the right panel
   - Select from 1 to 12 revolutions
   - Each airfoil is evenly spaced around 360°
   - Examples:
     - 3 revolutions: Creates a pattern matching the base shape's 3-fold symmetry
     - 6 revolutions: Creates a denser pattern with 6 airfoils

4. **Export your logo**:
   - Click the "Export to SVG" button in the right panel
   - Choose where to save the file (default name includes timestamp and revolution count)
   - The SVG file contains the complete logo with both the revolution shape and airfoils
   - Output is scalable vector graphics - perfect for any size without quality loss

5. **Visual feedback**:
   - All sliders show current values next to them
   - Both graphs automatically rescale to maintain proper aspect ratio
   - Grid lines help with alignment and positioning

## Application Structure

The application consists of:
- **JoukowskyCanvas**: Matplotlib canvas for displaying the airfoil
- **RevolutionCanvas**: Matplotlib canvas for displaying the combined revolution shape and airfoil
- **SpinPAKApp**: Main window that coordinates both panels and slider controls

## Technical Details

### Joukowsky Airfoil Generation
The Joukowsky transformation maps a circle in the complex plane to an airfoil shape:
- A circle with radius R and center (x_center, y_center) is transformed
- The transformation is: z = w + a²/w, where a = R

### Revolution Shape
The revolution shape is generated from the `simplified_logo.ipynb` notebook:
- Base shape with rounded corners
- Reflected at 150° angle
- Rotated at 0°, 120°, and 240° to create the 3-fold pattern

## Tips

- Start with default values to see a well-formed airfoil
- Small changes to X Center and Y Center have significant effects on airfoil shape
- Use the **Scale slider** to make the airfoil larger or smaller relative to the revolution shape
  - Scale 0.5 = half size (good for subtle details)
  - Scale 1.0 = original size (default)
  - Scale 2.0 = double size (good for bold designs)
- Use Y Offset to position the airfoil at different locations on the revolution pattern
- The airfoil maintains its shape when moved with Y Offset; use the left panel sliders to change the shape itself
- Try 3 revolutions to match the 3-fold symmetry of the base SpinPAK shape
- Experiment with different numbers of revolutions (2, 4, 6, 8, 12) for various symmetric patterns
- Adjust all parameters to your liking before exporting - the SVG captures exactly what you see
- SVG files can be opened in any vector graphics editor (Inkscape, Adobe Illustrator, etc.) for further refinement

## Export Format

The exported SVG files include:
- **Revolution shape paths** in blue with 60% opacity
- **Airfoil paths** in red (80% opacity for multiple revolutions)
- **Proper scaling**: 300 pixels per unit for high resolution
- **ViewBox**: Automatically calculated to fit all elements with padding
- **Metadata**: Title showing number of revolutions
- **White background** for easy viewing and printing

## Future Enhancements

Possible improvements:
- Add PNG export option
- Add X offset slider for horizontal positioning
- Add rotation slider for individual airfoil orientation
- Add scaling control for the airfoil size
- Color customization for shapes
- Fill options for closed paths
- 3D visualization option
