import argparse
import os
import sys

import gpxslicer
from gpxslicer import slicer

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
                        dest="slice_distance", required=False, type=int, metavar="METERS",
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


    args = parser.parse_args()

    if args.inputfile:
        input_data = open(args.inputfile, 'r')
    else:
        input_data = sys.stdin.read()     

    sourcedata = slicer.parse_gpx(input_data)

    if args.slice_distance:
        result = slicer.slice_gpx_at_interval(sourcedata, args.slice_distance)
    elif args.slice_file:
        result = slicer.slice_gpx_at_points(sourcedata, slicer.load_gpx(args.slice_file))
    elif args.slice_waypoints:
        result = slicer.slice_gpx_at_points(sourcedata)

    if not args.quietly:
        p = 0
        for t in result.tracks:
            for s in t.segments:
                p += len(s.points)
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