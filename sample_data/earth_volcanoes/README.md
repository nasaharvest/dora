```python
import rasterio
import rasterio.features
import fiona

import matplotlib.pyplot as plt
%matplotlib inline
```

Load the ASTER thermal image using rasterio.


```python
img_name = 'AST_08_00310252015145234_20170919180811_13210.SurfaceKineticTemperature.KineticTemperature.tif'
```


```python
with rasterio.open(img_name) as src:
    # Print the raster metadata
    print(src.meta)
    # Read the first (and only) band
    img = src.read(1)
```

    {'driver': 'GTiff', 'dtype': 'uint16', 'nodata': None, 'width': 830, 'height': 700, 'count': 1, 'crs': CRS.from_epsg(32750), 'transform': Affine(89.01411239141112, 13.28487091278009, 281279.41706948756,
           13.28487091278009, -89.01411239141112, 9073854.504899446)}



```python
plt.imshow(img, cmap='magma')
```




    <matplotlib.image.AxesImage at 0x7f9ca8210898>




![png](output_4_1.png)


The volcanic thermal feature (VTF) or anomaly is in the top right corner.


```python
plt.imshow(img[0:100,550:650], cmap='magma')
```




    <matplotlib.image.AxesImage at 0x7f9cf99cbeb8>




![png](output_6_1.png)


Load the reference shapefile that defines where the anomaly is located.


```python
shp_path = 'ref/Agung102515hotspot.shp'
```


```python
with fiona.open(shp_path, 'r') as shapefile:
    shapes = [feature['geometry'] for feature in shapefile]
```

Convert the shapes to a raster so we can compare directly with our image.


```python
vtf = rasterio.features.rasterize(shapes, out_shape=img.shape, transform=src.transform)
```


```python
plt.imshow(vtf)
```




    <matplotlib.image.AxesImage at 0x7f9ca8382a58>




![png](output_12_1.png)



```python
plt.imshow(vtf[0:100,550:650])
```




    <matplotlib.image.AxesImage at 0x7f9cb80ea9b0>




![png](output_13_1.png)


Plot the known anomaly shape on top of the raster.


```python
plt.imshow(img[0:100,550:650], cmap='magma')
plt.imshow(vtf[0:100,550:650], cmap='magma', alpha=0.2)
```




    <matplotlib.image.AxesImage at 0x7f9cb811a550>




![png](output_15_1.png)

