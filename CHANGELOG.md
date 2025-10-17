# SpinPAK Interactive Application - Changelog

## Version 1.1 (2025-10-15)

### ✨ New Features
- **Scale Slider** added to Left Panel
  - Range: 0.10 - 3.00
  - Default: 1.00 (original size)
  - Uniformly scales the entire Joukowsky airfoil
  - Works independently of R, X Center, and Y Center parameters
  - Updates both panels in real-time

### 🎯 Use Cases for Scale
- **Scale < 1.0**: Create subtle, delicate airfoil patterns
  - Example: Scale 0.5 for fine details within the revolution shape
- **Scale = 1.0**: Default size, well-balanced with revolution shape
- **Scale > 1.0**: Create bold, prominent airfoil patterns
  - Example: Scale 2.0 for airfoils extending beyond the revolution shape

### 🔧 Technical Details
- Modified `plot_joukowsky()` function to accept scale parameter
- Updated `JoukowskyCanvas` class with scale attribute
- Updated `RevolutionCanvas` class with scale attribute
- Modified SVG export to include scaled airfoils
- Added `on_scale_changed()` event handler

### 📝 Files Modified
- `spinpak_interactive_app.py`: Core application logic
- `README_SpinPAK_App.md`: User documentation
- `FEATURES.md`: Feature summary

---

## Version 1.0 (2025-10-15)

### 🎉 Initial Release

#### Core Features
- **Dual-panel interface**
  - Left: Joukowsky airfoil editor
  - Right: Revolution shape with airfoil overlay

#### Joukowsky Airfoil Editor
- **Radius (R) Slider**: 0.50 - 1.20
- **X Center Slider**: -0.50 - 0.50
- **Y Center Slider**: 0.00 - 0.50

#### Revolution Controls
- **Y Offset Slider**: -1.00 - 1.00 (vertical positioning)
- **Number of Revolutions Slider**: 1 - 12
  - Even angular spacing (360° / N)
  - Examples: 3 rev, 6 rev, 12 rev patterns

#### SVG Export
- High-quality vector output (300 px/unit)
- Auto-generated filenames with timestamp
- Includes revolution shape (blue) and airfoils (red)
- White background
- Metadata text

#### User Experience
- Real-time preview in both panels
- Synchronized parameter updates
- Grid overlay for alignment
- Equal aspect ratio maintenance
- Success/error dialogs

---

## Future Enhancements

### Planned Features
- [ ] PNG export option
- [ ] X offset slider for horizontal positioning
- [ ] Individual airfoil rotation slider
- [ ] Color customization UI
- [ ] Fill/stroke style options
- [ ] Multiple airfoil layers with different parameters
- [ ] 3D visualization mode
- [ ] Preset library (save/load configurations)
- [ ] Undo/redo functionality
- [ ] Live animation of parameter changes

### Possible Improvements
- Performance optimization for high revolution counts
- Zoom/pan controls for canvases
- Export to other formats (PDF, EPS, DXF)
- Batch export with parameter sweeps
- Command-line interface for automation
- Plugin system for custom transformations

---

## Bug Fixes

### Version 1.1
- No bugs reported yet

### Version 1.0
- No bugs in initial release

---

## Breaking Changes

### Version 1.1
- None (backward compatible)

### Version 1.0
- Initial release (no previous version)

---

## Dependencies

### Required
- PyQt6 >= 6.4.0
- matplotlib >= 3.5.0
- numpy >= 1.21.0
- scipy >= 1.7.0
- shapely >= 1.8.0
- svgwrite >= 1.4.0

### Optional
- None

---

## Installation Notes

No changes required for upgrade from v1.0 to v1.1.
Simply restart the application to access the new Scale slider.

---

## Acknowledgments

Built on the foundation of `simplified_logo.ipynb` notebook.
Uses Joukowsky transformation for airfoil generation.
Revolution shape generation from SpinPAK logo design.
