import gpxpy


def slice_gpx_at_points(source_gpx, other_gpx=None):
    """ Takes all tracks segments found in source_gpx and splits them up by
    taking all waypoints in other_gpx (or source_gpx if other_gpx is None) and
    finding the track points of source_gpx closest to these points and taking
    these as the points to cut the tracks.
    
    Arguments:
        `source_gpx`: gpxpy.GPX
        `other_gpx`: gpxpy.GPX or None
    
    Returns:
        a new gpxpy.GPX object with the now-split segments as separate tracks
        and all identified cut points as waypoints
    """

    if not other_gpx:
        other_gpx = source_gpx.clone()
    
    out_gpx = gpxpy.gpx.GPX()

    # GPX.split() is done in place, so we'll copy the source not to modify it
    temp_gpx = gpxpy.gpx.GPX()
    temp_gpx.tracks = source_gpx.tracks[:]

    for point in other_gpx.waypoints:
        nearest_point_on_track = temp_gpx.get_nearest_location(gpxpy.geo.Location(latitude = point.latitude,
                                                                                 longitude = point.longitude))
        
        cut_point = gpxpy.gpx.GPXWaypoint(latitude = nearest_point_on_track.location.latitude,
                                          longitude = nearest_point_on_track.location.longitude,
                                          elevation = nearest_point_on_track.location.elevation)

        # split at the closest point on the closest track segment
        temp_gpx.split(track_no = nearest_point_on_track.track_no,
                      track_segment_no = nearest_point_on_track.segment_no,
                      track_point_no = nearest_point_on_track.point_no)

        # splitting causes a hole between the last and next first point,
        # therefore we add the split point to the next (new) segment as well.
        (temp_gpx
            .tracks[nearest_point_on_track.track_no]
            .segments[nearest_point_on_track.segment_no + 1]
            .points.insert(0, 
                gpxpy.gpx.GPXTrackPoint(latitude = cut_point.latitude,
                                        longitude = cut_point.longitude,
                                        elevation = cut_point.elevation)
            )
        )

        # store the cut point in the output
        out_gpx.waypoints.append(cut_point)
    
    # every new segment should be its own track (for analysis, display etc.)
    # so let's take all tracks and all segments in the temporary gpx and turn
    # them into tracks with one segment each.
    tracker = 0
    for track in temp_gpx.tracks:
        for segment in track.segments:
            out_track = gpxpy.gpx.GPXTrack(name = 'track{}'.format(tracker))
            tracker += 1
            out_track.segments.append(segment)
            out_gpx.tracks.append(out_track)

    return out_gpx

def slice_gpx_at_interval(source_gpx, slice_interval, dist3d=True):
    """ Takes all track segments found in source_gpx and splits them up into
    segments of approximately slice_interval long (always takes the first point
    after reaching the next multiple of slice_interval; distance is counted
    cumulatively, not after the cut point to ensure more precision).

    Arguments:
        `source_gpx`: gpxpy.GPX
        `slice_interval`: a number (will be converted to int)
    
    Returns:
        a gpxpy.GPX object with the now-split segments as separate tracks  
        and all identified cut points as waypoints
    """
    out_gpx = gpxpy.gpx.GPX()

    tracker = 0
    for track in source_gpx.tracks:
        out_track = gpxpy.gpx.GPXTrack(name = 'track{}'.format(tracker))
        tracker += 1
        for segment in track.segments:
            out_segment = gpxpy.gpx.GPXTrackSegment()

            # we need a previous_point to calculate distances later on
            # for the first point, it will be itself
            previous_point = segment.points[0]

            # we store both a cumulative distance since the start of the segment
            # as well as the distance since the last cut point
            cumulative_distance = 0
            distance_since_slice = 0

            for point in segment.points:
                if dist3d:
                    current_distance = point.distance_3d(previous_point)
                else:
                    current_distance = point.distance_2d(previous_point)
                
                cumulative_distance += current_distance
                distance_since_slice += current_distance
                
                # we always add a point to a segment, which we then add to the track
                # since there will be points in the track after the last slice point as well
                # and we don't want to lose that part of the track
                out_segment.points.append(point)

                # when we pass the slice interval:
                if distance_since_slice > int(slice_interval):
                    distance_since_slice = 0

                    # store the point as a waypoint
                    out_gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(latitude = point.latitude,
                                                                    longitude = point.longitude,
                                                                    elevation = point.elevation))
                    
                    # if we arrive at a slice point, finish the currently
                    # running segment AND track and initialize a clean one
                    # for each, add the current point to the new segment 
                    # to ensure continuity
                    out_track.segments.append(out_segment)
                    out_gpx.tracks.append(out_track)
                    out_track = gpxpy.gpx.GPXTrack(name = 'track{}'.format(tracker))
                    tracker += 1
                    out_segment = gpxpy.gpx.GPXTrackSegment()
                    out_segment.points.append(point)

                previous_point = point
            out_track.segments.append(out_segment)
        out_gpx.tracks.append(out_track)

    return out_gpx

def parse_gpx(file):
    return gpxpy.parse(file)