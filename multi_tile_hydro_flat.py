from demLib import Raster, Vector, Common


if __name__ == '__main__':

    multi_lake_tiles = 'multi_lake_tiles.shp'
    tile_file = 'cgrid_tile_file.shp'
    out_shpfile = 'multi_tile_lake_summary.shp'
    raster_file_dir = 'raster_file_dir/'

    buffer = 2000
    max_ntiles = 69

    stats = ['mean', 'std_dev'] + list('pctl_{}'.format(str(i*5)) for i in range(0, 21))

    multi_vec = Vector(multi_lake_tiles)
    tile_vec = Vector(tile_file)

    vec_outside_buffer = Vector(geom_type=3,
                                spref_str=multi_vec.spref_str)

    vec_outside_buffer.add_field('filename', 'string', width=35)
    vec_outside_buffer.add_field('orig_id', 'string', width=50)
    vec_outside_buffer.add_field('n_tiles', 'int')

    for tile_idx, tile_num in enumerate(range(max_ntiles)):
        vec_outside_buffer.add_field('tile{}'.format(str(tile_idx + 1)),
                                     'string',
                                     width=10)

    vec_tile_dict = {}

    for vec_idx in range(multi_vec.nfeat):

        lake_geom = Vector.get_osgeo_geom(multi_vec.wktlist[vec_idx])

        tile_names = list(multi_vec.attributes[vec_idx]['tile{}'.format(tile_idx + 1)]
                          for tile_idx in range(multi_vec.attributes['n_tiles']))

        tile_idxs = []
        for tile_name in tile_names:

            tile_idx = next((tile_idx for tile_idx in range(len(tile_vec.nfeat))
                             if tile_vec.attributes["grid_id"] == tile_name), None)
            if tile_idx is not None:
                tile_idxs.append(tile_idx)

        crossing_tile_idxs = []
        if len(tile_idxs) > 0:
            for tile_idx in tile_idxs:
                tile_geom = Vector.get_osgeo_geom(tile_vec.wktlist[tile_idx])

                tile_geom_buffer = tile_geom.Buffer(buffer)

                if tile_geom_buffer.Crosses(lake_geom):
                    crossing_tile_idxs.append(tile_idx)

        if len(crossing_tile_idxs) > 0:
            print('Lake {} : Tiles - {}'.format(str(multi_vec.attributes['orig_id']),
                                                ' '.join([tile_vec.attributes[tile_idx]['grid_id']
                                                          for tile_idx in crossing_tile_idxs])))
            vec_tile_dict[vec_idx] = crossing_tile_idxs

    print('Number of Multi-tile lakes: {}'.format(len(vec_tile_dict)))

    print('Extracting multi-tile values....')

    out_vec = Vector(spref_str=multi_vec.spref_str,
                     geom_type=3,
                     in_memory=True)

    out_vec.add_field('orig_id', 'string', width=50)

    for stat in stats:
        out_vec.add_field(stat, 'float', precision=8)

    for vec_idx, tile_idx_list in vec_tile_dict.items():
        vec_geom = Vector.get_osgeo_geom(multi_vec.wktlist[vec_idx])

        pixel_list = []

        for tile_idx in tile_idx_list:
            tile_geom = Vector.get_osgeo_geom(tile_vec.wktlist[tile_idx])
            vec_tile_intrsctn = vec_geom.Intersection(tile_geom)

            raster_tile = raster_file_dir + tile_vec.attributes[tile_idx]['grid_id'] + '.tif'

            vector_tile = Vector(spref_str=multi_vec.spref_str,
                                 geom_type=3,
                                 in_memory=True)
            vector_tile.add_feat(vec_tile_intrsctn)

            tile = Raster(raster_tile,
                          get_array=True)

            pixel_list += tile.vector_extract(vec_tile_intrsctn,
                                              return_values=True)

        vec_stats = dict(zip(stats, Common.get_stats(pixel_list, stats)))
        vec_attr = {'orig_id': multi_vec.attributes['orig_id'],
                    'fid': vec_idx}

        vec_attr.update(vec_stats)

        out_vec.add_feat(vec_geom, attr=vec_attr)

    out_vec.write_vector(out_shpfile)





