# gpxslicer

gpxslicer slices GPX tracks at a given interval or at a list of provided cut points.

## Installation

The best way to install gpxslicer is via pip: `pip install gpxslicer`. You can alternatively install it from the source code: `python setup.py install`.

## Usage

### Command line

gpxslicer is primarily intended to be used as a command line tool (with support for redirection and piping data in/out).

`gpxslicer -i in.gpx -d 5000 > out.gpx` would, for example, take the tracks in `infile.gpx`, split them at every five kilometers, then pipe the results into `out.gpx`.

Full description of command line options:

| flag | command | description |
|------|----------------|-----------------------------------------------------------------------------------------------------------------|
| -h | --help | Show the help. |
| -i | --input | Specify the input GPX file with tracks to be sliced.  If not given, input is read from stdin. |
| -o | --output | Specify the output GPX file. If not given,  input is written to stdout. |
| -d | --distance | Slice tracks at every DISTANCE meters. |
| -e | --external | Slice tracks at waypoints found in EXTERNAL file. |
| -w | --waypoints | Slice tracks at waypoints found in INPUT. |
|  | --no-tracks | Do not store sliced tracks in the output. Useful when slicing using `-d` and only the cut points are of interest. |
|  | --no-waypoints | Do not store cut points in the output. Useful when slicing using `-e` or `-w` so the points are already (approximately) known. |
| -q | --quietly | Do not display status messages (that are normally sent to stderr). |

#### Slicing at intervals

When using `-d`, gpxslicer goes through each track and track segment separately (always restarting the distance counter when a new track or track segment starts in the input file). 

Cut points are not interpolated but chosen from available points on the track. Therefore, if there are very few points in the track or the chosen interval is small, there can be a significant variation in the actual length of the cut segments. There should be no major problems with sufficiently many track points and large slice distances.

#### Slicing at waypoints

When using `-e` or `-w`, gpxslicer uses the `get_nearest_location` method from the GPX class of gpxpy. This finds the point of the tracks stored in the input file that is closest to the given slice point, and then splits the track there. Finally, it duplicates this point into the new track to prevent a gap. When the slice points are very far from the track, there can be unexpected or insensible results.

Note that all waypoints in the gpx file will be used, so any unnecessary waypoints should be removed beforehand.

### Python package

The two main functions, `slice_gpx_at_points()` and `slice_gpx_at_interval()` can be accessed by

```python
from gpxslicer import slicer
slicer.slice_gpx_at_interval(gpx_data, interval)
slicer.slice_gpx_at_points(gpx_data)
```

Detailed documentation of these functions can be found in the code.

## More info

Read more about this package, including the motivation to write it [on my blog](https://hann.io/articles/2020/introducing-gpxslicer/).

