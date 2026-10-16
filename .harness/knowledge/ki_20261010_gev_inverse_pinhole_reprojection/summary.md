# Equirectangular Inverse-Sampling Pinhole Camera Reprojection Engine

## Mathematical Formulation
Forward projection iterates over spherical equirectangular coordinates $(	heta, \phi)$ and maps them to planar camera pixel coordinates $(u, v)$. In areas of camera magnification or high field-of-view, this produces severe pixel gaps and raster tearing.

`tools/pano-pinhole.mjs` implements **Inverse Mapping**:
1. Iterate over every output image pixel coordinate $(x, y) \in [0, W] 	imes [0, H]$.
2. Normalize $(x, y)$ to normalized device coordinates (NDC) $[-1, 1]$.
3. Apply camera intrinsics (focal length $f = rac{W}{2 	an(	ext{HFOV}/2)}$) and camera rotation matrix $\mathbf{R}(	ext{heading}, 	ext{pitch}, 	ext{roll})$ to compute ray direction vector $\mathbf{v} = (v_x, v_y, v_z)$.
4. Compute spherical angles:
   $$\lambda = 	ext{atan2}(v_x, v_z), \quad \phi = 	ext{asin}\left(rac{v_y}{\|\mathbf{v}\|}ight)$$
5. Sample input equirectangular texture at $(\lambda, \phi)$ via 4-point bilinear interpolation.
6. Guarantees 100% fill rate with zero holes or tearing at any zoom or tilt angle.

## Provenance & Isnad Lineage
- Primary Implementation: `D:\GitHub\cloned\gods-eye-view\tools\pano-pinhole.mjs`
- Upstream Panorama Stitcher: `D:\GitHub\cloned\gods-eye-view\tools\streetview-panorama.mjs`
