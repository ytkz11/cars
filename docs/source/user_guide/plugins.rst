.. include:: ../common.rst

.. _plugins:

=======
Plugins
=======

This section describes optional plugins possibilities of CARS. 

.. note::
    
    Work in progress !

.. _plugin_geometry_shareloc:

Shareloc Geometry plugin
========================

By default, the geometry functions in CARS are run through |otb|.

Another geometry library called `Shareloc`_ is installed with CARS and can be configured to be used as another option.

To use Shareloc library, CARS input configuration should be defined as :

.. code-block:: json

    {
      "inputs": {
        "sensors": {
          "one": {
            "image": "img1.tif",
            "geomodel": "img1.geom",
            "geomodel_type": "RPC"
          },
          "two": {
            "image": "img2.tif",
            "geomodel": "img2.geom",
            "geomodel_type": "RPC"
          }
        },
        "pairing": [["one", "two"]],
        "initial_elevation": "path/to/srtm_file"
      },
      "output": {
        "out_dir": "outresults"
      },
      "applications": {
        "grid_generation": {
          "method": "epipolar",
          "geometry_loader": "SharelocGeometry"
        },
        "triangulation": {
          "method": "line_of_sight_intersection",
          "geometry_loader": "SharelocGeometry"
        }
      }
    }

The standards parts are described in CARS :ref:`configuration`.

The particularities in the configuration file are:

* **geomodel**: field contain the paths to the geometric model files related to `img1` and `img2` respectively. These files have to be supported by the Shareloc library.
* **geomodel_type**: Depending on the nature of the geometric models indicated above, this field as to be defined as `RPC` or `GRID`. By default, "RPC"
* **initial_elevation**: Shareloc must have **a file**, typically a SRTM tile (and **not** a directory as |otb| default configuration !!)
* **geometry_loader**: field in `grid_generation` and `triangulation` applications configured to "SharelocGeometry" to use Shareloc plugin.


.. note::

  This library is foreseen to replace |otb| default in CARS for maintenance and installation ease.
  Be aware that geometric models must therefore be opened by shareloc directly in this case, and supported sensors may evolve.




