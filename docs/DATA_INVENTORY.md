# Data Inventory

Round 00 inventory is intentionally lightweight. It records file names, byte sizes, and CSV headers
only. It does not parse large GTFS files or load `shapes.txt` or `stop_times.txt` into memory.

## Local TfNSW data observed

Static TfNSW GTFS data is already present under:

`data/raw/tfnsw/gtfs_static/`

Optional supporting material is also present under:

- `data/raw/tfnsw/gtfs_realtime_trip_updates/`
- `data/raw/tfnsw/gtfs_realtime_vehicle_positions/`
- `data/raw/tfnsw/station_entries_exits/`
- `data/raw/tfnsw/specs/`

## Static GTFS files

| File                 |    Size bytes | Header                                                                                                                                      |
| -------------------- | ------------: | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `agency.txt`         |        58,336 | `agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone`                                                                 |
| `calendar.txt`       |       143,779 | `service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date`                                                   |
| `calendar_dates.txt` |       868,292 | `service_id,date,exception_type`                                                                                                            |
| `levels.txt`         |           162 | `level_id,level_index,level_name`                                                                                                           |
| `notes.txt`          |        78,148 | `note_id,note_text`                                                                                                                         |
| `pathways.txt`       |       426,341 | `pathway_id,from_stop_id,to_stop_id,pathway_mode,is_bidirectional,traversal_time`                                                           |
| `routes.txt`         |     1,250,327 | `route_id,agency_id,route_short_name,route_long_name,route_desc,route_type,route_color,route_text_color,exact_times`                        |
| `shapes.txt`         | 1,004,104,020 | `shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence,shape_dist_traveled`                                                                  |
| `stop_times.txt`     |   437,809,794 | `trip_id,arrival_time,departure_time,stop_id,stop_sequence,stop_headsign,pickup_type,drop_off_type,shape_dist_traveled,timepoint,stop_note` |
| `stops.txt`          |    16,942,457 | `stop_id,stop_code,stop_name,stop_lat,stop_lon,location_type,parent_station,wheelchair_boarding,level_id,platform_code`                     |
| `trips.txt`          |    29,017,575 | `route_id,service_id,trip_id,shape_id,trip_headsign,direction_id,block_id,wheelchair_accessible,route_direction,trip_note,bikes_allowed`    |

## Deferred data interpretation

- Realtime data is optional and deferred.
- Station entry/exit data is monthly calibration material, not realtime passenger demand.
- The final Sydney subset remains undecided.
- The static feed must be checked for calendar coverage before selecting a demonstration date.
