import argparse
import os
import sys

import gpxslicer
from gpxslicer import slicer
from gpxpy import gpx, geo
import math

def file_exists(x):
        """
        'Type' for argparse - checks that file exists but does not open it.
        https://stackoverflow.com/posts/11541495/revisions
        """
        if not os.path.exists(x):
            # Argparse uses the ArgumentTypeError to give a rejection message like:
            # error: argument input: x does not exist
            raise argparse.ArgumentTypeError("input file {0} does not exist".format(x))
        return x

def calc_gradients(seg, gradient_len, gradient_pc, dist3d):

    # No threshold data, return the old calculation
    if gradient_len is None or gradient_pc is None:
        return seg.get_uphill_downhill()

    if not seg.points:
        return 0,0

    gain = 0
    loss = 0
    notes = ""

    current = []
    is_climbing = False

    for point in seg.points:
        if not current:
            current.append(point)
        elif 1 == len(current):
            is_climbing = (current[-1].elevation < point.elevation)
            current.append(point)
        else:
            if is_climbing and (current[-1].elevation < point.elevation):
                current.append(point)
            elif not is_climbing and (current[-1].elevation > point.elevation):
                current.append(point)
            else:
                dist = current[0].distance_3d(current[-1]) if dist3d else current[0].distance_2d(current[-1])

                # Calculate the average gradient over the distance
                elev_radians = 0.0
                for i in range(len(current)-1):
                    elev_radians += geo.elevation_angle(current[i], current[i+1], True)
                elev_radians /= len(current);

                elev_pc = math.tan(abs(elev_radians)) * 100
                if dist >= gradient_len and elev_pc >= gradient_pc:

                    if not notes:
                        notes += 'Start Lat, Start Long, End Lat, End Long, Length, Angle, Grade, Gain, Loss\n'

                    elevations = [point.elevation for point in current]
                    slope_gain, slope_loss = geo.calculate_uphill_downhill(elevations)
                    gain += slope_gain
                    loss += slope_loss

                    notes += '{},{},{},{},{:.2f},{:.4f},{:.2f},{:.2f},{:.2f}\n'.format(current[0].latitude, current[0].longitude,
                        current[-1].latitude, current[-1].longitude, dist, math.degrees(elev_radians), elev_pc, slope_gain, slope_loss)

                current = [point]

    return gain, loss, notes


def main():
    parser = argparse.ArgumentParser(description='Slice GPX tracks at given intervals or near provided points.')
    parser.add_argument("-i", "--input",
                        dest="inputfile", type=file_exists,
                        help="GPX file to be sliced", metavar="FILE")
    parser.add_argument("-o", "--output",
                        dest="outputfile", required=False,
                        help="Output file to be written. If not given, will print results to stdout.", 
                        metavar="FILE")

    slice_group = parser.add_mutually_exclusive_group(required=True)

    slice_group.add_argument("-d", "--distance",
                        dest="slice_distance", required=False, nargs='+', metavar="METERS",
                        help="Slice the GPX track(s) at every METERS meters starting from the beginning")
    slice_group.add_argument("-e", "--external",
                        dest="slice_file", required=False,  metavar="EXT_WPTS_FILE", type=file_exists,
                        help="Slice the GPX track(s) at points nearest to the waypoints in the file EXT_WPTS_FILE")
    slice_group.add_argument("-w", "--waypoints",
                        dest="slice_waypoints", required=False,  action="store_true",
                        help="Use waypoints found in inputfile to slice tracks found in inputfile at the points closest to the waypoints")
                        
    parser.add_argument("--no-tracks",
                        dest="no_tracks", required=False, action="store_true",
                        help="Do not store sliced tracks in output")
    parser.add_argument("--no-waypoints",
                        dest="no_waypoints", required=False, action="store_true",
                        help="Do not store cut points in output")

    parser.add_argument("-q", "--quietly",
                        dest="quietly", required=False, action='store_true',
                        help="Don't print diagnostic messages")

    parser.add_argument("--extra-info",
                        dest="extra_info", required=False, action='store_true',
                        help="Print extra info about each segment")

    parser.add_argument("--dist3d",
                        dest="dist3d", required=False, action='store_true',
                        help="Calculate distance in 3 dimensions")

    parser.add_argument("--min-grad-len", type=float,
                        dest="min_grad_len", required=False,
                        help="Minumum gradient length threshold (m)")

    parser.add_argument("--min-grad-pc", type=float,
                        dest="min_grad_pc", required=False,
                        help="Minumum gradient percent threshold (%)")

    args = parser.parse_args()

    if args.inputfile:
        input_data = open(args.inputfile, 'r')
    else:
        input_data = sys.stdin.read()     

    sourcedata = slicer.parse_gpx(input_data)

    if args.slice_distance:
        result = slicer.slice_gpx_at_interval(sourcedata, args.slice_distance, args.dist3d)
    elif args.slice_file:
        result = slicer.slice_gpx_at_points(sourcedata, slicer.load_gpx(args.slice_file))
    elif args.slice_waypoints:
        result = slicer.slice_gpx_at_points(sourcedata)

    if not args.quietly:
        p = 0
        if args.extra_info and len(result.tracks) > 0:
            sys.stderr.write('Track,Segment,Length,Elevation Min, Elevation Max, Elevation Gain, Elevation Loss\n')
        for t in result.tracks:
            for idx, s in enumerate(t.segments, start=1):
                p += len(s.points)

                if args.extra_info:
                    ele_min, ele_max = s.get_elevation_extremes();
                    ele_gain, ele_loss, notes = calc_gradients(s, args.min_grad_len, args.min_grad_pc, args.dist3d);
                    sys.stderr.write('{0},{1},{2:.0f},{3:.0f},{4:.0f},{5:.0f},{6:.0f}\n'.format(
                            t.name,idx,s.length_3d() if args.dist3d else s.length_2d(),ele_min, ele_max, ele_gain, ele_loss))

                    if notes:
                        with open(t.name + '_notes.txt', 'w') as f:
                            f.write(notes);

        sys.stderr.write('GPX result has {t} tracks with {p} points in total and {w} waypoints.\n'.format(
            t = len(result.tracks),
            p = p,
            w = len(result.waypoints)
        ))

    if args.no_waypoints:
        result.waypoints = []
        if not args.quietly:
            sys.stderr.write('No waypoints will be saved in the output.\n')
    if args.no_tracks:
        result.tracks = []
        if not args.quietly:
            sys.stderr.write('No tracks will be saved in the output.\n')

    if args.outputfile:
        with open(args.outputfile, 'w') as o:
            o.write(result.to_xml())
            if not args.quietly:
                sys.stderr.write('Saved data to {}.\n'.format(args.outputfile))
    else:
        if not args.quietly:
            sys.stderr.write('Your GPX data will be printed to stdout.\n')
        sys.stdout.write(result.to_xml())
            
if __name__ == '__main__':
    main()
